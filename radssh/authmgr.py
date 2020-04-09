#
# Copyright (c) 2014, 2016, 2018 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#
'''
AuthManager module for setting up a concise, flexible collection of available
authentication possibilities to connect to multiple servers via Paramiko.
Supports loading from an authentication file that can contain passwords
or key files, and a way to match them to a host or hosts.
'''

from __future__ import print_function  # Requires Python 2.6 or higher

import os
import warnings
import fnmatch
import threading
import logging
import base64

import netaddr

with warnings.catch_warnings(record=True):
    import paramiko

from .pkcs import PKCS_OAEP, PKCSError
from .console import user_password


class PlainText(object):
    '''
    PlainText simply saves the string, and returns it. Nothing fancy.
    '''
    def __init__(self, plaintext):
        self.plaintext = plaintext

    def __str__(self):
        return self.plaintext


class RSAES_OAEP_Text(object):
    '''
    Class to permit decryption of password encoded with user's private key.
    Save the ciphertext, defer the decryption to plaintext until the
    plaintext is requested. Only decrypt on the initial get, save the result
    internally for subsequent calls.
    '''
    decoder_ring = PKCS_OAEP()

    def __init__(self, ciphertext):
        # Do base64 decode at load time - no sense deferring that potential error
        self.ciphertext = base64.b64decode(ciphertext)
        self.plaintext = None
        # Use a lock to avoid multiple threads decrypting
        self.lock = threading.Lock()

    def __str__(self):
        if self.decoder_ring.unsupported:
            return None
        with self.lock:
            if not self.plaintext:
                self.plaintext = self.decoder_ring.decrypt_binary(self.ciphertext)
        return self.plaintext


def _importKey(filename, allow_prompt=True, logger=None):
    '''
    Import a RSA or DSA key from file contents
    If the key file requires a passphrase, ask for it only if allow_prompt is
    True. Otherwise, reraise the paramiko.PasswordRequiredException. If the
    key fails to load as a RSA key, try loading as DSA key. If it fails both,
    then raises a ValueError with the reported errors from both RSA and DSA
    attempts.
    '''
    # Try RSA first
    try:
        key = paramiko.RSAKey(filename=filename)
        if logger:
            logger.debug('Loaded unprotected RSA key from %s', filename)
        return key
    except paramiko.PasswordRequiredException:
        # Need passphrase for RSA key
        if not allow_prompt:
            return RuntimeError('RSA Key is Passphrase-Protected')
        retries = 3
        while retries:
            try:
                passphrase = user_password('Enter passphrase for RSA key [%s]: ' % filename)
                key = paramiko.RSAKey(filename=filename, password=passphrase)
                if logger:
                    logger.debug('Loaded passphrase protected RSA key from %s', filename)
                return key
            except paramiko.SSHException as e:
                print(repr(e))
                retries -= 1
        return Exception('3 failed passphrase attempts for %s' % filename)
    except paramiko.SSHException as e:
        rsa_exception = e
    if logger:
        logger.debug('Failed to load %s as RSA key\n\t%s', filename, repr(rsa_exception))

    # Format error - could be ECDSA key instead...
    try:
        key = paramiko.ECDSAKey(filename=filename)
        if logger:
            logger.debug('Loaded unprotected ECDSA key from %s', filename)
        return key
    except paramiko.PasswordRequiredException:
        # Need passphrase for ECDSA key
        if not allow_prompt:
            return RuntimeError('ECDSA Key is Passphrase-Protected')
        retries = 3
        while retries:
            try:
                passphrase = user_password('Enter passphrase for ECDSA key [%s]: ' % filename)
                key = paramiko.ECDSAKey(filename=filename, password=passphrase)
                if logger:
                    logger.debug('Loaded passphrase protected ECDSA key from %s', filename)
                return key
            except paramiko.SSHException as e:
                print(repr(e))
                retries -= 1
        return Exception('3 failed passphrase attempts for %s' % filename)
    except paramiko.SSHException as e:
        ecdsa_exception = e

    if logger:
        logger.debug('Failed to load %s as ECDSA key\n\t%s', filename, repr(ecdsa_exception))

    # Format error - could be DSA key instead...
    try:
        key = paramiko.DSSKey(filename=filename)
        if logger:
            logger.debug('Loaded unprotected DSA key from %s', filename)
        return key
    except paramiko.PasswordRequiredException:
        # Need passphrase for DSA key
        if not allow_prompt:
            return RuntimeError('DSA Key is Passphrase-Protected')
        retries = 3
        while retries:
            try:
                passphrase = user_password('Enter passphrase for DSA key [%s]: ' % filename)
                key = paramiko.DSSKey(filename=filename, password=passphrase)
                if logger:
                    logger.debug('Loaded passphrase protected DSA key from %s', filename)
                return key
            except paramiko.SSHException as e:
                print(repr(e))
                retries -= 1
        return Exception('3 failed passphrase attempts for %s' % filename)
    except paramiko.SSHException as e:
        dsa_exception = e

    if logger:
        logger.debug('Failed to load %s as DSA key\n\t%s', filename, repr(dsa_exception))
    # Give up on using this key
    if logger:
        logger.error('Unable to load key from [%s] | RSA failure: %r | ECDSA failure: %r | DSA failure: %r' % (filename, rsa_exception, ecdsa_exception, dsa_exception))
    # Return, rather than raise the exception - Caller just needs something to
    # fill the deferred_keys entry with that's not a paramiko.PKey and not None.
    return RuntimeError('Unrecognized key: %s' % filename)


