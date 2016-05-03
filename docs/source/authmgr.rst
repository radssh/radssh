.. _authmgr:

Authentication Manager
======================

.. automodule:: radssh.authmgr
   :members:

Sample AuthFile format:
-----------------------

authfile::

        # Lines starting with # are comments
        # Non-comment lines should be 3 (or 2) fields with '|' separator
        #     1st field: either 'password' or 'keyfile'
        #     2nd field (optional): hostname or IP matching filter
        #     last field: password plaintext, ciphertext, or keyfile name
        #
        # Try this password for single host 'neptune'
        password|neptune|C0p3rn1cu5

        # Common password for all hosts in DMZ
        password|*.dmz.company.org|INSECURE

        # Common password for all hosts on IP subnet (requires netaddr)
        password|192.168.65.0/24|Chewbacca

        # Can overlap filters, AuthMgr will attempt using any match
        # Also, can use IPNetwork or IPGlob (see netaddr docs)
        password|192.168.65.100-120|Wookie

        # Common (default) password:  2 fields = no host filtering
        password|also_insecure

        # Old style 1-field entry is also default password
        # should be deprecated
        my_voice_is_my_password

        # Keyfiles specified in a similar way
        # NOTE: standard keyfiles in ~/.ssh normally will not need
        # to be specified in the authfile, default keys will be available
        # unless explicitly disabled during __init__ call.o

        # Try a DB server key for all hosts starting with 'db'
        keyfile|db*|/home/mysqldba/admin/id_rsa

	# You can include passwords encrypted with your RSA public key
	# with the PKCS-OAEP mechanism of the cryptography module. Use
	# the radssh.pkcs module to encrypt passwords, then copy/paste
	# the encrypted results into the auth file like this:
	PKCSOAEP|*|nPIC8J08T7x4G1PsZPKH9bjeQd/8A1vLiOCCrH1chSvpz0hEfJqeqPMyLxhqCames5ID9eqvFmbyZBBfPPxGjoAJMHgKc+xfF68+nLjE87pc6WlbeTu9jQKeS5Xeu+oeuwTx81xFTDSyrUyW6/eo88jPxS2w0LjYqfn5RNsBEDygpD7Hah0BVbqSUhDwx4m8Qw4MI4kMzqWFS9Ev8Vo5yomQ3fSSJsun2OgK+d0DLWl4eMmVU+fmFbRSZdoSRL1/1Kadl2jBuhOu9j9nhGS2NEhxE5OZd26EX7jD8KrRq7JSsCExUbrnKgykri3RL0BS3mhXsnv1crINBh2+mamh0Q==
	# See: http://radssh.readthedocs.org/en/latest/pkcs.html#pkcs for more details
