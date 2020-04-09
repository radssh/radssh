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
RadSSH Module
Simplified Paramiko interface for managing clustered SSH interaction
'''
from __future__ import print_function  # Requires Python 2.6 or higher


import os
import threading
import socket
import time
import uuid
import fnmatch
import netaddr
import re
import logging
import hashlib
import shlex
import subprocess
try:
    import queue
except ImportError:
    import Queue as queue

import paramiko

from .authmgr import AuthManager
from .streambuffer import StreamBuffer
from .dispatcher import Dispatcher, UnfinishedJobs
from .console import RadSSHConsole, user_password
from . import known_hosts
from . import config
from .keepalive import KeepAlive, ServerNotResponding

# If main thread gets KeyboardInterrupt, use this to signal
# running background threads to terminate prior to command completion
user_abort = threading.Event()

FILTER_TTY_ATTRS_RE = re.compile(b"\x1b\\[(\d)+(;(\d+))*m")

# Map ssh_config LogLevels to Python logging module levels
# This may need some future adjustment, as the labels don't quite line up
sshconfig_loglevels = {
    'QUIET': 0,
    'FATAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'INFO': logging.WARNING,
    'VERBOSE': logging.INFO,
    'DEBUG': logging.DEBUG,
    'DEBUG1': logging.DEBUG,
    'DEBUG2': logging.DEBUG,
    'DEBUG3': logging.DEBUG
}


def filter_tty_attrs(line):
    '''Handle the attributes for colors, etc.'''
    return FILTER_TTY_ATTRS_RE.sub('', line)


class Quota(object):
    '''Quota values for auto-termination of in-flight commands'''
    def __init__(self, defaults={}):
        self.time_limit = int(defaults.get('quota.time', 0))
        self.byte_limit = int(defaults.get('quota.bytes', 0))
        self.line_limit = int(defaults.get('quota.lines', 0))

    def settings(self):
        return self.time_limit, self.byte_limit, self.line_limit

    def time_exceeded(self, elapsed_time):
        if self.time_limit and elapsed_time > self.time_limit:
            return True
        else:
            return False

    def bytes_exceeded(self, bytes):
        if self.byte_limit and bytes > self.byte_limit:
            return True
        else:
            return False

    def lines_exceeded(self, lines):
        if self.line_limit and lines > self.line_limit:
            return True
        else:
            return False


class CommandResult(object):
    '''Generic object to save a bunch of fields'''
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def __repr__(self):
        return '%s "%s" : [%s]' % (self.status, self.command, self.return_code)


class Chunker(object):
    '''Allow list of host connections to be chunkified into sublists'''
    def __init__(self, grouping=10, delay=30):
        self.data = [[]]
        self.grouping = grouping
        self.delay = delay

    def add(self, *args):
        for x in args:
            if self.grouping and len(self.data[-1]) >= self.grouping:
                self.data.append([])
            self.data[-1].append(x)

    def __len__(self):
        return sum([len(x) for x in self.data])

    def __iter__(self):
        for x in self.data[:-1]:
            yield x
            if self.delay:
                try:
                    time.sleep(self.delay)
                except KeyboardInterrupt:
                    print('<Ctrl-C> in chunk mode delay')
        # Yield the last one without adding a delay, since it is the last
        yield self.data[-1]


def run_local_command(original_name, remote_hostname, port, remote_username, sshconfig):
    '''
    Handle preparing command line to run on connecting to remote host. This
    includes doing possible substitutions that are not done by Paramiko's
    ssh_config, as they involve connection specific values that are not known
    at the time of original lookup.
    '''
    if sshconfig.get('permitlocalcommand', 'no') != 'yes':
        return
    cmd = sshconfig.get('localcommand')
    if not cmd:
        return
    if '%' in cmd:
        translations = {
            '%d': os.path.expanduser('~'),
            '%h': remote_hostname,
            '%l': socket.gethostname(),
            '%n': original_name,
            '%p': str(port),
            '%r': sshconfig.get('user', remote_username),
            '%u': os.getlogin(),
            '%C': hashlib.sha1((
                socket.gethostname() +
                remote_hostname +
                str(port) +
                sshconfig.get('user', remote_username)).encode('UTF8')).hexdigest()
        }
        for token, subst in translations.items():
            cmd = cmd.replace(token, subst)
    logging.getLogger('radssh').info('Executing LocalCommand "%s" for connection to %s', cmd, original_name)
    # Self-inflicted harm if this never returns...
    p = subprocess.Popen(shlex.split(cmd))
    logging.getLogger('radssh').debug('LocalCommand "%s" completed with return code %d', cmd, p.wait())


def connection_worker(host, conn, auth, sshconfig={}):
    check_host_key = True
    # host is the label of the host, conn is the "real" name/ip to connect
    # to, or an already established socket-like object. If conn is not
    # filled in, use the label as the hostname.
    if not conn:
        conn = host
    if isinstance(conn, basestring):
        hostname = sshconfig.get('hostname', conn)
        port = sshconfig.get('port', '22')
        proxy = sshconfig.get('proxycommand')
        if proxy:
            logging.getLogger('radssh').info('Connecting to %s via ProxyCommand "%s"', hostname, proxy)
            s = paramiko.ProxyCommand(proxy)
        else:
            try:
                timeout = sshconfig.get('connecttimeout')
                if timeout:
                    timeout = float(timeout)
            except Exception as e:
                logging.getLogger('radssh').error('Invalid ConnectTimeout value "%s" ignored: %s', timeout, e)
                timeout = None
            s = socket.create_connection((hostname, int(port)), timeout=timeout)
        run_local_command(conn, hostname, port, auth.default_user, sshconfig)
        t = paramiko.Transport(s)
        t.setName(host)

        ciphers = sshconfig.get('ciphers')
        if ciphers:
            logging.getLogger('radssh').debug('Limit Ciphers to %s', ciphers)
            preferred = []
            for name in ciphers.split(','):
                if name in t._preferred_ciphers:
                    preferred.append(name)
                else:
                    logging.getLogger('radssh').debug('Ignoring cipher %s (not supported by Paramiko)', name)
            t._preferred_ciphers = tuple(preferred)
            logging.getLogger('radssh').debug('Setting Paramiko _preferred_ciphers to %s', t._preferred_ciphers)
        kex_algorithms = sshconfig.get('kexalgorithms')
        if kex_algorithms:
            logging.getLogger('radssh').debug('Limit KexAlgorithms to %s', kex_algorithms)
            preferred = []
            for name in kex_algorithms.split(','):
                if name in t._preferred_kex:
                    preferred.append(name)
                else:
                    logging.getLogger('radssh').debug('Ignoring KexAlgorithm %s (not supported by Paramiko)', name)
            t._preferred_kex = tuple(preferred)
            logging.getLogger('radssh').debug('Setting Paramiko _preferred_kex to %s', t._preferred_kex)
        macs = sshconfig.get('macs')
        if macs:
            logging.getLogger('radssh').debug('Limit MACs to %s', macs)
            preferred = []
            for name in macs.split(','):
                if name in t._preferred_macs:
                    preferred.append(name)
                else:
                    logging.getLogger('radssh').debug('Ignoring MAC %s (not supported by Paramiko)', name)
            t._preferred_macs = tuple(preferred)
            logging.getLogger('radssh').debug('Setting Paramiko _preferred_macs to %s', t._preferred_macs)
    elif isinstance(conn, paramiko.Transport):
        # Reuse of established Transport, don't overwrite name
        # and don't bother doing host key verification
        t = conn
        check_host_key = False
    else:
        # Socket (or sock-like) which is a probably a tunneled connection
        t = paramiko.Transport(conn)
        port = t.getpeername()[1]
        t.setName(host)
        hostname = host
    t.set_log_channel('radssh.paramiko.transport.%s' % host)
    # Assign the ssh_config LogLevel to the paramiko.transport logger
    loglevel = sshconfig.get('loglevel', 'INFO')
    if loglevel.upper() in sshconfig_loglevels:
        logging.getLogger(t.get_log_channel()).setLevel(sshconfig_loglevels[loglevel.upper()])
    else:
        logging.getLogger('radssh').warning('Unknown LogLevel (%s) for %s', loglevel, host)

    try:
        if check_host_key:
            verify_host = sshconfig.get('hostkeyalias', str(hostname))
            sys_known_hosts = known_hosts.load(sshconfig.get('globalknownhostsfile', '/etc/ssh/ssh_known_hosts'))
            user_known_hosts = known_hosts.load(sshconfig.get('userknownhostsfile', '~/.ssh/known_hosts'))
            keys = list(sys_known_hosts.matching_keys(verify_host, int(port)))
            keys.extend(user_known_hosts.matching_keys(verify_host, int(port)))
            if keys:
                # Only request the key types from known_hosts
                t._preferred_keys = [x.key.get_name() for x in keys]
            else:
                # Order per HostKeyAlgorithms, or bump Paramiko precedence of ECDSA
                t._preferred_keys = sshconfig.get('hostkeyalgorithms', 'ecdsa-sha2-nistp256,ssh-rsa,ssh-dss').split(',')
            if not t.is_active():
                t.start_client()
            # Do the key verification based on sshconfig settings
            known_hosts.verify_transport_key(t, verify_host, int(port), sshconfig)

    except Exception as e:
        logging.getLogger('radssh').error('Unable to verify host key for %s\n%s', verify_host, repr(e))
        print('Unable to verify host key for', verify_host)
        print(repr(e))
        t.close()
        print('Connection to %s closed.' % str(hostname))
        return t
    # After connection and passing host key verification, now try to authenticate
    auth.authenticate(t, sshconfig)
    return t


def exec_command(host, t, cmd, quota, streamQ, encoding='UTF-8'):
    '''Run a command across a transport via exec_cmd. Capture stdout, stderr, and return code, streaming to an optional output queue'''
    return_code = None
    if isinstance(t, paramiko.Transport) and t.is_authenticated():
        stdout = StreamBuffer(streamQ, (str(host), False), blocksize=2048, encoding=encoding)
        stderr = StreamBuffer(streamQ, (str(host), True), blocksize=2048, encoding=encoding)
        keepalive = KeepAlive(t)
        # If transport has a persistent session (identified by being named same as the transport.remote_version)
        # then use the persistent session via send/recv to the shell quasi-interactively, rather than
        # creating a single-use session with exec_command, which gives true process termination (exit_status_ready)
        # and process return code capabilities.
        persistent_session = None
        for s in t._channels.values():
            if s.get_name() == t.remote_version:
                persistent_session = s
                while s.recv_ready():
                    # clear out any accumulated data
                    s.recv(2048)
                    time.sleep(0.4)
                # Send a bunch of newlines in hope to get a bunch of prompt lines
                s.sendall('\n\n\n\n\n')
                time.sleep(0.5)
                try:
                    s.settimeout(3.0)
                    # Read the queued data as the remote host prompt
                    # to check for command completion if we get the prompt again
                    data = s.recv(2048)
                    prompt_lines = [x.strip() for x in data.split('\n') if x.strip()]
                    persist_prompt = prompt_lines[-1]
                    stdout.push('\n=== Start of Exec: Prompt is [%s] ===\n\n' % persist_prompt)
                except (socket.timeout, IndexError) as e:
                    persist_prompt = None
                    stdout.push('\n=== Start of Exec: Failed to read prompt [%s] ===\n\n' % data)
                s.send('%s\n' % cmd)
                break
        else:
            s = t.open_session()
            s.set_name(t.getName())
            xcmd = cmd
            s.exec_command(xcmd)
        stdout_eof = stderr_eof = False
        quiet_increment = 0.4
        quiet_time = 0
        while not (stdout_eof and stderr_eof and s.exit_status_ready()):
            # Read from stdout socket
            s.settimeout(quiet_increment)
            try:
                data = s.recv(16384)
                quiet_time = 0
                if data:
                    stdout.push(data)
                    if persistent_session:
                        if persist_prompt and persist_prompt in data:
                            stdout_eof = True
                            process_completion = '*** Returned To Prompt ***'
                            break
                        if data.strip().endswith('--More--'):
                            s.sendall(' ')
                else:
                    stdout_eof = True
                    # Avoid wild CPU-bound thrashing under Python3 GIL
                    s.status_event.wait(0.01)
            except socket.timeout:
                # Push out a (nothing) in case the queue needs to do a time-based dump
                stdout.push('')
                quiet_time += quiet_increment
                try:
                    if quiet_time > 5.0:
                        keepalive.ping()
                except ServerNotResponding:
                    t.close()
                    process_completion = '*** Server Not Responding ***'
                    break
            # Read from stderr socket, altered timeout
            try:
                s.settimeout(0.1)
                data = s.recv_stderr(4096)
                if data:
                    stderr.push(data)
                else:
                    stderr_eof = True
            except socket.timeout:
                pass
            # Check quota limits
            if quota.time_exceeded(quiet_time):
                process_completion = '*** Time Limit (%d) Reached ***' % quota.time_limit
                break
            if quota.bytes_exceeded(len(stdout)):
                process_completion = '*** Byte Limit (%d) Reached ***' % quota.byte_limit
                break
            if quota.lines_exceeded(stdout.line_count):
                process_completion = '*** Line Limit (%d) Reached ***' % quota.line_limit
                break
            if user_abort.isSet():
                process_completion = '*** <Ctrl-C> Abort ***'
                break
            # Make a guess if the command completed, since persistent sessions
            # via invoke_shell don't do EOF or exit_status at all...
            if persistent_session and quiet_time > 30:
                process_completion = '*** Presumed Complete ***'
                break
        else:
            process_completion = '*** Complete ***'
            return_code = s.recv_exit_status()
        if persistent_session:
            return_code = 0
        else:
            s.close()
        stdout.close()
        if stdout.discards:
            logging.getLogger('radssh').warning('StreamBuffer encountered %d discards', stdout.discards)
            process_completion += 'StreamBuffer encountered %d discards' % stdout.discards
        stderr.close()
        return CommandResult(command=cmd, return_code=return_code, status=process_completion, stdout=stdout.buffer, stderr=stderr.buffer)
    else:
        process_completion = '*** Skipped ***'
        return CommandResult(command=cmd, return_code=return_code, status=process_completion, stdout=b'', stderr=b'')


def sftp_thread(host, t, srcfile, dstfile=None, attrs=None):
    if not attrs:
        attrs = paramiko.sftp_attr.SFTPAttributes.from_stat(os.stat(srcfile))
    s = t.open_sftp_client()
    if not dstfile:
        dstfile = srcfile
    s.put(srcfile, dstfile)
    s.chmod(dstfile, attrs.st_mode % 4096)
    try:
        s.chown(dstfile, attrs.st_uid, attrs.st_gid)
    except IOError:
        pass
    s.close()
    return CommandResult(command='SFTP %s -> %s' % (srcfile, dstfile),
                         return_code=0, status='*** Complete ***',
                         stdout='Transferred %d bytes' % attrs.st_size, stderr='')


def close_connection(t, k, signoff=''):
    '''Close Paramiko transport connections'''
    if isinstance(t, paramiko.Transport):
        if t.is_authenticated():
            # Scan for persisitent session, and sign-off cleanly
            for s in t._channels.values():
                if s.get_name() == t.remote_version:
                    s.send('\n'.join(signoff.split(';')) + '\n')
        t.close()


class Cluster(object):
    '''SSH Cluster'''
    def __init__(self, hostlist, auth=None, console=None, mux={}, defaults={}, commandline_options={}):
        '''Create a Cluster object from a list of host entries'''
        if auth:
            self.auth = auth
        else:
            self.auth = AuthManager()
        if console:
            self.console = console
        else:
            # Limit console queue size to 4x connections to avoid excess
            # bottleneck when extremely high volume output
            outQ = queue.Queue(min(100, 4 * len(hostlist)))
            self.console = RadSSHConsole(outQ)
            self.console.quiet(True)
        if defaults:
            self.defaults = defaults
        else:
            self.defaults = config.load_default_settings()
        self.log_out = self.defaults.get('log_out', 'out.log').strip()
        self.log_err = self.defaults.get('log_err', 'err.log').strip()
        thread_count = min(int(self.defaults.get('max_threads')), len(hostlist))
        self.dispatcher = Dispatcher(outQ=queue.Queue(), threadpool_size=thread_count)
        self.pending = {}
        self.uuid = uuid.uuid1()
        self.connections = {}
        self.connect_timings = {}
        self.mux = {}
        self.reverse_port = {}
        self.disabled = set()
        self.last_result = None
        self.user_vars = {}
        self.quota = Quota(self.defaults)
        self.chunk_size = None
        self.chunk_delay = 0
        self.output_mode = self.defaults['output_mode']
        self.sshconfig = paramiko.SSHConfig()
        # Only load SSHConfig if path is set in RadSSH config
        if defaults.get('ssh_config'):
            logging.getLogger('radssh').warning('Loading SSH Config file: %s', defaults['ssh_config'])
            try:
                with open(os.path.expanduser(defaults['ssh_config'])) as user_config:
                    self.sshconfig.parse(user_config)
            except IOError as e:
                logging.getLogger('radssh').warning('Unable to process user ssh_config file: %s', e)
            if os.path.isdir('/etc/ssh'):
                system_config = '/etc/ssh/ssh_config'
            else:
                # OSX location
                system_config = '/etc/ssh_config'
            try:
                with open(system_config) as sysconfig:
                    self.sshconfig.parse(sysconfig)
            except IOError as e:
                logging.getLogger('radssh').warning('Unable to process system ssh_config file (%s): %s', system_config, e)

        for label, conn in hostlist:
            config = self.get_ssh_config(label, conn)
            if mux:
                for idx, mux_var in enumerate(mux.get(label, [])):
                    mux_label = '%s:%d' % (label, idx)
                    self.pending[self.dispatcher.submit(connection_worker, mux_label, conn, self.auth, config)] = label
                    self.mux[mux_label] = mux_var
            else:
                self.pending[self.dispatcher.submit(connection_worker, label, conn, self.auth, config)] = label
        self.update_connections()
        # Start remainder of dispatcher threads
        self.dispatcher.start_threads(len(self.connections))

    def update_connections(self):
        '''Pull completed transport creations and save in connections dict'''
        while True:
            try:
                for pid, summary in self.dispatcher.async_results(5):
                    host = self.pending.pop(pid)
                    transport = summary.result
                    self.connections[host] = transport
                    self.connect_timings[host] = summary.end_time - summary.start_time
                    try:
                        if transport.is_authenticated():
                            transport.set_keepalive(int(self.defaults.get('keepalive', 0)))
                            self.console.progress('.')
                            logging.getLogger('radssh.connection').info('Authenticated to %s' % host)
                            # IOS switch may require invoke_shell instead of exec_command
                            for id_string in self.defaults.get('force_tty', '').split(','):
                                if id_string and id_string in transport.remote_version:
                                    self.console.message('%s (%s)' % (host, transport.remote_version), 'FORCE TTY')
                                    tty = transport.open_session()
                                    tty.set_name(transport.remote_version)
                                    tty.get_pty(width=132, height=43)
                                    tty.invoke_shell()
                                    # If we have a signon string, send it to the remote host
                                    # translate semi-colons as newlines (and tack on an extra \n at the end)
                                    if self.defaults.get('force_tty.signon'):
                                        tty.send('\n'.join(self.defaults.get('force_tty.signon', '').split(';')) + '\n')
                                        time.sleep(0.5)
                                    while tty.recv_ready():
                                        banner = tty.recv(2048)
                                        self.console.message(str(banner), 'SIGNON')
                                    # Issue a final empty line to trigger a fresh prompt
                                    tty.send('\n')
                        else:
                            self.console.progress('O')
                            logging.getLogger('radssh.connection').warning('Failed to authenticate to %s: %s' % (host, str(transport)))
                    except Exception as e:
                        self.console.progress('X')
                        logging.getLogger('radssh.connection').warning('Failed to connect to %s: %s' % (host, str(transport)))
                break
            except UnfinishedJobs as e:
                self.console.message(e.message, 'STALLED')
            except KeyboardInterrupt:
                self.console.message('Aborting %d pending connections' % len(self.pending), 'Ctrl-C')
                for label in self.pending.values():
                    self.console.message(label, 'FAILED CONNECTION')
                    self.connections[label] = Exception('Failed to connect/Ctrl-C')
                    logging.getLogger('radssh.connection').warning('Aborted connect to %s: Ctrl-C' % host)
                self.pending.clear()
                # Blocked threads can cause issues with internal recordkeeping of Dispatcher
                # object, and havoc if the thread ever unblocks and sends a completion message
                # via outQ when async_results are used for another batch of jobs. Safest
                # thing in this case is to abandon the Dispatcher blocked on connection
                # results, and begin the session with a new Dispatcher object for
                # the exec_command calls. The terminate() call will safely terminate the
                # unblocked threads, freeing some resources for the new Dispatcher.
                self.dispatcher.terminate()
                new_dispatcher = Dispatcher(outQ=queue.Queue(), threadpool_size=self.dispatcher.threadpool_size)
                self.dispatcher = new_dispatcher
                break
        self.console.progress('\n')
        self.console.status('Ready')

    def reauth(self, user):
        '''Attempt to reconnect and reauthenticate to any hosts in the cluster that are not already properly established'''
        if not user or user == self.auth.default_user:
            # Not switching users, we know the existing auth won't work
            retry = AuthManager(self.auth.default_user, auth_file=None,
                                try_auth_none=False)
        else:
            # Give the option of reusing the existing auth options with new user
            alternate_password = user_password(
                'Please enter a password for (%s) or leave blank to retry auth options with new user:' % user)
            if alternate_password:
                retry = AuthManager(user, auth_file=None, default_password=alternate_password)
            else:
                retry = self.auth
            self.auth.default_user = user

        for k, t in self.connections.items():
            if isinstance(t, paramiko.Transport) and t.is_authenticated():
                continue
            if isinstance(t, paramiko.Transport) and t.is_active():
                t.close()
            self.console.message(str(k), 'RECONNECT')
            conn = None
            try:
                conn = socket.create_connection((str(k), 22), timeout=float(self.defaults.get('socket.timeout', 2.0)))
            except socket.gaierror as e:
                if '.' not in k and e.args == (-2, 'Name or service not known'):
                    # Try extended domain searches
                    for suffix in self.defaults.get('domains', '').split():
                        fqdn = '%s.%s' % (k, suffix)
                        try:
                            conn = socket.create_connection((fqdn, 22), timeout=float(self.defaults.get('socket.timeout', 2.0)))
                            self.console.message('%s -> %s' % (k, fqdn), 'FQDN')
                            break
                        except socket.error as e:
                            # self.console.mesage (repr(e))
                            pass
            except Exception as e:
                self.console.message('%s - %s' % (str(k), str(e)), 'EXCEPTION')
            # For Reauth, do not pass sshconfig options since we're just trying to force a password authentication
            # self.pending[self.dispatcher.submit(connection_worker, k, conn, retry, self.sshconfig.lookup(str(k)))] = k
            self.pending[self.dispatcher.submit(connection_worker, k, conn, retry, {'identityfile': []})] = k
        self.update_connections()

    def get_ssh_config(self, label, connection_spec=None):
        '''Lookup or create a dict of SSHConfig options for the given host'''
        if isinstance(connection_spec, basestring):
            host_spec = connection_spec
        else:
            host_spec = label
        # Support specs in form of user@host:port
        if '@' in host_spec:
            supplied_user, host_spec = host_spec.split('@', 1)
        else:
            supplied_user = None
        if ':' in host_spec:
            # Attempt to disambiguate IPv6
            host_spec, supplied_port = host_spec.rsplit(':', 1)
            if ':' in host_spec:
                if host_spec[0] == '[' and host_spec[-1] == ']':
                    host_spec = host_spec[1:-1]
                else:
                    host_spec = host_spec + ':' + supplied_port
                    supplied_port = None
        else:
            supplied_port = None
        config = self.sshconfig.lookup(host_spec)
        # If spec included port or user, overrride the SSHConfig values
        if supplied_port:
            config['port'] = supplied_port
        if supplied_user:
            config['user'] = supplied_user
        # if SSHConfig has no value for LogLevel, use the cluster setting
        if 'loglevel' not in config:
            config['loglevel'] = self.defaults['loglevel'].upper()
        return config

    def tunnel_connections(self, hostlist, jumpbox=None):
        '''Create a cluster of tunneled connections through a jumpbox'''
        if jumpbox:
            t = self.connections.get(jumpbox)
        else:
            t = self.connections.values()[0]
        tunnel_list = []
        if not t:
            return None
        for host in hostlist:
            try:
                s = t.open_channel('direct-tcpip', (host, 22), (host, 22))
                tunnel_list.append((host, s))
            except Exception as e:
                self.console.q.put((('TUNNEL', True), 'Unable to tunnel to %s: %s' % (host, e)))
        return Cluster(tunnel_list, self.auth)

    def multiplex(self, mux_command='echo /mnt/gluster-brick*'):
        '''Create a multiplex cluster based on the output of a command against the current cluster'''
        self.console.quiet(True)
        res = self.run_command(mux_command)
        self.console.quiet(False)
        mux_data = {}
        mux_list = []
        for host, vars in [(k, job.result.stdout) for k, job in res.items() if job.completed and job.result.return_code == 0]:
            mux_data[host] = vars.split()
            mux_list.append((host, self.connections[host]))
        return Cluster(mux_list, self.auth, console=self.console, mux=mux_data, defaults=self.defaults)

    def enable(self, enable_list=None):
        '''Set active set of connections via list of fnmatch/IP patterns to limit run_command; pass in None to reset to enable all connections'''
        self.disabled = set()
        if enable_list is None:
            self.console.q.put((('ENABLED', True), 'All %d hosts currently enabled' % len(self.connections)))
            return
        if isinstance(enable_list, basestring):
            # Handle single value being passed instead of list
            enable_list = [enable_list]

        # Assemble an enabled list, then complement it at the end
        enabled = set()
        for pattern in enable_list:
            direct_match = self.locate(pattern)
            if direct_match:
                enabled.add(direct_match)
                continue
            # Try using pattern as IP network or glob first
            # if it doesn't look like either, then treat it as a name wildcard
            pattern_match = set()
            try:
                ip_match = netaddr.IPNetwork(pattern)
            except Exception as e:
                try:
                    ip_match = netaddr.IPSet(netaddr.IPGlob(pattern))
                except Exception as e:
                    ip_match = None
            for host, t in self.connections.items():
                if ip_match:
                    try:
                        if netaddr.IPAddress(t.getpeername()[0]) in ip_match:
                            pattern_match.add(host)
                    except Exception as e:
                        pass
                else:
                    if fnmatch.fnmatch(str(host), pattern):
                        pattern_match.add(host)
            if len(pattern_match) > 1:
                    self.console.q.put((('ENABLED', True), 'Pattern wildcard "%s" matched %d hosts' % (pattern, len(pattern_match))))
            enabled.update(pattern_match)
        # Take complement of enabled set
        for host in self.connections:
            if host not in enabled:
                self.disabled.add(host)
        self.console.q.put((('ENABLED', True), '%d hosts currently enabled' % len(enabled)))

    def prep_command(self, cmd, target):
        '''Preprocess command line for target host execution (%ip%, %host%, etc)'''
        # Scan for all %var% constructs - we won't care to honor any quoting rules
        vars = set(re.findall('%[a-zA-Z_]+%', cmd))
        if not vars:
            return cmd
        t = self.connections[target]
        # Handle predefined %%'s (host, ip, port, tunnel, mux) first
        auto_vars = {
            '%host%': str(target),
            '%ip%': t.getpeername()[0] if isinstance(t, paramiko.Transport) else '0.0.0.0',
            '%ssh_version%': t.remote_version if isinstance(t, paramiko.Transport) else 'No Connection',
            '%uuid%': str(self.uuid)
        }
        if self.mux:
            auto_vars['%mux%'] = self.mux.get(target, '')
        if target in self.reverse_port:
            port = self.reverse_port[target]
            auto_vars['%port%'] = '%d' % port
            auto_vars['%tunnel%'] = '127.0.0.1:%d' % port

        for v in vars:
            if v in auto_vars:
                try:
                    cmd = cmd.replace(v, auto_vars[v])
                except Exception as e:
                    self.console.q.put((('EXCEPTION', True),
                                        'Substituting %s for %s: %s' % (v, target, str(e))))
                    return None
            else:
                if v not in self.user_vars:
                    x = raw_input('Missing variable setting for %s\nEnter value : ' % v)
                    self.user_vars[v] = x
                cmd = cmd.replace(v, self.user_vars[v])

        return cmd

    def run_command(self, template):
        '''Execute a command line (template) string across all enabled host connections'''
        result = {}
        last_interrupt = 0
        chunker = Chunker(self.chunk_size, self.chunk_delay)
        for k in self:
            if k in self.disabled:
                continue
            chunker.add(k)

        total = len(chunker)
        for chunk in chunker:
            ordered_list = []
            for k in chunk:
                t = self.connections[k]
                ordered_list.append(k)

                # Patch up command line with host/mux specific data prior to queueing
                cmd = self.prep_command(template, k)
                if not cmd:
                    continue
                # Now we have a legit command line to execute
                if self.output_mode == 'stream':
                    self.pending[self.dispatcher.submit(exec_command, k, t, cmd, self.quota, self.console.q, self.defaults['character_encoding'])] = k
                else:
                    self.pending[self.dispatcher.submit(exec_command, k, t, cmd, self.quota, None, self.defaults['character_encoding'])] = k
            # Wait for background jobs to complete
            while self.pending:
                try:
                    self.console.status('Completed on %d/%d hosts' % (len(result), total))
                    for pid, summary in self.dispatcher.async_results():
                        host = self.pending.pop(pid)
                        result[host] = summary
                        if self.output_mode == 'ordered':
                            while ordered_list and ordered_list[0] in result:
                                host = ordered_list.pop(0)
                                job = result[host]
                                if job.result.stdout:
                                    self.console.q.put(((host, False), job.result.stdout.decode(self.defaults['character_encoding'])))
                                else:
                                    self.console.q.put(((host, False), '[No Output]'))
                                if job.result.stderr:
                                    self.console.q.put(((host, True), job.result.stderr.decode(self.defaults['character_encoding'])))
                        else:
                            ordered_list.remove(host)
                        self.console.status('Completed on %d/%d hosts' % (len(result), total))

                except UnfinishedJobs as e:
                    pass
                except KeyboardInterrupt:
                    self.console.status('<Ctrl-C>')
                    if time.time() - last_interrupt < 2.0:
                        user_abort.set()
                        # break
                    else:
                        last_interrupt = time.time()
                        self.console.status('Completed on %d/%d hosts' % (len(result), total))
                        self.console.q.put((('CONSOLE', True), '*** <Ctrl-C> ***'))
                        in_flight = sorted([str(k) for k in self.pending.values() if k not in result])
                        for host in in_flight:
                            self.console.replay_recent(host)

                        self.console.q.put((('CONSOLE', True), 'In-Flight commands running on %s' % str(in_flight)))
                        self.console.q.put((('CONSOLE', True), 'To kill: Press <Ctrl-C> again within 2 seconds'))
                except Exception as e:
                    self.console.q.put((('EXCEPTION', True), '%s' % str(e)))
            self.console.join()
            self.console.status('Completed on %d/%d hosts' % (len(result), total))

        self.console.status('Ready')
        # join(True) here causes the last_lines buffer to be cleared
        self.console.join(True)
        user_abort.clear()
        self.last_result = result
        return result

    def log_result(self, logdir=None, command_header=True, encoding='UTF-8'):
        '''Save last_result content to a log directory - 1 file per host'''
        if logdir:
            for k, job in self.last_result.items():
                v = job.result
                if isinstance(v, CommandResult):
                    if self.log_out:
                        lines = v.stdout.strip().split(b'\n')
                        if lines:
                            with open(os.path.join(logdir, self.log_out), 'ab') as f:
                                f.write(('[%s] === "%s" %s [%s] ===\n' %
                                        (str(k), v.command, v.status, v.return_code)).encode(encoding))
                                for line in lines:
                                    f.write(("[{0}]".format(str(k)) + filter_tty_attrs(line).decode(encoding, 'replace') + "\n").encode(encoding))
                    with open(os.path.join(logdir, str(k) + '.log'), 'ab') as f:
                        if command_header:
                            f.write(('=== "%s" %s [%s] ===\n' %
                                    (v.command, v.status, v.return_code)).encode(encoding))
                        f.write(v.stdout)
                        f.write(b'\n')
                    if v.stderr:
                        if self.log_err:
                            lines = v.stderr.strip().split(b'\n')
                            if lines:
                                with open(os.path.join(logdir, self.log_err), 'ab') as f:
                                    f.write(('[%s] === "%s" %s [%s] ===\n' %
                                            (str(k), v.command, v.status, v.return_code)).encode(encoding))
                                    for line in lines:
                                        f.write(("[{0}]".format(str(k)) + filter_tty_attrs(line).decode(encoding, 'replace') + "\n").encode(encoding))
                        with open(os.path.join(logdir, str(k) + '.stderr'), 'ab') as f:
                            f.write(v.stderr)
                            f.write(b'\n')
                else:
                    if self.log_err:
                        lines = str(v).split('\n')
                        if lines:
                            with open(os.path.join(logdir, self.log_err), 'ab') as f:
                                for line in lines:
                                    f.write(("[{0}]".format(str(k)) + line + "\n").encode(encoding))
                    with open(os.path.join(logdir, str(k) + '.log'), 'ab') as f:
                        f.write(('%s\n' % str(v)).encode(encoding))

    def sftp(self, src, dst=None, attrs=None):
        '''SFTP a file (put) to all nodes'''
        for k in self:
            t = self.connections[k]
            if k in self.disabled:
                continue
            if not isinstance(t, paramiko.Transport) or not t.is_authenticated():
                continue
            self.pending[self.dispatcher.submit(sftp_thread, k, t, src, dst, attrs)] = k
        total = len(self.pending)

        result = {}
        while self.pending:
            try:
                for pid, summary in self.dispatcher.async_results():
                    host = self.pending.pop(pid)
                    result[host] = summary
                    if not summary.completed:
                        self.console.message('%s - %s' % (str(host), repr(summary.result)), 'EXCEPTION')
                    self.console.status('Completed on %d/%d hosts' % (total - len(self.pending), total))
            except UnfinishedJobs as e:
                pass
            except KeyboardInterrupt:
                self.console.message('<Ctrl-C> SFTP Transfer ignored.')
                continue
        self.last_result = result
        self.console.status('Ready')
        return result

    def status(self):
        '''Return a combined list of connection status text messages'''
        good = []
        bad = []
        for k in self:
            t = self.connections[k]
            if k in self.connect_timings:
                connect_time = self.connect_timings[k]
            else:
                connect_time = -1
            if isinstance(t, paramiko.Transport):
                if not t.is_active():
                    bad.append((k, '(%7.3fs) Not connected' % connect_time))
                elif not t.is_authenticated():
                    bad.append((k, '(%7.3fs) Connected to %s / not authenticated' % (connect_time, t.getpeername()[0])))
                else:
                    if k in self.disabled:
                        good.append((k, '(%7.3fs) Authenticated as %s to %s (Disabled)' % (connect_time, t.get_username(), t.getpeername()[0])))
                    else:
                        good.append((k, '(%7.3fs) Authenticated as %s to %s' % (connect_time, t.get_username(), t.getpeername()[0])))
            else:
                bad.append((k, '(%8.3fs) %s' % (connect_time, str(t))))
        return good + bad

    def connection_summary(self):
        '''Determine counts of various connection statuses'''
        ready = disabled = failed_auth = failed_connect = dropped = 0
        for k, t in self.connections.items():
            if isinstance(t, paramiko.Transport):
                if not t.is_active():
                    dropped += 1
                elif not t.is_authenticated():
                    failed_auth += 1
                else:
                    if k in self.disabled:
                        disabled += 1
                    else:
                        ready += 1
            else:
                failed_connect += 1
        return (ready, disabled, failed_auth, failed_connect, dropped)

    def locate(self, s):
        '''Lookup cluster entry - keys may be netaddr.IPAddress, not string'''
        # Trivial case, string to string match
        if s in self.connections:
            return s
        # Loop and compare string conversion of key to s
        for k in self.connections:
            if str(k) == s:
                return k
        return None

    def __iter__(self):
        '''Get connection keys in (hybrid) sorted order'''
        def hybrid_key(x):
            return(str(type(x)), x)
        result = sorted(self.connections.keys(), key=hybrid_key)
        return iter(result)

    def close_connections(self):
        '''Disconnect from all remote hosts'''
        for k in list(self.connections):
            t = self.connections.pop(k)
            self.dispatcher.submit(close_connection, t, k, self.defaults.get('force_tty.signoff', ''))
        self.dispatcher.wait()