UNUSED_PARAMETER = object()


class AuthManager(object):
    '''Manage keys and passwords used for paramiko authentication'''
    # Next major release (2.0) change the API call to no longer support include_agent
    # and include_userkeys parameters in favor of ssh_config based options to control
    # exactly the same behavior. Issue a FutureWarning for now if these parameters are used.
    def __init__(self, default_user, auth_file='./.radssh_authfile', include_agent=UNUSED_PARAMETER, include_userkeys=UNUSED_PARAMETER, default_password=None, try_auth_none=True):
        if include_agent != UNUSED_PARAMETER:
            warnings.warn(FutureWarning('AuthManager will no longer support include_agent starting with 2.0: passed value (%s) ignored' % include_agent), stacklevel=2)
        if include_userkeys != UNUSED_PARAMETER:
            warnings.warn(FutureWarning('AuthManager will no longer support include_userkeys starting with 2.0: passed value (%s) ignored' % include_userkeys), stacklevel=2)
        self.keys = []
        self.passwords = []
        self.default_passwords = {}
        self.try_auth_none = try_auth_none
        self.logger = logging.getLogger('radssh.auth')
        self.import_lock = threading.Lock()
        if default_password:
            self.add_password(PlainText(default_password))
        self.deferred_keys = dict()
        if default_user:
            self.default_user = default_user
        else:
            self.default_user = os.environ.get('SSH_USER', os.environ['USER'])

        self.agent_connection = paramiko.Agent()

        if auth_file:
            self.read_auth_file(auth_file)

    def read_auth_file(self, auth_file):
        ''' Read in settings from an authfile. See docs for example format.'''
        try:
            with open(auth_file, 'r') as f:
                for line_no, line in enumerate(f, 1):
                    line = line.rstrip('\n\r')
                    fields = line.split('|', 2)
                    if not line.strip() or fields[0].startswith('#'):
                        continue
                    if len(fields) == 3:
                        filter = fields.pop(1)
                    else:
                        filter = None
                    data = fields[-1]
                    if fields[0] == 'password' or len(fields) == 1:
                        self.add_password(PlainText(data), filter)
                        self.logger.info('PlainText password loaded from %s (line %d)', auth_file, line_no)
                    elif fields[0] == 'PKCSOAEP':
                        try:
                            encrypted_password = RSAES_OAEP_Text(data)
                            if encrypted_password.decoder_ring.unsupported:
                                warnings.warn(RuntimeWarning(
                                    'Ignoring unusable PKCSOAEP encrypted password from %s (line %d)' %
                                    (auth_file, line_no)))
                                self.logger.error('PKCS encryption not supported by cryptography module - Ignoring encrypted password from %s (line %d)', auth_file, line_no)
                                continue
                            self.add_password(encrypted_password, filter)
                            self.logger.info('PKCS encrypted password loaded from %s (line %d)', auth_file, line_no)
                        except Exception as e:
                            warnings.warn(RuntimeWarning('Failed to load base64 PKCS encrypted password from %s (line %d)\n\t%s' % (auth_file, line_no, repr(e))))
                            self.logger.error('Failed to load base64 PKCS encrypted password from %s (line %d)\n\t%s', auth_file, line_no, repr(e))
                    elif fields[0] == 'keyfile':
                        k = os.path.expanduser(data)
                        if os.path.exists(k):
                            self.deferred_keys[k] = None
                            self.add_key(k, filter)
                            self.logger.info('Deferred load of SSH private key [%s] from %s (line %d)', k, auth_file, line_no)
                        else:
                            self.logger.error('Nonexistent private key file [%s] referenced by %s (line %d)', k, auth_file, line_no)
                            # raise ValueError('Unable to load key from [%s]' % k)
                    else:
                        warnings.warn(RuntimeWarning('Unsupported auth type [%s:%d] %s' % (auth_file, line_no, fields[0])))
                        self.logger.error('Unsupported auth type "%s" referenced in %s (line %d)', fields[0], auth_file, line_no)
        except IOError:
            # Quietly fail if auth_file cannot be read
            pass

    def add_password(self, password, filter=None):
        '''Append to list of passwords to try based on filtering, but only keep at most one default'''
        if filter:
            self.passwords.append((filter, password))
        else:
            self.default_passwords[None] = password

    def add_key(self, key, filter=None):
        '''Append to a list of explicit keys to try, separate from any agent keys'''
        self.keys.append((filter, key))

    def authenticate(self, T, sshconfig={}):
        '''
        Try available ways to authenticate a paramiko Transport.
        Attempts are made in the following progression:
        - Keys listed in ssh_config as IdentityFile
        - User keys (~/.ssh/id_rsa, id_dsa, id_ecdsa) if loaded
        - Explicit keys loaded from authfile (for matched hostname/IP)
        - Keys available via SSH Agent (if enabled)
        - Passwords loaded from authfile
        - Default password (if set)
        '''
        if T.is_authenticated():
            return
        if not T.is_active():
            T.connect()
        auth_user = sshconfig.get('user', self.default_user)
        allow_prompt = sshconfig.get('batchmode', 'no') == 'no'
        preferred_auth_types = []
        for auth_type in sshconfig.get('preferredauthentications', ['publickey', 'password']):
            if auth_type not in preferred_auth_types:
                preferred_auth_types.append(auth_type)
        # Do an auth_none() call for 3 reasons:
        #    1) Get server response for available auth mechanisms
        #    2) OpenSSH 4.3 (CentOS5) fails to send banner unless this is done
        #       http://www.frostjedi.com/phpbb3/viewtopic.php?f=46&t=168230#p391496
        #    3) https://github.com/paramiko/paramiko/issues/432 workaround requires
        #       hacky save/restore of banner to keep Transport.get_banner() content
        try:
            auth_success = False
            T.save_banner = None
            server_authtypes_supported = preferred_auth_types
            if self.try_auth_none:
                T.auth_none(self.default_user)
                # If by some miracle or misconfiguration, auth_none succeeds...
                return True
        except paramiko.BadAuthenticationType as e:
            if hasattr(T.auth_handler, 'banner'):
                T.save_banner = T.auth_handler.banner
            server_authtypes_supported = e.allowed_types

        # Go by ordering specified in ssh_config, only trying the ones accepted by the remote host
        for auth_type in preferred_auth_types:
            if auth_type not in server_authtypes_supported:
                continue
            if auth_type == 'publickey' and sshconfig.get('pubkeyauthentication', 'yes') == 'yes':
                # Try explicit keys first
                identity_keys = []
                for keyfile in sshconfig.get('identityfile', ['~/.ssh/id_rsa', '~/.ssh/id_dsa', '~/.ssh/id_ecdsa']):
                    k = os.path.expanduser(keyfile)
                    if os.path.exists(k):
                        if k not in self.deferred_keys:
                            self.deferred_keys[k] = None
                        identity_keys.append((None, k))
                auth_success = self.try_auth(T, identity_keys, False, auth_user, allow_prompt=allow_prompt)
                if auth_success:
                    break
                if sshconfig.get('identitiesonly', 'no') == 'no':
                    # Try loaded authmgr keys
                    auth_success = self.try_auth(T, self.keys, False, auth_user, allow_prompt=allow_prompt)
                    if auth_success:
                        break
                    # Next, try agent keys, if enabled
                    if self.agent_connection:
                        agent_connection = paramiko.Agent()
                        agent_keys = [(None, x) for x in agent_connection.get_keys()]
                        auth_success = self.try_auth(T, agent_keys, False, auth_user)
                        # Early versions of Paramiko would raise exception if
                        # attempting to close Agent socket if there was no running ssh-agent
                        # AttributeError: Agent instance has no attribute 'conn'
                        try:
                            agent_connection.close()
                        except AttributeError:
                            pass
                        if auth_success:
                            break
            elif (auth_type == 'password' and sshconfig.get('passwordauthentication', 'yes') == 'yes') or \
                    (auth_type == 'keyboard-interactive' and sshconfig.get('kbdinteractiveauthentication', 'yes') == 'yes'):
                # Paramiko will fake keyboard-interactive as password authentication
                auth_success = self.try_auth(T, self.passwords, True, auth_user, allow_prompt=allow_prompt)
                if auth_success:
                    break
                # Try "universal" default password if it is set
                if self.default_passwords.get(None):
                    auth_success = self.try_auth(T, [(None, self.default_passwords[None])], True, auth_user)
                retries = int(sshconfig.get('numberofpasswordprompts', 3))
                if sshconfig.get('batchmode', 'no') == 'yes':
                    retries = 0
                with self.import_lock:
                    password = self.default_passwords.get(auth_user)
                    while not auth_success and retries > 0 and T.is_active():
                        if not password:
                            password = PlainText(user_password(
                                'Please enter a password for (%s@%s) :' % (auth_user, T.getName())))
                            retries -= 1
                        auth_success = self.try_auth(T, [(None, password)], True, auth_user)
                        if auth_success:
                            # If the password worked, save it
                            self.default_passwords[auth_user] = password
                        else:
                            # Wipe password and prompt again, if able
                            print('Password incorrect')
                            password = None

        # Part 2 of save_banner workaround - shove it into the current auth_handler
        if T.save_banner:
            T.auth_handler.banner = T.save_banner
        return auth_success

    def interactive_password(self):
        self.default_passwords[None] = PlainText(user_password(
            'Please enter a password for (%s) :' % self.default_user))

    def __str__(self):
        return '<%s for %s : [%d Keys, Agent %s, %d Passwords]>' \
            % (self.__class__.__name__,
               self.default_user,
               len(self.keys),
               'Enabled' if self.agent_connection else 'Disabled',
               len(self.passwords))

    def try_auth(self, T, candidates, as_password=False, auth_user=None, allow_prompt=True):
        if not auth_user:
            auth_user = self.default_user
        for filter, value in candidates:
            if not T.is_active():
                self.logger.error('Remote dropped connection')
                return None
            if filter and filter != '*':
                remote_ip = netaddr.IPAddress(T.getpeername()[0])
                try:
                    subnet = netaddr.IPGlob(filter)
                    if remote_ip not in subnet:
                        continue
                except netaddr.AddrFormatError:
                    try:
                        subnet = netaddr.IPNetwork(filter)
                        if remote_ip not in subnet:
                            continue
                    except netaddr.AddrFormatError:
                        # Not a subnet or IPGlob - try name based matching (fnmatch style, not regex)
                        if not fnmatch.fnmatch(T.name, filter):
                            continue
            try:
                if as_password:
                    try:
                        key = str(value)
                    except Exception as e:
                        self.logger.debug('Unusable password value (%s): [%s]', str(e), repr(value))
                        continue

                    self.logger.debug('Trying password (%s) for %s', '*' * len(key), T.getpeername()[0])
                    # Quirky Force10 servers seem to request further password attempt
                    # for a second stage - retry password as long as it is listed as an option
                    while True:
                        if 'password' not in T.auth_password(auth_user, str(key)):
                            break
                else:
                    # Actual keys may not be loaded yet. Only loaded when actively used, so
                    # we don't prompt for passphrases unless we absolutely have to.
                    # Python3: paramiko.AgentKey is not hashable, but also not eligible for
                    # deferred loading, so don't try to lookup in dict as its not hashable, and
                    # can't be used as a dict key.
                    self.logger.debug('Trying private key (%s) for %s', repr(value), T.getpeername()[0])
                    if isinstance(value, paramiko.AgentKey) or value not in self.deferred_keys:
                        # Not deferred - the value IS the key
                        key = value
                    elif not self.deferred_keys[value]:
                        # Deferred, and not yet loaded - try _importKey() to load it
                        # limit to single thread for the _importKey() call
                        with self.import_lock:
                            if not self.deferred_keys[value]:
                                self.deferred_keys[value] = _importKey(value, allow_prompt=allow_prompt, logger=self.logger)
                        key = self.deferred_keys[value]
                    else:
                        # Deferred and already loaded
                        key = self.deferred_keys[value]
                    try:
                        if isinstance(key, paramiko.PKey):
                            T.auth_publickey(auth_user, key)
                        else:
                            self.logger.error('Skipping SSH key %s (%s)', value, str(key))
                    except paramiko.BadAuthenticationType as e:
                        # Server configured to reject keys, don't bother trying any others
                        return None
                if T.is_authenticated():
                    return key
            except paramiko.AuthenticationException as e:
                pass

        return None

