# vim: set fileencoding=utf-8 :
# Solfege - free ear training software
# Copyright (C) 2007, 2008 Tom Cato Amundsen
# License is GPL, see file COPYING

from __future__ import absolute_import
import unittest
import traceback
import codecs

from solfege.testlib import I18nSetup, outdir
from solfege.dataparser import *
import solfege.i18n
import os

class TestLexer(unittest.TestCase):
    def test_get_line(self):
        l = Lexer("""#comment1
#comment2
#comment3

var = 3
""", None)
        self.assertEquals(l.get_line(0), "#comment1")
        self.assertEquals(l.get_line(1), "#comment2")
        self.assertEquals(l.get_line(2), "#comment3")
        self.assertEquals(l.get_line(3), "")
        self.assertEquals(l.get_line(4), "var = 3")
    def test_scan(self):
        p = Dataparser({}, {})
        p._lexer = Lexer("\"string\" name 1.2 2 (", p)
        self.assertEquals(p._lexer.scan(STRING), "string")
        self.assertEquals(p._lexer.scan(NAME), "name")
        self.assertEquals(p._lexer.scan(FLOAT), "1.2")
        self.assertEquals(p._lexer.scan(INTEGER), "2")
        p._lexer = Lexer("1 2 3", p)
        try:
            p._lexer.scan(STRING)
        except DataparserException, e:
            self.assertEquals(u"(line 1): 1 2 3\n"
                              u"          ^",
                              e.m_nonwrapped_text)
    def test_unable_to_tokenize(self):
        p = Dataparser({}, {})
        try:
            p._lexer = Lexer("question { a = 3} |!", p)
        except UnableToTokenizeException, e:
            self.assertEquals("(line 1): question { a = 3} |!\n"
                              "                            ^",
                              e.m_nonwrapped_text)
        try:
            p._lexer = Lexer("x = 4\n"
                             "question { a = 3} |!", p)
        except UnableToTokenizeException, e:
            self.assertEquals("(line 1): x = 4\n"
                              "(line 2): question { a = 3} |!\n"
                              "                            ^",
                              e.m_nonwrapped_text)
    def test_encodings_utf8(self):
        s = """
        name = "øæå" """
        f = codecs.open(os.path.join(outdir, "file1"), 'w', 'utf-8')
        f.write(s)
        f.close()
        f = open(os.path.join(outdir, "file1"), 'rU')
        s = f.read()
        f.close()
        p = Dataparser({}, {})
        p._lexer = Lexer(s, p)
        self.assertEquals(p._lexer.m_tokens[2][1], "øæå")
    def test_encodings_iso88591(self):
        s = '#vim: set fileencoding=iso-8859-1 : \n' \
            'name = "øæå" '
        f = codecs.open(os.path.join(outdir, "file1"), 'w', 'iso-8859-1')
        f.write(s)
        f.close()
        f = open(os.path.join(outdir, "file1"), 'rU')
        s = f.read()
        f.close()
        p = Dataparser({}, {})
        p._lexer = Lexer(s, p)
        self.assertEquals(p._lexer.m_tokens[2][1], "øæå")
    def _test_encodings_delcar_not_first(self):
        """
        FIXME: I disabled this test because people suddenly started
        to report that UnableToTokenizeException was not raised.
        """
        s = '#\n#\n#vim: set fileencoding=iso-8859-1 : \n' \
            'name = "øæå" '
        f = codecs.open(os.path.join(outdir, "file1"), 'w', 'iso-8859-1')
        f.write(s)
        f.close()
        f = open(os.path.join(outdir, "file1"), 'rU')
        s = f.read()
        f.close()
        self.assertRaises(UnableToTokenizeException,
            lambda: Lexer(s, Dataparser({}, {})))
    def _test_missing_encoding_definition_iso88591(self):
        """
        FIXME: I disabled this test because people suddenly started
        to report that UnableToTokenizeException was not raised.
        We write a simple datafile in iso-8859-1 encoding, but does not
        add the encoding line. The dataparser will assume files are utf-8
        by default, and will fail to tokenize.
        """
        s = 'name = "øæå" '
        f = codecs.open(os.path.join(outdir, "file1"), 'w', 'iso-8859-1')
        f.write(s)
        f.close()
        f = open(os.path.join(outdir, "file1"), 'rU')
        s = f.read()
        f.close()
        self.assertRaises(UnableToTokenizeException,
            lambda: Lexer(s, Dataparser({}, {})))
    def test_X(self):
        s = r"""
question {
   music = music("\staff \stemUp  {
   \clef violin \key d \minor \time 4/4
    c4
    }a")
}
"""
        p = Dataparser({}, {})
        p._lexer = Lexer(s, p)

