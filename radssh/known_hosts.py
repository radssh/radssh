#
# Copyright (c) 2014, 2016, 2018, 2020 LexisNexis Risk Data Management Inc.
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

import os
import threading
import base64
import fnmatch
import logging
from collections import defaultdict
import pathlib
import hashlib

import paramiko

# from .console import user_input


key_generators = {
    'ssh-rsa': paramiko.RSAKey,
    'ssh-dss': paramiko.DSSKey,
    'ssh-ed25519': paramiko.Ed25519Key,
    'ecdsa-sha2-nistp256': paramiko.ECDSAKey,
    'ecdsa-sha2-nistp384': paramiko.ECDSAKey,
    'ecdsa-sha2-nistp521': paramiko.ECDSAKey,
}


class KnownHostsEntry():
    """
    Representation of a known_hosts file entry
    An entry corresponds to a single line in a file, with the following fields:
    (Optional) marker: @revoked or @cert-authority
    hostnames: comma separated list of patterns
    keytype: ssh-rsa, ssh-ecdsa-nistp256, etc.
    keyvalue: base64 encoded public key value
    (Optional) comment: remainder of line
    """
    def __init__(self, filename, linenumber, contents):
        self.filename = filename
        self.linenumber = linenumber
        self.contents = contents

        # If unable to interpret line, just keep it as a placeholder
        self.marker_value = None
        self.keytype = None
        self.keyvalue = None

        contents = contents.strip()
        if not contents or contents.startswith("#"):
            self.comment = contents
            return
        if contents.startswith("@"):
            # Marker is present
            fields = contents.split(None, 4)
            if len(fields) == 4:
                comment = ""
                marker, patterns, keytype, keyvalue = fields
            else:
                marker, patterns, keytype, keyvalue, comment = fields
            if marker not in ("@revoked", "@cert-authority"):
                raise ValueError("[{}:{}] - Invalid marker: {}".format(
                    filename, linenumber, marker
                ))
            self.marker_value = marker
        else:
            fields = contents.split(None, 3)
            if len(fields) == 3:
                comment = ""
                patterns, keytype, keyvalue = fields
            else:
                patterns, keytype, keyvalue, comment = fields
        if keytype not in key_generators:
            return
        try:
            self.keyblob = base64.b64decode(keyvalue)
        except ValueError:
            return

        self.keytype = keytype

        self.comment = comment
        self.hashed_host = None
        self.negations = []
        self.patterns = []
        self.hosts = []
        # Filter each pattern as one of:
        #   Negation: !pattern
        #   HashedEntry: |pattern
        #   WildcardEntry: contains "*" or "?"
        #   ExactMatchEntry: everything else
        for p in patterns.split(","):
            if p.startswith("!"):
                self.negations.append(p[1:])
            elif p.startswith("|1|"):
                self.hashed_host = p
            elif "*" in p or "?" in p:
                self.patterns.append(p)
            else:
                self.hosts.append(p)
        # Defer decoding of key value until it is actually needed
        self.key_value = None

    @property
    def marker(self):
        return self.marker_value

    def match(self, hostname):
        """
        Determine if the given 'hostname' matches this entry
        Fails outright if it successfully matches a negation, otherwise
        continue checking against explicit hosts, patterns or hashed_host
        """
        if not self.keytype:
            # Skip any Comment/blank/unrecognizable lines
            return False
        for p in self.negations:
            if fnmatch.fnmatch(hostname, p):
                return False
        if self.hashed_host:
            # Hash given hostname with same salt to compare
            x = paramiko.HostKeys.hash_host(hostname, self.hashed_host)
            if x == self.hashed_host:
                return True
        if hostname in self.hosts:
            return True
        for p in self.patterns:
            if fnmatch.fnmatch(hostname, p):
                return True
        return False

    @property
    def key(self):
        if not self.keytype:
            return None
        if self.key_value:
            return self.key_value
        # Do the decode
        self.key_value = key_generators[self.keytype](data=self.keyblob)
        return self.key_value

    def fingerprint(self, hash_algorithm="sha256"):
        """
        Printable fingerprint representation of the (public) key
        Can be either SHA256 (default) or legacy MD5 fingerprint
        """
        if hash_algorithm == "sha256":
            hashvalue = hashlib.sha256(self.key.asbytes()).digest()
            return "SHA256:" + base64.b64encode(hashvalue).decode()
        else:
            hashvalue = hashlib.md5(self.key.asbytes()).digest()
            return "MD5:" + ":".join(["%02x" % x for x in hashvalue])


class KnownHostsFile():
    """
    Load a known_hosts file contents, and build a list of KnownHostEntry
    values for each line loaded from the file.
    """
    def __init__(self, filename):
        self.filename=pathlib.Path(filename).expanduser()
        self.entries = []
        if not self.filename.exists():
            return
        for lineno, line in enumerate(open(self.filename), 1):
            self.entries.append(KnownHostsEntry(self.filename, lineno, line))

    def matching_keys(self, hostname):
        """
        Generator call for finding matching KnownHostEntry records for the
        given hostname. For non-standard ports, the hostname should be
        passed in as "[hostname]:NNNN". It is the responsibility of the
        caller to pay heed to the entry marker value to determine if the
        matched entry repesents a plain key, revoked key, or CA key.
        """
        for hostkey in self.entries:
            if hostkey.match(hostname):
                yield hostkey


class KnownHostFileCache():
    """
    Keep loaded known_hosts files cached in a dict, and only load on first use
    """
    def __init__(self):
        self.lock = threading.RLock()
        self.entries = {}

    def load(self, filename="~/.ssh/known_hosts"):
        p = pathlib.Path(filename).expanduser()
        # Use lock to prevent multiple threads from loading the same file
        with self.lock:
            if p not in self.entries:
                self.entries[p] = KnownHostsFile(p)
        return self.entries.get(p)


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
