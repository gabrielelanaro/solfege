#!/usr/bin/python
# vim: set fileencoding=utf8:
# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005, 2007, 2008  Tom Cato Amundsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This script is used to launch Solfege when running
# it from the source dir without installing.
from __future__ import absolute_import
import __builtin__
import time
__builtin__.start_time = time.time()

import sys
import os
import os.path
import shutil
import traceback
import textwrap

from solfege import cfg
from solfege import filesystem

if sys.platform == 'win32':
    # Migration added in solfege 3.9.0.
    try:
        if not os.path.exists(filesystem.app_data()):
            if os.path.exists(os.path.join(filesystem.get_home_dir(), ".solfege")):
                shutil.copytree(os.path.join(filesystem.get_home_dir(), ".solfege"),
                                filesystem.app_data())
            else:
                os.mkdir(filesystem.app_data())
        if not os.path.exists(filesystem.rcfile()):
            if os.path.exists(os.path.join(filesystem.get_home_dir(), ".solfegerc")):
                shutil.copy(os.path.join(filesystem.get_home_dir(), ".solfegerc"),
                            filesystem.rcfile())
    except (IOError, os.error), e:
        print "Migration failed:", e

if not os.path.exists(filesystem.app_data()):
    os.makedirs(filesystem.app_data())
if not os.path.exists(filesystem.user_data()):
    os.makedirs(filesystem.user_data())

try:
    cfg.initialise("default.config", None, filesystem.rcfile())
except UnicodeDecodeError, e:
    traceback.print_exc()
    print >> sys.stderr
    print >> sys.stderr, "\n".join(textwrap.wrap(
          "Your %s file is not properly utf8 encoded. Most likely"
          " it is the path to some external program that contain non-ascii"
          " characters. Please edit or delete the file. Or email it to"
          " tca@gnu.org, and he will tell you what the problem is." % filesystem.rcfile().encode("ascii", "backslashreplace")))
    print >> sys.stderr
    sys.exit("I give up (solfege.py)")


# i18n should be imported very early in program init because it setup
# the _ and _i functions for the whole program.
import solfege.i18n
# MIGRATION from 2.9.2 to 2.9.3
if cfg.get_string("app/lc_messages") == 'C (english)':
    cfg.set_string("app/lc_messages", "C")
solfege.i18n.setup(".", cfg.get_string("app/lc_messages"))

import solfege.startup

solfege.startup.start_app(".")
