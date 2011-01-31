# Solfege - free ear training software
# Copyright (C) 2007, 2008 Tom Cato Amundsen
# License is GPL, see file COPYING

from __future__ import absolute_import
import unittest
from solfege.utils import string_get_line_at


class TestStringGetLineAt(unittest.TestCase):
    def test1(self):
        self.assertEquals(string_get_line_at("abc", 1), "abc")
        self.assertEquals(string_get_line_at("\nabc", 1), "abc")
        self.assertEquals(string_get_line_at("abc\n", 0), "abc")
        self.assertEquals(string_get_line_at("abc\n", 2), "abc")
        self.assertEquals(string_get_line_at("abc\n", 3), "abc")
        self.assertEquals(string_get_line_at("abc\n\n", 3), "abc")
        self.assertEquals(string_get_line_at("abc\n\n", 4), "")
        self.assertEquals(string_get_line_at("abc\n\nx", 4), "")
        self.assertEquals(string_get_line_at("abc\n\nx", 5), "x")
        self.assertRaises(IndexError, lambda x: string_get_line_at("", 0), "")
        self.assertEquals(string_get_line_at("  \n\n   \t \n \t abc \n", 3), "")
        self.assertEquals(string_get_line_at("  \n\n   \t \n \t abc \n", 4), "   \t ")

suite = unittest.makeSuite(TestStringGetLineAt)
