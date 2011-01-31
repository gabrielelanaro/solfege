# GNU Solfege - free ear training software
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2006, 2007, 2008  Tom Cato Amundsen
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

import datetime

import gtk

from solfege import gu
from solfege import lessonfile
from solfege import lessonfilegui

display_max_num_tests = 10

class SimpleTable(gtk.VBox):
    def __init__(self, heading):
        gtk.VBox.__init__(self)
        self.m_heading = heading
        self.m_data = []
    def add_row(self, cell1, cell2):
        self.m_data.append((cell1, cell2))
    def create(self):
        table = gtk.Table()
        label = gtk.Label()
        label.set_alignment(0.0, 0.5)
        label.set_markup(u"<b>%s</b>" % self.m_heading)
        self.pack_start(label)
        for idx, (cell1, cell2) in enumerate(self.m_data):
            table.attach(gtk.Label(cell1), 1, 2, idx*2+1, idx*2+2,
                         xoptions=gtk.SHRINK, xpadding=2)
            table.attach(gtk.Label(cell2), 3, 4, idx*2+1, idx*2+2,
                         xoptions=gtk.SHRINK, xpadding=2)
        for idx in range(len(self.m_data) + 1):
            table.attach(gtk.HSeparator(), 0, 5, idx*2, idx*2+1, xoptions=gtk.FILL)
        table.attach(gtk.VSeparator(), 0, 1, 0, idx*2+2, xoptions=gtk.SHRINK)
        table.attach(gtk.VSeparator(), 2, 3, 0, idx*2+2, xoptions=gtk.SHRINK)
        table.attach(gtk.VSeparator(), 4, 5, 0, idx*2+2, xoptions=gtk.SHRINK)
        self.pack_start(table, False)
        self.show_all()

class MatrixTable(gtk.VBox):
    def __init__(self, heading, st_data, st):
        """
        st_data is the statistics data we want displayled
        st is the statistics object the statistics are collected from.
        """
        gtk.VBox.__init__(self)
        label = gtk.Label(heading)
        label.set_name("StatisticsH2")
        label.set_alignment(0.0, 0.0)
        self.pack_start(label, False)
        hbox = gu.bHBox(self, False)
        frame = gtk.Frame()
        hbox.pack_start(frame, False)
        t = gtk.Table()
        frame.add(t)
        keys = st.get_keys(True)
        for x in range(len(keys)):
            t.attach(gtk.VSeparator(), x*2+1, x*2+2, 0, len(keys)*2)
        for x in range(len(keys)-1):
            t.attach(gtk.HSeparator(), 0, len(keys)*2+1, x*2+1, x*2+2)
        for y, key in enumerate(keys):
            l = lessonfilegui.new_labelobject(st.key_to_pretty_name(key))
            l.set_alignment(0.0, 0.5)
            t.attach(l, 0, 1, y*2, y*2+1, xpadding=gu.PAD)
            for x, skey in enumerate(keys):
                try:
                    s = st_data[key][skey]
                except KeyError:
                    s = '-'
                l = gtk.Label(s)
                if x == y:
                    l.set_name('BoldText')
                t.attach(l, x*2+2, x*2+3, y*2, y*2+1, xpadding=gu.PAD)
        self.show_all()


class PercentagesTable(gtk.Frame):
    def __init__(self, statistics):
        gtk.Frame.__init__(self)
        table = gtk.Table()
        self.add(table)

        self.boxdict = {}
        for k, l, x in (('session', _("Session"), 2), ('today', _("Today"), 5),
                     ('last7', _("Last 7 days"), 8), ('total', _("Total"), 11)):
            table.attach(gtk.Label(l), x, x+2, 0, 1)
            b = gtk.VBox()
            table.attach(b, x, x+1, 4, 5)
            self.boxdict[k+'percent'] = b
            b = gtk.VBox()
            table.attach(b, x+1, x+2, 4, 5)
            self.boxdict[k+'count'] = b
        for x in (2, 5, 8, 11):
            table.attach(gtk.Label(_("Percent")), x, x+1, 2, 3)
            table.attach(gtk.Label(_("Count")), x+1, x+2, 2, 3)
        table.attach(gtk.HSeparator(), 0, 13, 1, 2)
        table.attach(gtk.HSeparator(), 0, 13, 3, 4)
        table.attach(gtk.VSeparator(), 1, 2, 0, 6)
        table.attach(gtk.VSeparator(), 4, 5, 0, 6)
        table.attach(gtk.VSeparator(), 7, 8, 0, 6)
        table.attach(gtk.VSeparator(), 10, 11, 0, 6)
        self.boxdict['keys'] = key_box = gtk.VBox()
        table.attach(key_box, 0, 1, 4, 5)
        for box in self.boxdict.values():
            box.set_border_width(gu.PAD_SMALL)
        self.update(statistics)
        self.show_all()
    def update(self, statistics):
        for box in self.boxdict.values():
            for o in box.get_children():
                o.destroy()
        for k in statistics.get_keys(True):
            l = lessonfilegui.new_labelobject(statistics.key_to_pretty_name(k))
            l.set_alignment(0.0, 0.5)
            self.boxdict['keys'].pack_start(l)
            for sk, seconds in (('session', 0),
                       ('today', 60*60*24),
                       ('last7', 60*60*24*7),
                       ('total', -1)):

                percentage = statistics.get_percentage_correct_for_key(seconds, k)
                if percentage == 0.0:
                    self.boxdict[sk+'percent'].pack_start(gtk.Label("-"))
                else:
                    self.boxdict[sk+'percent'].pack_start(
                        gtk.Label("%.0f" % percentage))
                self.boxdict[sk+'count'].pack_start(
                    gtk.Label(str(statistics.get_num_guess_for_key(seconds, k))))
        self.show_all()

