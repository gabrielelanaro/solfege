# -*- coding: iso-8859-1 -*-
# GNU Solfege - free ear training software
# Copyright (C) 2001, 2002, 2003, 2004, 2007, 2008  Tom Cato Amundsen
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

# 4.69
from __future__ import absolute_import
"""
prog             The test done before calling
 +statementlist
  +statement
   +assignment   peek: 'NAME', '='
    +faktorlist  scan('NAME') scan('=')
     +faktor
      +atom()  kalles direkt på første linje. Så evt på nytt etter +-/%
       +functioncall    peek: 'NAME' '('
        +faktorlist     peek() != ')'
   +block        peek: 'NAME', '{'
    +assignmentlist
    +faktor     peek_type()!= '}'
   +include      peek: 'NAME'("include"), '(
    +prog

assignmentlist peek: 'NAME' '='
+assignment

"""
# på singchord-1 sparer jeg ca 0.03 på å ha _peek_type
# På singchord-1 sparer jeg ikke noe på å ha en peek2_type(t1, t2)
# som tester de to neste token.

import os
import re
import sys
import weakref

from solfege import i18n

tokens = ('NAME', 'STRING', 'OPERATOR', 'INTEGER', 'FLOAT', 'CHAR', 'EOF')
for t in tokens:
    globals()[t] = t
del t

NEW_re = re.compile("""(?:
                        (\s+)|  #space
                        (\#.*?$)| #comment
                        (-?\d+\.\d+) | #float
                        (-?\d+)| #integer
                        (\"\"\"(.*?)\"\"\")| #multiline string
                        ("(.*?)")| #string
                        (\w[\[\]\w-]*) #name
                )""",
                      re.VERBOSE|re.MULTILINE|re.DOTALL|re.UNICODE)

LI_INTEGER = NEW_re.match("-3").lastindex
LI_FLOAT = NEW_re.match("3.3").lastindex
LI_MSTRING = NEW_re.match('"""string"""').lastindex
LI_STRING = NEW_re.match('"string"').lastindex
LI_NAME = NEW_re.match("name").lastindex
LI_COMMENT = NEW_re.match("# comment").lastindex

lastindex_to_ID = {LI_INTEGER: INTEGER,
                     LI_FLOAT: FLOAT,
                    LI_STRING: STRING,
                     LI_MSTRING: STRING,
                     LI_NAME: NAME,
                    }

lastindex_to_group = {LI_INTEGER: 4,
                     LI_STRING: 8,
                     LI_MSTRING: 6,
                     LI_NAME: 9,
                     LI_FLOAT: 3,
                    }

# Used to find elements in the token tuple
TOKEN_TYPE = 0
TOKEN_STRING = 1
TOKEN_IDX = 2
TOKEN_LINENO = 3

class istr(unicode):
    def __init__(self, s):
        self.cval = s
        self.m_added_language = None
    def add_translation(self, lang, s):
        """
        Use this method to add translations that are included directly in
        the lesson file like this:

          name = "major"
          name[no] = "dur"
        """
        if lang in i18n.langs():
            # i18n.langs() has a list of the langauges we can use.
            # The first language in the list is preferred.
            new_pos = i18n.langs().index(lang)
            if not self.m_added_language:
                old_pos = sys.maxint
            else:
                old_pos = i18n.langs().index(self.m_added_language)
            if new_pos < old_pos:
                retval = istr(s)
                retval.m_added_language = lang
                retval.cval = self.cval
                return retval
        return self
    def new_translated(cval, translated):
        retval = istr(translated)
        retval.cval = cval
        return retval
    new_translated = staticmethod(new_translated)

def dataparser_i18n_func(s):
    retval = istr(_(s))
    retval.cval = s
    return retval

def dataparser_i18n__i_func(s):
    retval = istr(_i(s))
    retval.cval = s
    return retval


class Question(dict):
    def __getattr__(self, n):
        if n in self:
            return self[n]
        raise AttributeError()
    def __setattr__(self, name, value):
        self[name] = value


class DataparserException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class NameLookupException(DataparserException):
    def __init__(self, parser, bad_pos):
        DataparserException.__init__(self,
            _("Unknown name \"%(name)s\" in line %(line)i of file \"%(filename)s\":") % {
                'name': parser._lexer.m_tokens[bad_pos][TOKEN_STRING],
                'line': parser._lexer.m_tokens[bad_pos][TOKEN_LINENO],
                'filename': parser.m_filename})
        # This variable is only used by the module test code.
        self.m_token = parser._lexer.m_tokens[bad_pos]
        self.m_nonwrapped_text = parser._lexer.get_err_context(bad_pos)

