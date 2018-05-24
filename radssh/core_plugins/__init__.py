#
# Copyright (c) 2014, 2016, 2018 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

'''
RadSSH Plugins
==============

Command line module to assist in installation and reporting info
on available plugin modules. Also used by Shell API to manage the
discovery and loading of plugin modules.

A RadSSH plugin module is a Python source file that can be dynamically
imported at runtime by the RadSSH Shell. In order for the Shell to make
use of a plugin module, the module should contain at least one of the
following named objects:

 - A callable init() function
 - A callable lookup() function
 - A dict (or dict-like) object named *star_commands*


Init Function
-------------

If a module has an init() function, this will be called by the shell
when the module is loaded. The shell will pass a limited number of keyword
arguments, and for future/backward compatibility, the plugin's init
function should be defined as init(\*\*kwargs) and permit the caller to
pass in any superset of arguments beyond what is strictly necessary for
the plugin's initialization needs.

The current (API v1.0) list of arguments passed into a plugin init() call:
 - defaults: Dictionary of configuration settings {keyword: value}
 - auth: The shell's AuthManager object
 - plugins: The shell's list object of loaded plugin modules
 - star_commands: The shell's dict object mapping \*command to callable function


Lookup Function
---------------

If a module has a lookup() function, it may be called from the shell in an
attempt to translate a symbolic name into a collection of zero or more host
connections to add to the cluster. If the plugin can translate the given
string, the lookup function should pass back an iterator object, otherwise
the function should return None.

The iterator should yield a 3-tuple with the following elements:
 - Label: Typically the hostname, for display purposes in the shell
 - Host: A DNS resolvable host (or IP) to connect. Use None if Label is appropriate to use
 - Connection: An established socket-like connection to use, or None if RadSSH should initiate

For the baseline case, a tuple of (hostname, None, None) is suitable.


Star Commands
-------------

If a module has a dictionary object named 'star_commands', this mapping
will be integrated into the RadSSH shell star_command mapping. The keys
should be strings of the form '\*command', and the values should either be
objects of type StarCommand, or plain callable functions that the shell
will use to create StarCommand objects from (with defaults).

When the user enters '\*command' to the shell, the corresponding function
is called, passing the following arguments:

  - cluster: the RadSSH Cluster object managed by the shell
  - logdir: the path to the RadSSH shell log directory
  - command_line: the *entire* command line text, including the \*command and all embedded spaces
  - \*args: The space-delimited arguments from the command line (spaces are stripped)

The \*command routine is passed total control of the RadSSH shell execution process.
It can make use of the Cluster object to perform remote command execution, file
transfers, connections and disconnections, enables & disables, etc. It can also
create, update, read, delete files in the log directory. It can also create a new
Cluster object and pass it back as a return value, which will cause RadSSH to
shift context to the new cluster for the remainder of the session.
'''

from __future__ import print_function

import imp
import os
import warnings

import radssh


class StarCommand(object):
    '''
    StarCommand Class
    Allow offloading of special help/synopsis text handling from a basic
    callable \*command handler callable function. If no synopsis or help text
    is provided, the function docstring will be used. Help can be auto-invoked
    if help flags are discovered on the command line or if the parameter count
    is out of range.
    '''
    def __init__(self, handler, synopsis=None, help_text=None, auto_help=True, min_args=0, max_args=None, version=None, tab_completion=None):
        self.handler = handler
        if synopsis:
            self.synopsis = synopsis
        elif handler.__doc__:
            self.synopsis = handler.__doc__
        else:
            self.synopsis = 'Synopsis not provided and no docstring available'
        if help_text:
            self.help_text = help_text
        elif handler.__doc__:
            self.help_text = handler.__doc__
        else:
            self.synopsis = 'Help not provided and no docstring available'
        self.auto_help = auto_help
        self.min_args = min_args
        self.max_args = max_args
        self.version = version
        self.tab_completion = tab_completion

    def __call__(self, cluster, logdir, cmd, *args):
        # Bypass calling if auto-help or if argument count out of range
        if (self.auto_help and ('--help' in args or '-h' in args or '-?' in args)):
            print(self.help_text)
        elif len(args) < self.min_args:
            if self.max_args == self.min_args:
                print(cmd.split()[0], 'takes exactly', self.min_args, 'arguments')
            else:
                print(cmd.split()[0], 'takes at least', self.min_args, 'arguments')
            print(self.help_text)
        elif (self.max_args is not None and len(args) > self.max_args):
            if self.max_args:
                print(cmd.split()[0], 'takes at most', self.max_args, 'arguments')
            else:
                print(cmd.split()[0], 'takes no arguments')
            print(self.help_text)
        else:
            # Otherwise call the handler
            return self.handler(cluster, logdir, cmd, *args)


def load_plugin(src):
    '''
    Load a RadSSH Plugin module
    Returns successfully imported module object
    '''
    plugin_dir = os.path.dirname(os.path.abspath(os.path.expanduser(src)))
    src = os.path.basename(src)
    if not src.endswith('.py'):
        raise RuntimeError('RadSSH Plugins must be .py files [%s]' % src)
    module = src[:-3]
    handle = imp.find_module(module, [plugin_dir])
    plugin = imp.load_module(module, *handle)
    # Patch in StarCommand class wrapper for plain *command functions
    if hasattr(plugin, 'star_commands'):
        for name, cmd in plugin.star_commands.items():
            if not isinstance(cmd, StarCommand):
                plugin.star_commands[name] = StarCommand(cmd)
    return plugin


def discover_plugin(src):
    '''
    Attempts to load a module. If successful, returns tuple (init, lookup, star_commands).
    If an exception occurs, translate to RuntimeWarning, and return (None, None, {}).
    '''
    star_commands = {}
    lookup = None
    init = None
    try:
        plugin = load_plugin(src)
    except Exception as e:
        warnings.warn(RuntimeWarning('Could not load plugin [%s]' % os.path.basename(src), repr(e)))
        return (None, None, {})
    if hasattr(plugin, 'lookup'):
        lookup = plugin.lookup
    if hasattr(plugin, 'init'):
        init = plugin.init
    if hasattr(plugin, 'star_commands'):
        star_commands = plugin.star_commands
    return (init, lookup, star_commands)
