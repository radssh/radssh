.. RadSSH documentation master file, created by
   sphinx-quickstart on Tue Jul 22 09:00:40 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Installation Guide
==================
 
The preferred way to install RadSSH is to use Python's `pip <http://pip.readthedocs.org/en/latest/>` utility. If you do not have administration (root) privileges to install Python packages into the system level directories, pip can install RadSSH to a `virtual environment <https://pypi.python.org/pypi/virtualenv>`.

*Add `PyPI <https://pypi.python.org/pypi>` details once RadSSH is registered.*

Pip will handle the appropriate installation of RadSSH for your Python environment, either system-wide or virtual environment, and also utilitze the Python Package Index to install any missing dependencies. RadSSH currently requires `Paramiko <https://pypi.python.org/pypi/paramiko>` and `netaddr <https://pypi.python.org/pypi/netaddr>` packages, and pip will download these (and their dependencies) and install them if they are not already installed.


Installing from PyPI
--------------------

Not yet available, until package is registered.

Installing from Local Repository
--------------------------------

Until the package is available via PyPI, the preferred installation method is to use pip along with the source repository URL. Pip will download the repository content via http (or https, git+git, git+https) and install.

If you are installing to a virtual environment, be sure to activate the environment prior to running pip.

Invoke the command ``pip install http://10.173.0.129/repos/scripts/radssh`` to begin the download and installation process. Below is an output listing of a successful pip install, including dependencies; Actual output may vary slightly, based on Python version:

