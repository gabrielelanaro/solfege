# vim: set fileencoding=utf-8:
# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008  Tom Cato Amundsen
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


from __future__ import absolute_import
from __future__ import with_statement

import codecs
import glob
import logging
import os
import pprint
import sys

from solfege import filesystem
from solfege import lessonfile
from solfege.gpath import Path

import solfege

def mk_rel(filename, save_location):
    assert os.path.isabs(filename) or filename.startswith(lessonfile.solfege_uri), filename
    if filename.startswith(save_location):
        return filename[len(save_location):]
    return filename

def mk_abs(filename, save_location):
    if not lessonfile.is_uri(filename) and not os.path.isabs(filename):
        return os.path.join(save_location, filename)
    return filename

def escape(s):
    return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')

def get_front_pages_list(debug):
    files = []
    def is_frontpage(fn):
            # no subdirs
            if not os.path.isfile(fn):
                return False
            # filter out bzr revert backups
            if fn.endswith("~"):
                return False
            if os.path.split(fn)[1] == u"Makefile":
                return False
            return True
    def add_subdir(subdir):
        if os.path.isdir(subdir):
            v = [os.path.join(subdir, fn) for fn in os.listdir(subdir)]
            return [x for x in v if is_frontpage(x)]
        return []
    files = [fn for fn in glob.glob(os.path.join(u"exercises", "*", "*"))
             if is_frontpage(fn)]
    # The next line is for pre 3.15 compat. We used to place learning
    # trees there.
    files.extend(add_subdir(os.path.join(filesystem.app_data(), u"learningtrees")))
    # This is the recommended place to save front page files
    files.extend([
        fn for fn in glob.glob(os.path.join(filesystem.user_data(), u"exercises", "*", "*"))
        if is_frontpage(fn)])
    if not debug:
        try:
            files.remove(os.path.join(lessonfile.exercises_dir, 'debugtree.txt'))
        except ValueError:
            # The debugtree.txtfile is for some reason missing
            pass
    return files


class _TreeCommon(list):
    def __init__(self, items=[]):
        if isinstance(items, _TreeCommon):
            list.__init__(self, [items])
        else:
            list.__init__(self, items)
    def dump(self, stream, level=0):
        print >> stream, "%s%s([" % (" " * level, self.__class__.__name__)
        self.dump_children(stream, level)
        print >> stream, "%s ])," % (" " * level)
    def dump_children(self, stream, level):
        for child in self:
            if isinstance(child, _TreeCommon):
                child.dump(stream, level + 1)
            else:
                print >> stream, "%su'%s'," % (" " * (level + 1), escape(child))
    def iterate_filenames(self):
        """
        Yield the filenames of each lesson that has been added to this
        object or its children.
        """
        for child in self:
            if isinstance(child, _TreeCommon):
                for c in child.iterate_filenames():
                    yield c
            if isinstance(child, (str, unicode)):
                yield child
    def get_use_dict(self):
        """
        Return a dict where the keys are the filename of lessons used
        in this objects and its children. The values are an integer
        value telling how many times it have been used.
        """
        retval = {}
        for filename in self.iterate_filenames():
            retval[filename] = retval.get(filename, 0) + 1
        return retval
    def iterate_topics_for_file(self, filename):
        for child in self:
            if isinstance(child, (Page, Column, LinkList)):
                for c in child.iterate_topics_for_file(filename):
                    yield c
            elif child == filename:
                yield self.m_name
    def iterate_flattened(self):
        for child in self:
            yield child
            if not isinstance(child, unicode):
                for subchild in child.iterate_flattened():
                    yield subchild
    @staticmethod
    def tests_in_sub(sub):
        if isinstance(sub, unicode):
            try:
                return bool(solfege.lessonfile.infocache.get(sub, 'test'))
            except solfege.lessonfile.infocache.FileNotFound:
                return False
        for child in sub:
            if _TreeCommon.tests_in_sub(child):
                return True
        return False
    def foreach_file(self, callback, data=None):
        try:
            for idx, child in enumerate(self):
                if getattr(self[idx], 'foreach_file', None):
                    self[idx].foreach_file(callback, data)
                else:
                    if data:
                        self[idx] = callback(self[idx], data)
                    else:
                        self[idx] = callback(self[idx])
        except TypeError:
            pass
    def get_topic_of_lesson_file(self, filename):
        """
        Return the title of the first topic where filename is linked.
        Return None if not found.
        """
        for x in self.iterate_topics_for_file(filename):
            return x

class _NamedTreeCommon(_TreeCommon):
    def __init__(self, name=u'', listitems=[]):
        assert isinstance(name, unicode)
        _TreeCommon.__init__(self, listitems)
        self.m_name = name
    def dump(self, stream, level=0):
        print >> stream, "%s%s(_(u'%s'), [" % (" " * level, self.__class__.__name__, escape(self.m_name))
        self.dump_children(stream, level)
        print >> stream, "%s ])," % (" " * level)

class LinkList(_NamedTreeCommon):
    """
    A list of links leading to exercises or new pages.
    """
    def append(self, item):
        assert isinstance(item, (str, unicode, Page))
        super(LinkList, self).append(item)
    def __str__(self):
        return "LinkList(_('%s')# len: %i)" % (self.m_name, len(self))

class Column(_TreeCommon):
    def add_linklist(self, heading):
        self.append(LinkList(heading))
        return self[-1]
    def __str__(self):
        return "Column(#len: %i)" % len(self)

