Basic Star Commands in RadSSH
=============================

Most of the time, the text that you enter at a RadSSH prompt is sent to execute on remote nodes. Sometimes during a session, it is useful to issue commands that instruct RadSSH to perform something other than its normal command dispatching. Starting any command with an asterisk (``*``) will enable this behavior, and RadSSH will attempt to interpret what special behavior or operation is requested.

This mechanism of intercepting StarCommands operates not only with the colleciton of RadSSH built-in commands, but can be extended by user PlugIns. For details on coding PlugIns to add (or replace) StarCommands, see :doc:`plugin_developer_guide`.

Here is a brief summary of the RadSSH built-in StarCommands:

**\*?** or **'*'**
------------------
Prints a summary listing of available \*commands. Includes built-in commands as well as any available through loaded plugins.

**\*exit**
----------
Exits RadSSH

**\*info**
----------
Prints a listing of the host connections handled by the current RadSSH sessions. Authenticated sessions are listed first, and include the time taken to establish the connection, the remote IP address, and authenticated username. Any failed connections or failed authentications are listed at the bottom to make it easier to identify problem hosts.

Also printed are the current session quota settings and output mode.

**\*output**
------------
Select one of RadSSH's output modes. Available mode settings:

========== =====================================
  Mode              Description
========== =====================================
stream     Output is printed to the console as it arrives, with limited buffering
ordered    Output is collected per host, and printed only when the host has completed execution of the command. Host output is always in order of the listed host connections.
off        Console output is disabled. RadSSH still collects and logs output.
========== =====================================

**\*sh**
--------
Invoke a local subshell. RadSSH session persists, so when you exit the subshell, you do not need to reconnect to your remote hosts. The subshell will have an environment variable RADSSH_CONNECTIONS set to the current names of the active session hosts.

**\*result**
------------
Prints the output of the most recently run command. This does not rerun the command, instead prints the data preserved in the RadSSH buffers. \*result can be limited to a single host, multiple hosts, or if no hostnames are listed, all active hosts.

**\*status**
------------
Prints a status summary of the most recently run command. This does not rerun the command, instead prints the data preserved inf the RadSSH buffers. Summary status includes command completion, return code, and execution time.

**\*auth**
----------
Attempt to reconnect and reauthenticate to any connection that is not already authenticated. \*auth allows you to attempt different password sets, and even try alternate usernames to login, without requiring starting a new session. ``*auth`` will attempt to authenticate as the default user; you can supply an explicit username with ``*auth root``, for example.
