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

'''Jumpbox support - allow connections to be made through paramiko connections via tunneling'''
import paramiko
import getpass

import radssh.ssh as ssh
from radssh.authmgr import AuthManager
import radssh.star_commands as star

init_data = {}


class JumpData(object):
    pass

jb = JumpData()


def init(**kwargs):
    init_data.update(kwargs)
    jb.cluster = ssh.Cluster([], kwargs['auth'], console=None, defaults=kwargs['defaults'])


def do_jumpbox_connections(via, dest):
    k = jb.cluster.locate(via)
    if not k:
        print('Jumpbox', via, 'not found')
        return
    jump = jb.cluster.connections[k]
    if not jump.is_authenticated():
        print('Jumpbox', via, 'does not have authenticated connection')
        print('Skipping connections through jumpbox to:', dest)
        return
    for y in dest:
        try:
            s = jump.open_channel('direct-tcpip', (y, 22), ('', 0))
            yield (('--'.join([via, y]), y, s))
        except Exception as e:
            print('Unable to connect to %s via jumpbox %s' % (y, via))
            print(repr(e))


def add_jumpbox(host):
    if jb.cluster.locate(host):
        return
    print('Connecting to jumpbox:', host)
    try:
        t = ssh.connection_worker(host, None, init_data['auth'])
        retries = 3
        while not t.is_authenticated() and retries > 0:
            # Try interactive password authentication
            print('Failed to authenticate to Jumpbox (%s)' % host)
            jb_user = raw_input('Enter username for [%s]: ' % host)
            jb_passwd = getpass.getpass('Enter password for %s@%s: ' % (jb_user, host))
            reauth = AuthManager(jb_user, auth_file=None, include_agent=False,
                                 include_userkeys=False, default_password=jb_passwd)
            t = ssh.connection_worker(host, None, reauth)
            retries -= 1

    except Exception as e:
        print(host, repr(e))
    finally:
        jb.cluster.connections[host] = t


def lookup(name):
    if not name.startswith('jump:'):
        return None
    hops = name[5:].rsplit('/', 1)
    add_jumpbox(hops[0])
    return do_jumpbox_connections(hops[0], hops[1].split(','))


def jump_info(cluster, logdir, cmd, *args):
    print(jb)
    print(jb.cluster)
    star.star_info(jb.cluster, logdir, cmd, *args)


star_commands = {'*jump': jump_info}
