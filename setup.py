#!/usr/bin/env python
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
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Topic :: System :: Shells',
          'Topic :: Utilities'],
      packages=['radssh', 'radssh.plugins'],
      package_data={'': pkg_data_files},
      install_requires=['paramiko', 'netaddr'],
      long_description='''High level Paramiko-based toolkit, with an extensible parallel cluster "shell"''',
      **auto_2to3)
