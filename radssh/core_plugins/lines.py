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

'''Breakdown of unique lines (or words) from last command output'''

from __future__ import print_function  # Requires Python 2.6 or higher


class Histogram(object):
    def __init__(self):
        self.d = {}

    def add(self, x):
        if not isinstance(x, list):
            x = list(x)
        for y in x:
            self.d[y] = self.d.get(y, 0) + 1

    def __iter__(self):
        values = [(v, k) for k, v in self.d.items()]
        for count, value in sorted(values, reverse=True):
            yield(count, value)


def lines(cluster, logdir, cmd, *args):
    '''Print line content and count of repeated lines from last command output'''
    h = Histogram()
    for host in cluster.connections.keys():
        job = cluster.last_result.get(host)
        if job:
            res = job.result
            h.add(res.stdout.split(b'\n'))
    for count, line in h:
        print('%6d - %s' % (count, line.decode(cluster.defaults['character_encoding'], 'replace')))


def words(cluster, logdir, cmd, *args):
    '''Print line content and count of repeated words from last command output'''
    h = Histogram()
    for host in cluster.connections.keys():
        job = cluster.last_result.get(host)
        if job:
            res = job.result
            for line in res.stdout.split(b'\n'):
                h.add(line.split())
    for count, line in h:
        print('%6d - %s' % (count, line.decode(cluster.defaults['character_encoding'], 'replace')))

star_commands = {'*lines': lines, '*words': words}

if __name__ == '__main__':
    h = Histogram()
    h.add(['a', 'b', 'a', 'c', 'a', 'a', 'A', 'boogie', 'woogie'])
    print(list(h))