class WrongArgumentCount(DataparserException):
    def __init__(self, parser, bad_pos):
        DataparserException.__init__(self,
            _("Wrong argument count in line %(line)i of file \"%(filename)s\":") % {
                'line': parser._lexer.m_tokens[bad_pos][TOKEN_LINENO],
                'filename': parser.m_filename})
        # This variable is only used by the module test code.
        self.m_token = parser._lexer.m_tokens[bad_pos]
        self.m_nonwrapped_text = parser._lexer.get_err_context(bad_pos)


class DataparserSyntaxError(DataparserException):
    def __init__(self, parser, bad_pos, expect):
        DataparserException.__init__(self, _('Syntax error in file "%(filename)s". %(expected)s') % {'filename': parser.m_filename, 'expected': expect})
        # This variable is only used by the module test code.
        self.m_token = parser._lexer.m_tokens[bad_pos]
        self.m_nonwrapped_text = parser._lexer.get_err_context(bad_pos)

class AssignmentToReservedWordException(DataparserException):
    def __init__(self, parser, bad_pos, word):
        DataparserException.__init__(self, _("Assignment to the reserved word \"%(word)s\"") % {'word': word})
        # This variable is only used by the module test code.
        self.m_token = parser._lexer.m_tokens[bad_pos]
        self.m_nonwrapped_text = parser._lexer.get_err_context(bad_pos)

class CannotTranslateListsException(DataparserException):
    def __init__(self, parser, bad_pos, variable):
        DataparserException.__init__(self, _("Cannot translate lists using in-file translations (ex var[no]=...). See the variable \"%(variable)s\" in the file \"%(filename)s\"") % {'filename': parser.m_filename, 'variable': variable})
        # This variable is only used by the module test code.
        self.m_token = parser._lexer.m_tokens[bad_pos]
        self.m_nonwrapped_text = parser._lexer.get_err_context(bad_pos)


class UnableToTokenizeException(DataparserException):
    def __init__(self, lexer, lineno, token, pos):
        """
        lineno is the zero indexed line number where the exception happened.
        token is the char that we cannot tokenize
        pos is the position in the string we are tokenizing.
        """
        # This line will add a fake token tuple, so that get_err_context
        # can produce useful output.
        lexer.m_tokens.append(('FIXME', token, pos, lineno))
        # This variable is only used by the module test code.
        self.m_token = lexer.m_tokens[-1]
        DataparserException.__init__(self,
            _('Unable to tokenize line %(lineno)i of the file "%(filename)s"') % {
                'lineno': lineno + 1,
                'filename': lexer.m_parser().m_filename})
        self.m_nonwrapped_text = lexer.get_tokenize_err_context()


