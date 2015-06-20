#
# Copyright (c) 2014 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

'''Configuration file module'''
from __future__ import print_function  # Requires Python 2.6 or higher


import sys
import os
import warnings
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO


system_settings_file = '/etc/radssh_config'
deprecated = {
    'verbose': 'Use loglevel=[CRITICAL|ERROR|WARNING|INFO|DEBUG] instead',
    'paramiko_log_level': 'Use loglevel for controlling RadSSH and Paramiko logging'
}

default_config = '''
# Package supplied configuration settings
### All lines starting with # are comments
### All other lines should be of the form keyword=value

### Shell Behavior Defaults
# NOTE: verbose and paramiko_log_level settings have been deprecated
# Use loglevel instead, and logging from both RadSSH and paramiko get captured to radssh.log
#
# loglevel can be set to [CRITICAL|ERROR|WARNING|INFO|DEBUG]
loglevel=ERROR

shell.prompt=RadSSH $
shell.console=color
max_threads=120
# Automatically save log files into date/time-stamped local directory
logdir=session_%Y%m%d_%H%M%S
# Log all normal output to given filename in logdir. Set empty to turn off
# NOTE: This logging is in addition to host-by-host logging
log_out=out.log
# Log all error output to given filename in logdir. Set empty to turn off
# NOTE: This is in addition to host-by-host error logging
log_err=err.log

# Command line history file, saved across sessions
historyfile=~/.radssh_history

# Available modes: {stream, ordered, off}
output_mode=stream
# Avoiding runaway commands with either too much output, or
# waiting indefinately at a user prompt...
quota.time=0
quota.lines=0
quota.bytes=0

# Connection & Authentication Options
# Username defaults to $SSH_USER (or $USER) if not set here
# username=root
# Permit public key authentication by keys loaded into ssh-agent
ssh-agent=off
# Also access ~/.ssh/id_rsa and ~/.ssh/id_dsa without needing ssh-agent
ssh-identity=off
# Supplemental authentication file for more keys and/or passwords
authfile=~/.radssh_auth

# Network Tweaks
socket.timeout=30
keepalive=180

# Extensions to the shell via plugins
# System plugin collections always loaded from ${EXEC}/plugins
# User plugins loaded from directories listed here (optional)
plugins=
# Selectively disable plugins, if for some reason you want to
# avoid loading some system (or user) plugins that normally load
disable_plugins=

# How to handle host key verification
# Valid settings, in decreasing order of security/paranoia
#     reject - (default) host key must be in ~/.ssh/known_hosts (and match)
#     prompt - ask user to add missing host keys
#     accept_new - missing host keys added without prompt
#     ignore - No host key checking is done
# In all cases, mismatched key info between known_hosts and current connection
# will report the conflict, and drop the connection without sending any more data
hostkey.verify=reject
hostkey.known_hosts=~/.ssh/known_hosts

# Enable loading of user specific settings (and command line options)
# Only if this is set.
user.settings=~/.radssh_config

# Rudimentary command safeguards
# First, outright forbid commands that should only be run with a TTY
# which RadSSH typically does not provide...
commands.forbidden=telnet,ftp,sftp,vi,vim,ssh
# Also, for commands that could have devastating side effects, have
# RadSSH prompt the user if they are 100% sure they want to run...
commands.restricted=rm,reboot,shutdown,halt,poweroff,telinit

# Some SSH hosts do not support exec_command invocation, and require
# a session to be used via invoke_shell() instead. In addition, based
# on observation, the underlying transport is terminated when the session
# is closed, so the open session MUST stay persistent across command
# invocations.
# Identify such "problem" hosts by their SSH Server version string, which
# can be gathered using ssh-keyscan.
force_tty=Cisco,force10networks
# In addition, allow custom command(s) to be issued at signon and signoff
# to permit session to behave as RadSSH expects, without user input...
force_tty.signon=term length 0
force_tty.signoff=term length 20

# Should RadSSH initially send auth_none request (needed for OpenSSH 4.3 banner)
try_auth_none=off
'''

if sys.version_info[:2] == (2, 7):
    default_config = unicode(default_config)


def load_settings_file(f):
    '''Load settings from a file-like object, returning a dict'''
    settings = {}
    for line_number, line in enumerate(f, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            setting = line.split('=', 1)
            settings[setting[0].strip()] = setting[1].strip()
        else:
            if hasattr(f, 'name'):
                warnings.warn_explicit('Invalid line in settings file [%s]' % line, RuntimeWarning, f.name, line_number)
            else:
                warnings.warn(RuntimeWarning('Invalid line in default settings (Line %d) "%s"' % (line_number, line)))
    return settings


def deprecated_check(d, filename=None):
    '''Check settings dict against the deprecated options'''
    for k in deprecated:
        if k in d:
            warnings.warn('DEPRECATED: [%s] found in %s is ignored.\n\t%s' % (k, filename, deprecated[k]))
            d.pop(k)


def load_default_settings():
    '''Load just the default settings, ignoring system and user settings files'''
    # Start with the default_config settings from the module
    defaults = StringIO(default_config)
    settings = load_settings_file(defaults)
    return settings


def load_settings(cmdline_args=[]):
    '''Load a full settings dict from defaults, system, user, and command line settings'''
    settings = load_default_settings()
    # Also load the system-wide settings
    if os.path.exists(system_settings_file):
        with open(system_settings_file) as f:
            system_settings = load_settings_file(f)
            deprecated_check(system_settings, system_settings_file)
            settings.update(system_settings)
    # If admin has not disabled user settings, load them and finally the command line settings
    if settings.get('user.settings'):
        user_settings_file = os.path.expanduser(settings.get('user.settings'))
        if os.path.exists(user_settings_file):
            with open(user_settings_file) as f:
                user_settings = load_settings_file(f)
                deprecated_check(user_settings, user_settings_file)
                settings.update(user_settings)
    for arg in list(cmdline_args):
        if arg.startswith('--'):
            try:
                k, v = arg.split('=', 1)
                # Only apply command line option if user.settings is still enabled
                if settings.get('user.settings'):
                    commandline_setting = {k[2:]: v}
                    deprecated_check(commandline_setting, 'command line argument')
                    settings.update(commandline_setting)
                else:
                    warnings.warn(RuntimeWarning('Command line option: %s (ignored) - User settings disabled by administrator' % (arg)))
            except ValueError:
                warnings.warn(RuntimeWarning('Invalid command line option: %s (ignored)' % (arg)))
            cmdline_args.remove(arg)
    # Fill username in from environments if not supplied from configuration source(s)
    if 'username' not in settings:
        settings['username'] = os.environ.get(
            'SSH_USER', os.environ.get('USER', os.environ.get('USERNAME', 'default')))
    return settings


def main():
    '''Print the RadSSH default settings as reference'''
    for x in default_config.split('\n'):
        if x.startswith('#'):
            print('##%s' % str(x))
        elif not x.strip():
            print()
        else:
            print('# %s' % str(x))

if __name__ == '__main__':
    main()
