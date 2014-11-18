.. RadSSH documentation master file, created by
   sphinx-quickstart on Tue Jul 22 09:00:40 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to RadSSH!
==================
 
RadSSH is a Python package for Python 2.6+/3.3+. It builds upon the Paramiko package, and PyCrypto, and provides a simple, yet powerful and extensible user "shell" environment, along with some other minor utilities, and a higher level core API for Python programmers.

RadSSH began as a single purpose tool to simplify the operational pattern of constructing ad-hoc 'for' loops in shell to invoke the command line ssh client in order to invoke a single command in sequence across dozens or hundreds of server nodes. Since its original implementation, that small utility has evolved into what is now RadSSH.

Design Principles
-----------------

RadSSH strives to always be:
 - Simple: Simple to install, simple to use, simple to understand.
 - Powerful: Combining SSH connection with parallel execution.
 - Resilient: No operational environment is perfect.
 - Flexible: No two operational environments are the same.
 - Extensible: As powerful as the core may be, Customization is where the real power lies.

Installation
------------

.. toctree::

    installation

Shell Mode
----------

For non-programmers, RadSSH's main purpose is to provide a rudimentary command execution shell. RadSSH connects and authenticates a user login to a set of hosts, which can be anywhere from a couple, a dozen, a few dozen, up to several hundred. Once connected and authenticated, the user can enter almost any shell command line text, and have it invoked, in parallel, on every remote host. The RadSSH session will remain connected, allowing the user to run multiple commands within a single session.

Users do not need to have any programming experience in order to use the shell, although familiarity with command line utilities is strongly recommended.

Contents:

.. toctree::

    shell
    shell_quickstart
    star_commands
    additional_star_commands

Additional Command Line Utilities
---------------------------------
Supplemental to the RadSSH Shell, the following command line utilities are available.
 - radssh.config
    Print a default configuration template to the console. To assist in creating a customized configuration settings file, run **python -m radssh.config > ~/.radssh_config**, and then edit the ``~/.radssh_config`` file and uncomment the lines to change the default settings.

 - radssh.plugins
    Utility to list available plugins, or install plugin modules from a single source file or all modules from a directory. Installation to the system directory will likely require administrative (root) rights.

 - radssh.pkcs
    Utility to use RSA key to encrypt/decrypt. See :ref:`pkcs` for details.

 - radssh.authmgr
    Validate a RadSSH AuthFile, and print a summary of its contents. An AuthFile is a convenient way to centrally manage many passwords and/or SSH keys that can be used by RadSSH to authenticate to all of your managed hosts. See :ref:`authmgr` for details.


Programmer Mode (API)
---------------------

For users with Python programming knowledge, the RadSSH modules can be used in other Python scripts to automate processes that can make use of SSH connectivity and parallel execution.

In addition, the RadSSH shell can make use of modular extensions in the form of plugins, which can be loaded by the shell to provide additional functionality.

.. toctree::

    plugin_developer_guide
    programmers_guide

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
