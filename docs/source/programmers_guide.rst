RadSSH Programmer's Guide
=========================

This is the documentation for the RadSSH API for Programmers.

If you are developing in Python, and want to make use of RadSSH, start with this overview on how to get started. Familiarity of the behavior of the RadSSH Shell is beneficial, but not completely necessary. Basic understanding of SSH command line utilities, as well as Python programming knowledge is expected.

The primary Python class provided by RadSSH is the Cluster object. A single Cluster object incorporates a number of SSH connections, a thread pool to handle parallel execution, a flexible mechanism to stream output from many hosts to the console, and a common logging facility. Typically, a single Cluster object is created and used for the duration of a session, however some applications can make use of multiple different Cluster objects at the same time. RadSSH does not impose specific limits on the size or number of Clusters that can be created, the upper limit is dependent on operating system resources (typically threads or maximum number of open files/sockets).

Prior to creating a RadSSH Cluster object, you should familiarize yourself with some of the more fundamental building blocks that are part of RadSSH.


AuthManager
-----------

The RadSSH AuthManager object is used to attempt SSH user authentication. It provides a common mechanism to identify available ways to try to authenticate a user for SSH login to various remote hosts. AuthManager supports password-based authentication as well as public key-based authentication. It also permits association of a password or a key with a specific host or matching range of hosts.

An AuthManager is associated with a single user login name. If you need to support multiple usernames, you will need to create unique AuthManager objects for each. Most SSH servers do not permit authentication attempts to switch user names during the process anyway, so a disconnect/reconnect will be necessary when switching to the new AuthManager attempts.

For basic password authentication, you can get by with only a username when creating a AuthManager object. If there are no available authentication options, then the AuthManager constructor will interactively prompt the user for the password. If you supply the password in the constructor call, then it will be registered without prompting the user. Alternatively, you can explicitly pass in either ```include_userkeys=True``` or ```include_agent=True``` to have the AuthManager load user identity keys from their home directory or access keys from a locally running SSH Agent. Either or both options can be requested. If you also supply a default password, then all available keys will be attempted first, and the password will be used if none of the keys granted access.

For more elaborate control of limiting passwords and/or keys to specific hosts, you can construct an AuthFile, and have the AuthManager load the collection of passwords and keys from the AuthFile.

If you do not pass an AuthManager object to the Cluster constructor, one will be created automatically for the currently logged in user, and the user will be prompted for a password.


Console
-------

The RadSSH Console object uses a Python Queue object to coordinate the output from multiple concurrent SSH session streams to a single console output stream. With support for ANSI escape sequences, the output on screen can be color coded to visually identify output lines from the same source. ANSI sequnces are also used to change the window title bar to present status messages that are not prone to scrolling off the screen.

A single background thread is started when the Console object is created. It loops constantly reading messages off the queue, and formatting them and printing them to the user.

As with AuthManager objects discussed above, if you do not pass a Console object when creating a Cluster, a default one will be created for you.


Configuration Settings
----------------------

Most of the settings applicable to the RadSSH Shell have direct influence on the behavior of the RadSSH Cluster object itself. If you want to provide the same custom configuration options as the RadSSH shell, you should call radssh.config.load_settings() to get a Python dictionary that is the accumulation of the embedded default settings, the (optional) system settings read from ```/etc/radssh_config```, and the (optional) user settings read from ```~/.radssh_config```. You may also include any additional override settings, similar to RadSSH Shell command line options, passing in a list of strings of the form **--keyword=value**. 


Creating The Cluster Object
---------------------------

The only required parameter to creating the Cluster object is a list of hosts, specifically a list of host/connection pairs. The first element in the pair is a label, typically a hostname or IP address, but it can be any arbitrary string. The second element should be either a connected network socket object, or **None** if the label should be used as a hostname for creating socket connections.

Connections will be established, if needed, and RadSSH handles the SSH protocol negotiation, host key verification (if enabled), and user authentication. Note that any error(s) that are encountered at any stage of the process will not raise an exception or error back to the caller. The Cluster object returned can be considered a valid Cluster, even if some (or all) of the connections are not able to be connected or authenticated; attempts to execute a command on any such host will merely be skipped. You can get the status of all host connections from the Cluster.status() call.

Once you do have a Cluster object, you can execute commands via the run_command() call, transfer files to the remote system with the sftp() call, get results from the Cluster.last_result object.

When done using a cluster, you should call Cluster.close_connections() to cleanly log out of all established sessions.
