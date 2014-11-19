RadSSH ChangeLog
================

Version 0.3.3 (2014-12-03 r5239)
--------------------------------
Core Fixes:
 - Added log_out and log_err settings to capture unified session output to a common file
 - Added %ssh_version% variable substitution
 - Fixed regression that left TAB completion feature completely broken
 - Basic Windows platform support - formatting needs work in the absence of ANSI.SYS

Plugins:
 - New \*pushkey command to add, if necessary, publickey to ~/.ssh/authorized_keys


Version 0.3.3 rc6 (2014-11-19 r5174)
------------------------------------
Core Fixes:
 - AuthManager now closes thread-specific Agent connection to not exhaust open file/socket handles.
 - Added try_auth_none=on as configuration option.  Must be **ON** for CentOS5 to get hte SSH signon banner. Must be set to **OFF** for connecting to Cisco switches.
 - Use proper key value for loaded_plugins to detect duplicates.

Plugins:
 - Add support for plugins to supply a ``command_listener()`` function. RadSSH shell will feed command lines to the plugin for informational review.
 - Plugin ``init()`` function now includes RadSSH shell as an argument.
 - VCR plugin updated to use command_listener instead of monkeypatching.  Playback files no longer treat blank lines as EOF.


Version 0.3.3 rc5 (2014-11-12 r5123)
------------------------------------
Core Fixes:
 - Added Revised BSD License info
 - Added license block command to all source files
 - Added Frequently Asked Questions file
 - New module radssh.plugins to manage install/listing of plugins
 - Removed import check of dependency modules (broke setup.py)
 - Better handling of Cluster creation with omitted defaults
 - Rework enabled connections via a Set (of disabled) connections. Simpler and should be better performance
 - setup.py imports radssh to get common versioning info
 - Add plugins and disable_plugins to config defaults (blank setting)
 - Failures loading plugins report as summary only, unless --verbose=on
 - Console quiet() call returns existing setting for save/restore
 - Cluster enable() call can now take an empty list to disable ALL hosts
 - Preliminary plugin package code - StarCommand class added
 - Fix __main__ to import paramiko and Crypto for version information
 - Added ability to force RadSSH to use invoke_shell() as a persistent session instead of open_session() + exec_command() for each command.  Apparently needed for some IOS hosts (Force10/Cisco). Triggered by matching server SSH version string. *** Very Experimental ***


Plugins:
 - \*sftp now populates cluster.last_result for status info
 - \*tty better handling of multi-byte keystrokes (arrow keys)
 - \*tty prompt user prior to connecting per host to skip/abort
 - Genders database support plugin (https://computing.llnl.gov/linux/genders.html)
 - Update \*match to issue a single cluster.enable call due to Set reworking
 - \*status behaves better if cluster.last_result is not set
 - New \*banner plugin to print SSH banner contents on demand (requires Paramiko >= 1.13)

API:
 - Changed AuthManager default parameters to False for ssh_agent and identity file usage

Version 0.2.0 (2014-09-19 r4830)
--------------------------------
Core Fixes:
 - Beta support for Python3 (relies on setup.py invoking 2to3 at install)
 - If console output is not a tty, revert to monochrome output even if shell.console is set to color

Plugins:
 - \*tty properly heeds enabled hosts, will refuse to run with >5 enabled hosts


Version 0.1.1 (2014-09-08 r4681)
--------------------------------
Core Fixes:
 - Include paramiko and netaddr as dependencies in setup.py
 - Fix TAB-completion for paths including dashes (like hpcc-data)
 - TAB-completion no longer searches $PATH for executable names
 - Added __main__ for radssh.authmgr to syntax check user auth files
 - Allow \*auth to reuse existing auth options if switching to a new user
 - Better handling of deferred errors when referencing PKCS under old PyCrypto
 - Coding style adopting PEP8 guidelines, early Py3K support (alpha)

Configuration Changes/Additions:
 - shell.prompt=RadSSH $ 
 - shell.console=[color|monochrome] 
 - commands.forbidden=telnet,ftp,sftp,vi,vim,ssh (previously hard-coded)
 - commands.restricted=rm,reboot,shutdown,halt,poweroff,telinit (previously hard-coded)

Plugins:
 - Jumpbox: Handle exceptions from open_channel failures and duff connections

Version 0.1.0 (2014-08-19 r4552)
--------------------------------
First officially versioned release
