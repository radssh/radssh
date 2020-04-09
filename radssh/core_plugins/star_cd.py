#
# Copyright (c) 2017, 2018 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

import os

curr_dir = ''


def star_cd(cluster, logdir, cmd, *args):
    '''global chdir (prepends to all cmds)'''
    global curr_dir
    if not args:
        curr_dir = ''
        return
    if os.path.isabs(args[0]) or args[0].startswith('~'):
        curr_dir = args[0]
        return
    curr_dir = os.path.join(curr_dir, args[0])


def command_listener(cmd):
    if (curr_dir and cmd and cmd[0] != '*'):
        return 'cd %s ; %s' % (curr_dir, cmd)

star_commands = {'*cd': star_cd}
