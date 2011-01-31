# GNU Solfege - free ear training software
# Copyright (C) 2005, 2007, 2008 Tom Cato Amundsen
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

import random
import string
import sys
import urllib2

import gtk

from solfege import buildinfo
from solfege import cfg
from solfege import gu
from solfege import pmwiki
from solfege import runtime
from solfege import utils

RESPONSE_SEND = 1011
RESPONSE_SEE = 1010

class ShowTextDialog(gtk.Dialog):
    def __init__(self, parent, text):
        gtk.Dialog.__init__(self, _("Bug report"), parent,
            buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        self.add_button(_("_Send"), RESPONSE_SEND)
        self.set_default_size(600, 500)
        sc = gtk.ScrolledWindow()
        self.vbox.pack_start(sc)
        sc.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.g_tw = gtk.TextView()
        self.g_tw.set_wrap_mode(gtk.WRAP_WORD)
        self.g_tw.set_editable(False)
        buf = self.g_tw.get_buffer()
        buf.insert(buf.get_end_iter(), text)
        sc.add(self.g_tw)
        self.show_all()

class ReportBugWindow(gtk.Dialog):
    def __init__(self, parent, error_text):
        gtk.Dialog.__init__(self, _("Make bug report"), parent,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        self.m_error_text = error_text
        self.add_button(_("See complete _report"), RESPONSE_SEE)
        self.add_button(_("_Send"), RESPONSE_SEND)
        self.set_default_size(400, 400)
        sizegroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.g_email = gtk.Entry()
        self.vbox.pack_start(
            gu.hig_label_widget(_("_Email:"), self.g_email, sizegroup),
            False)
        self.g_mangled_email = gtk.Label()
        self.vbox.pack_start(
            gu.hig_label_widget(_("Mangled email address:"), self.g_mangled_email,
                sizegroup), False)
        self.g_email.set_text(cfg.get_string('user/email'))
        self.g_email.connect('changed', self.on_update_mangle)
        self.g_description = gtk.Entry()
        self.vbox.pack_start(
            gu.hig_label_widget(_("S_hort description:"), self.g_description,
                     sizegroup), False)
        label = gtk.Label(_("_Describe how to produce the error message:"))
        label.set_use_underline(True)
        label.set_alignment(0.0, 0.5)
        self.vbox.pack_start(label, False)
        self.g_tw = gtk.TextView()
        self.g_tw.set_wrap_mode(gtk.WRAP_WORD)
        self.g_tw.set_border_width(10)
        # translators, please notice that the word NO_DESCRIPTION must not be
        # translated in this string.
        self.g_tw.get_buffer().insert_at_cursor(_("""Describe as exactly as you can what you did when this error occurred. If you give no description at all, you make it very difficult to track down this bug. You should replace this text with your description, and also remove the "bug-tag" in the bottom of this text so that this bug is not automatically sorted among the bug reports with no description.\n\n(bug-tag: NO_DESCRIPTION)"""))
        label.set_mnemonic_widget(self.g_tw)
        self.vbox.pack_start(self.g_tw)
        self.show_all()
    def on_update_mangle(self,  *v):
        cfg.set_string('user/email', self.g_email.get_text())
        self.g_mangled_email.set_text(utils.mangle_email(self.g_email.get_text()))
    def send_bugreport(self):
        """
        Return None if successful. Return the urllib2 execption if failure.
        """
        pagename = self.g_description.get_text()
        pagename = "".join([s.capitalize() for s in pagename.split()])
        if not pagename:
            pagename = "NoDescription"
        pagename = "SITS-Incoming.%s" % pagename
        wiki = pmwiki.PmWiki("http://www.solfege.org")
        add_str=""
        try:
            while 1:
                if wiki.page_exists(pagename+add_str):
                    if not add_str:
                        add_str = "-"
                    add_str += random.choice(string.ascii_letters)
                    continue
                else:
                    wiki.write_page(pagename+add_str, self.get_bugreport(), "Solfege")
                break
        except urllib2.URLError, e:
            return e
    def get_bugreport(self):
        email = utils.mangle_email(self.g_email.get_text())
        buf = self.g_tw.get_buffer()
        description = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        try:
            windowsversion = str(sys.getwindowsversion())
        except AttributeError:
            windowsversion = "(not running ms windows)"
        return "\n".join([
            "!%s" % self.g_description.get_text(),
            "Submitter: %s\\\\" % email,
            "Long desciption: %s\n" % description,
            "||border=1",
            "|| Solfege version||%s ||" % buildinfo.VERSION_STRING,
            "|| Bzr revision info ||%s ||" % buildinfo.get_bzr_revision_info_pmwiki(),
            "|| gtk.pygtk_version||%s ||" % str(gtk.pygtk_version),
            "|| gtk||%s ||" % gtk,
            "|| sys.version_info||%s||" % str(sys.version_info),
            "|| sys.version||%s||" % sys.version.replace("\n", ""),
            "|| sys.prefix||%s||" % sys.prefix,
            "|| sys.platform||%s||" % sys.platform,
            "|| windowsversion||%s||" % windowsversion,
            "\n",
            "Message from stderr:",
            " %apply=block bgcolor=silver margin=1em padding=1em border='1px dashed black'%[=",
            self.m_error_text,
            "=]",
            ])


