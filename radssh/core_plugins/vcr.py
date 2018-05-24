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

'''Plugin to provide VCR-like capabilities for command lines'''

from __future__ import print_function  # Requires Python 2.6 or higher


import os
import atexit
import pprint


vcr = None
shell = None


def init(**kwargs):
    # VCR needs access ot the parent shell for playback
    global shell
    try:
        shell = kwargs['shell']
    except KeyError:
        raise RuntimeError('VCR: Unable to initialize', 'RadSSH shell not accessible')


class Recorder(object):
    def __init__(self, filename, vars={}):
        self.active = True
        self.data = []
        self.filename = filename
        self.vars = vars

    def pause(self):
        self.active = not self.active

    def feed(self, x):
        if self.active:
            self.data.append(x)

    def save(self):
        with open(self.filename, 'a') as f:
            f.write('\n'.join(self.data))
        if self.vars:
            with open(self.filename + '.vars', 'w') as f:
                f.write(pprint.pformat(self.vars))


def command_listener(cmd):
    global vcr
    if vcr:
        args = cmd.split()
        if args and not args[0] in star_commands:
            vcr.feed(cmd)


def eject():
    '''Register this as an atexit function to save off vcr session when shell terminates'''
    global vcr
    if vcr:
        print('Auto-saving VCR contents')
        vcr.save()

atexit.register(eject)


def record(cluster, logdir, cmd, *args):
    '''Begin recording of session commands for later playback'''
    global vcr
    if not args:
        if vcr:
            print('Stop Recording')
            vcr.save()
            print('Finished recording saved to %s (%d lines)' % (vcr.filename, len(vcr.data)))
            vcr = None
        else:
            print('Use "*record <filename>" to begin recording')
        return
    if os.path.sep in args[0]:
        filename = args[0]
    else:
        filename = os.path.join(logdir, args[0])
    if vcr:
        # Save off old recording session
        vcr.save()
        print('Saved existing recording to %s (%d lines)' % (vcr.filename, len(vcr.data)))
    vcr = Recorder(filename, cluster.user_vars)
    print('Started new recording to %s' % filename)


def pause(cluster, logdir, cmd, *args):
    '''Temporary suspend/resume toggle for VCR-like recording'''
    global vcr
    if not vcr:
        print('VCR not running. Did you put in a tape?')
        return
    vcr.pause()
    if vcr.active:
        print('VCR unpaused')
    else:
        print('VCR paused (%d lines in buffer)' % len(vcr.data))


def playback(cluster, logdir, cmd, *args):
    '''Playback scripted commands from *record save file, or other script file'''
    if len(args) != 1:
        print('Try "*playback <filename>"')
        return
    filename = args[0]
    if os.path.exists(filename + '.vars'):
        print('Loading saved variables...')
        try:
            with open(filename + '.vars', 'r') as var_file:
                cluster.user_vars.update(eval(var_file.read()))
        except Exception as e:
            print('Failed to load variables from [%s]' % filename + '.vars')
            print('%r' % e)
    with open(filename) as f:
        shell(cluster, logdir, f)
    print('*** Playback of %s complete ***' % filename)

star_commands = {'*record': record, '*pause': pause, '*playback': playback}