if __name__ == '__main__':
    import sys
    from .known_hosts import printable_fingerprint
    logging.basicConfig(level=logging.ERROR)
    if not sys.argv[1:]:
        print('RadSSH AuthManager')
        print('Usage: python -m radssh.authmgr <authfile> [...]')
    for authfile in sys.argv[1:]:
        authfile = os.path.expanduser(authfile)
        sample = AuthManager(os.path.basename(authfile), auth_file=authfile, default_password='')
        print('\nLoaded authfile:', authfile)
        print(sample)
        if sample.keys:
            print('Explicit keys (%d)' % len(sample.keys))
            for filter, keyfile in sample.keys:
                if keyfile in sample.deferred_keys:
                    try:
                        key = _importKey(keyfile, allow_prompt=False)
                        key_info = '%s (%s:%d bit)' % (keyfile, key.get_name(), key.get_bits())
                    except Exception as e:
                        key_info = '%s (Passphrase-Protected)' % (keyfile)
                if not filter:
                    filter = '(ALL)'
                print('\t', key_info, 'for hosts matching:', filter)
        else:
            print('No explicit keys loaded')
        if sample.agent_connection:
            agent_keys = sample.agent_connection.get_keys()
            print('SSH Agent available (contains %d keys)' % len(agent_keys))
            for key in agent_keys:
                print('\t', key.get_name(), printable_fingerprint(key))
        else:
            print('No SSH Agent connection')
        if sample.passwords:
            print('Explicit passwords (%d)' % len(sample.passwords))
            for filter, password in sample.passwords:
                if not filter:
                    filter = '(ALL)'
                print('\t', repr(password), 'for hosts matching:', filter)
        else:
            print('No explicit passwords loaded')
        if sample.default_passwords:
            print('Authfile includes a default password [%s]' % repr(sample.default_passwords))
