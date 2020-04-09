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

'''Reauthentication - Provide a 2nd chance connect/auth without needing
to exit and re-run the shell'''


def star_auth(cluster, logdir, cmd, *args):
    '''Attempt another auth to any unauthenticated nodes'''
    if len(args) == 0:
        user = None
    else:
        user = args[0]
    cluster.reauth(user)

star_commands = {'*auth': star_auth}
