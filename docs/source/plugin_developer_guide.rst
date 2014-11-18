.. _DevelopingPlugIns:

Developing RadSSH Plugins
=========================

As an alternative to writing Python programs that use the RadSSH API, the RadSSH Shell supports dynamic runtime extension through a loadable plugin architecture. By relying on the RadSSH shell to manage the cluster creation and management, the code required to implement a plugin module is very small in relation to the powerful functionality that can be added. While a basic understanding of the RadSSH API is beneficial to a plugin developer, it is not necessary to achieve expert knowledge about the API in order to start writing some very powerful extensions to the RadSSH shell.

RadSSH plugins are written in Python, so it is expected that plugin developers know the Python language. Familiarity with the RadSSH Shell, from a user's perspective, is also needed.

There are two basic types of RadSSH plugins: Command plugins, which define (or redefine) RadSSH StarCommands, and Lookup plugins, which can handle custom translation of a symbolic name (or names) into a collection of hosts. A plugin module can be both a Command plugin as well as a Lookup plugin at the same time. Future releases of RadSSH may introduce additional plugin types.

By default, the RadSSH shell will load plugins from the installation directory's ``plugins`` directory only. Additional plugin directories can be specified with the ``plugins`` configuration setting, either listed in the RadSSH configuration file, or on the command line with the form ``plugins=~/radssh_plugins``

Anatomy of a RadSSH Plugin Module
---------------------------------

A RadSSH Plugin module is an importable Python source file. It must end with a **.py** filename suffix, and reside either in the system plugin directory, or in a directory that is listed in the configuration setting parameter named "plugins", which can be defined either in the ``.radssh_config`` file or on the RadSSH Shell command line. Running the RadSSH Shell with ``verbose=on`` will print out plugin names as they are loaded by the shell, and include errors and traceback information when a plugin fails to load. It is recommended to have ``verbose=on`` when developing and testing plugins.

A plugin module may contain whatever Python code is needed for the plugin to operate, including ``import`` statements, class and function definitions, and variables. Executable statements are also permitted, and will be executed when the module is imported by the RadSSH shell. In order for the plugin to be able to be integrated into the RadSSH shell itself, Python objects with specific names need to be defined within the module. It is permissible to define any combination of these special object names, or even define none of them (resulting in a very limited plugin).

The plugin "special" names are:
 * **init** - A Python function that will be called after the module is successfully imported by the RadSSH Shell. This gives the plugin access to shell variables it may need during execution. The init function should be defined as **init(\*\*kwargs)**, and explcitly reference the keyword arguments that are needed.
    Keyword arguments currently passed from the RadSSH Shell (subject to change):
     *  **defaults** - Python dict object of the user configuration setting defaults
     *  **auth** - The AuthManager object used by the shell
     *  **plugins** - Python dict object of loaded plugin modules, indexed by module name
     *  **star_commands** - Python dict object of StarCommands
     *  **shell** - The RadSSH shell invocation function itself
    
  All but the shell object are mutable; use extreme caution if you attempt to alter them. When in doubt, treat them as read-only.

  If your plugin has no need to read (or update) these objects, and does not require any runtime initialization steps, you do not need to define an **init** function.

 * **lookup** - A Python function that takes a single argument (name), and returns an iterator object or None. If the symbolic name passed in can be translated to a set of zero or more hosts, the iterator object will be used by the shell to fetch the connection info. If the name can not be translated by the lookup function, the function should return None.

  When returning an iterator, the iterator should produce 3-tuples or the form (label, hostname, socket). The label should be a string, which is used for labeling the console output, as well as the logfile(s) associated with the host. It is not required for the label to be a resolvable hostname or IP address. The hostname element of the tuple should be an actual hostname or IP address that can be used as a destination for connecting a socket. It may include a port specifier, if the connection destination is not the default SSH port (22); use the form "hostname:port" if needed. The socket element of the tuple, under normal circumstances should be None, in which case the shell will establish the socket connection using the hostname (and possibly port) passed back in the previous tuple element. If the host can not be connected to by a plain socket connection, perhaps needing some firewall/proxy/port-knock manipulation, then it is the responsibility of the plugin to perform these steps and open the socket connection, passing the open socket object back via the iterator

 * **command_listener** - A Python function that takes a single argument (command_line). The plugin is notified of each command line content from the shell, just prior to execution. Informative only.


 * **star_commands** - A Python dict object, with strings of the form ``*command`` as keys, and values of StarCommand class objects (plain functions will be converted to default StarCommand instances). This dict handles the mapping of ``*command`` to the underlying callable function that will be invoked by the shell. A plugin module can define and implement multiple ``*commands`` in the dict object.


StarCommand Class Objects
-------------------------

The :class:`radssh.plugins.StarCommand` class object provides the standardized interface for defining custom ``*command`` functions. It extends the basic call interface to include independent function synopsis and help_text strings (previously were combined as the function docstring), and under what conditions the shell will print help text on demand or if an improper number of arguments are supplied on the command line.

The ``*command`` handler function itself will be passed in the following arguments:
 * **cluster** - The RadSSH Cluster object - Can be used to read the results of the previous command, or to execute command lines from under control of the ``*command`` itself. Refer to the API documentation :class:`radssh.ssh.Cluster`
 * **logdir** - the path to the RadSSH Shell session specific logging directory.
 * **command_line** - the text input as the command line (with spaces preserved)
 * **\*args** - The (space delimited) split of command line arguments