class Lexer:
    def __init__(self, src, parser):
        if parser:
            self.m_parser = weakref.ref(parser)
        else:
            self.m_parser = parser
        r = re.compile("#.*?coding\s*[:=]\s*([\w_.-]+)")
        # according to http://www.python.org/dev/peps/pep-0263/
        # the encoding marker must be in the first two lines
        m = r.match("\n".join(src.split("\n")[0:2]))
        if m:
            src = unicode(src, m.groups()[0], errors="replace")
        else:
            src = unicode(src, "UTF-8", errors="replace")
        src = src.replace("\r", "\n")
        self.m_src = src
        self.pos = 0
        pos = 0
        lineno = 0
        self.m_tokens = []
        while 1:
            try:
                if src[pos] in " \n\t{}=%+,/()":
                    if src[pos] in ' \t':
                        pos += 1
                        continue
                    if src[pos] == '\n':
                        pos += 1
                        lineno += 1
                        continue
                    self.m_tokens.append(('%s' % src[pos], src[pos], pos, lineno))
                    pos += 1
                    continue
            except IndexError:
                break
            m = NEW_re.match(src, pos)
            if not m:
                raise UnableToTokenizeException(self, lineno, src[pos], pos)
            if m.lastindex == LI_COMMENT:
                pass
            else:
                self.m_tokens.append((lastindex_to_ID[m.lastindex],
                         m.group(lastindex_to_group[m.lastindex]), pos, lineno))
            pos = m.end()
        self.m_tokens.append(("EOF", None, pos, lineno))
        self.m_tokens.append(("EOF", None, pos, lineno))
        self.m_tokens.append(("EOF", None, pos, lineno))
        self.m_tokens.append(("EOF", None, pos, lineno))
    def _err_context_worker(self, lexer_pos):
        ret = ""
        lineno = self.m_tokens[lexer_pos][TOKEN_LINENO]
        x = self.m_tokens[lexer_pos][TOKEN_IDX]
        while x > 0 and self.m_src[x-1] != "\n":
            x -= 1
        linestart_idx = x
        erridx_in_line = self.m_tokens[lexer_pos][TOKEN_IDX] - linestart_idx
        if lineno > 1:
            ret += "\n(line %i): %s" % (lineno-1, self.get_line(lineno-2))
        if lineno > 0:
            ret += "\n(line %i): %s" % (lineno, self.get_line(lineno-1))
        ret += "\n(line %i): %s" % (lineno + 1, self.get_line(lineno))
        ret += "\n" + " " * (erridx_in_line + len("(line %i): " % (lineno+1))) + "^"
        return ret.strip()
    def get_tokenize_err_context(self):
        """
        return a string with the last part of the file that we were able
        to tokenize. Used by UnableToTokenizeException
        """
        return self._err_context_worker(len(self.m_tokens)-1)
    def get_err_context(self, pos):
        return self._err_context_worker(pos)
    def peek(self, forward=0):
        return self.m_tokens[self.pos+forward]
    def peek_type(self, forward=0):
        return self.m_tokens[self.pos+forward][TOKEN_TYPE]
    def peek_string(self, forward=0):
        return self.m_tokens[self.pos+forward][TOKEN_STRING]
    def scan_any(self):
        """scan the next token"""
        self.pos += 1
        return self.m_tokens[self.pos-1][TOKEN_STRING]
    def scan(self, t=None):
        """t is the type of token we expect"""
        if self.m_tokens[self.pos][TOKEN_TYPE] == t:
            self.pos += 1
            return self.m_tokens[self.pos-1][TOKEN_STRING]
        else:
            # Tested in TestLexer.test_scan
            raise DataparserSyntaxError(self.m_parser(), self.pos,
                _("Token \"%(nottoken)s\" not found, found \"%(foundtoken)s\" of type %(type)s.") % {
                    'nottoken': t,
                    'foundtoken': self.m_tokens[self.pos][TOKEN_STRING],
                    'type': self.m_tokens[self.pos][TOKEN_TYPE]})
    def get_line(self, lineno):
        """line 0 is the first line
        Return an empty string if lineno is out of range.
        """
        idx = 0
        c = 0
        while c < lineno and idx < len(self.m_src):
            if self.m_src[idx] == '\n':
                c += 1
            idx += 1
        x = idx
        while x < len(self.m_src) and self.m_src[x] != '\n':
            x += 1
        return self.m_src[idx:x]


