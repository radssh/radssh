#!/usr/bin/env python
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
Python wrapper for parallel execution shell
===========================================

*** This module should be run, not imported ***

Usage: ```python -m radssh.shell host [...]```

Will read settings from /etc/radssh_config, and supplement with ~/.radssh_config.
Settings may also be provided on the command line, using the form --keyword=value.
'''
from __future__ import print_function  # Requires Python 2.6 or higher


import sys
import os
import time
import socket
import pprint
import readline
import atexit
import logging
import warnings
import traceback

# Avoid having PowmInsecureWarning show on stderr every time
with warnings.catch_warnings(record=True) as paramiko_load_warnings:
    import paramiko

from . import ssh
from . import config
from .console import RadSSHConsole, monochrome
try:
    from . import star_commands as star
    import radssh.plugins
except ImportError:
    class NullStarCommands(object):
        '''Use stub if plugins or star_commands can not be loaded'''
        @classmethod
        def call(*args, **kwargs):
            print('Plugins directory not found - *commands disabled')
        star_help = call
        star_info = call
        commands = {'*help': star_help}

    star = NullStarCommands()


# Try using colorama when running on Windows
if sys.platform.startswith('win'):
    try:
        import colorama
        colorama.initialise.init()
    except Exception as e:
        print('Unable to support ANSI escape sequences via colorama module')
        print(e)
        sys.exit(1)

# Ensure ~/.ssh directory exists, with sensible permissions
try:
    os.mkdir(os.path.expanduser('~/.ssh'), 0o700)
except OSError:
    pass

################################################################################

command_listeners = []


def shell(cluster, logdir=None, playbackfile=None, defaults=None):
    '''Very basic interactive shell'''
    if not defaults:
        defaults = config.load_default_settings()
    try:
        while True:
            if playbackfile:
                try:
                    cmd = next(playbackfile)
                    print('%s %s' % (defaults['shell.prompt'], cmd.strip()))
                except StopIteration:
                    break
            else:
                try:
                    cmd = raw_input('%s ' % defaults['shell.prompt'])
                except KeyboardInterrupt:
                    print('\n<Ctrl-C> during input\nUse EOF (<Ctrl-D>) or *exit to exit shell\n')
                    continue
                # Feed command line to any registered listeners from plugins
                for feed in command_listeners:
                    feed_result = feed(cmd)
                    if feed_result:
                        if defaults['show_altered_commands'] == 'on':
                            cluster.console.message('Command modified from "%s" to "%s"' % (cmd, feed_result))
                        cmd = str(feed_result)
                if logdir:
                    with open(os.path.join(logdir, 'session.commands'), 'a') as f:
                        f.write('%s\n' % cmd)
            args = cmd.split()
            if len(args) > 0:
                if os.path.basename(args[0]) == 'sudo' and len(args) > 1:
                    initial_command = os.path.basename(args[1])
                else:
                    initial_command = os.path.basename(args[0])
                if initial_command in defaults['commands.forbidden'].split(','):
                    print('You really don\'t want to run %s without a TTY, do you?' % initial_command)
                    continue
                if initial_command in defaults['commands.restricted'].split(','):
                    print('STOP! "%s" is listed as a restricted command (Potentially dangerous)' % initial_command)
                    print('and requires explicit confirmation before running.')
                    print('Please double check all parameters, just to be sure...')
                    print('   >>>', cmd)
                    confirm = raw_input('Enter \'100%\' if completely sure: ')
                    if confirm != '100%':
                        continue
                if args[0].startswith('#'):
                    # Comment
                    continue
                if args[0].startswith('*'):
                    ret = star.call(cluster, logdir, cmd)
                    cluster.console.join()
                    if isinstance(ret, ssh.Cluster):
                        cluster.console.message('Switched cluster from %r to %r' % (cluster, ret))
                        cluster = ret
                    continue
                r = cluster.run_command(cmd)
                if logdir:
                    cluster.log_result(logdir, encoding=defaults['character_encoding'])
                # Quick summary report, if jobs failed
                failures = {}
                completions = []
                completion_time = 0.0
                for k, job in r.items():
                    v = job.result
                    if job.completed:
                        if v.return_code == 0:
                            completions.append(str(k))
                            completion_time += job.end_time - job.start_time
                        else:
                            failures.setdefault(v.return_code, []).append(str(k))
                    else:
                        failures.setdefault(None, []).append(str(k))
                if failures:
                    print('\nSummary of return codes:')
                    for k, v in [(0, completions)] + list(failures.items()):
                        if len(v) > 5:
                            print(k, '\t- (%d hosts)' % len(v))
                        else:
                            print(k, '\t-', sorted(v))
                if completions:
                    print('Average completion time for %d hosts: %fs' % (len(completions), (completion_time / len(completions))))
    except EOFError as e:
        print(e)
    print('Shell exiting')
    cluster.close_connections()

################################################################################
# Readline/libedit command completion
# Supports *commands, executables (LOCAL), and path (REMOTE) completion


class radssh_tab_handler(object):
    '''Class wrapper for readline TAB key completion'''
    def __init__(self, cluster, star):
        # Need access to the cluster object to get SFTP service
        # for remote path completion, and the star command dictionary
        # to know what *commands are available.
        self.cluster = cluster
        self.star = star
        try:
            self.using_libedit = ('libedit' in readline.__doc__)
        except TypeError:
            # pyreadline (windows) readline.__doc__ is None (not iterable)
            self.using_libedit = False
        self.completion_choices = []
        readline.set_completer()
        readline.set_completer(self.complete)
        readline.set_completer_delims(' \t\n/*')
        if self.using_libedit:
            readline.parse_and_bind('bind ^I rl_complete')
        else:
            readline.parse_and_bind('tab: complete')

    def complete_star_command(self, lead_in, text, state):
        if state == 0:
            # Rebuild cached list of choices that match
            # Reset list to empty (choices = [] would reference local, not persistent list)
            del self.completion_choices[:]
            for choice in self.star.commands.keys():
                if choice.startswith(lead_in):
                    self.completion_choices.append(choice + ' ')
        # Discrepancy with readline/libedit and handling of leading *
        if self.using_libedit:
            return self.completion_choices[state]
        else:
            return self.completion_choices[state][1:]

    def complete_executable(self, lead_in, text, state):
        if state == 0:
            del self.completion_choices[:]
            for path_dir in os.environ['PATH'].split(os.path.pathsep):
                try:
                    for f in os.listdir(path_dir):
                        try:
                            if os.path.isdir(os.path.join(path_dir, f)):
                                continue
                            st = os.stat(os.path.join(path_dir, f))
                            if (st.st_mode & 0o111) and f.startswith(text):
                                self.completion_choices.append(f + ' ')
                        except OSError as e:
                            continue
                except OSError as e:
                    continue
            self.completion_choices.append(None)
        return self.completion_choices[state]

    def complete_remote_path(self, lead_in, text, state):
        if state == 0:
            del self.completion_choices[:]
            for t in self.cluster.connections.values():
                if t.is_authenticated():
                    break
            else:
                print('No authenticated connections')
                raise RuntimeError('Tab Completion unavailable')
            s = t.open_sftp_client()
            parent = os.path.dirname(lead_in)
            partial = os.path.basename(lead_in)
            if not parent:
                parent = './'
            for x in s.listdir(parent):
                if x.startswith(partial):
                    full_path = os.path.join(parent, x)
                    try:
                        # See if target is a directory, and append '/' if it is
                        s.chdir(full_path)
                        x += '/'
                        full_path += '/'
                    except Exception as e:
                        pass
                    if self.using_libedit:
                        self.completion_choices.append(full_path)
                    else:
                        self.completion_choices.append(x)
            self.completion_choices.append(None)
        return self.completion_choices[state]

    def complete_local_path(self, lead_in, text, state):
        if state == 0:
            del self.completion_choices[:]
            parent = os.path.dirname(lead_in)
            partial = os.path.basename(lead_in)
            if not parent:
                parent = './'
            for x in os.listdir(parent):
                if x.startswith(partial):
                    full_path = os.path.join(parent, x)
                    if os.path.isdir(full_path):
                        # See if target is a directory, and append '/' if it is
                        x += '/'
                        full_path += '/'
                    if self.using_libedit:
                        self.completion_choices.append(full_path)
                    else:
                        self.completion_choices.append(x)
            self.completion_choices.append(None)
        return self.completion_choices[state]

    def complete(self, text, state):
        buffer = readline.get_line_buffer()
        lead_in = buffer[:readline.get_endidx()].split()[-1]
        try:
            if buffer.startswith('*') and ' ' in buffer:
                # See if *command has custom tab completion
                star_command = self.star.commands.get(buffer.split()[0], None)
                if star_command and star_command.tab_completion:
                    return star_command.tab_completion(self, buffer, lead_in, text, state)
            if lead_in.startswith('*'):
                # User needs help completing *command...
                return self.complete_star_command(lead_in, text, state)
            else:
                # Default behavior - remote file path completion
                return self.complete_remote_path(lead_in, text, state)
        except Exception as e:
            raise


################################################################################
# Workaround for https://github.com/radssh/radssh/issues/32
# Newer GNU Readline library raise false errno value that the Python
# wrapper reraises as IOError. https://bugs.python.org/issue10350 not
# being backported to Python 2.7, so handle it with more code...
def safe_write_history_file(filename):
    # To avoid false negative, use stat() to test the file modification times
    try:
        readline.write_history_file(filename)
    except IOError as e:
        # Ignore this exception if we wrote out the history file recently
        try:
            post = os.stat(filename).st_mtime
            if post > time.time() - 3:
                logging.debug('Ignoring "%s" writing history file', str(e))
        except Exception:
            raise e


################################################################################

def radssh_shell_main():
    args = sys.argv[1:]
    defaults = config.load_settings()
    # Keep command line options separately, for reuse in sshconfig defaults
    cmdline_options = config.command_line_settings(args, defaults.get('user.settings'))
    defaults.update(cmdline_options)

    if 'socket.timeout' in defaults:
        socket.setdefaulttimeout(float(defaults['socket.timeout']))

    # Setup Logging
    logformat = '%(asctime)s %(levelname)-8s [%(name)s:%(thread)08X] %(message)s'
    logdir = os.path.expanduser(time.strftime(defaults.get('logdir', '')))
    if logdir:
        if not os.path.exists(logdir):
            os.mkdir(logdir)
        logging.basicConfig(filename=os.path.join(logdir, 'radssh.log'),
                            format=logformat)
    else:
        logging.basicConfig(format=logformat)
        pass
    try:
        logging.getLogger().setLevel(getattr(logging, defaults['loglevel'].upper()))
    except AttributeError:
        raise RuntimeError('RadSSH setting "loglevel" should be set to one of [CRITICAL,ERROR,WARNING,INFO,DEBUG] instead of "%s"', defaults['loglevel'])
    logger = logging.getLogger('radssh')

    # With logging setup, output any deferred warnings
    for w in paramiko_load_warnings:
        logger.warning(warnings.formatwarning(w.message, w.category, w.filename, w.lineno))

    # Make an AuthManager to handle user authentication
    a = ssh.AuthManager(defaults['username'],
                        auth_file=os.path.expanduser(defaults['authfile']),
                        try_auth_none=(defaults['try_auth_none'] == 'on'))

    # Load Plugins to aid in host lookups and add *commands dynamically
    loaded_plugins = {}
    exe_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    system_plugin_dir = os.path.join(exe_dir, 'plugins')
    disable_plugins = defaults['disable_plugins'].split(',')
    plugin_dirs = [x for x in defaults['plugins'].split(';') if x]
    plugin_dirs.append(system_plugin_dir)

    for x in plugin_dirs:
        plugin_dir = os.path.abspath(os.path.expanduser(x))
        if not os.path.exists(plugin_dir):
            continue
        for module in sorted(os.listdir(plugin_dir)):
            if module.endswith('.py') and not module.startswith('__'):
                plugin = module[:-3]
                # Skip modules found in more that 1 location, and ones explicitly disabled
                if plugin in loaded_plugins or plugin in disable_plugins:
                    continue
                try:
                    logger.info('Loading plugin module: %s', plugin)
                    this_plugin = radssh.plugins.load_plugin(os.path.join(plugin_dir, module))
                    if hasattr(this_plugin, 'init'):
                        logger.debug('Calling init method for plugin: %s', plugin)
                        this_plugin.init(defaults=defaults, auth=a, plugins=loaded_plugins, star_commands=star.commands, shell=shell)
                    if hasattr(this_plugin, 'star_commands'):
                        logger.debug('Registering *commands for plugin: %s %s', plugin, this_plugin.star_commands.keys())
                        star.commands.update(this_plugin.star_commands)
                    if hasattr(this_plugin, 'settings'):
                        prefix = 'plugin.%s.' % plugin
                        user_settings = {}
                        user_settings = dict([(k[len(prefix):], v) for k, v in defaults.items() if k.startswith(prefix)])
                        logger.info('Updating settings for plugin %s with: %s', plugin, user_settings)
                        this_plugin.settings.update(user_settings)
                    if hasattr(this_plugin, 'command_listener'):
                        command_listeners.append(this_plugin.command_listener)
                    loaded_plugins[plugin] = this_plugin

                except Exception as e:
                    logger.error('Failed to load plugin (%s): %s', plugin, repr(e))

    # Use command line args as connect list, or give user option to supply list now
    if not args:
        print('No command line arguments given.')
        print('You can connect to a number of hosts by hostname or IP')
        if loaded_plugins:
            print('You can also give symbolic names that can be translated by')
            print('the following loaded plugins:')
            for module, plugin in loaded_plugins.items():
                try:
                    lookup_doc = plugin.lookup.__doc__
                    print(module, plugin.__doc__)
                    print('\t%s' % lookup_doc)
                    try:
                        plugin.banner()
                    except AttributeError:
                        pass
                except AttributeError:
                    pass
        connect_list = raw_input('Enter a list of connection destinations: ').split()
    else:
        connect_list = args

    if not connect_list:
        sys.exit(0)

    # Do the connections if needed, offer names to plugin lookup() functions
    hosts = []
    for arg in connect_list:
        for helper, resolver in loaded_plugins.items():
            if hasattr(resolver, 'lookup'):
                try:
                    cluster = resolver.lookup(arg)
                    if cluster:
                        logger.debug('%s expanded by %s', arg, helper)
                        for label, host, conn in cluster:
                            if conn:
                                hosts.append((label, conn))
                            else:
                                hosts.append((label, host))
                        break
                except Exception as e:
                    logger.error('Exception looking up %s via %s: %r', arg, helper, e)
                    cluster = None
        else:
            hosts.append((arg, None))

    # Almost done with all the preliminary setup steps...
    if defaults['loglevel'] not in ('CRITICAL', 'ERROR'):
        print('*** Parallel Shell ***')
        print('Using AuthManager:', a)
        print('Logging to %s' % logdir)
        pprint.pprint(defaults, indent=4)
        print()
        star.star_help()

    # Create a RadSSHConsole instance for screen output
    job_buffer = int(defaults['stalled_job_buffer'])
    if '.' in defaults['shell.console']:
        # Try finding formatter as module.function from loaded plugins
        logger.info('Attempting to load custom console formatter: %s', defaults['shell.console'])
        module_name, function_name = defaults['shell.console'].split('.', 1)
        try:
            custom_formatter = getattr(loaded_plugins[module_name], function_name)
            console = RadSSHConsole(formatter=custom_formatter, retain_recent=job_buffer)
        except KeyError:
            logger.error('Plugin not loaded for shell.console formatter %s', defaults['shell.console'])
        except AttributeError:
            logger.error('Plugin formatter not found for shell.console formatter %s', defaults['shell.console'])
        except Exception as e:
            logger.error('Exception on console formatter %s: %r', defaults['shell.console'], e)
    elif defaults['shell.console'] != 'color' or not sys.stdout.isatty():
        console = RadSSHConsole(formatter=monochrome, retain_recent=job_buffer)
    else:
        console = RadSSHConsole(retain_recent=job_buffer)

    # Finally, we are able to create the Cluster
    print('Connecting to %d hosts...' % len(hosts))
    cluster = ssh.Cluster(hosts, auth=a, console=console, defaults=defaults)
    if defaults['loglevel'] not in ('CRITICAL', 'ERROR'):
        star.star_info(cluster, logdir, '', [])
    else:
        # If cluster is not 100% connected, let user know even if loglevel is not low enough
        ready, disabled, failed_auth, failed_connect, dropped = cluster.connection_summary()
        if any((failed_auth, failed_connect, dropped)):
            print('There were problems connecting to some nodes:')
            if failed_connect:
                print('    %d nodes failed to connect' % failed_connect)
            if failed_auth:
                print('    %d nodes failed authentication' % failed_auth)
            if dropped:
                print('    %d dropped connections' % dropped)
            print('    Use "*info" for connection details.')

    # Command line history support
    if defaults.get('historyfile'):
        histfile = os.path.expanduser(defaults['historyfile'])
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        readline.set_history_length(int(os.environ.get('HISTSIZE', 1000)))
        if sys.version_info.major == 2:
            # Workaround #32 - fix not backported to Python 2.X
            atexit.register(safe_write_history_file, histfile)
        else:
            atexit.register(readline.write_history_file, histfile)

    # Add TAB completion for *commands and remote file paths
    tab_completion = radssh_tab_handler(cluster, star)

    # With the cluster object, start interactive session
    shell(cluster=cluster, logdir=logdir, defaults=defaults)


if __name__ == '__main__':
    radssh_shell_main()
