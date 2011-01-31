#!/usr/bin/python
# vim: expandtab:

# Copyright (C) 2007, 2008 Tom Cato Amundsen
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


"""
Read sys.stdin to get the list of files to copy.
We read from stdin instead of getting all the file names
in sys.argv because sys.argv got too long on win32.
"""

import sys, shutil, os.path
filelist = sys.stdin.read().split()
todir = sys.argv[-1]

for fn in filelist:
    if os.path.isdir(fn):
        continue
    head, tail = os.path.split(fn)
    if head:
        if not os.path.exists(os.path.join(todir, head)):
            os.makedirs(os.path.join(todir, head))
    shutil.copy(fn, os.path.join(todir, fn))