class Page(_NamedTreeCommon):
    def __init__(self, name=u'', listitems=[]):
        assert isinstance(name, unicode)
        _NamedTreeCommon.__init__(self, name, listitems)
        self.m_modified = False
    def __repr__(self):
        return "<Page name=%s>" % self.m_name
    def get(self, path):
        """
        Return the element pointed to by path.
        """
        elem = self
        for idx in path[1:]:
            elem = elem[idx]
        return elem
    def is_empty(self):
        """
        Return True if all columns are empty or only contain empty sections.
        """
        for col in self:
            for sect in col:
                if isinstance(sect, LinkList) and len(sect) != 0:
                    return False
        return True

class Paragraph(object):
    def __init__(self, text):
        self.m_text = text

class FileHeader(_TreeCommon):
    def __init__(self, version, page):
        _TreeCommon.__init__(self, [page])
        self.m_version = version
    def dump(self, stream, level=0):
        print >> stream, "%s%s(%s, " % (" " * level, self.__class__.__name__, self.m_version)
        self.dump_children(stream, level)
        print >> stream, "%s )" % (" " * level)
    def save_file(self, filename):
        """
        Rules:
        * file is solfege: URI: do nothing
          if old_location != save_location:
            if old_location:
                make filename absolute
            make relto new location if possible
        """
        save_location = os.path.split(filename)[0] + os.sep
        self.foreach_file(mk_rel, save_location)
        assert filename
        f = codecs.open(filename, 'w', 'utf-8')
        self.dump(f)
        f.close()
        self.foreach_file(mk_abs, save_location)

def convert_old_learningtree_data(data):
    """
    fn is the filename of a learningtree file. It reads the file as
    the default format was for solfege 3.14.
    Returns the Page objects
    """
    p = Page(_('Untitled%s' % ''), [Column()])
    col = p[-1]
    if isinstance(data, list):
        if data[0] == 2: # Version 2
            menudata = data[1]
        elif (len(data) == 3 and isinstance(data[0], list)
              and isinstance(data[1], dict)): # solfege 3.2.2
            for section in data[0]:
                linklist = col.add_linklist(unicode(section['name']))
                for child in section['lessons']:
                    linklist.append(child)
            return p
    else:
        menudata = data['menu']
    for d in menudata:
        linklist = col.add_linklist(unicode(d['name']))
        for section in d['children']:
            assert isinstance(section, dict)
            # We create a new page with 1 col for each set of links
            subpage = Page(unicode(section['name']))
            subpage.append(Column())
            subcol = subpage[-1]
            sublinklist = subcol.add_linklist(unicode(section['name']))
            for child in section['children']:
                sublinklist.append(unicode(child))
            linklist.append(subpage)
    return p

def may_be_frontpage(filename):
    """
    Return True if we think this is a front page file.
    This is not a 100% test, but it should be safe enough to avoid
    locking the program at startup if someone places a very large file
    in the directory where front page files is supposed to be.
    """
    with codecs.open(filename, "rU", 'utf-8', 'replace') as f:
        s = f.readline().strip()
        while s:
            if s.startswith("#"):
                s = f.readline().strip()
                continue
            # '{' is 3.14
            # 'Page' is bzr branch 3.15.x
            # 'FileHeader is 3.15.3 (or was it .2?)
            if s.startswith(('{', 'Page', 'FileHeader')):
                return True
            logging.debug("my_be_frontpage(%s) => False" % filename)
            return False
        return False


def parse_tree(s, C_locale=False):
    """
    This function can load both new (3.15.2) and older learning trees.
    This function will convert old format to new format, and always return
    new format files.
    """
    if C_locale:
        def ifu(s):
            # We do the isinstance check because this way we can handle
            # people manually editing the data file and adding strings that
            # are plain ascii, but not marked as unicode ( u'' )
            return s if isinstance(s, unicode) else unicode(s)
        ifunc = ifu
    else:
        # The headings and links to exercises or pages should not have
        # accels (defined in gtk+ by underlines "_") or ellipsis "…" that
        # are used in menu items and command button labels. So we remove
        # them, if found, in the string. This way we can reuse strings
        # with accels that are translated, saving translator work.
        def _s(s):
            return _(s).replace("_", "").replace(u"…", "")
        ifunc = _s
    namespace = {
        'FileHeader': FileHeader,
        'Page': Page,
        'Column': Column,
        'LinkList': LinkList,
        'Paragraph': Paragraph,
        '_': ifunc,
        '__builtins__': {},
    }
    ret = eval(s, namespace, namespace)
    if isinstance(ret, dict):
        name = ret['title']
        ret = convert_old_learningtree_data(ret)
        ret.m_name = name
    if isinstance(ret, FileHeader):
        return ret[0]
    else:
        if not isinstance(ret, Page):
            ret = convert_old_learningtree_data(ret)
        # Convert from solfege 3.15.2 to 3.15.3 file format
        # New front page files should store the filename, not the uuid
        lessonfile.require_mgr()
        def cnv_2_3(lesson_id):
            try:
                return lessonfile.mk_uri(lessonfile.mgr.get(lesson_id, 'filename'))
            except lessonfile.mgr.UnknownLessonID, e:
                return unicode(e)
        ret.foreach_file(cnv_2_3)
        return ret

def load_tree(fn, C_locale=False):
    ret = parse_tree(codecs.open(fn, "rU", 'utf-8', 'replace').read(), C_locale)
    # We store all files by absolute filename or solfege: uri internally
    ret.foreach_file(mk_abs, os.path.split(fn)[0] + os.sep)
    return ret

