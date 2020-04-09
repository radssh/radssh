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
RadSSH Main Module
==================

Rather than defaulting to running a RadSSH Shell session, this main module
just reports on version information on RadSSH itself, and the strict dependent
modules. This information list should be included in any bug reports.

It also runs a few basic limit checks to determine the maximum concurrent
threads and open file handles for the runtime environment. These two limits
factor into the maximum number of simultaneous connections that RadSSH
can manage.
'''
from __future__ import print_function  # Requires Python 2.6 or higher

import os
import sys
import time
import platform
import threading

import netaddr
import radssh
import paramiko

# Paramiko 2.0 switched dependency from PyCrypto to cryptography.io
if paramiko.__version_info__ >= (2, 0):
    import cryptography as crypto_module
else:
    import Crypto as crypto_module


def open_file(name):
    """
    Return an open file object.
    """
    return open(name, 'r')


def start_thread(event):
    """
    Start a thread that waits on a given event, then terminates.
    Used for determining how many threads can be successfully
    started before Python or OS reaches an upper limit.
    """

    def dummy_thread(event):
        """
        Simply wait on event to keep thread active.
        """
        event.wait()

    t = threading.Thread(target=dummy_thread, args=(event,))
    t.start()
    return t


if __name__ == '__main__':
    print('RadSSH Main Module')
    print('Package RadSSH %s from (%s)' % (radssh.version, radssh.__file__))
    # Dependent modules - Print version and location
    print('  Using Paramiko ', paramiko.__version__, 'from', paramiko.__file__)
    print('  Using', crypto_module.__name__, crypto_module.__version__, 'from', crypto_module.__file__)
    print('  Using netaddr', netaddr.__version__, 'from', netaddr.__file__)
    print()

    # Runtime environment info
    print('Python %s (%s)' % (platform.python_version(), platform.python_implementation()))
    print('Running on', platform.system(), '[%s]' % platform.node())
    if platform.system() == 'Linux':
        print('  %s (%s)' % (platform.linux_distribution()[0],
                             '/'.join(platform.linux_distribution()[1:])))
    print('Encoding for stdout:', sys.stdout.encoding)

    # Test runtime limits of open files and threads
    print('\nChecking runtime limits...')
    lim = []
    t0 = time.time()
    try:
        for x in xrange(10000):
            lim.append(open_file(os.devnull))
    except Exception as e:
        print('  System is able to open a maximum of %d concurrent files' % len(lim))
        print('    Attempting to open file #%d reported (%s)' % (len(lim) + 1, repr(e)))
    else:
        print('  System is able to open at least %d concurrent files' % len(lim))
    finally:
        t1 = time.time()
        print('  File check completed in %f seconds\n' % (t1 - t0))
        while lim:
            lim.pop().close()
    t0 = time.time()
    kill_threads = threading.Event()
    try:
        for x in xrange(10000):
            lim.append(start_thread(kill_threads))
    except Exception as e:
        print('  System is able to run %d concurrent threads' % len(lim))
        print('    Attempting to start thread #%d reported (%s)' % (len(lim) + 1, repr(e)))
    else:
        print('  System is able to run %d concurrent threads' % len(lim))
    finally:
        t1 = time.time()
        print('  Thread check completed in %f seconds\n' % (t1 - t0))
        kill_threads.set()
        while lim:
            lim.pop().join()
    print('End of runtime check')
