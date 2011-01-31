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

from __future__ import absolute_import

import logging
import random

import gobject
import gtk

from solfege import abstract
from solfege import gu
from solfege import lessonfile
from solfege import statistics, statisticsviewer
from solfege import utils

import solfege

class Teacher(abstract.Teacher):
    def __init__(self, exname):
        abstract.Teacher.__init__(self, exname)
        self.lessonfileclass = lessonfile.HeaderLessonfile
        # 60, 84, 100, 120
        self.m_ped = [60, 120, 40, 168, 208, 80, 96, 139, 48, 69, 108, 192, 152,
                      88, 63, 100, 116, 176, 200, 52, 76, 126, 160,
                      84, 56, 44, 66, 72, 92, 104, 112, 132, 144, 184]
        self.m_bpms = [40, 44, 48, 52, 56, 60, 63, 66, 69,      # 0 - 8
                       72, 76, 80, 84, 88, 92, 96, 100, 104,    # 9 - 17
                       108, 112, 116, 120, 126, 132, 138, 144,  # 18 - 25
                       152, 160, 168, 176, 184, 192, 200, 208]  # 26 - 33
        self.m_statistics = statistics.LessonStatistics(self)
        self.m_timeout_tag = None
        self.m_question = None
        self.m_practise_these = {}
        v = self.get_list('active_bpms')
        for bpm in self.m_bpms:
            if bpm in v:
                self.m_practise_these[bpm] = 1
            else:
                self.m_practise_these[bpm] = 0
    def toggle_active(self, bpm):
        self.m_practise_these[bpm] = not self.m_practise_these[bpm]
        v = [bpm for bpm in self.m_practise_these if self.m_practise_these[bpm]]
        self.set_string('active_bpms', str(v))
    def get_possible_bpms(self):
        return [n for n in self.m_practise_these.keys() \
            if self.m_practise_these[n]]
    def get_number_of_levels(self):
        return len(self.m_ped)
    def new_question(self):
        last = self.m_question
        if not self.get_possible_bpms():
            return False

        self.m_question = random.choice(self.get_possible_bpms())
        while self.m_question == last and len(self.get_possible_bpms()) > 1:
            self.m_question = random.choice(self.get_possible_bpms())
        self.start_question(self.m_question)
        self.q_status = self.QSTATUS_NEW
        return True
    def start_question(self, bpm):
        self.tick()
        if self.m_timeout_tag:
            gobject.source_remove(self.m_timeout_tag)
        self.m_timeout_tag = gobject.timeout_add(60000/bpm, self.tick)
    def stop_question(self):
        if self.m_timeout_tag:
            gobject.source_remove(self.m_timeout_tag)
            self.m_timeout_tag = None
    def tick(self, _o=None):
        utils.play_perc(8, 60)
        return 1
    def guess_answer(self, bpm):
        assert self.q_status != self.QSTATUS_NO
        if self.m_question == bpm:
            self.stop_question()
            if self.q_status == self.QSTATUS_NEW:
                self.m_statistics.add_correct(unicode(bpm))
            self.q_status = self.QSTATUS_SOLVED
            solfege.app.play_happy_sound()
            return 1
        else:
            if self.q_status == self.QSTATUS_NEW:
                self.m_statistics.add_wrong(str(self.m_question), unicode(bpm))
            self.q_status = self.QSTATUS_WRONG
            solfege.app.play_sad_sound()
    def end_practise(self):
        super(Teacher, self).end_practise()
        self.stop_question()
        self.q_status = self.QSTATUS_NO
    def give_up(self):
        self.stop_question()
        logging.debug("identifybpm.give_up:FIXME not saving statistics")
        self.q_status = self.QSTATUS_GIVE_UP

class Gui(abstract.Gui):
    def __init__(self, teacher):
        abstract.Gui.__init__(self, teacher)
        ################
        # practise_box #
        ################
        self.practise_box.set_spacing(gu.PAD)
        self.m_buttons = []
        vbox = gu.bVBox(self.practise_box, False)
        for s, e in ((0, 9), (9, 18), (18, 26), (26, 34)):
            box = gtk.HBox()
            vbox.pack_start(box)
            for i in range(s, e):
                bpm = self.m_t.m_bpms[i]
                button = gtk.Button(str(bpm))
                box.pack_start(button)
                button.connect('clicked', self.on_click)
                button.connect('event', self.on_event)
                button.set_data('bpm', bpm)
                self.m_buttons.append(button)

        self.g_flashbar = gu.FlashBar()
        self.g_flashbar.show()
        self.practise_box.pack_start(self.g_flashbar, False)

        self.std_buttons_add(
            ('new', self.on_new),
            ('give_up', self.on_give_up)
        )
        self.practise_box.show_all()
        ##############
        # statistics #
        ##############
        self.g_statview = statisticsviewer.StatisticsViewer(self.m_t.m_statistics, _('Bpm'))
        self.g_statview.show()
        self.g_notebook.append_page(self.g_statview,
                                    gtk.Label(_("Statistics")))
        ########
        # init #
        ########
        self.g_notebook.get_nth_page(1).hide()
        self.update_buttons()
    def on_event(self, button, event):
        if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 3:
            self.m_t.toggle_active(button.get_data('bpm'))
            self.update_buttons()
    def on_level_change(self, adjustment):
        self.set_int('level', adjustment.value)
        self.update_buttons()
    def on_new(self, _o=None):
        try:
            n = self.m_t.new_question()
        except Exception, e:
            if not self.standard_exception_handler(e):
                raise
            self.m_t.stop_question()
            return
        if n:
            self.std_buttons_new_question()
            self.m_buttons[0].grab_focus()
        else:
            self.g_flashbar.flash(_("You have to select some tempos to practise."))
    def on_give_up(self, _o):
        self.m_t.give_up()
        self.g_flashbar.flash(str(self.m_t.m_question))
        self.std_buttons_give_up()
    def update_buttons(self):
        v = self.m_t.get_possible_bpms()
        for b in self.m_buttons:
            if b.get_data('bpm') in v:
                b.get_children()[0].set_name("BpmActiveLabel")
            else:
                b.get_children()[0].set_name("BpmInactiveLabel")
    def on_click(self, _o):
        if self.m_t.q_status in (self.QSTATUS_SOLVED, self.QSTATUS_GIVE_UP):
            return
        if _o.get_data('bpm') not in self.m_t.get_possible_bpms():
            return
        if self.m_t.q_status == self.QSTATUS_NO:
            self.g_flashbar.flash(_("Click 'New tempo' to begin."))
            return
        if self.m_t.guess_answer(_o.get_data('bpm')):
            self.g_flashbar.flash(_("Correct, it is %i") % _o.get_data('bpm'))
            self.std_buttons_answer_correct()
        else:
            self.g_flashbar.flash(_("Wrong"))
        self.g_statview.update()
    def on_start_practise(self):
        self.g_flashbar.flash(_("Click 'New tempo' to begin."))
        self.std_buttons_start_practise()
        self.m_t.m_statistics.reset_session()
        self.g_statview.update()
    def on_end_practise(self):
        self.m_t.end_practise()
        self.std_buttons_end_practise()
