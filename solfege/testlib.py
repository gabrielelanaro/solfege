# Solfege - free ear training software
# Copyright (C) 2007, 2008 Tom Cato Amundsen
# License is GPL, see file COPYING

# Utility functions used by the test suite.

from __future__ import absolute_import

import __builtin__
import os
import unittest

from solfege import i18n

__builtin__.testsuite_is_running = True

outdir = 'test-outdir'

class I18nSetup(unittest.TestCase):
    def setUp(self):
        self.__saved_LANGUAGE = os.environ.get('LANGUAGE', None)
        os.environ['LANGUAGE'] = 'nb'
        i18n.setup(".")
    def tearDown(self):
        if self.__saved_LANGUAGE:
            os.environ['LANGUAGE'] = self.__saved_LANGUAGE

