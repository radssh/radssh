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
SFTP plugin for RadSSH
======================

Various useful operations based on being able to use existing transports
within the cluster to create sftp sessions, allowing remote file get/put
structured in an easy to use fashion.

*sftp /path/to/local/file [/remote/file/system/path/to/file]
    Push out a local file, via sftp, to remote nodes. If remote filesystem
    path is not specified, the same local path and filename is used. Paths
    can be specified as either relative or absolute.

*run /path/to/local/script [arg]...
    Push out a local file (script or binary compaitble executable) into /tmp
    on remote nodes, and after transfer, invoke it with the supplied command
    line arguments.

*propagate host:/path/to/file
    Similar to *sftp, but master copy of the file resides on remote host,
    not locally. File is retrieved into a temporary file, then the existing
    cluster.sftp() call is used to put the file. File attributes for file
    permissions and user/group ownership is attempted to be preserved.
'''

from __future__ import print_function  # Requires Python 2.6 or higher


import os
import stat
import tempfile

from radssh.plugins import StarCommand

# Add a settings dict so user can override plugin rutime parameters
settings = {
    'temp_dir': '/tmp',
    'script_exec': 'bash -c "%s"'
}


def sftp(cluster, logdir, cmd, *args):
    '''SFTP put a local file on cluster nodes'''
    src = args[0]
    if len(args) > 1:
        dst = args[1]
    else:
        dst = src
    cluster.sftp(src, dst)


def script_file_runner(cluster, logdir, cmd, *args):
    '''Push a local script file out to nodes and run it with optional arguments'''
    st = os.stat(args[0])
    if not (st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)):
        raise RuntimeError('Script file %s not executable' % args[0])
    srcfile = args[0]
    dstfile = os.path.join(settings['temp_dir'], os.path.basename(args[0]))
    sftp(cluster, logdir, cmd, srcfile, dstfile)
    remote_cmd = '%s %s' % (dstfile, ' '.join(args[1:]))
    if settings['script_exec']:
        remote_cmd = settings['script_exec'] % remote_cmd
    cluster.run_command(remote_cmd)
    if logdir:
        cluster.log_result(logdir)


def propagate_file(cluster, logdir, cmd, *args):
    '''Use SFTP to replicate a file on one remote node to all other nodes'''
    if len(args) != 1:
        print('Usage: *propagate host:/path/to/file')
        return
    host, path = args[0].split(':', 1)
    source_host = cluster.locate(host)
    if not source_host:
        print('Host [%s] does not appear to be part of current cluster' % host)
        return
    # Get a temp filename (and fd, but close that immediately, we just want the name)
    fd, tempname = tempfile.mkstemp()
    os.close(fd)
    print('Fetching master copy of %s from [%s]' % (path, source_host))
    # Here, we don't care if the source node is enabled or not, grab the file content regardless
    t = cluster.connections[source_host]
    s = t.open_sftp_client()
    s.get(path, tempname)
    attrs = s.stat(path)
    s.close()
    # Now use cluster.sftp directly to push out the file, including the saved attrs
    print('Pushing master copy to remote hosts...')
    cluster.sftp(tempname, path, attrs)
    os.remove(tempname)


def custom_completer(completer, buffer, lead_in, text, state):
    words = buffer.split()
    # Shift to local path completion only for the 1st parameter (2nd arg)
    if len(words) == 2:
        return completer.complete_local_path(lead_in, text, state)
    return completer.complete_remote_path(lead_in, text, state)


star_commands = {
    '*sftp': StarCommand(sftp, tab_completion=custom_completer),
    '*run': StarCommand(script_file_runner, tab_completion=custom_completer),
    '*propagate': propagate_file
}
