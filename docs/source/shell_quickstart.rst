RadSSH Shell - Your First Session
=================================

Start here if you want to jump right in!

To test if RadSSH is properly installed with all prerequisites, you can run: ``python -m radssh`` (If you get an error stating that radssh is a package and can not be directly executed, your Python is likely version 2.6, and you should run ``python -m radssh.__main__`` instead). You should see a short output summary of RadSSH, along with version information on RadSSH itself, and the Paramiko and PyCrypto modules that it depends on. If you get errors, there is a problem with the installation, and you should resolve it : see :doc:`Installation Guide`.

If the main module summary is functioning, you should be ready to go!

Starting Up A Shell Session
---------------------------

For this example session, I will use huey, dewey, louie, and scrooge as sample hostnames. For your environment, you should use three or four hosts (by name or IP) that you typically access via ssh. You can also, for demonstration purposes, use localhost, 127.0.0.1, and the hostname of your client to mimic 3 separate hosts, even though each connection will wind up being the same destination.

Start the session by running ``python -m radssh.shell huey dewey louie scrooge``. You should be prompted to enter a password associated with the current user. Once entered, network connections are attempted to the remote (or local) hosts via SSH on the default port (22). Once connections are made, user authentication is attempted with the username and provided password, and at the conclusion, the default **RadSSH $** prompt is displayed::

    [paul@darkstar ~]$ python -m radssh.shell huey dewey louie scrooge
    Please enter a password for (paul) :
    Connecting to 4 hosts...
    X...
    RadSSH $
    
The progress of connections is indicated by a series of 1-character codes:
 - **.**    Connection has been established with successful user authentication
 - **O**    Connection was established, but user authentication failed
 - **X**    Network connection failed to be established

First Meta-Command: ***info**
-----------------------------

The connection progress line of dots, with maybe a few X's and O's, is intentionally terse. RadSSH does keep more detailed information about connections and authentication status. This information can be printed on demand, using one of the built-in meta-commands, ``*info`` ::

    RadSSH $ *info
    *** Cluster Status ***
         dewey : (  0.210s) Authenticated as paul to 10.176.156.25
          huey : (  0.151s) Authenticated as paul to 10.176.156.26
         louie : (  0.313s) Authenticated as paul to 10.173.217.15
       scrooge : (   0.001s) [Errno -2] Name or service not known
    Current Quota Settings:
        Idle (not Total) Time: Unlimited
        Output Byte Limit: Unlimited
        Output Byte Limit: Unlimited
    Cluster output mode: stream
    RadSSH $ 

The names display along with the elapsed time taken to connect and authenticate, as well as the authenticated username and remote IP address of the socket connection. Any problem connections will appear grouped at the end of the list, and include information about what specifically prevented the connection or authentication. In our example, RadSSH failed to establish a connection to ``scrooge`` because it is not a known host. RadSSH does not treat this as a critical error; commands will not be run on ``scrooge`` unless it is later reconnected and authenticated. The list entry for ``scrooge`` is kept as a dormant connection.

``*info`` is one of many available meta-commands, or StarCommands available when using RadSSH. All command lines that begin with ``*`` are never invoked on the remote hosts; instead these are handled within RadSSH itself, or a RadSSH plugin. For details, see :doc:`Star Commands`

Running Some Basic Commands
---------------------------

You can enter shell command line(s) at the **RadSSH $** prompt. Press [Enter] to submit them for execution on all active remote hosts. The example shows a few basic informational commands ``uptime``, ``date`` and ``df -h /`` to report on a few details of each server::

    RadSSH $ uptime
    [louie] 13:51  up 512 days,  2:07, 0 users, load averages: 2.15 2.10 2.09
    [huey]  13:36:22 up 29 days,  1:41,  8 users,  load average: 0.00, 0.00, 0.00
    [dewey]  13:36:23 up 29 days,  2:42,  1 user,  load average: 0.00, 0.01, 0.05
    
    Summary of failures:
    None    - ['scrooge']
    Average completion time for 3 hosts: 0.050224s
    RadSSH $ date
    [huey] Tue Jul 22 13:36:31 EDT 2014
    [louie] Tue Jul 22 13:51:10 EDT 2014
    [dewey] Tue Jul 22 13:36:31 EDT 2014

    Summary of failures:
    None    - ['scrooge']
    Average completion time for 3 hosts: 0.044666s
    RadSSH $ df -h /
    [louie] Filesystem     Size   Used  Avail Capacity  Mounted on
    [louie] /dev/disk0s3   234G   134G    99G    57%    /
    [huey] Filesystem                 Size  Used Avail Use% Mounted on
    [huey] /dev/mapper/vg-RootFS   24G   16G  7.4G  68% /
    [dewey] Filesystem                        Size  Used Avail Use% Mounted on
    [dewey] /dev/mapper/vg-LogVol00   20G   15G  3.7G  80% /

    Summary of failures:
    None    - ['scrooge']
    Average completion time for 3 hosts: 0.046714s
    RadSSH $ 

Each command resulted in one (or two) lines of output from each host. On terminals with ANSI code support, they should also be presented with color coding, adding distinction between lines of output from different hosts. Because the commands were run on the remote hosts in parallel, the ordering of the output is not guaranteed to be printed in a predetermined order; results are printed (by default) in the order that they arrive on the network. In addition, at the conclusion of the output section is a summary of failures (if any) and a timing summary for the execution of the command line across all of the remote connections.

Try other various commands, and get a taste for the output. The RadSSH shell does retain command line history, so you can use up/down arrows, and <Ctrl-R> for searching history. At this time, Tab-Completion is not available for command and path/filename completion.

Ending A RadSSH Session
-----------------------

In most shells, typing ``exit`` normally exits the shell. In RadSSH, typing exit results in actually running the exit command on all active remote nodes, which produces no output and lands you right back at the **RadSSH $** prompt. You can confirm this not only by running ``exit`` (which returns a default status code of 0, indicating success), but if you run ``exit 100``, you will see in the summary of failures, the return code 100, followed by a list of servers that reported back a process status of 100. In the event that the list of servers is lengthy, then only a count of the number of servers is printed, not the entire list.

In order to cleanly exit from RadSSH, you should indicate EOF on input by typing <Ctrl-D>, or you can use the StarCommand ``*exit``. Like ``*info``, ``*exit`` is a RadSSH built-in meta-command that does not get passed on to the remote hosts to run.

A Bonus Directory (Default Logging)
-----------------------------------

When RadSSH exits, and you return back you your normal shell prompt, do a directory listing with ``ls -ltr``, and you should see a newly created directory *session_YYYYMMDD_hhmmss* with recent Year+Month+Day and Hour+Minute+Seconds. RadSSH, by default, will log session commands, and host output (both stdout and stderr, if applicable) into individual files in this session directory.