::

    (sample_env)[paul@pkapp2 ~]$ pip install http://10.173.0.129/repos/scripts/radssh
    Downloading/unpacking http://10.173.0.129/repos/scripts/radssh
      Downloading radssh
      Checking out http://10.173.0.129/repos/scripts/radssh to /tmp/pip-y7vzj7-build
      Running setup.py egg_info for package from http://10.173.0.129/repos/scripts/radssh
        radssh/core_plugins/__init__.py -> radssh/plugins
        radssh/core_plugins/auth.py -> radssh/plugins
        radssh/core_plugins/grep.py -> radssh/plugins
        radssh/core_plugins/lines.py -> radssh/plugins
        radssh/core_plugins/test_tty.py -> radssh/plugins
        radssh/core_plugins/vcr.py -> radssh/plugins
        radssh/core_plugins/file_lookup.py -> radssh/plugins
        radssh/core_plugins/ip.py -> radssh/plugins
        radssh/core_plugins/jumpbox.py -> radssh/plugins
        radssh/core_plugins/swedish_chef.py -> radssh/plugins
        radssh/core_plugins/sftp.py -> radssh/plugins
        radssh/core_plugins/add_drop.py -> radssh/plugins
    Downloading/unpacking paramiko (from radssh==0.1)
      Downloading paramiko-1.14.1.tar.gz (1.1MB): 1.1MB downloaded
      Running setup.py egg_info for package paramiko
    Downloading/unpacking netaddr (from radssh==0.1)
      Downloading netaddr-0.7.12.tar.gz (1.5MB): 1.5MB downloaded
      Running setup.py egg_info for package netaddr
        warning: no previously-included files matching '*.svn*' found anywhere in distribution
        warning: no previously-included files matching '*.git*' found anywhere in distribution
    Downloading/unpacking pycrypto>=2.1,!=2.4 (from paramiko->radssh==0.1)
      Downloading pycrypto-2.6.1.tar.gz (446kB): 446kB downloaded
      Running setup.py egg_info for package pycrypto
    Downloading/unpacking ecdsa (from paramiko->radssh==0.1)
      Downloading ecdsa-0.11.tar.gz (45kB): 45kB downloaded
      Running setup.py egg_info for package ecdsa
    Installing collected packages: paramiko, netaddr, radssh, pycrypto, ecdsa
      Running setup.py install for paramiko
      Running setup.py install for netaddr
        changing mode of build/scripts-2.6/netaddr from 664 to 775
        warning: no previously-included files matching '*.svn*' found anywhere in distribution
        warning: no previously-included files matching '*.git*' found anywhere in distribution
        changing mode of /home/paul/sample_env/bin/netaddr to 775
      Running setup.py install for radssh
        radssh/core_plugins/__init__.py -> radssh/plugins
        radssh/core_plugins/auth.py -> radssh/plugins
        radssh/core_plugins/grep.py -> radssh/plugins
        radssh/core_plugins/lines.py -> radssh/plugins
        radssh/core_plugins/test_tty.py -> radssh/plugins
        radssh/core_plugins/vcr.py -> radssh/plugins
        radssh/core_plugins/file_lookup.py -> radssh/plugins
        radssh/core_plugins/ip.py -> radssh/plugins
        radssh/core_plugins/jumpbox.py -> radssh/plugins
        radssh/core_plugins/swedish_chef.py -> radssh/plugins
        radssh/core_plugins/sftp.py -> radssh/plugins
        radssh/core_plugins/add_drop.py -> radssh/plugins
      Running setup.py install for pycrypto
        checking for gcc... gcc
        checking whether the C compiler works... yes
        checking for C compiler default output file name... a.out
        checking for suffix of executables...
        checking whether we are cross compiling... no
        checking for suffix of object files... o
        checking whether we are using the GNU C compiler... yes
        checking whether gcc accepts -g... yes
        checking for gcc option to accept ISO C89... none needed
        checking for __gmpz_init in -lgmp... no
        checking for __gmpz_init in -lmpir... no
        checking whether mpz_powm is declared... no
        checking whether mpz_powm_sec is declared... no
        checking how to run the C preprocessor... gcc -E
        checking for grep that handles long lines and -e... /bin/grep
        checking for egrep... /bin/grep -E
        checking for ANSI C header files... yes
        checking for sys/types.h... yes
        checking for sys/stat.h... yes
        checking for stdlib.h... yes
        checking for string.h... yes
        checking for memory.h... yes
        checking for strings.h... yes
        checking for inttypes.h... yes
        checking for stdint.h... yes
        checking for unistd.h... yes
        checking for inttypes.h... (cached) yes
        checking limits.h usability... yes
        checking limits.h presence... yes
        checking for limits.h... yes
        checking stddef.h usability... yes
        checking stddef.h presence... yes
        checking for stddef.h... yes
        checking for stdint.h... (cached) yes
        checking for stdlib.h... (cached) yes
        checking for string.h... (cached) yes
        checking wchar.h usability... yes
        checking wchar.h presence... yes
        checking for wchar.h... yes
        checking for inline... inline
        checking for int16_t... yes
        checking for int32_t... yes
        checking for int64_t... yes
        checking for int8_t... yes
        checking for size_t... yes
        checking for uint16_t... yes
        checking for uint32_t... yes
        checking for uint64_t... yes
        checking for uint8_t... yes
        checking for stdlib.h... (cached) yes
        checking for GNU libc compatible malloc... yes
        checking for memmove... yes
        checking for memset... yes
        configure: creating ./config.status
        config.status: creating src/config.h
        warning: GMP or MPIR library not found; Not building Crypto.PublicKey._fastmath.
        building 'Crypto.Hash._MD2' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/MD2.c -o build/temp.linux-x86_64-2.6/src/MD2.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/MD2.c:31:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/string.h:27,
                     from src/MD2.c:30:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/MD2.c:31:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/string.h:27,
                     from src/MD2.c:30:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/MD2.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Hash/_MD2.so
        building 'Crypto.Hash._MD4' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/MD4.c -o build/temp.linux-x86_64-2.6/src/MD4.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/MD4.c:31:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/string.h:27,
                     from src/MD4.c:30:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/MD4.c:31:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/string.h:27,
                     from src/MD4.c:30:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/MD4.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Hash/_MD4.so
        building 'Crypto.Hash._SHA256' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/SHA256.c -o build/temp.linux-x86_64-2.6/src/SHA256.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/hash_SHA2_template.c:33,
                     from src/SHA256.c:72:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/hash_SHA2.h:72,
                     from src/SHA256.c:35:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/hash_SHA2_template.c:33,
                     from src/SHA256.c:72:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/hash_SHA2.h:72,
                     from src/SHA256.c:35:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/SHA256.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Hash/_SHA256.so
        building 'Crypto.Hash._SHA224' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/SHA224.c -o build/temp.linux-x86_64-2.6/src/SHA224.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/hash_SHA2_template.c:33,
                     from src/SHA224.c:73:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/hash_SHA2.h:72,
                     from src/SHA224.c:36:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/hash_SHA2_template.c:33,
                     from src/SHA224.c:73:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/hash_SHA2.h:72,
                     from src/SHA224.c:36:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/SHA224.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Hash/_SHA224.so
        building 'Crypto.Hash._SHA384' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/SHA384.c -o build/temp.linux-x86_64-2.6/src/SHA384.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/hash_SHA2_template.c:33,
                     from src/SHA384.c:80:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/hash_SHA2.h:72,
                     from src/SHA384.c:36:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/hash_SHA2_template.c:33,
                     from src/SHA384.c:80:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/hash_SHA2.h:72,
                     from src/SHA384.c:36:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/SHA384.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Hash/_SHA384.so
        building 'Crypto.Hash._SHA512' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/SHA512.c -o build/temp.linux-x86_64-2.6/src/SHA512.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/hash_SHA2_template.c:33,
                     from src/SHA512.c:80:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/hash_SHA2.h:72,
                     from src/SHA512.c:36:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/hash_SHA2_template.c:33,
                     from src/SHA512.c:80:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/hash_SHA2.h:72,
                     from src/SHA512.c:36:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/SHA512.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Hash/_SHA512.so
        building 'Crypto.Hash._RIPEMD160' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -DPCT_LITTLE_ENDIAN=1 -Isrc/ -I/usr/include/python2.6 -c src/RIPEMD160.c -o build/temp.linux-x86_64-2.6/src/RIPEMD160.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/RIPEMD160.c:57:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/RIPEMD160.c:48:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/RIPEMD160.c:57:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/RIPEMD160.c:48:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/RIPEMD160.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Hash/_RIPEMD160.so
        building 'Crypto.Cipher._AES' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/AES.c -o build/temp.linux-x86_64-2.6/src/AES.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/AES.c:29:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/assert.h:37,
                     from src/AES.c:27:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/AES.c:29:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/assert.h:37,
                     from src/AES.c:27:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/AES.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Cipher/_AES.so
        building 'Crypto.Cipher._ARC2' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/ARC2.c -o build/temp.linux-x86_64-2.6/src/ARC2.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/ARC2.c:45:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/string.h:27,
                     from src/ARC2.c:44:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/ARC2.c:45:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/string.h:27,
                     from src/ARC2.c:44:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/ARC2.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Cipher/_ARC2.so
        building 'Crypto.Cipher._Blowfish' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/Blowfish.c -o build/temp.linux-x86_64-2.6/src/Blowfish.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/Blowfish.c:39:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/Blowfish.c:31:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/Blowfish.c:39:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/stdint.h:26,
                     from src/Blowfish.c:31:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/Blowfish.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Cipher/_Blowfish.so
        building 'Crypto.Cipher._CAST' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/CAST.c -o build/temp.linux-x86_64-2.6/src/CAST.o
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/CAST.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Cipher/_CAST.so
        building 'Crypto.Cipher._DES' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -Isrc/libtom/ -I/usr/include/python2.6 -c src/DES.c -o build/temp.linux-x86_64-2.6/src/DES.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/DES.c:37:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/assert.h:37,
                     from src/libtom/tomcrypt.h:3,
                     from src/libtom/tomcrypt_des.c:11,
                     from src/DES.c:32:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/DES.c:37:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/assert.h:37,
                     from src/libtom/tomcrypt.h:3,
                     from src/libtom/tomcrypt_des.c:11,
                     from src/DES.c:32:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/DES.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Cipher/_DES.so
        building 'Crypto.Cipher._DES3' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -Isrc/libtom/ -I/usr/include/python2.6 -c src/DES3.c -o build/temp.linux-x86_64-2.6/src/DES3.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/DES.c:37,
                     from src/DES3.c:26:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/assert.h:37,
                     from src/libtom/tomcrypt.h:3,
                     from src/libtom/tomcrypt_des.c:11,
                     from src/DES.c:32,
                     from src/DES3.c:26:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/DES.c:37,
                     from src/DES3.c:26:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/assert.h:37,
                     from src/libtom/tomcrypt.h:3,
                     from src/libtom/tomcrypt_des.c:11,
                     from src/DES.c:32,
                     from src/DES3.c:26:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/DES3.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Cipher/_DES3.so
        building 'Crypto.Cipher._ARC4' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/ARC4.c -o build/temp.linux-x86_64-2.6/src/ARC4.o
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/ARC4.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Cipher/_ARC4.so
        building 'Crypto.Cipher._XOR' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/XOR.c -o build/temp.linux-x86_64-2.6/src/XOR.o
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/XOR.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Cipher/_XOR.so
        building 'Crypto.Util.strxor' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/strxor.c -o build/temp.linux-x86_64-2.6/src/strxor.o
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/strxor.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Util/strxor.so
        building 'Crypto.Util._counter' extension
        gcc -pthread -fno-strict-aliasing -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic -D_GNU_SOURCE -fPIC -fwrapv -fPIC -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/python2.6 -c src/_counter.c -o build/temp.linux-x86_64-2.6/src/_counter.o
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/_counter.c:28:
        /usr/include/python2.6/pyconfig-64.h:1034:1: warning: "_POSIX_C_SOURCE" redefined
        In file included from /usr/include/assert.h:37,
                     from src/_counter.c:25:
        /usr/include/features.h:162:1: warning: this is the location of the previous definition
        In file included from /usr/include/python2.6/pyconfig.h:6,
                     from /usr/include/python2.6/Python.h:8,
                     from src/_counter.c:28:
        /usr/include/python2.6/pyconfig-64.h:1043:1: warning: "_XOPEN_SOURCE" redefined
        In file included from /usr/include/assert.h:37,
                     from src/_counter.c:25:
        /usr/include/features.h:164:1: warning: this is the location of the previous definition
        gcc -pthread -shared build/temp.linux-x86_64-2.6/src/_counter.o -L/usr/lib64 -lpython2.6 -o build/lib.linux-x86_64-2.6/Crypto/Util/_counter.so
      Running setup.py install for ecdsa
    Successfully installed paramiko netaddr radssh pycrypto ecdsa
    Cleaning up...
    (sample_env)[paul@pkapp2 ~]$ 


