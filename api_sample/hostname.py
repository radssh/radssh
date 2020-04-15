'''
NetTest Module
==============

Use RadSSH API to connect to several hosts, run 'hostname',
and report on any issues via syslog and stdout.

The basics involve building a list of hosts to connect to, and
an AuthManager to handle the user login (either by password or
by SSH key). These are used to build a RadSSH Cluster object
that can be used to inspect the status of the connections, run
arbitrary command line(s), and programmatic access to the command
results (in addition to streaming stdout/stderr to the console).

This can be used as a template for developing customized scripts
that leverage RadSSH, if the general purpose radssh.shell module
is too interactive.
'''
import sys
import socket
import syslog

from radssh.ssh import Cluster
from radssh.console import RadSSHConsole
from radssh.authmgr import AuthManager
import radssh.config

if len(sys.argv) < 2:
    print('Usage: %s [--password=<password> ] host1 [...]' % sys.argv[0])
    sys.exit(1)

# Setup stuff that the shell module would
password = '********'
socket.setdefaulttimeout(10)

hosts = sys.argv[1:]

if hosts[0].startswith('--password='):
    password = hosts[0][11:]
    hosts = hosts[1:]

# Create an AuthManager to do login with password only
login = AuthManager('root', default_password=password)

# Create a Console for streaming the results of running command output
# This can be suppressed via the console.quiet() call
console = RadSSHConsole()

# Create a list of tuples for the connections
# Leave the 2nd element as None to let RadSSH do the socket connections
connections = [(x, None) for x in hosts]

print('\nConnecting...')
C = Cluster(connections, login, console=console)
for host, status in C.status():
    print('%14s : %s' % (str(host), status))

# Cluster connections and authentications established
# Use the run_command to execute just about any command line
print('\nRunning a command')
C.run_command('hostname')

# All hosts have finished (or were skipped)
# We can access the cluster last_result to post-process the results

print('\nCommand post-processing')
for host, job in C.last_result.items():
    if job.completed and job.result.return_code == 0:
        print(job.result.stdout)
    else:
        print(host, C.connections[host])
        print(job, job.result.status, job.result.stderr)

        syslog.syslog(syslog.LOG_ERR, '%s -%s' % (host, C.connections[host]))
        syslog.syslog(syslog.LOG_ERR, '%s, %s, %s' % (job, job.result.status, job.result.stderr))
