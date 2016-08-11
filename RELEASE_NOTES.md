Features
==========
 - New module for host key handling and validation, closer to the functionality of OpenSSH. Significantly improved performance when operating with very large known_hosts files.

 - Now relies on standard OpenSSH config file settings for options related to connection, host key validation, and user authentiction. Many, but not all options are supported.

    #### Connection Options Supported
    Hostname, Port, LogLevel, ConnectTimeout, Ciphers, KexAlgorithms, Macs, ProxyCommand, LocalCommand, PermitLocalCommand

    #### Hostkey Validation Options Supported
    GlobalKnownHostsFile, UserKnownHostsFile, StrictHostKeyChecking, HostKeyAlias, HostKeyAlgorithms, HashKnownHosts, CheckHostIP

    #### User Authentication Options Supported
    User, PreferredAuthentications, KbdInteractiveAuthentiction, PasswordAuthentication, PubkeyAuthentication, NumberOfPasswordPrompts, IdentityFile, IdentitiesOnly, BatchMode

 - Added support for ECDSA key files for user authentication.

 - Now supports for Paramiko version 2.0, and cryptography.io. Installations using Paramiko 1.X can continue to be used along with the unmaintained PyCrypto module.

  - Improved support for specifying explicit port and username with URI style formatting (user@host:port).

Issues Fixed
==========
 - A missing *plugins* directory is no longer a fatal runtime error.
 - StreamBuffer closing is no longer vulnerable to **Queue.Full** exception.
 - Fix thread contention issue when prompting user for passwords and accepting new host keys concurrently.
 - Ordered output mode fixed under Python3. [ Fixed in 1.1.1 ]

Enhancements
============
 - Reworded user prompt when encountering a restricted command.
 - Command result summary explicitly lists return codes and hosts when any host returns a non-zero status.
 - Formerly deprecated configuration options are now categorized as "obsolete", since attempts to use them are ignored.
 - New "obsolete" configuration options, and their corresponding SSH Config option names:

    Obsolete RadSSH Option|Current SSH Option
    -------------------------|------------------------
    hostkey.verify|StrictHostKeyChecking
    hostkey.known_hosts|UserKnownHostsFile
    ssh_identity|IdentityFile
    ssh_agent|IdentitiesOnly

 - Added new config option **ssh_config** to allow overriding the default location of the user SSH Config file (~/.ssh/config).


Plugin Enhancements
=================
 - **\*enable** now includes explicit count of hosts when all hosts enabled.
 - **\*drop** with no arguments will now drop hosts that are not connected/authenticated.
 - **\*add** now handles URI style (user@host:port) format; lists summary of connections added to cluster.
 - Now supports shell alias definitions with escaped single quotes are supported.
 - **\*result** can include > and >> to save/append to local file [ Added in 1.1.1 ]
 - **\*history** added to alias plugin, with support for `!nnn` replay of command by history number [ Added in 1.1.1 ]

API Changes
==========
 - hostkey module will be removed in 2.0 release in favor of the new known_hosts module.
 - AuthManager will no longer support parameters **include_agent** or **include_userkeys**. Settings are now controlled by the OpenSSH configuration options.

Known Issues
==========
 - Paramiko ProxyCommand may not function correctly under Python3 (https://github.com/paramiko/paramiko/issues/673)
 - Ability to mix & match hostnames and IP addresses leads to many sorting issues under Python3 (#21) [ Fixed in 1.1.1 ]

Additional Notes
==============
 - **PyCrypto** identified as an unmaintained module. **Paramiko** 2.0 has transitioned to using **cryptography**. RadSSH usage will prefer to use **cryptography**, but will continue to work with **PyCrypto** and **Paramiko** 1.X. Installations are strongly recommended to upgrade to using **cryptography** (and **Paramiko** 2.0) from **PyCrypto**. When RadSSH is unable to load the preferred **cryptography** module and reverts to using **PyCrypto**, a warning will be issued encouraging users to install **cryptography**.
 - **Paramiko** library does not include support for OpenSSH configuration *Match* blocks, so currently these are not supported for RadSSH configuration options as well.
 - Python 2.6 and Python 3.2 will continue to be supported by RadSSH 1.1.0, even though these Python versions are no longer being actively maintained. Future releases of RadSSH may not continue focus or effort on compatibility with these python versions.
