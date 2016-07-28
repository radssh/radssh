Features
==========
 - Newly written module for handling checking of host keys. Greatly improved performance when operating with very large known_hosts files. Closer functionality to OpenSSH handling of host keys.

 - Rely on SSH Config settings for options related to connection, authentication, and host key validation. Many, but not all options are supported.

    #### Connection Options Supported
    Hostname, Port, LogLevel, ConnectTimeout, Ciphers, KexAlgorithms, Macs, ProxyCommand, LocalCommand, PermitLocalCommand

    #### Verification Options Supported
    GlobalKnownHostsFile, UserKnownHostsFile, StrictHostKeyChecking, HostKeyAlias, HostKeyAlgorithms, HashKnownHosts, CheckHostIP

    #### User Authentication Options Supported
    User, PreferredAuthentications, KbdInteractiveAuthentiction, PasswordAuthentication, PubkeyAuthentication, NumberOfPasswordPrompts, IdentityFile, IdentitiesOnly, BatchMode

 - Added support for ECDSA key files for user authentication.

 - Support for Paramiko version 2.0, and cryptography.io. Installations using Paramiko 1.X can continue to be used along with the unmaintained PyCrypto module.

Issues Fixed
==========
 - Missing plugins directory is no longer a fatal runtime error.
 - StreamBuffer closing no longer vulnerable to **Queue.Full** exception.
 - Fix thread contention when prompting user for passwords and accepting new host keys concurrently.

Enhancements
============
 - Reworded user prompt when encountering a restricted command.
 - Command result summary explicitly lists return codes and hosts when any host returns a non-zero status.
 - Recategorized deprecated configuration options as "obsolete", since attempts to use them are ignored.
 - Additional "obsolete" configuration options, and their corresponding SSH Config option names:

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
 - **\*drop** with no arguments will now drop hosts that are not connected/authenticated
 - Shell alias definitions with escaped single quotes are supported.

API Changes
==========
 - hostkey module will be removed in 2.0 release in favor of the new known_hosts module.
 - AuthManager will no longer support parameters **include_agent** or **include_userkeys**. Behavior now controlled by the ssh_config dict passed in to AuthManager.authenticate().

Known Issues
==========
 - Paramiko ProxyCommand may not function correctly under Python3 (https://github.com/paramiko/paramiko/issues/673)
 - Ability to mix & match hostnames and IP addresses leads to many sorting issues under Python3 (#21)
