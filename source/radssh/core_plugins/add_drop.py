#
# Copyright (c) 2014 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

'''Add/Drop plugin for RadSSH - Add or drop connection from the cluster list'''
# Give user the ability to add or drop connections from the working
# set of cluster connections.

from __future__ import print_function  # Requires Python 2.6 or higher

import radssh.ssh as ssh


def star_add(cluster, logdir, cmd, *args):
    '''Add node connections to the cluster working set'''
    for host in args:
        if not cluster.locate(host):
            try:
                t = ssh.connection_worker(host, None, cluster.auth)
                cluster.connections[host] = t
            except Exception as e:
                print(host, repr(e))
        else:
            print('Host %s already connected' % host)


def star_drop(cluster, logdir, cmd, *args):
    '''Drop node connections from the cluster - If hosts not listed, use the currently disabled hosts'''
    if not args:
        hosts = list(cluster.disabled)
    else:
        hosts = args

    for host in hosts:
        host_key = cluster.locate(host)
        if host_key:
            print('Disconnecting from %r' % host_key)
            try:
                t = cluster.connections[host_key]
                t.close()
                cluster.disabled.discard(host_key)
            except Exception as e:
                print(repr(e))
            cluster.connections.pop(host_key)
        else:
            print('Host %s not connected' % host)

star_commands = {'*add': star_add, '*drop': star_drop}
