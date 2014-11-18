Introduction to RadSSH Shell
============================

RadSSH provides a user shell-like environment. It is not quite a "real" shell; there are several restrictions and shortcomings that probably warrant calling it a glorified command line dispatcher utility. Unfortunately "shell" is much easier to type and read, and it behaves closely enough to a shell (with restrictions), that it will be called shell.

It is like a shell, because:
 - You get a prompt
 - You type shell command(s) at the prompt and you press [Enter]
 - The commands you typed run (or fail to run), and may produce output
 - On completion, you get a prompt

It is not like a shell, because:
 - No persistent state in between command invocations. You can "run" **cd /tmp**, but on completion you won't be in the ``/tmp`` directory
 - RadSSH does very minimal interpretation of the typed input; it is passed mostly verbatim to the remote hosts
 - By default, your connected SSH sessions are not associated with a pty
 - Commands that require interactive input are not recommended, and will probably behave badly when run via RadSSH


Host Connections
----------------

RadSSH can connect to remote hosts either by name (as long as system name resolution is functional) or by IP address (IPv4; not tested with IPv6). Depending on system resource availability, RadSSH is capable of several hundred to over one thousand concurrent connections. RadSSH can also utilize connections through the use of connections through an intermediate host (jumpbox), for use in environments where connection security and/or VLAN isolation may prevent other solutions from working.

You can leverage Bash expansion when invoking RadSSH to provide concise shorthand notation for specifying a range of hosts::

    # Example for IP expansion
    192.168.100.{1..100}
    # Example for hostname expansion
    webfarm_{00..59}
    # Hostname with domain expansion
    ldap.{bos,ny,chi,atl,stl}.example.org

By default, RadSSH will ensure that all remote host connections are validated against the user's list of accepted host keys, saved in ``~/.ssh/known_hosts``. Only hosts whose identities have previously been established (and saved) will be considered trusted.

User Authentication
-------------------

RadSSH supports password authentication as well as SSH Public Key based authentication. Keys can be used from the standard user identity file locations, from a running SSH Agent, or from explicit file locations. Initial authentication is attempted with the current user, but can also be configured to authenticate as a different username for remote login purposes.


Resilience
----------

RadSSH does not require 100% success regarding network connectivity or user authentication. A session can be started, attempting to connect to 100 remote host nodes. If 50 connect and authenticate, 30 connect but fail to properly authenticate, and the remaining 20 fail to connect, RadSSH will operate with 50 live connections and 50 inactive connections. At any time during the session, the user can attempt to retry the connection/authentication process to the inactive hosts, via the ``*auth`` meta-command (See :doc:`star_commands`). In some environments, having less than 100% success rate in connecting and authenticating winds up being the norm, rather than the exception. RadSSH is designed to cope with these environments as gracefully as possible.

