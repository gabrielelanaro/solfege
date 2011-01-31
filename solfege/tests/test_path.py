# Solfege - free ear training software
# Copyright (C) 2007, 2008 Tom Cato Amundsen
# License is GPL, see file COPYING

from __future__ import absolute_import
import unittest
from solfege.gpath import Path

class TestPath(unittest.TestCase):
    def test_next(self):
        p = Path((1, 2, 3))
        self.assert_(p.next(), (1, 2, 4))
    def test_prev(self):
        p = Path((1, 2, 3))
        self.assert_(p.prev(), (1, 2, 2))
    def test_child(self):
        p = Path((1, 2, 3))
        self.assert_(p.child(), (1, 2, 3, 0))
    def test_parent(self):
        p = Path((1, 2, 3))
        self.assert_(p.parent(), (1, 2))

suite = unittest.makeSuite(TestPath)