Installing from Developer Source
--------------------------------

If you have a local source tree, either from a developer checkout or from un-tarred source package, you can install RadSSH in a similar fashion, replacing the URL of the repository with the local directory. Alternatively, you can ``cd`` into the source directory and run ``pip install .`` 

Verifying the Install
=====================

Once installed, you should run ``python -m radssh`` (or if running Python 2.6, ``python -m radssh.__main__``) as a diagnostic test. If successful, it will report the results of loading the RadSSH package and its dependencies, along with some details about the Python runtime environment and current host. It will also run some capacity checks for the system limitations on concurrent open files and execution threads. These upper limits, if listed, are a significant factor in how many concurrent connections RadSSH will be able to handle on your system.

Sample Output::

    (sample_env)[paul@pkapp2 ~]$ python -m radssh.__main__
    RadSSH Main Module
    Package RadSSH 0.1.0 [r4637 @ 2014-09-01 14:21:42Z] from (/home/paul/sample_env/lib/python2.6/site-packages/radssh/__init__.pyc)
      Using Paramiko  1.14.1 from /home/paul/sample_env/lib/python2.6/site-packages/paramiko/__init__.pyc
      Using PyCrypto 2.6.1 from /home/paul/sample_env/lib/python2.6/site-packages/Crypto/__init__.pyc
      Using netaddr 0.7.12 from /home/paul/sample_env/lib/python2.6/site-packages/netaddr/__init__.pyc
    
    Python 2.6.6 (CPython)
    Running on Linux [pkapp2.example.org]
      Scientific Linux (6.5/Carbon)

    Checking runtime limits...
    Limitation reached after 1021 open files (IOError(24, 'Too many open files'))
    File check completed in 0.005245 seconds
    Limitation reached after 823 running threads (error("can't start new thread",))
    Thread check completed in 0.436855 seconds

