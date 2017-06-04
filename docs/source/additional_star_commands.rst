Additional Star Commands
========================

Info on other StarCommands

BuiltIn Star Commands
---------------------
In addition to the built-in StarCommands listed in the intro (LINK), the following commands are also available:

\*enable [host|wildcard|address|subnet] ...
  Dynamically reduce (or expand) the active set of connections. RadSSH will only attempt to execute commands against hosts that are enabled. Running **\*enable** without any arguments will restore all host connections to the default enabled state. Supplying one or more arguments will explicitly enable only the hosts that match the arguments. Arguments can be hostnames (with or without wildcards), or network addresses (optionally wildcarded or with CIDR subnet notation).

\*get </path/to/file>
  Retrieve a file from remote hosts. Save contents in a **files** subdirectory in the session log directory.

\*quota [time_limit [byte_limit [line_limit]]]
  Set (or print) RadSSH quota limits. RadSSH can automatically abandon reading command output when detecting "runaway" commands, based on idle time (no output received) or volume of output, either based on byte count or line count. When run with no arguments, \*quota will print the current quota limits.

\*chunk [size [delay]]
  Alter the RadSSH command dispatch to limit concurrent command execution to fixed size groupings, or **chunks**, with an optional sleep delay in between each chunk. By default, RadSSH will submit commands for all hosts to a queue, and the commands are executed with maximum parallelism. In some cases, this behavior can be detremental (running a **wget** command in parallel could overload a web server, for example). In these cases, you may want to limit the concurrency to a modest size with **\*chunk 10** prior to running **wget**, and the wget will execute in chunks of 10 hosts at a time. Each chunk will be allowed to complete in its entirety before the command is issued to the next chunk of hosts. Running **\*chunk 0** will reset back to the default setting of not chunking (maximum concurrency).

\*fwd host [port]
  **Experimental** Request SSH port forwarding from the connected hosts back through the client for connections to the specified host and optional port (default: 80). In order to reference the tunnel on the remote hosts, command line substitutions are enabled for **%port%** for just the "local" port, or **%tunnel%** for the usable tunnel endpoint (127.0.0.1:%port%)

\*vars
  **Experimental** Print or set internal variable settings

Star Commands From Core Plugins
-------------------------------
Many additional StarCommands are loaded by RadSSH in the form of Plugins. These can be copied and customized. Star Commands from user plugins will override the ones loaded from system plugins.

Add & Drop Host Connections
---------------------------
To change the cluster connections during an active RadSSH session.

\*add host [host] ...
  Add host connections to the active cluster.

\*drop [host] ...
  Drop host connections from the active cluster. If no hosts are listed, then \*drop will reference the set of currently enabled hosts (from \*enable) and drop the connections to any non-enabled host.

Handy Enable Shortcuts
----------------------
Based on results of the most recently run command, either output or exit status, you can use the following StarCommands to effectively \*enable without explicitly listing hosts.

\*err [status_code] ...
  Enable hosts that had an exit status that matches any listed status code. Omitting any status code will match all non-zero status codes.

\*noerr
  Enable hosts that returned success (status code 0) from the most recently run command. Equivalent to **\*err 0**.

\*match text
  Enable hosts that contain "text" in the command output (stdout, not stderr) from the most recently run command. As of 1.0.1, stderr content is included in the search.

\*nomatch text
  The logical inverse of \*match. Enables the hosts that DO NOT contain "text" in the output of the most recently run command. As of 1.0.1, stderr content is included in the search.

Searching Through Command Output
--------------------------------

\*grep text
  Print matching lines (and line numbers) from the most recently run command. This does not change the enabled set of hosts. Despite the name "grep", this does not match on regular expressions.  As of 1.0.1, stderr content is included in the search.

\*lines
  Print unique lines of output from all hosts from the most recently run command. Prints counts and sorts based on frequency (high to low).

\*words
  Print unique words (whitespace separated) from the most recently run command. Prints counts and sorts based on frequency (high to low).

File Transfer And Script Execution
----------------------------------
\*sftp source_file [destination_file]
  Copy a local file to the remote hosts. File must be on the host where RadSSH is being executed, and will be copied out using the established SSH transport using the sftp subsystem. Remote hosts must have the sftp subsystem enabled for this to work.

\*propagate host:/path/to/file
  Like \*sftp, but file to be copied resides on ONE of the remote hosts, and will be first pulled down to the RadSSH host temporarily, then pushed out to the remainder of the cluster.

\*run script_file [arg] ...
  Uses \*sftp to copy an executable script file from the RadSSH host to a temporary location on the remote hosts, and run with the supplied command line arguments. Equivalent to "\*sftp script_file /tmp/script_file; chmod +x /tmp/script_file; /tmp/script_file arg ...".

Record And Playback Session Commands
------------------------------------
Allow VCR-style recording and playing back commands from a session.

\*record filename
  Begins recording of commands to local filename. Entering \*record without a filename will stop the recording.

\*pause
  Pauses (or unpauses) the recording of commands. When unpaused, recording resumes to the same exisiting recording file.

\*playback filename
  Loads and executes session commands that were previously \*record'ed

Miscellaneous StarCommands
--------------------------
\*cd [directory]
  Have RadSSH keep track of the specified directory as the preferred "current" directory for all subsequent command invocations. Typically, each invoked command is executed in an independent session, which resets the current directory to the user home directory as a default. This plugin provides a handy way to keep track of the preferred working directory to set prior to each command invocation. Use **\*cd** with no parameters to reset back to default (no chosen directory).

\*tty [host] ...
  Sequentially invoke TTY sessions on select hosts (or entire cluster, if no hosts listed). Useful for when a fully interactive shell session is required. Since this utilized the established authenticated SSH connections, it avoids the overhead of reestablishing the connections.

\*banner
  Print the SSH signon banner received from each enabled host. For brevity, this information is not printed during signon, but is made viewable via this command.
