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

'''RadSSH setuptools interface'''
from __future__ import print_function  # Requires Python 2.6 or higher

import sys
import os
import shutil

from setuptools import setup
from os import listdir
from os.path import isfile, join

import radssh

# Apply auto-changes to make Python3 code from 2.X
if sys.version_info >= (3,):
    skip_fixes = 'print callable dict future imports'
    do_not_fix = ['lib2to3.fixes.fix_%s' % x for x in skip_fixes.split()]
    auto_2to3 = {'use_2to3': True,
                 'use_2to3_exclude_fixers': do_not_fix}
else:
    auto_2to3 = {}

# Gather up all supplemental plugins from various directories
# and copy them into the core plugins directory prior to install
if not os.path.exists('radssh/plugins'):
    os.mkdir('radssh/plugins')
for p, d, f in os.walk('radssh'):
    for ignore in [subdir for subdir in d if not subdir.endswith('_plugins')]:
        d.remove(ignore)
    if p.endswith('_plugins'):
        print('Merging plugins from %s' % p)
        for plugin in f:
            if not plugin.endswith('.pyc'):
                shutil.copy2(os.path.join(p, plugin), 'radssh/plugins')

# Get list of non .py files in plugins directory to include as pkg_data
olddir = os.getcwd()
os.chdir('radssh')
pkg_data_files = [join('plugins', f) for f in listdir('plugins') if not f.endswith('.py') and isfile(join('plugins', f))]
os.chdir(olddir)

# Conditional requirements (colorama for Windows platform only)
required_packages = ['paramiko', 'netaddr']
if sys.platform.startswith('win'):
    required_packages.append('colorama>=0.3.9')
    required_packages.append('pyreadline')

setup(name='radssh',
      version=radssh.version,
      description='RadSSH Module',
      author=radssh.__author__,
      author_email=radssh.__author_email__,
      license='BSD',
      keywords='ssh parallel paramiko',
      url='https://github.com/radssh/radssh',
      # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: POSIX',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: MacOS :: MacOS X',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: System :: Shells',
          'Topic :: Utilities'],
      packages=['radssh', 'radssh.plugins'],
      package_data={'': pkg_data_files},
      install_requires=required_packages,
      long_description='''
RadSSH Package
==============

RadSSH is a Python package that is built with Paramiko.

Documentation for the project is hosted on ReadTheDocs, at http://radssh.readthedocs.org

Frequently Asked Questions: https://github.com/radssh/radssh/blob/master/FAQ.md

RadSSH is installable via **pip**, using "**pip install radssh**".

----


The RadSSH shell behaves similar to a normal ssh command line client, but instead of connecting to one host (at a time), you can connect to dozens or even hundreds at a time, and issue interactive command lines to all hosts at once. It requires very little learning curve to get started, and leverages on existing command line syntax that you already know. ::

   [paul@localhost ~]$ python -m radssh.shell huey dewey louie
   Please enter a password for (paul) :
   Connecting to 3 hosts...
   ...
   RadSSH $ hostname
   [huey] huey.example.org
   [dewey] dewey.example.org
   [louie] louie.example.org
   Average completion time for 3 hosts: 0.058988s

   RadSSH $ uptime
   [huey]  15:21:28 up 6 days, 22:49, 17 users,  load average: 0.30, 0.43, 0.39
   [louie] 15:43  up 652 days,  4:59, 0 users, load averages: 0.44 0.20 0.17
   [dewey]  15:21:28 up 109 days, 23:28,  3 users,  load average: 0.27, 0.09, 0.07
   Average completion time for 3 hosts: 0.044532s

   RadSSH $ df -h /
   [huey] Filesystem            Size  Used Avail Use% Mounted on
   [huey] /dev/mapper/vg-Scientific
   [huey]                        24G   22G  694M  97% /
   [louie] Filesystem     Size   Used  Avail Capacity  Mounted on
   [louie] /dev/disk0s3   234G   134G    99G    57%    /
   [dewey] Filesystem                        Size  Used Avail Use% Mounted on
   [dewey] /dev/mapper/vg_pkapp745-LogVol00   20G   17G  2.1G  89% /
   Average completion time for 3 hosts: 0.036792s

   RadSSH $ *exit
   Shell exiting


RadSSH includes a loadable plugin facility to extend the functionality of the shell with basic Python scripting, as well as a high level API that can be used to build stand alone applications for dedicated SSH control processing in a parallel environment.

Interested in more?
 * Download at https://pypi.python.org/pypi/radssh
 * Read the Docs at http://radssh.readthedocs.org/en/latest/index.html
 * Participate at https://github.com/radssh/radssh
''',
      **auto_2to3)
