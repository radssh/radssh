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

'''File and Directory lookups'''

import os


def __generator(x):
    for line in x:
        line = line.strip()
        if not line or line[0] in '#.[':
            continue
        fields = line.split()
        if len(fields) == 1:
            yield((fields[0], fields[0], None))
        else:
            # Make the label be the first N-1 fields, and the hostname/IP be the last
            yield ((' '.join(fields[0:-1]), fields[-1], None))


def lookup(name):
    '''Filenames will be read for hostnames/ips; Directory names will be listed for same'''
    if os.path.isdir(name):
        return __generator(os.listdir(name))
    if os.path.isfile(name) or os.path.islink(name):
        content = open(name, 'r').readlines()
        if content:
            return __generator(content)
    return None
