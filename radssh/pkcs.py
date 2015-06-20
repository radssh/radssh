#
# Copyright (c) 2014 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

'''
PKCS - Encryption/Decryption helper derived from PyCrypto

Uses a key (RSA) to encrypt and/or decrypt a short plaintext message, like a password.

See: http://tools.ietf.org/html/rfc3447
'''
from __future__ import print_function  # Requires Python 2.6 or higher


import os
import base64
import getpass
import warnings

import Crypto.PublicKey.RSA as RSA

# Earlier versions of PyCrypto do not have PKCS1_OAEP
# Handle this gracefully by making the class still able to be instantiated
# but attempts to encrypt/decrypt raising exceptions instead of import or
# class constructor.
try:
    from Crypto.Cipher import PKCS1_OAEP
except ImportError:
    warnings.warn(Warning('PyCrypto module does not support PKCS1_OAEP. Encrypt/Decrypt operations disabled'))
    PKCS1_OAEP = None


class PKCSError(Exception):
    pass


class PKCS_OAEP(object):
    '''
        Asymmetric key encryptor/decryptor based on PKCS#1 RSAES-OAEP
        Based on a loadable RSA key (private or public), provide encrypt() and
        decrypt() operations for short plaintext input (length is limited by
        the size of the loaded key).  Encryption can be done with either
        private or public key; Decryption requires private key only.
    '''
    def __init__(self, keyfile='~/.ssh/id_rsa', default_passphrase=None):
        self.keyfile = os.path.expanduser(keyfile)
        self.default_passphrase = default_passphrase
        try:
            with open(self.keyfile, 'r') as f:
                self.keydata = f.read()
            if 'BEGIN RSA PRIVATE KEY' in self.keydata or self.keydata.startswith('ssh-rsa '):
                # Defer loading the key, in case a passphrase is required
                # Handle that when/if the key is needed to instantiate the cipher
                self.rsakey = None
            else:
                raise PKCSError('Key format not recognized', keyfile)
        except IOError:
            self.keydata = None
        self.cipher_object = None
        self.unsupported = not PKCS1_OAEP

    def _cipher(self):
        '''
        Obtain a usable cipher object based on the text representation of the key
        loaded from the file.  Allows defering the possible passphrase prompting
        until the key (and resulting cipher) is actually used. Downside is that if
        there is a more fundamental format issue with the key data, we encounter
        it here.
        '''
        if not PKCS1_OAEP:
            raise PKCSError('PKCS1_OAEP cipher unavailable in this version of PyCrypto')
        if self.cipher_object:
            return self.cipher_object
        if not self.rsakey:
            # Construct the key object from the source - may need to prompt for passphrase
            try:
                try:
                    self.rsakey = RSA.importKey(self.keydata, self.default_passphrase)
                except ValueError:
                    if self.default_passphrase:
                        # No need to interactively prompt - we failed
                        raise
                    passphrase = getpass.getpass('Enter passphrase for [%s]: ' % self.keyfile)
                    self.rsakey = RSA.importKey(self.keydata, passphrase)
            except Exception as e:
                raise PKCSError('Unable to load key - %s' % str(e))
        self.cipher_object = PKCS1_OAEP.new(self.rsakey)
        return self.cipher_object

    def encrypt_binary(self, blob):
        '''Encrypt a bytestring, returning ciphertext as binary'''
        try:
            return self._cipher().encrypt(blob)
        except Exception as e:
            raise PKCSError('Unable to encrypt - %s' % str(e))

    def encrypt(self, plaintext):
        '''Encrypt a string, returning base64 encoded ciphertext'''
        return base64.b64encode(self.encrypt_binary(plaintext.encode())).decode()

    def decrypt_binary(self, blob):
        '''Decrypt ciphertext passed in binary form back into plaintext'''
        try:
            return self._cipher().decrypt(blob)
        except Exception as e:
            raise PKCSError('Unable to decrypt - %s' % str(e))

    def decrypt(self, ciphertext):
        '''Decrypt ciphertext passed in as a base64 encoded string back into plaintext'''
        try:
            data = base64.b64decode(ciphertext)
        except Exception as e:
            raise PKCSError('Ciphertext cannot be base64 decoded: %s' % str(e))
        return self.decrypt_binary(data).decode()

__all__ = ['PKCSError', 'PKCS_OAEP']

##################################################################


def main(args):
    '''
    Command line processing: arguments processed in order, beginning in encrypt mode.
    Special arguments:
        --decrypt, -d: Switch to Decrypt mode for subsequent parameters
        --encrypt, -e: Switch to Encrypt mode for subsequent parameters
        --key=/path/to/keyfile: Use a different RSA key (public or private)
    All other command line arguments will be attempted to be used as
    plaintext or base64-encoded ciphertext for encrypt/decrypt calls.
    '''
    encoding_mode = True
    pkcs = PKCS_OAEP()
    print('Using RSA keyfile: [%s]' % pkcs.keyfile)

    for x in args:
        if x == '--decrypt' or x == '-d':
            print('Switching to Decrypt mode')
            encoding_mode = False
        elif x == '--encrypt' or x == '-e':
            print('Switching to Encrypt mode')
            encoding_mode = True
        elif x.startswith('--key='):
            print('Switching to key: %s' % x[6:])
            pkcs = PKCS_OAEP(x[6:])
        else:
            if encoding_mode:
                result = pkcs.encrypt(x)
            else:
                result = pkcs.decrypt(x)
            print('[%s] -> [%s]' % (x, result))

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print(__doc__)
        print(main.__doc__)