class TestDataParser(I18nSetup):
    def test_for_trainingset(self):
        p = Dataparser({}, {})
        p.parse_string("""fileformat_version = 1
        lesson {
        lesson_id = "lkalskdj alskdj lkj "
        count = 3
        repeat=2
        delay = 2}""")
        self.assertEqual(p.globals['fileformat_version'], 1)
        self.assertEqual(len(p.blocklists), 1)
        self.assertEqual(len(p.blocklists['lesson']), 1)
        l = p.blocklists['lesson'][0]
        self.assertEqual(l['count'], 3)
    def assertRaisedIn(self, methodname):
        t = traceback.extract_tb(sys.exc_info()[2])
        self.assertEquals(t[-1][2], methodname)
    def test_exception_statement_1(self):
        p = Dataparser({}, {})
        try:
            p.parse_string("b")
        except DataparserSyntaxError, e:
            self.assertRaisedIn('statement')
            self.assertEquals(u"(line 1): b\n"+
                              u"           ^",
                              e.m_nonwrapped_text)
            self.assertEquals(e.m_token, ('EOF', None, 1, 0))
    def test_exception_statement_2(self):
        p = Dataparser({}, {})
        try:
            p.parse_string("a)")
        except DataparserSyntaxError, e:
            self.assertRaisedIn('statement')
            self.assertEquals(u"(line 1): a)\n"+
                              u"           ^",
                              e.m_nonwrapped_text)
            self.assertEquals(e.m_token, (')', ')', 1, 0))
    def test_exception_statement_3(self):
        p = Dataparser({}, {})
        try:
            p.parse_string("""#comment
  XYZ
""")
        except DataparserSyntaxError, e:
            self.assertRaisedIn('statement')
            self.assertEquals(u"(line 1): #comment\n"+
                              "(line 2):   XYZ\n"+
                              "(line 3): \n"+
                              "          ^",
                              e.m_nonwrapped_text)
    def test_exception_statement_4(self):
        p = Dataparser({}, {})
        try:
            p.parse_string("""#comment
  A)
""")

        except DataparserSyntaxError, e:
            self.assertRaisedIn('statement')
            self.assertEquals(u"(line 1): #comment\n"+
                              "(line 2):   A)\n"+
                              "             ^",
                              e.m_nonwrapped_text)
    def test_exception_functioncall(self):
        p = Dataparser({}, {})
        try:
            p.parse_string("a=1\n"
                           "b = func() c=3")
        except NameLookupException, e:
            self.assertEquals(e.m_token[TOKEN_STRING], 'func')
            self.assertEquals("(line 1): a=1\n"
                              "(line 2): b = func() c=3\n"
                              "              ^",
                              e.m_nonwrapped_text)
        p = Dataparser({}, {})
        try:
            p.parse_string("a=1\n"
                           "b = func(3, 4) c=3")
        except NameLookupException, e:
            self.assertEquals(e.m_token[TOKEN_STRING], 'func')
            self.assertEquals("(line 1): a=1\n"
                              "(line 2): b = func(3, 4) c=3\n"
                              "              ^",
                              e.m_nonwrapped_text)
    def test_exception_atom(self):
        p = Dataparser({}, {})
        try:
            p.parse_string("a=b")
        except NameLookupException, e:
            self.assertEquals(e.m_token[TOKEN_STRING], "b")
            self.assertEquals("(line 1): a=b\n"
                              "            ^",
                              e.m_nonwrapped_text)
    def test_exception_assignment(self):
        p = Dataparser({}, {})
        try:
            p.parse_string("question = 3")
        except AssignmentToReservedWordException, e:
            self.assertRaisedIn('assignment')
            self.assertEquals(u"(line 1): question = 3\n" +
                              u"          ^",
                              e.m_nonwrapped_text)
    def test_istr(self):
        p = Dataparser({}, {'_': (False, dataparser_i18n_func)})
        p.parse_string("""name = _("minor")
         question { qname=_("major") } """)
        self.assertEquals(p.globals['name'], u'moll')
        self.assertEquals(p.globals['name'].cval, u'minor')
        self.assertEquals(p.questions[0]['qname'], u'dur')
        self.assertEquals(p.questions[0]['qname'].cval, u'major')
    def test_istr_translations_in_file1(self):
        p = Dataparser({}, {'_': (False, dataparser_i18n_func)})
        p.parse_string("""
         question {
           var = "var-C"
           var[nb] = "var-nb"
         }
        """)
        self.assertEquals(p.questions[0]['var'], u'var-nb')
        self.assert_(isinstance(p.questions[0]['var'], istr))
        self.assertEquals(p.questions[0]['var'].cval, u'var-C')
    def test_istr_translations_in_file2(self):
        p = Dataparser({}, {'_': (False, dataparser_i18n_func)})
        p.parse_string("""
         question {
           foo[no] = "foo-no"
         }
        """)
        self.assertEquals(p.questions[0]['foo'], u'foo-no')
        self.assertEquals(p.questions[0]['foo'].cval, u'foo-no')
    def test_istr_translations_in_file3(self):
        p = Dataparser({}, {'_': (False, dataparser_i18n_func)})
        p.parse_string("""
         question {
           foo[no] = "foo-no"
           foo = "foo-C"
         }
        """)
        self.assertEquals(p.questions[0]['foo'], u'foo-no')
        self.assertEquals(p.questions[0]['foo'].cval, u'foo-C')
    def test_i18n_list_fails(self):
        p = Dataparser({}, {'_': (False, dataparser_i18n_func)})
        def f():
            p.parse_string("""
             question {
               foo[no] = "foo-no", "blabla"
             }
            """)
        self.assertRaises(CannotTranslateListsException, f)
    def test_unsupported_named_block(self):
        p = Dataparser({}, {'_': (False, dataparser_i18n_func)})
        def f():
            p.parse_string("""
nonnamed header { 
    name  = "File with random chars"
}
            """)
        self.assertRaises(DataparserSyntaxError, f)

