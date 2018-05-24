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

'''Sequentially invoke single TTY ssh sessions'''

from __future__ import print_function  # Requires Python 2.6 or higher

import sys
import socket
import select
import termios
import tty
import os
import fcntl


def posix_shell(chan, encoding='UTF-8'):
    partial_buf = b''
    try:
        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if (chan in r):
                try:
                    x = chan.recv(1024)
                    r1, w1, e1 = select.select([], [sys.stdout], [])
                    if (sys.stdout in w1):
                        if len(x) == 0:
                            sys.stdout.write('\r\n*** EOF ***\r\n')
                            break
                        print((partial_buf + x).decode(encoding), end='')
                        sys.stdout.flush()
                        partial_buf = b''
                except socket.timeout:
                    pass
                except UnicodeError:
                    # Keep the bytes read to append to on next pass
                    partial_buf += x
            if sys.stdin in r:
                x = sys.stdin.read()
                chan.send(x.encode(encoding))
    except Exception as e:
        print('Exception in TTY session\n%r\n' % e)


def terminal_size():
    import termios
    import struct
    h, w, hp, wp = struct.unpack('HHHH',
                                 fcntl.ioctl(0, termios.TIOCGWINSZ,
                                             struct.pack('HHHH', 0, 0, 0, 0)))
    return w, h


def radssh_tty(cluster, logdir, cmd, *args):
    '''Invoke a TTY single session'''
    cols, lines = terminal_size()
    if not args:
        args = []
        for k in cluster:
            if k not in cluster.disabled:
                args.append(str(k))

    # Within this tinkering with stdin, output seems
    # to require \r\n for end of line
    oldtty = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())
    tty.setcbreak(sys.stdin.fileno())
    old_fcntl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, old_fcntl | os.O_NONBLOCK)
    prompt_delay = 3.0
    for x in args:
        if not cluster.locate(x):
            print('Skipping TTY request for %s (not found)\r' % str(x))
            continue
        try:
            print('Starting TTY session for [%s] in %g seconds...\r' % (x, prompt_delay))
            print(
                '(Press \'S\' to skip, \'X\' to abort, any other key to connect immediately)',
                end='')
            sys.stdout.flush()
            r, w, e = select.select([sys.stdin], [], [], prompt_delay)
            print('\r\n')
            if r:
                keystroke = sys.stdin.read()
                if keystroke in ('s', 'S'):
                    continue
                if keystroke in ('x', 'X'):
                    break
        except Exception as e:
            print(e)
        try:
            session = None
            t = cluster.connections[cluster.locate(x)]
            if not t.is_authenticated():
                print('Skipping TTY request for %s (not authenticated)\r' % str(x))
                continue
            session = t.open_session()
            session.set_combine_stderr(True)
            session.get_pty(width=cols, height=lines)
            print('Starting TTY session for %s\r' % str(x))
            session.invoke_shell()
            posix_shell(session, cluster.defaults['character_encoding'])
            print('TTY session for %s completed\r' % str(x))
            session.close()
        except Exception as e:
            print('Exception occurred while trying TTY for %s\r' % str(x))
            print(repr(e))
            if session:
                session.close()
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, old_fcntl)

star_commands = {'*tty': radssh_tty}
