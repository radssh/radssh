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

'''IP Lookup Plugin'''

import netaddr

# Lookup function for plugins
# Return an iterator if we accept responsibility, or None to pass


def lookup(name):
    '''Handle IPNetwork and IPGlob (and IPAddress) notation'''
    try:
        ip = netaddr.IPAddress(name)
        return __generator([ip])
    except Exception as e:
        pass

    try:
        subnet = netaddr.IPNetwork(name)
        return __generator(subnet)
    except Exception as e:
        pass

    try:
        glob = netaddr.IPGlob(name)
        return __generator(glob)
    except Exception as e:
        pass

    return None


def __generator(x):
    '''Pass back 3-tuple (label, host, socket) - socket is None to defer actual connection til later'''
    for item in x:
        yield (item, str(item), None)
