.. _ConfigurationSettings:

RadSSH Configuration Settings
=============================

RadSSH uses a number of configuration settings that may be of interest to customize and tweak the runtime behavior of the shell, its plugins, and/or the API Cluster behavior. While the default settings are intended to be generally appropriate for most environments, they are user-configurable to allow tailoring on a per-user or per-environment need.

The basic default settings are embedded in the RadSSH module itself, but can be amended by up to three additional stages of configuration: System Configuration, User Configuration, and Command Line Options.

To view the predefined default settings, or to produce a template file for a System Configuration file or User Configuration file, you can run ``python -m radssh.config``. This utility will output a sample settings file in comment form. If you save the output to a file, you will need to uncomment specific lines (and change values) in order to enable RadSSH configuration changes.

In general:
 - Blank lines are ignored
 - Lines starting with **#** are ignored (comment lines)
 - All other lines should be in the form **keyword=value**, where **keyword** is the option name to set, and **value** is the value to set.

System Level Configuration
--------------------------

If the file ``/etc/radssh_config`` exists, then the settings will be read in from that file. Any option settings found in the System Configuration file will supercede (not add to) the default setting. It is not necessary to specify every configuration option in the System Configuration file; only the settings you have need to change from the default.

**Important** If the System Configuration file sets **user.settings** to a blank string, then the RadSSH shell will not read settings from any User Configuration file, and will also ignore any command line options that would otherwise affect settings. If the **user.settings** option points to a file or pathname, then any settings in that file may override default or system values.

User Level Configuration
------------------------

By default, ``~/.radssh_config`` is used, but this location may be changed (or removed) by an optional System Level Configuration. Any option settings found in the User Configuration file will supercede the setting values from the default configuration or the System Configuration. The sole exception is the **user.settings** option; altering its value will have no effect if RadSSH is already processing the user settings file.

Command Line Options
--------------------

Settings provided on the command line take the highest precedence. Command line options of the form **keyword=value** override settings that are read from the User Configuration file (or any earlier location).


--------


General Settings
----------------
 - username (default: **$SSH_USER** or **$USER**)
    Login name for establishing SSH sessions
 - verbose (default: off) 
    Set to **on** to make RadSSH display more details about what it is doing while it is doing it.
 - output_mode (default: stream)
    **stream** will output lines of text to the console as they come in. **ordered** will preserve host ordering, which may give the appearance of disrupting parallelism on commands with lengthy output. **off** turns off console output while commands are running, but does not affect file logging of output. Can be changed within the shell via the **\*output** command.
 - max_threads (default: 120)
    Limit RadSSH processing threads. Independent of the baseline 1 thread per SSH connection overhead.
 - shell.console (default: color)
    Set to **mono** if the output color coding is not desired.
 - shell.prompt (default: "RadSSH $")
    The RadSSH shell prompt issued before reading each command line.
 - logdir (default: session_%Y%m%d_%H%M%S)
    Location of the session logging directory. Defaults to current directory, and supports expansion of datetime elements. Path prefix can be added, including ~ for user home directory.
 - log_out (default: out.log)
    Consolidated (all host) stdout filename. Created in the logdir directory.
 - log_err (default: err.log)
    Consolidated (all host) stderr filename. Created in the logdir directory.
 - historyfile (default: ~/.radssh_history)
    Save command line history across sessions to this file.
 - socket.timeout (default: 30)
    Network connection and read/write timeout (in seconds).
 - keepalive (default: 180)
    Send periodic network traffic to prevent connections from being terminated due to being idle.
 - hostkey.verify (default: reject)
    Determines how RadSSH handles verification of remote host keys against the ~/.ssh/known_hosts file. **reject** will reject connections if the remote host key is not already validated and accepted in the known hosts file. Other, less secure options include **prompt** which will interactively ask the user to accept unrecognized keys, **accept_new** which will automatically accept new entries, but reject if a previously accepted key no longer matches, and **ignore** which bypasses host key verification completely.
 - hostkey.known_hosts (default: ~/.ssh/known_hosts)
    Change to a new file path to keep RadSSH known hosts completely separate from OpenSSH client known hosts. If they share the common default file, keys accepted by one will be treated as accepted by the other.
 - ssh-identity (default: off)
    Set to **on** to allow RadSSH to use ~/.ssh/id_rsa, ~/.ssh/id_dsa, and ~/.ssh/identity keys
 - ssh-agent (default: off)
    Set to **on** to allow RadSSH to connect to running ssh-agent/keyring service for keys.
 - authfile (default: ~/.radssh_auth)
    Optional authentication file, to store collections of passwords and keys to use on a per host basis.
 - plugins (default: None)
    Set to a comma separated list of directories where RadSSH should look for user plugins. The system level plugin directory inside the RadSSH package is always searched, regardless of this setting; this is for additional plugin directories to be specified.
 - disable_plugins (default: None)
    Set to a comma separated list of plugins to bypass loading.
 - quota.time (default: 0)
    Avoid runaway command execution by having RadSSH abort commands if host does not produce output for a given duration (in seconds). Setting of 0 = Unlimited.
 - quota.lines (default: 0)
    Avoid runaway command execution by having RadSSH abort commands if host produces too many lines of output. Setting of 0 = Unlimited.
 - quota.bytes (default: 0)
    Avoid runaway command execution by having RadSSH abort commands if host produces too many bytes of output. Setting of 0 = Unlimited.
 - commands.forbidden (default: telnet,ftp,sftp,vi,vim,ssh)
    Prevent use of the comma separated list of programs. Anything that needs interactive keyboard input will not likely behave as anticipated under RadSSH, and should not be run.
 - commands.restricted (default: rm,reboot,shutdown,halt,poweroff,telinit)
    Have RadSSH intercept possibly dangerous commands (extremely dangerous if mistakenly run on hundreds of servers simultaneously) and require explicit confirmation that the user intends to do precisely what was typed in.
 - paramiko_log_level (default: 40)
    Set to lower numbers to increase logging output of paramiko low-level SSH operations.
 - try_auth_none (default: off)
    Perform a initial authentication probing request to determine whether the remote host accepts keys or passwords, or both. Setting to **on** may improve connection speeds by bypassing unsupported authentication attempts, but use caution, as some remote SSH implementations, like Cisco switches will abruptly drop connection if auth-none is attempted.  OpenSSH on RHEL/CentOS 5 will fail to send a banner unless auth-none is attempted.
 - force_tty=Cisco,force10networks
    Set to a comma separated list of SSH host identifiers for connections that do not support SSH exec_command. This triggers a secondary, less reliable command invocation that runs commands through a dedicated tty session. Both Cisco and Force10 switches have been identified as requiring RadSSH operate in this mode; there may be others.
 - force_tty.signon (default: "term length 0")
    When a TTY session is required, RadSSH will issue this command after initial signon. For switches, this should avoid accumulating several "--More--" prompts in the output.
 - force_tty.signoff (default: "term length 20")
    When a TTY session is required, RadSSH will issue this command prior to a clean termination.
