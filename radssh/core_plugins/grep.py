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

'''Finding and matching output content, or job return_code'''

from __future__ import print_function  # Requires Python 2.6 or higher


def star_grep(cluster, logdir, cmdline, *args):
    '''Scan (not real grep) for string matches in stdout'''
    # Get from cmdline, not args as it might have signifiance space
    pattern = cmdline[6:].encode(cluster.defaults['character_encoding'])
    for host in cluster:
        job = cluster.last_result.get(host)
        if job:
            res = job.result
            for line_number, line in enumerate(res.stdout.split(b'\n'), 1):
                if pattern in line:
                    print('%s [%d]: %s' % (host, line_number, line.rstrip().decode(cluster.defaults['character_encoding'], 'replace')))
            # Do a second pass through stderr, so matching lines can be tagged
            for line_number, line in enumerate(res.stderr.split(b'\n'), 1):
                if pattern in line:
                    print('%s [%d/stderr]: %s' % (host, line_number, line.rstrip().decode(cluster.defaults['character_encoding'], 'replace')))


def star_match(cluster, logdir, cmdline, *args):
    '''Combine *grep with *enable for hits (*match) or misses (*nomatch)'''

    if cmdline.startswith('*nomatch'):
        pattern = cmdline[9:].encode(cluster.defaults['character_encoding'])

        def include_host(pattern, buffer):
            return pattern not in buffer
    else:
        pattern = cmdline[7:].encode(cluster.defaults['character_encoding'])

        def include_host(pattern, buffer):
            return pattern in buffer
    enable_list = []
    for host in cluster:
        job = cluster.last_result.get(host)
        if job:
            res = job.result
            if include_host(pattern, res.stdout + res.stderr):
                enable_list.append(str(host))
    cluster.enable(enable_list)


def star_error(cluster, logdir, cmdline, *args):
    '''Do a *enable for hosts with specific error code(s), or any non-zero if no list specified'''

    enable_hosts = []
    specific_codes = [int(x) for x in args]
    for host in cluster:
        try:
            job = cluster.last_result[host]
            if job.completed:
                if not specific_codes and job.result.return_code != 0:
                    # Match any non-zero return code
                    enable_hosts.append(str(host))
                elif job.result.return_code in specific_codes:
                    # or if an explicit list was specified, check against that
                    enable_hosts.append(str(host))
        except (TypeError, KeyError) as e:
            pass
    if enable_hosts:
        print('Enabling:', enable_hosts, '( %d hosts)' % len(enable_hosts))
        cluster.enable(enable_hosts)
    else:
        print('No hosts had matching error codes. No change to *enable was made')


def star_noerror(cluster, logdir, cmdline, *args):
    '''Do a *enable for only the hosts with success return codes from last command'''
    star_error(cluster, logdir, '*error 0', 0)


star_commands = {
    '*grep': star_grep,
    '*match': star_match,
    '*nomatch': star_match,
    '*err': star_error,
    '*noerr': star_noerror,
}
