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
KnownHosts Module
Alternative to Paramiko HostKey checking, with better support for more
elaborate constructs in the known_hosts file format, as well as speed
improvements by not decoding all keys at load time, and avoiding checking
for duplicates.
'''
from __future__ import print_function  # Requires Python 2.6 or higher


import binascii
import os
import threading
import base64
import fnmatch
import warnings
import logging
from collections import defaultdict

import paramiko

from .console import user_input

# Keep a dict of the files we have loaded
_loaded_files = {}
_lock = threading.RLock()
unconditional_add = False


def printable_fingerprint(k):
    '''Convert key fingerprint into OpenSSH printable format'''
    fingerprint = k.get_fingerprint()
    # Handle Python3 bytes or Python2 8-bit string style...
    if isinstance(fingerprint[0], int):
        seq = [int(x) for x in fingerprint]
    else:
        seq = [ord(x) for x in fingerprint]
    return ':'.join(['%02x' % x for x in seq])


def load(filename):
    '''Load a known_hosts file, if not already loaded'''
    filename = os.path.expanduser(filename)
    with _lock:
        if filename not in _loaded_files:
            try:
                _loaded_files[filename] = KnownHosts(filename)
            except IOError as e:
                logging.getLogger('radssh.keys').info('Unable to load known_hosts from %s: %s' % (filename, str(e)))
                _loaded_files[filename] = KnownHosts()
                _loaded_files[filename]._filename = filename
    return _loaded_files[filename]


def find_first_key(hostname, known_hosts_files=['~/.ssh/known_hosts'], port=22):
    '''
    Look for first matching host key in a sequence of known_hosts files
    '''
    for f in known_hosts_files:
        x = load(f)
        try:
            entry = next(x.matching_keys(hostname, port))
            return entry
        except StopIteration:
            pass
    return None


def find_all_keys(hostname, port=22):
    '''
    Generator to yield all matching keys from all loaded files.
    If no files were loaded, autoload ~/.ssh/known_hosts
    '''
    if not _loaded_files:
        load('~/.ssh/known_hosts')
    for f in _loaded_files.values():
        for key in f.matching_keys(hostname, port):
            yield key


def verify_transport_key(t, hostname, port, sshconfig):
    '''
    With an active transport, verify the host key against known_hosts.
    Log and raise exception if key fails to pass verification.
    '''
    add_host_entry = add_ip_entry = False
    hostkey = t.get_remote_server_key()
    sys_known_hosts = load(sshconfig.get('globalknownhostsfile', '/etc/ssh/ssh_known_hosts'))
    user_known_hosts = load(sshconfig.get('userknownhostsfile', '~/.ssh/known_hosts'))
    keys = list(sys_known_hosts.matching_keys(hostname, int(port)))
    keys.extend(user_known_hosts.matching_keys(hostname, int(port)))
    for x in keys:
        if x.key.get_name() == hostkey.get_name():
            if x.key.get_fingerprint() == hostkey.get_fingerprint():
                break
            # Key types match, but not fingerprint
            logging.getLogger('radssh.keys').warning('Host %s failed SSH key validation - conflicting entry [%s:%d]' % (hostname, x.filename, x.lineno))
            raise Exception('Host %s failed SSH key validation - conflicting entry [%s:%d]' % (hostname, x.filename, x.lineno))
    else:
        # No match found
        if sshconfig.get('stricthostkeychecking', 'ask') == 'yes':
            logging.getLogger('radssh.keys').warning('No host key found for %s and StrictHostKeyChecking=yes' % hostname)
            raise Exception('Missing known_hosts entry for: %s' % hostname)
        add_host_entry = True
    # Check key for IP entry as well?
    if sshconfig.get('checkhostip', 'no') == 'yes':
        verify_ip = t.getpeername()[0]
        keys = list(sys_known_hosts.matching_keys(verify_ip, int(port)))
        keys.extend(user_known_hosts.matching_keys(verify_ip, int(port)))
        for x in keys:
            if x.key.get_name() == hostkey.get_name():
                if x.key.get_fingerprint() == hostkey.get_fingerprint():
                    break
                logging.getLogger('radssh.keys').warning(
                    'Host %s (IP %s) failed SSH key validation - conflicting entry [%s:%d]' %
                    (hostname, verify_ip, x.filename, x.lineno))
                raise Exception(
                    'Host %s (IP %s) failed SSH key validation - conflicting entry [%s:%d]' %
                    (hostname, verify_ip, x.filename, x.lineno))
        else:
            # No match found for IP
            if sshconfig.get('stricthostkeychecking', 'ask') == 'yes':
                logging.getLogger('radssh.keys').warning('No host key found for IP %s (%s) and StrictHostKeyChecking=yes' % (verify_ip, hostname))
                raise Exception('Missing known_hosts entry for IP: %s (%s)' % (verify_ip, hostname))
            add_ip_entry = True

    if not add_host_entry and not add_ip_entry:
        return
    entries = []
    if add_host_entry:
        if int(port) == 22:
            entries.append(hostname)
        else:
            entries.append('[%s]:%s' % (hostname, port))
    if add_ip_entry:
        if int(port) == 22:
            entries.append(verify_ip)
        else:
            entries.append('[%s]:%s' % (verify_ip, port))
    if sshconfig.get('stricthostkeychecking', 'ask') == 'no':
        add_key = user_known_hosts.add
    else:
        add_key = user_known_hosts.conditional_add

    if sshconfig.get('hashknownhosts', 'no') == 'yes':
        # Each hashed entry must be added independently
        for keyval in entries:
            if not add_key(keyval, hostkey, True):
                raise Exception('Declined host key for %s - aborting connection' % keyval)
    else:
        # Add host and IP entry as a single line
        if not add_key(','.join(entries), hostkey, False):
            raise Exception('Declined host key for %s - aborting connection' % ','.join(entries))


class KnownHosts (object):
    '''
    Implementation of SSH known_hosts file as a searchable object.
    Instead of Paramiko's lookup() returning a Dict (forcing a 1:1
    relation of (host, key_type) to key), KnownHosts search is an
    iterator of all matching keys, including support for markers
    @revoked and @cert-authority. See sshd man page for details.
    '''

    def __init__(self, filename=None):
        '''
        Load known_hosts file, or create an empty dictionary
        '''
        self._lines = []
        self._index = defaultdict(list)
        self._hashed_hosts = []
        self._wildcards = []
        self._filename = filename
        if filename is not None:
            self.load(filename)

    def add(self, hostname, key, hash_hostname=False):
        '''
        Add a host key entry to the table.  Any existing entries for
        ``hostname`` pair will be preserved.  Deletion or replacement
        is not implemented, but _lines entries can be flagged for
        deletion by setting entry to None.
        '''
        # Per sshd man page on known_hosts:
        # It is permissible (but not recommended) to have several lines or
        # different host keys for the same names.
        # So if called to add, it is not necessary to check for duplication
        # here, and hope that the caller is handling conflicts.
        with _lock:
            lineno = len(self._lines)
            keyval = key.get_base64()
            keytype = key.get_name()
            if hash_hostname or hostname.startswith('|'):
                if not hostname.startswith('|'):
                    # Add index entry for unhashed hostname
                    self._index[hostname].append(lineno)
                    hostname = paramiko.HostKeys.hash_host(hostname)
                else:
                    self._hashed_hosts.append((hostname, lineno))
            else:
                self._index[hostname].append(lineno)
            self._lines.append('%s %s %s' %
                               (hostname, keytype, keyval))
            if self._filename:
                self.save()
        logging.getLogger('radssh.keys').info('Added new known_hosts entry for %s (%s) to %s' % (hostname, printable_fingerprint(key), self._filename))
        return HostKeyEntry([hostname], key, lineno=lineno)

    def load(self, filename):
        '''
        Load and index keys from OpenSSH known_hosts file. In order to
        preserve lines, the text content is stored in a list (_lines),
        and indexes are used to keep line number(s) per host, as well as
        index lists for hashed hosts and wildcard matches, which would
        both need to be sequentially scanned if the host is not found
        in the primary index lookup.

        If this method is called multiple times, the host keys are appended,
        not cleared.  So multiple calls to `load` will produce a concatenation
        of the loaded files, in order.
        '''
        offset = len(self._lines)
        with open(filename, 'r') as f:
            for lineno, line in enumerate(f):
                self._lines.append(line.rstrip('\n'))
                try:
                    e = HostKeyEntry.from_line(line, lineno)
                    if e is not None:
                        # Just construct the host index entries during load
                        # Identify as hashed entry, negation, wildcard, or regular
                        # Keep the index by the source lineno (plus offset, if
                        # loading multiple files), as the matching needs the
                        # whole line for negation logic, and to pick up the
                        # optional @marker...
                        for h in e.hostnames:
                            if h.startswith('|'):
                                self._hashed_hosts.append((h, offset + lineno))
                            elif h.startswith('!'):
                                # negation - do not index
                                pass
                            elif '*' in h or '?' in h:
                                self._wildcards.append((h, offset + lineno))
                            else:
                                self._index[h].append(offset + lineno)
                except (UnreadableKey, TypeError) as e:
                    logging.getLogger('radssh.keys').error(
                        'Skipping unloadable key line (%s:%d): %s' % (filename, lineno + 1, line))
                    pass

    def save(self, filename=None):
        '''
        Save host keys into a file, in the format used by OpenSSH.  Keys added
        or modified after load will appear at the end of the file.  Original
        lines will be preserved (format and comments).  If multiple files
        were loaded, the saved file will be the concatenation of the loaded
        source files.
        '''
        if not filename:
            filename = self._filename
        with open(filename, 'w') as f:
            for line in self._lines:
                if line is not None:
                    f.write(line + '\n')

    def matching_keys(self, hostname, port=22):
        '''
        Generator for identifying all the matching HostKey entries for
        a given hostname or IP. Finds matches on exact lookup, hashed
        lookup, and wildcard matching, and pays heed to negation entries.
        '''
        if hostname and port != 22:
            hostname = '[%s]:%d' % (hostname, port)
        for lineno in self._index[hostname]:
            e = HostKeyEntry.from_line(self._lines[lineno], lineno, self._filename)
            if e and not e.negated(hostname):
                yield e
        for h, lineno in self._hashed_hosts:
            if h.startswith('|1|') and paramiko.HostKeys.hash_host(hostname, h) == h:
                e = HostKeyEntry.from_line(self._lines[lineno], lineno, self._filename)
                if e:
                    yield e
        for pattern, lineno in self._wildcards:
            if HostKeyEntry.wildcard_match(hostname, pattern):
                e = HostKeyEntry.from_line(self._lines[lineno], lineno, self._filename)
                if e and not e.negated(hostname):
                    yield e

    def check(self, hostname, key):
        '''
        Return True if the given key is associated with the given hostname
        for any non-negated matched line. If a marker is associated with the
        line, the line does not qualify as a direct key comparison, as it
        is either @revoked, or @cert-authority, which needs a different
        comparison to check.
        '''
        for e in self.matching_keys(hostname):
            if e.key.get_name() == key.get_name() and not e.marker:
                if e.key.get_base64() == key.get_base64():
                    return True
        return False

    def clear(self):
        """
        Remove all host keys from the dictionary.
        """
        self._lines = []
        self._index = defaultdict(list)
        self._hashed_hosts = []
        self._wildcards = []

    def conditional_add(self, host, key, hash_hostname=False):
        '''
        Add new host key, with confirmation by the user, which may be
        Yes, No, or All (which auto-replies Yes to all subsequent calls)
        '''
        global unconditional_add
        with _lock:
            if unconditional_add:
                self.add(host, key, hash_hostname)
            else:
                reply = ''
                fingerprint = printable_fingerprint(key)
                while reply.upper() not in ('Y', 'N', 'A'):
                    reply = user_input('Accept new %s key with fingerprint [%s] for host %s ? (y/n/a) ' % (key.get_name(), fingerprint, host))
                if reply.upper() == 'N':
                    return False
                if reply.upper() == 'A':
                    unconditional_add = True
                self.add(host, key, hash_hostname)
        return True


class UnreadableKey(Exception):
    pass


class HostKeyEntry:
    '''
    Close reimplementation of Paramiko HostKeys.HostKeyEntry, with added
    support for markers (@revoked, @cert-authority), SSH1 key format, and
    inclusion of line number for found matches.
    '''

    def __init__(self, hostnames=None, key=None, marker=None, lineno=None, filename=None):
        self.hostnames = hostnames
        self.key = key
        self.marker = marker
        self.lineno = lineno
        self.filename = filename

    @classmethod
    def from_line(cls, line, lineno=None, filename=None):
        '''
        Parses the given line of text to find the name(s) for the host,
        the type of key, and the key data.
        '''
        if not line or not line.strip():
            return None
        fields = line.strip().split(' ')
        if not fields or fields[0].startswith('#'):
            return None
        if fields[0].startswith('@'):
            marker = fields[0]
            fields = fields[1:]
        else:
            marker = None

        if len(fields) < 3:
            raise UnreadableKey('Invalid known_hosts line', line, lineno)

        names, keytype, key = fields[:3]
        names = names.split(',')

        # Decide what kind of key we're looking at and create an object
        # to hold it accordingly.
        key = key.encode('ascii')
        # SSH-2 Key format consists of 2 (text) fields
        #     keytype, base64_blob
        try:
            if keytype == 'ssh-rsa':
                key = paramiko.RSAKey(data=base64.b64decode(key))
            elif keytype == 'ssh-dss':
                key = paramiko.DSSKey(data=base64.b64decode(key))
            elif keytype == 'ecdsa-sha2-nistp256':
                key = paramiko.ECDSAKey(data=base64.b64decode(key), validate_point=False)
            elif len(fields) > 3:
                # SSH-1 Key format consists of 3 integer fields
                #     bits, exponent, modulus (RSA Only)
                try:
                    bits = int(fields[1])
                    exponent = int(fields[2])
                    modulus = long(fields[3])
                    key = paramiko.RSAKey(vals=(exponent, modulus))
                except ValueError:
                    raise UnreadableKey('Invalid known_hosts line', line, lineno, filename)
            else:
                raise UnreadableKey('Invalid known_hosts line', line, lineno, filename)
            return cls(names, key, marker, lineno, filename)
        except Exception as e:
            raise UnreadableKey('Invalid known_hosts line (%s)' % e, line, lineno, filename)

    def negated(self, hostname):
        '''
        Check if the hostname is in the entry list of hostnames as a matching
        negated pattern. This indicates that the key represented on the line
        fails to match for the given host, even if it does match other pattern(s)
        on the current line.
        '''
        for pattern in self.hostnames:
            if pattern.startswith('!'):
                if self.wildcard_match(hostname, pattern[1:]):
                    return True
        return False

    @staticmethod
    def wildcard_match(hostname, pattern):
        '''
        Match against patterns using '*' and '?' using simplified fnmatch
        '''
        # Simplified = add steps to disable fnmatch handling of [ and ]
        fn_pattern = ''
        for c in pattern:
            if c == '[':
                fn_pattern += '[[]'
            elif c == ']':
                fn_pattern += '[]]'
            else:
                fn_pattern += c
        return fnmatch.fnmatch(hostname, fn_pattern)
