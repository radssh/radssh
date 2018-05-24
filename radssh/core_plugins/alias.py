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
Basic support for local shell aliases to be usable on remote clusters.
Really crude support for shorthand !$ and !! expansion
'''

from __future__ import print_function

import os
import subprocess
import readline
import logging


def gather_history():
    '''Pull history lines as a list'''
    n = 1
    result = []
    while True:
        line = readline.get_history_item(n)
        if not line:
            break
        result.append(line)
        n += 1
    return result


def star_history(cluster, logdir, cmd, *args):
    '''Print recent RadSSH command line history'''
    hist = gather_history()
    for n, line in enumerate(hist, 1):
        print('%5d - %s' % (n, line))

last_command = ''
aliases = {}


def init(**kwargs):
    '''Use subprocess to get shell to source a likely alias defining file'''
    cmd = None
    if os.path.exists(os.path.expanduser('~/.bash_profile')):
        cmd = ['bash', '-ic',
               'source ~/.bash_profile; alias| sed -e \'s/^alias //\'']
    elif os.path.exists(os.path.expanduser('~/.bashrc')):
        cmd = ['bash', '-ic',
               'source ~/.bashrc; alias| sed -e \'s/^alias //\'']
    elif os.path.exists(os.path.expanduser('~/.profile')):
        cmd = ['sh', '-ic', '. ~/.profile; alias']
    if cmd:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        p.wait()
        for line in p.stdout:
            name, value = line.decode().split('=', 1)
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
    if len(words) == 1 and words[0][0] == '!':
        # History substitution !nnn
        try:
            n = int(words[0][1:])
            hist = gather_history()
            new_cmd = hist[n - 1]
        except ValueError:
            pass

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

star_commands = {'*alias': print_aliases,
                 '*history': star_history}
