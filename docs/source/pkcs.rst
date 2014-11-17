.. _pkcs:

PKCS Encryption/Decryption Module
=================================

RadSSH supports a mechanism to avoid storing plain-text passwords. Recent versions of the PyCrypto library offer RSAES-OAEP encryption and decryption with a RSA key. Encryption is performed with the public key; decryption requires the private key. If the private key is protected with a passphrase, the passphrase will be required in order to perform the decryption process. By leveraging existing RSA keys, this conveniently avoids introducing "Yet Another Password" to remember for fundamental encryption/decryption.

The RadSSH module **pkcs** provides a command line utility to convert between plaintext and ciphertext. By default, the user's private RSA key, located in ``~/.ssh/id_rsa``, is used. Since the private key actually contains both the private and public portions of the key, it can be used for both encryption and decryption. 

Command Line Options
--------------------
In addtion to the command to run the PKCS module (**python -m radssh.pkcs**), the following options are supported:

--decrypt     Switch to *decryption* mode for subsequent arguments
-d            Short form for **\-\-decrypt**
--encrypt     Switch to *encryption* mode for subsequent arguments
-e            Short form for **\-\-encrypt**
--key=<path/to/keyfile>      Use a different RSA key file for subsequent arguments

Encrypting A Password
---------------------

If you do not already have a RSA key in ``~/.ssh/id_rsa``, you can generate one with the command **ssh-keygen -t rsa**.

The PKCS utility defaults to starting in encrypt mode, and defaults to using ``~/.ssh/id_rsa`` as the key file. To encrypt a single password with the default RSA key, run **python -m radssh.pkcs MyPassword** ::

    [paul@pkapp2 ~]$ python -m radssh.pkcs MyPassword
    Using RSA keyfile: [/home/paul/.ssh/id_rsa]
    [MyPassword] -> [uVfL6crigKpeo9pPPByUAQb3OgC1SoVXfjnc4iP0O3/RTOgdn5gmXebJ53/LQoVVfvywgQafUb9TchIKNJwbMaPa/PXVGbha/h1m3zlyrK9GXGVZoN5ic3eumcWZxOy3iCPp9J4PLHARjDmaHzs7FPloQwhqn/rY7pdY41L4d9K72Xvc+EZoEoMdC76XKWklZH1E8RuhW7J54Qq2pf0DPyddqI5XX7jecC5aISGx9WSQAVRSlWtBq8fJ8caAaIkqIRww210Dzhv9j8n9JyW1UGeKTMZv51pWL9goZH9oaNFp5n3t8nnicUSQjIFY+HRIOEKjzy4JVguCIVOw9A8uCw==]
  
The very long string "uVfL6crigKpeo9pPPByUAQb3OgC1SoVXfjnc4iP0O3/RTOgdn5gmXebJ53/LQoVVfvywgQafUb9TchIKNJwbMaPa/PXVGbha/h1m3zlyrK9GXGVZoN5ic3eumcWZxOy3iCPp9J4PLHARjDmaHzs7FPloQwhqn/rY7pdY41L4d9K72Xvc+EZoEoMdC76XKWklZH1E8RuhW7J54Qq2pf0DPyddqI5XX7jecC5aISGx9WSQAVRSlWtBq8fJ8caAaIkqIRww210Dzhv9j8n9JyW1UGeKTMZv51pWL9goZH9oaNFp5n3t8nnicUSQjIFY+HRIOEKjzy4JVguCIVOw9A8uCw==" is the resulting ciphertext. Your actual result string will be different, since you will be using a different RSA key.

Decrypting A Password
---------------------
The plaintext password "MyPassword" is encrypted into a long Base64 encoded string, and printed to the console. The encrypted string inside the second pair of brackets can be decrypted with **python -m radssh.pkcs --decrypt uVfL6crigKpeo9pPPByUAQb3OgC1SoVXfjnc4iP0O3/RTOgdn5gmXebJ53/LQoVVfvywgQafUb9TchIKNJwbMaPa/PXVGbha/h1m3zlyrK9GXGVZoN5ic3eumcWZxOy3iCPp9J4PLHARjDmaHzs7FPloQwhqn/rY7pdY41L4d9K72Xvc+EZoEoMdC76XKWklZH1E8RuhW7J54Qq2pf0DPyddqI5XX7jecC5aISGx9WSQAVRSlWtBq8fJ8caAaIkqIRww210Dzhv9j8n9JyW1UGeKTMZv51pWL9goZH9oaNFp5n3t8nnicUSQjIFY+HRIOEKjzy4JVguCIVOw9A8uCw==**::

    [paul@pkapp2 ~]$ python -m radssh.pkcs --decrypt uVfL6crigKpeo9pPPByUAQb3OgC1SoVXfjnc4iP0O3/RTOgdn5gmXebJ53/LQoVVfvywgQafUb9TchIKNJwbMaPa/PXVGbha/h1m3zlyrK9GXGVZoN5ic3eumcWZxOy3iCPp9J4PLHARjDmaHzs7FPloQwhqn/rY7pdY41L4d9K72Xvc+EZoEoMdC76XKWklZH1E8RuhW7J54Qq2pf0DPyddqI5XX7jecC5aISGx9WSQAVRSlWtBq8fJ8caAaIkqIRww210Dzhv9j8n9JyW1UGeKTMZv51pWL9goZH9oaNFp5n3t8nnicUSQjIFY+HRIOEKjzy4JVguCIVOw9A8uCw==
    Using RSA keyfile: [/home/paul/.ssh/id_rsa]
    Switching to Decrypt mode
    [uVfL6crigKpeo9pPPByUAQb3OgC1SoVXfjnc4iP0O3/RTOgdn5gmXebJ53/LQoVVfvywgQafUb9TchIKNJwbMaPa/PXVGbha/h1m3zlyrK9GXGVZoN5ic3eumcWZxOy3iCPp9J4PLHARjDmaHzs7FPloQwhqn/rY7pdY41L4d9K72Xvc+EZoEoMdC76XKWklZH1E8RuhW7J54Qq2pf0DPyddqI5XX7jecC5aISGx9WSQAVRSlWtBq8fJ8caAaIkqIRww210Dzhv9j8n9JyW1UGeKTMZv51pWL9goZH9oaNFp5n3t8nnicUSQjIFY+HRIOEKjzy4JVguCIVOw9A8uCw==] -> [MyPassword]

Module Reference
----------------
.. automodule:: radssh.pkcs
  :members:
