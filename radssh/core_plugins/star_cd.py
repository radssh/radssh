#
# Copyright (c) 2017, 2018, 2020 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

import os

settings = {
    'curr_dir': '~',
    'paths': ''
}


def init(**kwargs):
    # convert plugin.star_cd.paths from colon-separated string to list
    settings['path_list'] = settings['paths'].split(':')


def star_cd(cluster, logdir, cmd, *args):
    '''global chdir (prepends to all cmds)'''
    if not args:
        settings['curr_dir'] = '~'
    elif os.path.isabs(args[0]) or args[0].startswith('~'):
        settings['curr_dir'] = args[0]
    else:
        settings['curr_dir'] = os.path.join(settings['curr_dir'], args[0])
    cluster.user_vars['%curr_dir%'] = settings['curr_dir']


def command_listener(cmd):
    if not cmd or cmd[0] == '*':
        return
    new_cmd = cmd
    if settings['paths']:
        new_cmd = "PATH=$PATH:{}; {}".format(settings['paths'], new_cmd)
    if settings['curr_dir'] != '~':
        new_cmd = "cd {}; {}".format(settings['curr_dir'], new_cmd)
    if new_cmd != cmd:
        return new_cmd


star_commands = {'*cd': star_cd}
