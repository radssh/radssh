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

from __future__ import print_function
'''Genders cluster database plugin'''

import genders

genders_file = None


def init(**kwargs):
    '''To get access to shell defaults dict'''
    global genders_file
    db_file = kwargs.get('defaults', {}).get('genders_file', None)
    if db_file:
        genders_file = db_file


def lookup(label):
    '''Process a genders query to resolve into host list'''
    if not label.startswith('genders:'):
        return
    g = genders.Genders(filename=genders_file)
    matches = []
    for host in g.query(label[8:]):
        ip = g.getattrval('ip', host)
        fqdn = g.getattrval('fqdn', host)
        port = g.getattrval('port', host)
        if not port:
            port = '22'
        if ip:
            matches.append((host, ip + ':' + port, None))
        elif fqdn:
            matches.append((host, fqdn + ':' + port, None))
        else:
            matches.append((host, host + ':' + port, None))
    return iter(matches)


def gender_lookup(cluster, logdir, cmd, *args):
    '''Lookup attributes/values for cluster hosts in genders database'''
    if not args:
        args = cluster
    g = genders.Genders(filename=genders_file)
    for host in args:
        print(host, ': ', end='')
        if not g.isnode(str(host)):
            print('not in genders database', end='')
        else:
            attr = g.getattr(str(host))
            data = []
            for a in attr:
                value = g.getattrval(a, str(host))
                if value:
                    data.append('%s=%s' % (a, value))
                else:
                    data.append(a)
            print(','.join(data), end='')
        print('')


star_commands = {'*genders': gender_lookup}


if __name__ == '__main__':
    import sys
    for x in sys.argv[1:]:
        print(x, list(lookup(x)))