class NewAbstractStatisticsViewer(gtk.ScrolledWindow):
    def __init__(self, statistics, heading):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(gu.PAD)
        self.vbox.set_border_width(gu.PAD)
        self.add_with_viewport(self.vbox)
        self.g_heading = gtk.Label(heading)
        self.g_heading.set_alignment(0.0, 0.5)
        self.g_heading.set_name("StatisticsH1")
        self.vbox.pack_start(self.g_heading, False)
        self.m_statistics = statistics
        self.g_tables = gtk.VBox()
        self.g_tables.show()
        self.vbox.pack_start(self.g_tables)
        self.show_all()

class PercentagesStatisticsViewer(NewAbstractStatisticsViewer):
    """
    A statistics viewer that will only display the Percentages table.
    """
    def __init__(self, statistics, heading):
        NewAbstractStatisticsViewer.__init__(self, statistics, heading)
        #self.clear = self.g_p.clear
    def clear(self):
        #UGH why cant we just destroy the children of g_tables??!!
        #for c in self.g_tables.children():
        #    c.destroy()
        self.g_tables.destroy()
        self.g_tables = gtk.VBox()
        self.g_tables.set_spacing(gu.hig.SPACE_LARGE)
        self.g_tables.show()
        self.vbox.pack_start(self.g_tables)
    def update(self):
        self.clear()
        self.g_p = PercentagesTable(self.m_statistics)
        self.g_p.show_all()
        self.g_tables.pack_start(self.g_p, False, False)
        if not self.m_statistics.m_t.m_P.header.test:
            return
        num_x_per_question = lessonfile.parse_test_def(self.m_statistics.m_t.m_P.header.test)[0]
        c = 0
        for time, f, result in self.m_statistics.iter_test_results():
            t = datetime.datetime.fromtimestamp(time)
            b = SimpleTable(_(u"Test dated %(date)s: %(percent).1f%%") % {
                'date': t.strftime("%x %X"),
                'percent': f
            })
            for k in result:
                count = result[k].get(k, 0)
                # More necessary than one would expect because we want to handle
                # the possibility that that result[key1][key2] == None
                # A user has reported that this can happen, but I don't know
                # what could insert a None into the database.
                if count is None:
                    count = 0
                b.add_row(self.m_statistics.key_to_pretty_name(k),
                    "%.1f%%" % (100.0 * count / num_x_per_question))
            b.create()
            self.g_tables.pack_start(b, False)
            # Don't show too many test results.
            c += 1
            if c == display_max_num_tests:
                break


class StatisticsViewer(NewAbstractStatisticsViewer):
    def __init__(self, statistics, heading):
        NewAbstractStatisticsViewer.__init__(self, statistics, heading)
        self.matrix_dict = {}
    def clear(self):
        #UGH why cant we just destroy the children of g_tables??!!
        #for c in self.g_tables.children():
        #    c.destroy()
        self.g_tables.destroy()
        self.g_tables = gtk.VBox()
        self.g_tables.show()
        self.vbox.pack_start(self.g_tables)
    def update(self):
        self.clear()
        self.g_p = PercentagesTable(self.m_statistics)
        self.g_p.show_all()
        self.g_tables.set_spacing(gu.hig.SPACE_LARGE)
        self.g_tables.pack_start(self.g_p, False)
        self.matrix_dict['session'] = MatrixTable(
                                _("Session"),
                                self.m_statistics.get_statistics(0),
                                self.m_statistics)
        self.matrix_dict['today'] = MatrixTable(
                                _("Today"),
                                self.m_statistics.get_statistics(60*60*24),
                                self.m_statistics)
        self.matrix_dict['last7'] = MatrixTable(
                                _("Last 7 days"),
                                self.m_statistics.get_statistics(60*60*24*7),
                                self.m_statistics)
        self.matrix_dict['total'] = MatrixTable(
                                _("Total"),
                                self.m_statistics.get_statistics(-1),
                                self.m_statistics)

        for k in ('session', 'today', 'last7', 'total'):
            self.g_tables.pack_start(self.matrix_dict[k], False)
        c = 0
        for time, f, result in self.m_statistics.iter_test_results():
            t = datetime.datetime.fromtimestamp(time)
            m = MatrixTable(_(u"Test dated %(date)s: %(percent).1f%%") % {
                'date': t.strftime("%x %X"),
                'percent': f}, result, self.m_statistics)
            m.show()
            self.g_tables.pack_start(m, False)
            # Don't show too many test results.
            c += 1
            if c == display_max_num_tests:
                break

