#
# Copyright (c) 2018 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

'''
Customizable RadSSH Console formatter module:
Allow plugins to provide formatter function(s) to supplement the
basic monochrome and colorizer formatters included as defaults.

This module can be copied and customized, and loaded as a RadSSH
plugin with an arbitrary name, and multiple formatter functions.

To enable custom formatter, set "shell.console=formatters.ansi256"
'''

import string
import fcntl
import termios
import struct

# See: http://misc.flogisoft.com/bash/tip_colors_and_formatting
# Grab a broad range of colors that avoid the muddled dark on dark contrast
palette = list(range(20, 230))


def ansi256(tag, text):
    '''ANSI 256 colorized output with semi-restricted palette'''
    label, hilight = tag
    color = palette[hash(label) % len(palette)]
    for line in text.split('\n'):
        if hilight:
            yield '\033[1;38;5;%dm[%s] %s\033[0m\n' % (color, label, line)
        else:
            yield '\033[38;5;%dm[%s] %s\033[0m\n' % (color, label, line)


def ansi256_rj(tag, text):
    '''ANSI 256 colorized output, with host label right-justified'''
    label, hilight = tag
    height, width = struct.unpack('hh', fcntl.ioctl(0, termios.TIOCGWINSZ, '1234'))

    color = palette[hash(label) % len(palette)]
    for line in text.split('\n'):
        wide_line = string.ljust(line, width - len(label) - 2, ' ')
        if hilight:
            yield '\033[1;38;5;%dm%s[%s]\033[0m\n' % (color, wide_line, label)
        else:
            yield '\033[38;5;%dm%s[%s]\033[0m\n' % (color, wide_line, label)


def ip_hash(hstr0):
    '''Improved hashing when dealing with consecutive IP addresses'''
    hstr1 = re.sub('[^0-9]', '.', hstr0)
    hstr2 = hstr1.replace(".", "0")
    hstr = hstr2[-3:]
    hval = int(hstr)
    return hval


def ip_colorizer(tag, text):
    '''Alternative ANSI colorized output - ensure that IP address ranges cycle colors more uniformly'''
    # Copied from standard colorizer, but with a custom hash function
    label, hilight = tag
    color = 1 + ip_hash(str(label)) % 7
    for line in text.split('\n'):
        if hilight:
            yield '\033[30;4%dm[%s]\033[0;1;3%dm %s\033[0m\n' % (color, label, color, line)
        else:
            yield '\033[3%dm[%s] %s\033[0m\n' % (color, label, line)
