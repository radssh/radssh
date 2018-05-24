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

'''
banner.py
=========

Use paramiko.Transport.get_banner() API call, introduced in 1.13
to allow print access to SSH banner text.
'''
import paramiko

from radssh.ssh import CommandResult
from radssh.dispatcher import JobSummary

if not hasattr(paramiko.Transport, 'get_banner'):
    raise RuntimeError('Paramiko >= 1.13 required for get_banner()')


def banner(cluster, logdir, cmd, *args):
    cluster.last_result = {}
    for host, conn in cluster.connections.items():
        if isinstance(conn, paramiko.Transport):
            banner_text = conn.get_banner()
            if banner_text is not None:
                cluster.console.q.put(((host, False), banner_text.decode(cluster.defaults['character_encoding'], 'replace')))
                result = CommandResult(command='*banner', return_code=0,
                                       status='*** Complete ***',
                                       stdout=banner_text, stderr=b'')
            else:
                cluster.console.q.put(((host, True), 'No SSH Banner Received'))
                result = CommandResult(command='*banner', return_code=0,
                                       status='*** Complete ***',
                                       stdout=b'', stderr=b'No SSH Banner Received')
        else:
            cluster.console.q.put(((host, True), str(conn)))
            result = CommandResult(command='*banner', return_code=0,
                                   status='*** Complete ***',
                                   stdout=b'', stderr=str(conn).encode(cluster.defaults['character_encoding'], 'xmlcharrefreplace'))
        cluster.last_result[host] = JobSummary(True, 0, result)
    if logdir:
        cluster.log_result(logdir)


star_commands = {'*banner': banner}