class TestIstr(I18nSetup):
    def test_musicstr(self):
        s = istr(r"\staff{ c e g }")
        self.assert_(isinstance(s, basestring))
    def test_add_translations1(self):
        #i18n.langs: nb_NO, nb, C
        # name = "Yes"
        # name[no] = "Ja"
        s = "Yes"
        s = istr(s)
        self.assertEquals(unicode(s), u'Yes')
        s = s.add_translation('nb', 'Ja')
        self.assertEquals(s, u'Ja')
        s = s.add_translation('nb_NO', 'Ja!')
        self.assertEquals(s, u'Ja!')
    def test_add_translations2(self):
        #i18n.langs: nb_NO, nb, C
        # name = "Yes"
        # name[no] = "Ja"
        s = "Yes"
        s = istr(s)
        self.assertEquals(s, u'Yes')
        s = s.add_translation('nb_NO', 'Ja!')
        self.assertEquals(s, u'Ja!')
        s = s.add_translation('nb', 'Ja')
        self.assertEquals(s, u'Ja!', "Should still be 'Ja!' because no_NO is preferred before no")
    def test_override_gettext(self):
        s = dataparser_i18n_func("major")
        self.assertEquals(s, "dur")
        self.assertEquals(s.cval, "major")
        s = s.add_translation('nb', "Dur")
        self.assertEquals(s, u"Dur")
    def test_type(self):
        s = istr("jo")
        self.assert_(type(s) == istr)
        self.assertRaises(TypeError, lambda s: type(s) == str)
        self.assert_(isinstance(s, istr))
        self.assert_(not isinstance(s, str))
        self.assert_(isinstance(s, unicode))


suite = unittest.makeSuite(TestLexer)
suite.addTest(unittest.makeSuite(TestDataParser))
suite.addTest(unittest.makeSuite(TestIstr))
