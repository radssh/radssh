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

'''Silly, simple, stupid example of a plugin that adds a *command'''

from __future__ import print_function  # Requires Python 2.6 or higher

# Define a python function that takes the following parameters:
#    cluster - gives access to cluster connection list, results, etc.
#    logdir - the current logging directory name for the cluster
#    cmd - the command line text as a string (unparsed)
#    *args - the parsed, whitespace delimited arguments from the command line


def star_bork(cluster, logdir, cmd, *args):
    '''Swedish Chef *command from plugin'''
    # *commands can read/update the cluster information, create
    # their own logfiles in the logdir, leverage the cluster to run jobs,
    # pull information from external sources, or print messages on console
    # or any combination.
    # This simple example only prints static text back to the console
    print('Bork bork bork')

# Shell picks up the available *commands from each plugin
# by looking for this named dictionary: keys are the text
# to match, and values are the functions to call...
star_commands = {'*chef': star_bork}