class Dataparser:
    def __init__(self, globals={}, function_dict={}, gd=[]):
        self.gd = gd
        self.globals = globals.copy()
        self.functions = function_dict.copy()
        self.header = {}
        self.questions = []
        # Each block type will have a list in blocklists,
        # for example self.blocklists['element'] = []
        self.blocklists = {}
        self.context = self.globals
        self.m_filename = None
        self.m_ignore_lookup_error = False
        self.m_translation_re = re.compile("(?P<varname>\w+)\[(?P<lang>[\w_+]+)\]")
    def parse_file(self, filename):
        """We always construct a new parser if we want to parse another
        file. So this method is never called twice for one parser.
        """
        self.m_filename = filename
        # Lexer will decode the string read
        infile = open(filename, 'rU')
        self._lexer = Lexer(infile.read(), self)
        infile.close()
        self.reserved_words = ('_', 'question', 'header')
        self.prog()
    def parse_string(self, s, really_filename=False):
        if really_filename:
            self.m_filename = really_filename
        else:
            self.m_filename = "<STRING>"
        self._lexer = Lexer(s, self)
        self.reserved_words = ('_', 'question', 'header')
        self.prog()
    def prog(self):
        """prog: statementlist EOF"""
        self.statementlist()
        if self._lexer.peek_type() != 'EOF':
            # This exception will be raised if we for example have
            # an extra { after a block definition.
            raise DataparserSyntaxError(self, self._lexer.pos,
                    'Expected end of file or statement.')
        self._lexer.scan('EOF')
    def statementlist(self):
        """statementlist: (statement+)"""
        while self._lexer.peek_type() == 'NAME':
            self.statement()
    def statement(self):
        """statement: assignment | block | include"""
        if self._lexer.peek_type(1) == '=':
            self.assignment()
        elif self._lexer.peek_type(1) == '{':
            self.block()
        elif self._lexer.peek_type(1) == 'NAME' \
                and self._lexer.peek_type(2) == '{':
            self.named_block()
        elif self._lexer.peek_type() == 'NAME' \
                and self._lexer.peek_string() == 'include' \
                and self._lexer.peek_type(1) == '(':
            self.include()
        else:
            if self._lexer.peek_type(1) == 'EOF':
                extra = " Found End of File."
            else:
                extra = ""
            # Add a single A to the end of a valid file to raise
            # this exception.
            raise DataparserSyntaxError(self, self._lexer.pos + 1,
              "Expected token '=' or '{'. %s" % extra)
    def include(self):
        self._lexer.scan_any() # scan include
        self._lexer.scan_any() # scan (
        try:
            filename = self._lexer.scan('STRING')
        except:
            print >> sys.stderr, "Warning: The file '%s' uses old style syntax for the include command." % self.m_filename
            print >> sys.stderr, 'This is not fatal now but will be in the future. You should change the code\nfrom include(filename) to include("filename")\n'
            filename = self._lexer.scan('NAME')
        old_lexer = self._lexer
        # don't let the new file pollute my header!
        old_header = self.header
        self.header = {}
        # Lexer will decode the string read
        ifile = open(os.path.join(self.m_location, filename), 'rU')
        self._lexer = Lexer(ifile.read(), self)
        ifile.close()
        self.prog()
        self._lexer = old_lexer
        for k, v in old_header.items():
            self.header[k] = v
        self._lexer.scan(')')
    def assignmentlist(self):
        """assignmentlist: (assignment+) """
        # FIXME peek(1) is added because of the music shortcut
        while self._lexer.peek_type() == 'NAME' and self._lexer.peek_type(1) == '=':
            self.assignment()
    def assignment(self):
        """NAME "=" faktor ("," faktor)* """
        npos = self._lexer.pos
        name = self._lexer.scan_any()#('NAME')
        if name in self.reserved_words:
            # do "question = 1" to raise this exception.
            raise AssignmentToReservedWordException(self, npos, name)
        self._lexer.scan_any()#('=')
        faktorlist = self.faktorlist()
        m = self.m_translation_re.match(name)
        if m:
            if len(faktorlist) != 1:
                raise CannotTranslateListsException(self, npos, name)
            faktor = faktorlist[0]
            assert type(faktor) == istr
            if m.group('varname') in self.context:
                self.context[m.group('varname')] = self.context[m.group('varname')].add_translation(m.group('lang'), faktor)
            else:
                # add the first translation as cval until we get the correct
                # value to use.
                self.context[m.group('varname')] = faktor
                # Also add faktor as a translation, since it might be the
                # translation we need.
                self.context[m.group('varname')] = self.context[m.group('varname')].add_translation(m.group('lang'), faktor)
        else:
            # We only check for cval if len(faktorlist) == 1, because
            # lists are not localized.
            if len(faktorlist) == 1:
                if name in self.context and isinstance(self.context[name], istr):
                    self.context[name].cval = faktorlist[0]
                else:
                    self.context[name] = faktorlist[0]
            else:
                self.context[name] = faktorlist
    def faktor(self):
        """faktor: atom
              ("+" atom
              |"-" atom
              |"/" atom
              )*
              """
        faktor = self.atom()
        peek = self._lexer.peek_type()
        while 1:
            if peek == '+':
                self._lexer.scan_any()
                faktor += self.atom()
            elif peek == '-':
                self._lexer.scan_any()
                faktor -= self.atom()
            elif peek == '/':
                self._lexer.scan_any()
                faktor = (faktor, self.atom())
            elif peek == '%':
                self._lexer.scan_any()
                faktor = faktor % self.atom()
            else:
                break
            peek = self._lexer.peek_type()
        return faktor
    def faktorlist(self):
        """faktorlist: faktor ("," faktor)* """
        faktorlist = [self.faktor()]
        while self._lexer.peek_type() == ',':
            self._lexer.scan_any()
            faktorlist.append(self.faktor())
        return faktorlist
    def atom(self):
        """atom: INTEGER | FLOAT | STRING | NAME | FUNCTIONCALL"""
        npos = self._lexer.pos
        peek = self._lexer.peek_type()
        if peek == 'STRING':
            return istr(self._lexer.scan('STRING'))
        elif peek == 'INTEGER':
            return int(self._lexer.scan('INTEGER'))
        elif peek == 'FLOAT':
            return float(self._lexer.scan('FLOAT'))
        elif peek == 'NAME':
            if self._lexer.peek_type(1) == '(':
                return self.functioncall()
            try:
                return self.lookup_name(self._lexer.scan('NAME'))
            except KeyError:
                # Tested in TestDataParser.test_exception_atom
                raise NameLookupException(self, npos)
        else:
            #print "FIXME: have no idea how to raise this exception"
            raise DataparserSyntaxError(self, npos + 1,
                "Expected STRING, INTEGER or NAME+'('")
    def functioncall(self):
        """functioncall: NAME "(" faktorlist ")" """
        npos = self._lexer.pos
        name = self._lexer.scan_any()#'NAME')
        self._lexer.scan('(')
        if self._lexer.peek_type() == ')':
            # functioncall()
            self._lexer.scan(')')
            try:
                if self.functions[name][0]:
                    return self.functions[name][1](self)
                else:
                    return self.functions[name][1]()
            except KeyError:
                raise NameLookupException(self, npos)
        else:
            # functioncall(arglist)
            arglist = self.faktorlist()
            self._lexer.scan(')')
            try:
                if self.functions[name][0]:
                    return self.functions[name][1](self, *arglist)
                else:
                    return self.functions[name][1](*arglist)
            except KeyError:
                raise NameLookupException(self, npos)
            except TypeError:
                raise WrongArgumentCount(self, npos)
    def block(self):
        """block: NAME "{" assignmentlist "}" """
        name = self._lexer.scan_any()
        if name == 'header':
            self.context = self.header
        elif name == 'question':
            self.questions.append(Question())
            self.context = self.questions[-1]
        else:
            if name not in self.blocklists:
                self.blocklists[name] = []
            self.blocklists[name].append(dict())
            self.context = self.blocklists[name][-1]
        self._lexer.scan_any() # scan '{'
        # The question block is a little more code because of the shortcut
        # we allow: question { "music string }
        if name == 'question':
            self.assignmentlist()
            if self._lexer.peek_type() != '}':
                self.context['music'] = self.faktor()
        # The single line two below is the code needed if we dont' have
        # shortcuts. Currently the headerblock goes here.
        else:
            self.assignmentlist()
        self._lexer.scan("}")
        if name == 'question': #FIXME this is code I want to remove.
            for n in self.gd:
                if not (n in self.context):
                    self.context[n] = self.globals[n]
        self.context = self.globals
    def named_block(self):
        blocktype = self._lexer.scan('NAME')
        name = self._lexer.scan('NAME')
        #FIXME right now named_block is reserved to element blocks, but
        # I hope to move other blocks here too. Or at least questions should
        # use self.blocklists, I think.
        if blocktype != 'element':
            raise DataparserSyntaxError(self, self._lexer.pos - 2, 'The only named block allowed are "element"')
        if blocktype not in self.blocklists:
            self.blocklists[blocktype] = []
        elem = dict()
        # We must add the name of the block to the global name space since
        # it will be referred from other blocks.
        self.globals[name] = elem
        # And they have to be added to the list of blocks because we may
        # need to access all blocks of a certain type.
        self.blocklists[blocktype].append(elem)
        elem['name'] = name
        self._lexer.scan('{')
        self.context = elem
        self.assignmentlist()
        self._lexer.scan("}")
        self.context = self.globals
    def lookup_name(self, name):
        """
        Raises KeyError if the name is not found.
        """
        if name in self.context:
            return self.context[name]
        elif name in self.globals:
            return self.globals[name]
        else:
            if self.m_ignore_lookup_error:
                return "LOOKUP IGNORED"
            raise KeyError

