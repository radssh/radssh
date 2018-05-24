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
RadSSH Console
==============
Handle output text streamed to a Queue to present on terminal.

Messages are expected to be tagged as to their origin, expected
to be a pair (label, stderr), where label is typically a hostname
and stderr is a boolean indicating if the message content came from
stderr (highlight) or not.
'''
from __future__ import print_function
import sys
import threading
import getpass
from collections import deque, defaultdict
try:
    import queue
except ImportError:
    import Queue as queue


console_mutex = threading.Lock()


def user_input(prompt):
    with console_mutex:
        answer = raw_input(prompt)
    return answer


def user_password(prompt):
    with console_mutex:
        answer = getpass.getpass(prompt)
    return answer


def monochrome(tag, text):
    '''Basic Formatter for plain (monochrome) output'''
    label, hilight = tag
    for line in text.split('\n'):
        yield '[%s] %s\n' % (label, line)


def colorizer(tag, text):
    '''Basic ANSI colorized output - host hash value map to 7-color palette, stderr bold'''
    label, hilight = tag
    color = 1 + hash(label) % 7
    for line in text.split('\n'):
        if hilight:
            yield '\033[30;4%dm[%s]\033[0;1;3%dm %s\033[0m\n' % (color, label, color, line)
        else:
            yield '\033[3%dm[%s] %s\033[0m\n' % (color, label, line)


class RadSSHConsole(object):
    '''
    Combine a Queue object with a daemon thread that pulls message
    output from the queue and pretties it up for on screen display.
    When run in a terminal window, uses ANSI escape sequences to
    colorize output, and use the window/tab title for status messages.
    '''
    def __init__(self, q=None, formatter=colorizer, retain_recent=0):
        if q:
            self.q = q
        else:
            self.q = queue.Queue(300)
        self.formatter = formatter
        self.quietmode = False
        self.background_thread = threading.Thread(target=self.console_thread, args=())
        self.background_thread.setDaemon(True)
        self.background_thread.setName('Console Output')
        self.background_thread.start()

        def limit_deque():
            return deque([], retain_recent)

        self.retain_recent = retain_recent
        self.recent_history = defaultdict(limit_deque)

    def quiet(self, enable=True):
        '''Set (or clear) console quietmode. Returns prior setting.'''
        # Wait for queue to drain before taking effect
        self.q.join()
        retval = self.quietmode
        self.quietmode = enable
        return retval

    def status(self, message):
        '''Set console (titlebar) status message'''
        if not self.quietmode:
            # Jam into window title bar
            print("\x1b]2;%s\x07" % message, end='')
            sys.stdout.flush()

    def join(self, clear_history=False):
        self.q.join()
        if clear_history:
            self.recent_history.clear()

    def message(self, message, label='CONSOLE'):
        '''Main thread can submit CONSOLE messages directly through instance'''
        self.q.put(((label, True), str(message)))

    def progress(self, s):
        '''For progress-bar like output; no newlines'''
        if not self.quietmode:
            with console_mutex:
                print(s, end='')
                sys.stdout.flush()

    def replay_recent(self, label):
        '''Output the recent lines sent tagged from "label" - Used for Ctrl-C handler'''
        if not self.retain_recent:
            return
        self.join()
        for line in self.recent_history.get(str(label), []):
            print('STALLED: ' + line, end='')

    def console_thread(self):
        '''Background-able thread to pull from outputQ and format and print to screen'''
        while True:
            try:
                tag, text = self.q.get()
                if not self.quietmode:
                    with console_mutex:
                        # Tag is tuple of (label, stderr_flag)
                        for line in self.formatter(tag, text):
                            print(line, end='')
                            if self.retain_recent:
                                self.recent_history[str(tag[0])].append(line)
                        sys.stdout.flush()
            except Exception as e:
                print('Console Thread Exception: %s\n' % str(e))
                print('(%s): %s\n' % (tag, text))
            finally:
                self.q.task_done()


if __name__ == '__main__':
    c = RadSSHConsole()
    c.message('Begin Console Output')
    c.status('Title Bar Set')
    for x in range(20):
        c.q.put((('Loop', False), str(x)))
    print('Loop complete\n', end='')
    c.join()
    print('Console output complete')
    sys.stdout.flush()
