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

'''HostKey Handling Module'''
from __future__ import print_function  # Requires Python 2.6 or higher


import os
import threading
import warnings
import paramiko.hostkeys


# Deprecated as of 1.1 - Use known_hosts rewrite instead if using this API
warnings.warn(FutureWarning('RadSSH hostkey module is no longer supported, and will be removed in release 2.0. Port existing code to use radssh.known_hosts instead.'))


class CodeMap(object):
    '''CodeMap class'''
    def __init__(self, **kwargs):
        self._fwd = kwargs
        self._reverse = {}
        for k, v in kwargs.items():
            self.__setattr__(k, v)
            self._reverse[v] = k

    def code(self, name):
        '''Given a name, return the code'''
        return self._fwd[name]

    def name(self, code):
        '''Given a code value, return the corresponding code'''
        return self._reverse[code]


verify_mode = CodeMap(
    # Different options for handling host key verification
    # Listed in decreasing order of security/paranoia
    reject=0,      # Missing keys are rejected
    prompt=1,      # Missing keys may be accepted, based on user prompt
    accept_new=2,  # Missing keys automatically accepted
    # After this point, key conflicts no longer hinder connections
    # Using these options, you become vulnerable to spoofing and
    # intercepted traffic for SSH sessions, and you don't care.
    ignore=100,    # Turn host key verification OFF
    overwrite_blindly=666  # Concentrated evil
)


def printable_fingerprint(k):
    '''Convert key fingerprint into OpenSSH printable format'''
    fingerprint = k.get_fingerprint()
    # Handle Python3 bytes or Python2 8-bit string style...
    if isinstance(fingerprint[0], int):
        seq = [int(x) for x in fingerprint]
    else:
        seq = [ord(x) for x in fingerprint]
    return ':'.join(['%02x' % x for x in seq])


class HostKeyVerifier(object):
    '''Class to control how (if) host keys are verified'''
    def __init__(self, mode='reject', known_hosts_file='~/.ssh/known_hosts'):
        self.mode = verify_mode.code(mode)
        self.hostkeys = paramiko.hostkeys.HostKeys()
        self.lock = threading.Lock()
        if mode == verify_mode.ignore:
            return
        self.known_hosts_file = os.path.expanduser(known_hosts_file)
        if os.path.exists(self.known_hosts_file):
            self.hostkeys.load(self.known_hosts_file)
        elif not os.path.exists(os.path.dirname(self.known_hosts_file)):
            os.makedirs(os.path.dirname(self.known_hosts_file))

    def verify_host_key(self, hostname, key):
        '''Verify a single hostkey against a hostname or IP'''
        if self.mode == verify_mode.ignore:
            return True
        # Special formatting for non-standard ports...
        if ':' not in hostname:
            lookup_name = hostname
        elif hostname.endswith(':22'):
            lookup_name = hostname[:-3]
        else:
            host_base, port_base = hostname.rsplit(':', 1)
            lookup_name = '[%s]:%s' % (host_base, port_base)
        # Try remainder of host verification with locking
        self.lock.acquire()
        if self.hostkeys.check(lookup_name, key):
            self.lock.release()
            return True
        host_entry = self.hostkeys.lookup(lookup_name)
        actual = printable_fingerprint(key)
        if host_entry and key.get_name() in host_entry:
            # Entry mismatch
            expected = printable_fingerprint(host_entry[key.get_name()])
            print('Host key mismatch for (%s)' % lookup_name)
            print('Expected:', expected)
            print('Got     :', actual)
            if self.mode == verify_mode.overwrite_blindly:
                print('Blindly accepting updated host key for %s' % lookup_name)
                self.hostkeys.add(lookup_name, key.get_name(), key)
                self.hostkeys.save(self.known_hosts_file)
                self.lock.release()
                return True
        else:
            # Missing key
            if self.mode == verify_mode.reject:
                self.lock.release()
                return False
            accept_and_add = False
            if self.mode == verify_mode.prompt:
                print('Unverified connection to "%s"' % lookup_name)
                print('(Host Key Fingerprint [%s])' % actual)
                answer = raw_input('Do you want to accept this key? (y/N): ')
                if answer[0].upper() == 'Y':
                    accept_and_add = True
            if self.mode in (verify_mode.accept_new, verify_mode.overwrite_blindly):
                accept_and_add = True
            if accept_and_add:
                print('Accepting new host key for %s' % lookup_name)
                self.hostkeys.add(lookup_name, key.get_name(), key)
                self.hostkeys.save(self.known_hosts_file)
                self.lock.release()
                return True
        self.lock.release()
        return False
