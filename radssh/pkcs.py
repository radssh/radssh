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
PKCS - Encryption/Decryption helper derived from cryptography

Uses a key (RSA) to encrypt and/or decrypt a short plaintext
message (like a password). Not suitable for large messages, as
maximum data length is determined by key size.

See: http://tools.ietf.org/html/rfc3447
'''

import os
import base64
import warnings

from .console import user_password


import cryptography
import cryptography.hazmat.backends
import cryptography.hazmat.primitives
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_ssh_public_key, load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding

# Replace PyCrypto OAEP functionality with crytpography
# cryptography.io way - RSA private key object provides decrypt,
# public key object provides encrypt, but each needs a padding
# parameter of OAEP that needs to be constructed.
class PKCS1_OAEP(object):
    """
    Low level class to perform PKCS primitives against cryptography backend
    """
    def __init__(self, setup):
        self.backend = cryptography.hazmat.backends.default_backend()
        self.oaep = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )
        if setup.keydata.startswith(b'ssh-rsa'):
            self.private_key = None
            self.public_key = load_ssh_public_key(setup.keydata, self.backend)
        else:
            try:
                self.private_key = load_pem_private_key(setup.keydata, password=setup.default_passphrase, backend=self.backend)
            except TypeError:
                if setup.default_passphrase:
                    # No need to interactively prompt - we failed
                    raise
                passphrase = user_password('Enter passphrase for [%s]: ' % setup.keyfile)
                self.private_key = load_pem_private_key(setup.keydata, password=passphrase, backend=self.backend)
            self.public_key = self.private_key.public_key()

    def encrypt(self, msg):
        return self.public_key.encrypt(msg, self.oaep)

    def decrypt(self, data):
        if not self.private_key:
            raise PKCSError('Unable to decrypt - No private key')
        return self.private_key.decrypt(data, self.oaep)


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
            with open(self.keyfile, 'rb') as f:
                self.keydata = f.read()
            # Peek to see if it looks like a pubkey or private key
            if self.keydata.startswith(b'ssh-rsa '):
                self.cipher_object = PKCS1_OAEP(self)
            elif b'BEGIN RSA PRIVATE KEY' in self.keydata:
                # Defer loading the key, in case a passphrase is required
                # Handle that when/if the key is needed to instantiate the cipher
                self.cipher_object = None
            else:
                raise PKCSError('Key format not recognized', keyfile)
        except IOError:
            self.cipher_object = None
            self.keydata = None

    def _cipher(self):
        '''
        Obtain a usable cipher object based on the text representation of the key
        loaded from the file.  Allows defering the possible passphrase prompting
        until the key (and resulting cipher) is actually used. Downside is that if
        there is a more fundamental format issue with the key data, we encounter
        it here.
        '''
        if self.cipher_object:
            return self.cipher_object
        if not self.keydata:
            raise PKCSError('No RSA Key available: %s' % self.keyfile)
        self.cipher_object = PKCS1_OAEP(self)

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


def main():
    '''
    Command line processing: arguments processed in order, beginning in encrypt mode.
    Special arguments:
        --decrypt, -d: Switch to Decrypt mode for subsequent parameters
        --encrypt, -e: Switch to Encrypt mode for subsequent parameters
        --key=/path/to/keyfile: Use a different RSA key (public or private)
    All other command line arguments will be attempted to be used as
    plaintext or base64-encoded ciphertext for encrypt/decrypt calls.
    '''
    import sys
    if len(sys.argv) == 1:
        print(__doc__)
        print(main.__doc__)
        sys.exit(0)

    encoding_mode = True
    pkcs = PKCS_OAEP()
    print('Using RSA keyfile: [%s]' % pkcs.keyfile)

    for x in sys.argv[1:]:
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
    main()
