'''
PKCS - Encryption/Decryption helper derived from PyCrypto

Uses a key (RSA) to encrypt and/or decrypt a short plaintext message, like a password.

See: http://tools.ietf.org/html/rfc3447
'''

from __future__ import print_function
from future_builtins import zip

import os
import sys

from radssh.pkcs import PKCSError, PKCS_OAEP

##################################################################


def test_cases():
    '''
        Run a basic series of tests to ensure proper behavior
        Uses ~/.ssh/id_rsa and ~/.ssh/id_rsa.pub
    '''
    public = PKCS_OAEP('~/.ssh/id_rsa.pub')
    private = PKCS_OAEP()

    plaintext = ['Correct Horse Battery Staple', 'PurpleMonkeyDishwasher', 'Klaatu Barada Nikto']
    cipher1 = [public.encrypt(s) for s in plaintext]
    cipher2 = [public.encrypt(s) for s in plaintext]
    cipher3 = [private.encrypt(s) for s in plaintext]
    cipher4 = [private.encrypt(s) for s in plaintext]

    print(private.__doc__)

    print('Plaintext:', plaintext)
    print()
    print('Cipher1 (Public):', cipher1)
    print('Cipher2 (Public):', cipher2)
    print('Cipher3 (Private):', cipher3)
    print('Cipher4 (Private):', cipher4)

    # Make sure that ciphertexts are unique
    for x in cipher1:
        if x in cipher2 or x in cipher3 or x in cipher4:
            print('Forward encryption duplicate for:', x)
    for x in cipher2:
        if x in cipher3 or x in cipher4:
            print('Forward encryption duplicate for:', x)
    for x in cipher3:
        if x in cipher4:
            print('Forward encryption duplicate for:', x)

    try:
        plain = public.decrypt(cipher1[0])
        print('Decryption should not be possible with public key, but it is: %s' % plain)
    except PKCSError:
        pass

    for orig, texts in enumerate(zip(cipher1, cipher2, cipher3, cipher4)):
        print('Checking results for plaintext #%d [%s]' % (orig, plaintext[orig]))
        for x in texts:
            if private.decrypt(x) != plaintext[orig]:
                print('Encrypted [%s] to [%s] but it came back [%s]' % (plaintext[orig], x, private.decrypt(x)))

test_cases()
