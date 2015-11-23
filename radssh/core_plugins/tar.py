# RadSSH plugin *tar
# Helper to simplify collecting files from remote hosts
# by tar'ing (and optionally compressing) them prior to transfer.
# Instead of using 'cat', as *get does, the remote command is 'tar'
# with options to feed the resulting tar file contents to stdout
# where RadSSH can write local files with the stdout buffer content.

import os
import itertools
import sys
import logging
import traceback

from radssh.plugins import StarCommand

tar_options = {
    '*tar': '-cv',
    '*tgz': '-cvz',
    '*tbz': '-cvj'
}

tar_sequence = itertools.count(1)


def tar_command(cluster, logdir, cmd, *args):
    '''Gather remote files in bulk as tar/tbz/tgz archive'''
    opts = tar_options.get(cmd.split()[0], '-cv')
    remote_command = 'tar %s %s' % (opts, ' '.join(args))
    print('Collecting files into %s' % logdir)
    # Temporarily disable console output, since tar contents are coming via stdout
    save_quiet = cluster.console.quiet(True)
    print(remote_command)
    tar_number = next(tar_sequence)
    res = cluster.run_command(remote_command)
    for host, job in res.items():
        result = job.result
        if job.completed and result.return_code == 0:
            outfile = os.path.join(logdir, 'tarfile_%d_%s.%s' % (tar_number, str(host), cmd.split()[0][1:]))
            with open(outfile, 'wb') as f:
                f.write(bytes(result.stdout))
                pass
        else:
            print(host, repr(job), result)
            traceback.print_exc()
    cluster.console.quiet(save_quiet)

star_commands = {
    '*tar': tar_command,
    '*tgz': tar_command,
    '*tbz': tar_command
}
