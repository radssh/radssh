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

'''Update ~/.ssh/authorized_keys file to add (if missing) a public key'''

import os
import socket

import radssh.plugins
from radssh.authmgr import _importKey


def push_key(cluster, logdir, cmd, *args):
    '''Use RadSSH facility to push out a public key into ~/.ssh/authorized_keys'''
    if not args:
        # prompt for key file
        keyfile = raw_input('Enter location of PRIVATE key [~/.ssh/id_rsa]: ')
        if not keyfile:
            keyfile = '~/.ssh/id_rsa'
    else:
        keyfile = args[0]
    # Use _importKey() to read the private key for RSA or DSA keys (may be
    # passphrase protected). Once loaded, use the get_base64 and get_name()
    # calls to get reliable public key data. Avoids having to validate pubkey
    # data by itself, and ensures that the pubkey that we push out is exactly
    # the counterpart to the private key file that the user specified.
    k = _importKey(os.path.expanduser(keyfile))

    # Use grep to determine if the key is already in place
    # Only echo (with append) to file if it is not present
    cluster.run_command('grep -q "^%s %s" .ssh/authorized_keys || echo "%s %s %s@%s" >> .ssh/authorized_keys' % (k.get_name(), k.get_base64(), k.get_name(), k.get_base64(), os.getlogin(), socket.gethostname()))


star_commands = {'*pushkey': push_key}
