'''
Basic support for local shell aliases to be usable on remote clusters.
Really crude support for shorthand !$ and !! expansion
'''

from __future__ import print_function

import os
import subprocess
import logging


last_command = ''
aliases = {}


def init(**kwargs):
    '''Use subprocess to get shell to source a likely alias defining file'''
    cmd = None
    if os.path.exists(os.path.expanduser('~/.bash_profile')):
        cmd = ['bash', '-c',
               'source ~/.bash_profile; alias| sed -e \'s/^alias //\'']
    elif os.path.exists(os.path.expanduser('~/.bashrc')):
        cmd = ['bash', '-c',
               'source ~/.bashrc; alias| sed -e \'s/^alias //\'']
    elif os.path.exists(os.path.expanduser('~/.profile')):
        cmd = ['sh', '-c', 'source ~/.profile; alias']
    if cmd:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p.wait()
        for line in p.stdout:
            name, value = line.split('=', 1)
            aliases[name] = value.strip()[1:-1].replace("'\\''", "'")


def command_listener(cmd):
    '''Handle alias replacement, along with crude !! and !$'''
    global last_command
    new_cmd = cmd
    words = cmd.split()
    if not words:
        return None
    if '!!' in words:
        new_cmd = new_cmd.replace('!!', last_command)
    if '!$' in words:
        new_cmd = new_cmd.replace('!$', last_command.split()[-1])

    # Save last_command prior to alias substitution so that alias
    # substitution result is not saved into last_command.
    last_command = new_cmd
    if words[0] in aliases:
        new_cmd = new_cmd.replace(words[0], aliases[words[0]], 1)
    if new_cmd != cmd:
        return new_cmd
    return None


def print_aliases(cluster, logdir, cmd, *args):
    '''Print loaded shell alias definitions'''
    if aliases:
        print('Aliases loaded:')
        for name, value in aliases.items():
            print('    %s = \'%s\'' % (name, value))
    else:
        print('No local aliases loaded')

star_commands = {'*alias': print_aliases}
