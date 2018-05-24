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

'''Add/Drop plugin for RadSSH - Add or drop connection from the cluster list'''
# Give user the ability to add or drop connections from the working
# set of cluster connections.

from __future__ import print_function  # Requires Python 2.6 or higher

import paramiko
import radssh.ssh as ssh


def star_add(cluster, logdir, cmd, *args):
    '''Add node connections to the cluster working set'''
    new_hosts = []
    for host in args:
        if not cluster.locate(host):
            new_hosts.append((host, None))
        else:
            print('Host %s already connected' % host)
    if new_hosts:
        new_cluster = ssh.Cluster(new_hosts, auth=cluster.auth, defaults=cluster.defaults)
        for k, v in new_cluster.connections.items():
            cluster.connections[k] = v
            cluster.connect_timings[k] = new_cluster.connect_timings[k]

        print('Added to cluster:')
        for host, status in new_cluster.status():
                print('%14s : %s' % (str(host), status))


def star_drop(cluster, logdir, cmd, *args):
    '''Drop node connections from the cluster - If hosts not listed, use the currently disabled hosts'''
    if args:
        hosts = args
    else:
        # If user didn't specify, implied drop of unauthenticated or disabled connections
        hosts = set([k for k, v in cluster.connections.items()
                     if not isinstance(v, paramiko.Transport) or not v.is_authenticated()])
        hosts.update(cluster.disabled)
        print('Dropping %d disabled/unauthenticated connections' % len(hosts))

    for host in hosts:
        host_key = cluster.locate(host)
        if host_key:
            print('Disconnecting from %r' % host_key)
            try:
                t = cluster.connections[host_key]
                cluster.disabled.discard(host_key)
                if hasattr(t, 'close'):
                    t.close()
            except Exception as e:
                print(repr(e))
            cluster.connections.pop(host_key)
        else:
            print('Host %s not connected' % host)

star_commands = {'*add': star_add, '*drop': star_drop}
