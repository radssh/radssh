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
Star Commands (*command) Support

Command lines beginning with '*', are either intended, in which case
the user is so clever that they can work around anything, or a mistake.
Almost certainly the latter; so the shell basic command line scanning
will divert command lines starting with '*' to an internal handler call
to a method mapped via a dict of star_commands.

This dict can be extended via plugins. This module provides the core
collection of *commands.
'''
from __future__ import print_function  # Requires Python 2.6 or higher


import os
import socket
import select
import sys
import threading
import pprint
import traceback
import logging

from .ssh import CommandResult
from .plugins import StarCommand

forwarding_dest = ('127.0.0.1', 80)

# Common parameters to all *commands
#    the RadSSH cluster object
#    Path to the current log directory (or None)
#    Entered command line string (unaltered)
#    Arguments (the command line split() result)


def star_help(cluster=None, logdir=None, cmdline=None, *args):
    '''Help on *commands'''
    if args:
        for cmd in args:
            if not cmd[0] == '*':
                cmd = '*' + cmd
            if cmd in commands:
                print('Help for', cmd)
                print(commands[cmd].help_text)
            else:
                print('Unknown command:', cmd)
        return
    for cmd in sorted(commands.keys()):
        func = commands[cmd]
        if not isinstance(func, StarCommand):
            print('%s (old-style) - %s' % (cmd, func.__doc__))
            continue
        if func.version:
            print('%s (%s) - %s' % (cmd, func.version, func.synopsis))
        else:
            print('%s - %s' % (cmd, func.synopsis))


def star_enable(cluster, logdir, cmdline, *args):
    '''Enable specific nodes by name, wildcard, network, or IP glob'''
    if args and args[0] != '*':
        cluster.enable(args)
    else:
        cluster.enable()


def star_info(cluster, logdir, cmdline, *args):
    '''Display detailed info for current cluster (connections, etc)'''
    print('*** Cluster Status ***')
    for host, status in cluster.status():
        print('%14s : %s' % (str(host), status))
    if cluster.disabled:
        print('-' * 40)
        print('Disabled Nodes:')
        print(','.join([str(x) for x in cluster.disabled]))
    star_quota(cluster, logdir, '')
    print('Cluster output mode: %s' % cluster.output_mode)


def star_status(cluster, logdir, cmdline, *args):
    '''Print result itemization'''
    if not args:
        args = cluster
    if not cluster.last_result:
        print('Cluster status not availble / no command has been run')
        return
    missing_results = []
    for x in args:
        job = cluster.last_result.get(cluster.locate(x), None)
        if job:
            res = job.result
            running_time = job.end_time - job.start_time
            if isinstance(res, CommandResult):
                print('%s: %s - Return Code [%s] took %0.4g seconds' % (x, res.status, res.return_code, running_time))
            else:
                print('%s: *** Error *** [%s] took %0.4g seconds' % (x, repr(res), running_time))
        else:
            missing_results.append(x)
    if missing_results:
        if len(missing_results) < 10:
            print('Missing results from:', ', '.join(missing_results))
        else:
            print('Missing results from %d hosts' % len(missing_results))


def star_result(cluster, logdir, cmdline, *args):
    '''Re-print stdout/stderr for last run job(s)'''
    # Check for redirect (> or >>)
    if '>>' in cmdline:
        hosts, outfile = cmdline.split('>>')
        result_file = open(outfile.strip(), 'ab')
        args = hosts.split()[1:]
    elif '>' in cmdline:
        hosts, outfile = cmdline.split('>')
        result_file = open(outfile.strip(), 'wb')
        args = hosts.split()[1:]
    else:
        result_file = None
    if not args:
        args = cluster
    for x in args:
        job = cluster.last_result.get(cluster.locate(x), None)
        if job:
            res = job.result
            running_time = job.end_time - job.start_time
            if isinstance(res, CommandResult):
                if result_file:
                    result_file.write(('<<< %s: "%s" %s - Return Code [%s] took %0.4g seconds >>>\n' % (x, res.command, res.status, res.return_code, running_time)).encode())
                if res.stdout:
                    cluster.console.q.put(((x, False), res.stdout.decode(cluster.defaults['character_encoding'], 'replace')))
                    if result_file:
                        result_file.write(res.stdout)
                if res.stderr:
                    cluster.console.q.put(((x, True), res.stderr.decode(cluster.defaults['character_encoding'], 'replace')))
                    if result_file:
                        result_file.write(res.stderr)
            else:
                cluster.console.q.put(((x, True), repr(res)))
                if result_file:
                    result_file.write(('<<< %s: Failed [%s] >>>\n' % (x, repr(res))).encode())
            cluster.console.join()
            if result_file:
                result_file.write(b'\n\n')
    if result_file:
        result_file.close()
        cluster.console.q.put((('*result', False), 'Output saved to file "%s"' % outfile.strip()))


def star_get(cluster, logdir, cmdline, *args):
    '''Get a file or files from all enabled hosts'''
    save_res = cluster.last_result
    save_mode = cluster.output_mode
    cluster.output_mode = 'off'
    dest = os.path.join(logdir, 'files')
    print('Collecting files into %s' % os.path.abspath(dest))

    for filename in args:
        print('Getting %s...' % filename)
        namepart = os.path.split(filename)[1]
        res = cluster.run_command('cat %s' % filename)
        for host, job in res.items():
            result = job.result
            if job.completed and result.return_code == 0:
                if not os.path.isdir(os.path.join(dest, str(host))):
                    os.makedirs(os.path.join(dest, str(host)))
                with open(os.path.join(dest, str(host), namepart), 'wb') as f:
                    f.write(result.stdout)
    cluster.output_mode = save_mode
    cluster.last_result = save_res


def star_shell(cluster, logdir, cmdline, *args):
    '''Drop into a local shell - exit subshell to return with session intact'''
    connections = []
    for k in cluster:
        if k not in cluster.disabled:
            connections.append(str(k))

    os.putenv('RADSSH_CONNECTIONS', ' '.join(connections))
    os.system('PS1="(RadSSH subshell) $ " bash')


def forwarding(channel, origin, server):
    # Handler is called from the Transport thread itself
    # That means in order to have data from the remote end, we
    # have to return so that the transport thread can manage its
    # own data transfer. Create a new socket for the destination end
    # and do the equivalent of netcat between the sockets in a
    # different thread. Otherwise we deadlock :(
    try:
        s = socket.create_connection(forwarding_dest)
        bk = threading.Thread(target=flow, args=(s, channel))
        bk.setName('RemoteTunnel_%s' % channel.get_name())
        bk.start()
    except Exception as e:
        print('Remote forward failed:', repr(e))


def flow(s1, s2):
    while True:
        r, w, x = select.select([s1, s2], [], [], 5.0)
        if s1 in r:
            data = s1.recv(4096)
            if data:
                s2.send(data)
            else:
                break
        if s2 in r:
            data = s2.recv(4096)
            if data:
                s1.send(data)
            else:
                break
    s1.close()
    s2.close()


def star_forward(cluster, logdir, cmdline, *args):
    '''Try to setup reverse tunnel back to here'''
    global forwarding_dest

    if len(args) == 1:
        forwarding_dest = (args[0], 80)
    elif len(args) > 1:
        forwarding_dest = (args[0], int(args[1]))
    print('Setting up remote port forwards to', forwarding_dest)

    for host, t in cluster.connections.items():
        # even do this on temporarily disabled servers, in case user
        # invokes *fwd then reenables hosts
        try:
            if host not in cluster.reverse_port:
                listener = t.request_port_forward('127.0.0.1', 0, forwarding)
                if listener:
                    cluster.reverse_port[host] = listener
                else:
                    print('Remote host %s denied port-forward request' % host)
        except Exception as e:
            print(e)


def star_output_mode(cluster, logdir, cmdline, *args):
    '''Select output mode: [stream|ordered|off]'''
    modes = ('stream', 'ordered', 'off')
    if args[0] not in modes:
        raise ValueError('Output mode must be one of: %s' % repr(modes))
    cluster.output_mode = args[0]
    print('Output mode set to %s' % cluster.output_mode)


def star_quota(cluster, logdir, cmdline, *args):
    '''Print or set Quota values'''
    if args:
        try:
            cluster.quota.time_limit = float(args[0])
            cluster.quota.byte_limit = int(args[1])
            cluster.quota.line_limit = int(args[2])
        except IndexError:
            pass
    print('Current Quota Settings:')
    if cluster.quota.time_limit:
        print('\tIdle (not Total) Time: %g seconds' % float(cluster.quota.time_limit))
    else:
        print('\tIdle (not Total) Time: Unlimited')
    if cluster.quota.byte_limit:
        print('\tOutput Byte Limit: %d bytes' % cluster.quota.byte_limit)
    else:
        print('\tOutput Byte Limit: Unlimited')
    if cluster.quota.line_limit:
        print('\tOutput Line Limit: %d lines' % cluster.quota.line_limit)
    else:
        print('\tOutput Byte Limit: Unlimited')


def star_vars(cluster, logdir, cmdline, *args):
    '''View or set user-defined session variables'''
    if not args:
        pprint.pprint(cluster.user_vars)
    else:
        var = args[0]
        if not (var.startswith('%') and var.endswith('%')):
            print('User variables must start and end with "%"')
            return
        if args[0] in cluster.user_vars:
            print('%s is currently set to [%s]' % (args[0], cluster.user_vars[args[0]]))
        else:
            print('%s is currently not set' % args[0])
        cluster.user_vars[args[0]] = raw_input('Enter new setting for "%s" : ' % args[0])


def star_chunk(cluster, logdir, cmdline, *args):
    '''View or set chunkiness of the cluster'''
    if args:
        cluster.chunk_size = int(args[0])
        if len(args) > 1:
            cluster.chunk_delay = float(args[1])
    print('Cluster chunk-factor is %s with a temporal warp of %s' % (cluster.chunk_size, cluster.chunk_delay))


def star_exit(cluster, logdir, cmdline, *args):
    '''Exit from shell'''
    cluster.close_connections()
    sys.exit(0)


commands = {
    '*?': StarCommand(star_help),
    '*help': StarCommand(star_help),
    '*enable': StarCommand(star_enable),
    '*info': StarCommand(star_info, max_args=0),
    '*status': StarCommand(star_status),
    '*result': StarCommand(star_result),
    '*get': StarCommand(star_get, min_args=1),
    '*sh': StarCommand(star_shell, max_args=0),
    '*output': StarCommand(star_output_mode, min_args=1, max_args=1),
    '*quota': StarCommand(star_quota),
    '*fwd': StarCommand(star_forward, max_args=2),
    '*vars': StarCommand(star_vars, max_args=1),
    '*chunk': StarCommand(star_chunk, max_args=2),
    '*exit': StarCommand(star_exit, max_args=0)
}


def call(cluster, logdir, cmd):
    '''*command caller'''
    try:
        args = cmd.split()
        fn = commands.get(args[0])
        if fn:
            return fn(cluster, logdir, cmd, *args[1:])
        else:
            StarCommand(star_help)(cluster, logdir, cmd)
            return None
    except Exception as e:
        logger = logging.getLogger('radssh')
        logger.error('Invoking *command failed: %s', repr(e))
        logger.debug(traceback.format_exc())
        print('Invoking *command failed:', repr(e))
