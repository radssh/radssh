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
RadSSH Plugins Manager Module
=============================

Runnable via ```python -m radssh.plugins```

Utility program to install or list available plugins.
'''

from __future__ import print_function

import sys
import os
import shutil

import radssh
import radssh.plugins


def usage():
    print('Usage:')
    print('    python -m radssh.plugins list [directory] ...')
    print('    python -m radssh.plugins install [plugin_file|directory] ...')


def install(plugin, dest):
    '''
    Install a single plugin module
    '''
    # Use discover_plugin to test load, and display warnings if plugin has issues
    # Install anyway (may consider blocking)
    init, lookup, cmds = radssh.plugins.discover_plugin(plugin)
    try:
        shutil.copy(plugin, dest)
        print('Installed plugin:', plugin)
    except Exception as e:
        print('Unable to install:', plugin)
        print(repr(e))


def install_plugins(*args):
    if not args:
        print('Nothing to install')
        return
    install_dir = os.path.dirname(radssh.plugins.__file__)
    print('Installing plugins into', install_dir)
    for x in args:
        if os.path.isdir(x):
            for plugin in sorted(os.listdir(x)):
                install(os.path.join(x, plugin), install_dir)
        elif os.path.isfile(x):
            install(os.path.abspath(x), install_dir)
        else:
            print('Skipping:', x, '(is not directory or file)')


def list_plugins(*args):
    if not args:
        args = [os.path.dirname(radssh.plugins.__file__)]
    for d in args:
        print('Plugins in', d)
        for src in sorted(os.listdir(d)):
            if src.endswith('.py') and not src.startswith('__'):
                try:
                    init, lookup, cmds = radssh.plugins.discover_plugin(os.path.join(d, src))
                    print('    ', src)
                    if init:
                        print('        plugin has init() function')
                    if lookup:
                        print('        plugin has lookup() function')
                    if cmds:
                        print('        plugin defines %d *commands' % len(cmds))
                        for name, cmd in cmds.items():
                            print('            %s - %s' % (name, cmd.synopsis))
                except Exception as e:
                    print('    ', src)
                    print('         *** Error loading plugin: [%s] ***' % src)
                    print('        ', repr(e))
                print()


subcommands = {'list': list_plugins, 'install': install_plugins}


if __name__ == '__main__':
    print('RadSSH Plugin Manager')
    if len(sys.argv) < 2 or sys.argv[1] not in subcommands:
        usage()
        sys.exit(1)
    subcommands[sys.argv[1]](*sys.argv[2:])
