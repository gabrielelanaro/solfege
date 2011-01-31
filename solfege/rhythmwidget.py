#!/usr/bin/python

from __future__ import absolute_import

import copy
import os
import re

import gtk


if __name__ == '__main__':
    import sys
    sys.path.insert(0, ".")
    import solfege.i18n
    solfege.i18n.setup(".")

from solfege.mpd.duration import Duration
from solfege.mpd import MusicalPitch
from solfege.mpd import const
from solfege.mpd import elems
from solfege.mpd import engravers
from solfege.mpd.musicdisplayer import MusicDisplayer
from solfege.mpd.rat import Rat


class Controller(gtk.HBox):
    def __init__(self, rwidget):
        """
        rwidget is the RhythmWidget we are controlling
        """
        gtk.HBox.__init__(self)
        self.g_rwidget = rwidget
        for k in (1, 2, 4, 8, 16, 32):
            im = gtk.Image()
            im.set_from_file(os.path.join("graphics", "note-%i.svg"% k))
            b = gtk.Button()
            b.add(im)
            self.pack_start(b, False)
            def f(widget, i):
                self.g_rwidget.on_add_item(elems.Note(
                    MusicalPitch.new_from_notename("c"),
                    Duration(i, 0)))
                self.g_rwidget.grab_focus()
            b.connect('clicked', f, k)
        for k in (1, 2, 4, 8, 16, 32):
            im = gtk.Image()
            im.set_from_file(os.path.join("graphics", "rest-%i.svg" % k))
            b = gtk.Button()
            b.add(im)
            self.pack_start(b, False)
            def f(widget, i):
                self.g_rwidget.on_add_item(elems.Rest(
                    Duration(i, 0)))
                self.g_rwidget.grab_focus()
            b.connect('clicked', f, k)
        im = gtk.Image()
        im.set_from_file(os.path.join("graphics", "add-dot.svg"))
        b = gtk.Button()
        b.add(im)
        b.connect('clicked', self.on_toggle_dots, 1)
        self.pack_start(b, False)
        im = gtk.Image()
        im.set_from_file(os.path.join("graphics", "remove-dot.svg"))
        b = gtk.Button()
        b.add(im)
        b.connect('clicked', self.on_toggle_dots, -1)
        self.pack_start(b, False)
        im = gtk.Image()
        im.set_from_file(os.path.join("graphics", "tie.svg"))
        b = gtk.Button()
        b.add(im)
        b.connect('clicked', self.on_toggle_tie)
        self.pack_start(b, False)
        im = gtk.Image()
        im.set_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU)
        b = gtk.Button()
        b.add(im)
        b.connect('clicked', self.ctrl_on_delete)
        self.pack_start(b, False)
        self.g_mode = gtk.ToggleButton(_i("insert-overwrite|INSRT"))
        self.g_mode.connect('clicked', self.ctrl_on_ins)
        self.g_rwidget.m_ins_mode = not self.g_mode.get_active()
        self.pack_start(self.g_mode, False)
        self.show_all()
    def ctrl_on_ins(self, button):
        self.g_rwidget.m_ins_mode = not self.g_mode.get_active()
        self.g_mode.set_label({False: _i("insert-overwrite|INSRT"),
            True: _i("insert-overwrite|OVER")}[button.get_active()])
        self.g_rwidget.grab_focus()
    def ctrl_on_delete(self, button):
        self.g_rwidget.on_delete()
        self.g_rwidget.grab_focus()
    def on_toggle_dots(self, button, delta):
        self.g_rwidget.on_toggle_dots(delta)
        self.g_rwidget.grab_focus()
    def on_toggle_tie(self, button):
        self.g_rwidget.on_toggle_tie()
        self.g_rwidget.grab_focus()
    def set_editable(self, b):
        self.g_rwidget.m_editable = b
        self.g_rwidget.queue_draw()
        self.set_sensitive(b)


class RhythmWidget(MusicDisplayer):
    """
    Rhythm widget editor.
    Before editing, we feed it a Score objects with notes and/or
    skips. The user is not allowed to add skips in the middle of
    the rhythm. Only rests.
    """
    skipdur = Duration(4, 0)
    def __init__(self):
        MusicDisplayer.__init__(self)
        self.g_d.connect("expose_event", self.on_draw_cursor)
        self.add_events(gtk.gdk.KEY_RELEASE_MASK)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect("key-release-event", self.on_keypress)
        self.set_flags(gtk.CAN_FOCUS)
        def f(*w):
            self.grab_focus()
        self.connect("button-press-event", f)
        self.m_cursor = None
    def get_cursor_timepos(self):
        """
        Return the timepos the cursor has. Return None if the
        cursor is not visible, for example when the staff is completely
        empty.
        """
        if self.m_cursor is None:
            return
        if not self.m_score.m_staffs:
            return None
        timeposes = self.m_score.m_staffs[0].get_timeposes()
        if timeposes:
            return self.m_score.m_staffs[0].get_timeposes()[self.m_cursor]
        return
    def cursor_prev(self):
        if self.m_cursor > 0:
            self.m_cursor -= 1
    def cursor_next(self):
        if self.m_cursor < len(self.m_score.m_staffs[0].get_timeposes()) - 1:
            self.m_cursor += 1
    def on_keypress(self, window, event):
        if not self.m_editable:
            return
        if event.keyval in (gtk.keysyms.Right, gtk.keysyms.KP_Right):
            self.cursor_next()
        elif event.keyval in (gtk.keysyms.Left, gtk.keysyms.KP_Left):
            self.cursor_prev()
        self.queue_draw()
    def on_toggle_tie(self):
        timepos = self.get_cursor_timepos()
        if not isinstance(self.m_score.voice11.m_tdict[timepos]['elem'][0], elems.Note):
            return
        if self.m_score.voice11.m_tdict[timepos]['elem'][0].m_tieinfo in (None, 'end'):
            if self.m_score.voice11.tie_timepos(timepos):
                self.score_updated()
        elif self.m_score.voice11.m_tdict[timepos]['elem'][0].m_tieinfo in ('start', 'go'):
            if self.m_score.voice11.untie_next(timepos):
                self.score_updated()
    def on_delete(self):
        timepos = self.get_cursor_timepos()
        self.m_score.voice11.del_elem(timepos)
        self.score_updated()
    def on_toggle_dots(self, delta):
        """
        delta is the number of dots to add or remove.
        Return True if the number of dots was changed.
        Return False if not allowed.
        """
        timepos = self.get_cursor_timepos()
        elem = self.m_score.voice11.m_tdict[timepos]['elem'][0]
        if isinstance(elem, elems.Skip):
            return False
        if elem.m_duration.m_dots + delta < 0:
            return False
        new_elem = copy.deepcopy(self.m_score.voice11.m_tdict[timepos]['elem'][0])
        new_elem.m_duration.m_dots += delta
        if self.m_score.voice11.try_set_elem(new_elem, timepos, False):
            self.score_updated()
        return True
    def on_add_item(self, item):
        if self.m_score.voice11.try_set_elem(item, self.get_cursor_timepos(),
                self.m_ins_mode):
            self.cursor_next()
            self.score_updated()
    def fill_score(self, timesig, skip, count):
        self.m_score = elems.Score()
        self.m_score.add_staff(staff_class=elems.RhythmStaff)
        self.m_score.add_bar(timesig)
        for c in range(count):
            self.m_score.voice11.append(skip)
        self.m_cursor = 0
        self.score_updated()
    def set_score(self, score, cursor=0):
        self.m_score = score
        self.m_cursor = cursor
        self.score_updated()
    def score_updated(self):
        """
        Redraw the staff. This should be called whenever m_score is updated.
        """
        self.m_scorecontext = engravers.ScoreContext(self.m_score)
        self.m_engravers = self.m_scorecontext.m_contexts
        self._display()
        if self.m_score.m_staffs:
            timeposes = self.m_score.m_staffs[0].get_timeposes()
            if self.m_cursor > len(timeposes) - 1:
                self.m_cursor = len(timeposes) - 1
        else:
            self.m_cursor = None
    def on_draw_cursor(self, darea, event):
        timepos = self.get_cursor_timepos()
        if not timepos:
            return
        engraver = None
        for e in self.m_scorecontext.m_contexts[0].m_engravers[timepos]['elem']:
            if isinstance(e, (engravers.NoteheadEngraver,
                              engravers.RestEngraver,
                              engravers.SkipEngraver)):
                engraver = e
                break
        if not engraver:
            return
        red = self.window.get_colormap().alloc_color('#FF0000', True, True)
        red = self.window.new_gc(red)
        y = engravers.dim20.first_staff_ypos + 10
        darea.window.draw_rectangle(red, True,
                     engraver.m_xpos, y, 10, 3)

class TestWin(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        vbox = gtk.VBox()
        self.add(vbox)
        self.set_default_size(600, 400)
        self.w = RhythmWidget()
        s = elems.Score()
        s.add_staff(staff_class=elems.RhythmStaff)
        for x in range(8):
            s.voice11.append(elems.Skip.new_from_string("4"))
        self.w.set_score(s)
        vbox.pack_start(self.w)
        #
        c = Controller(self.w)
        vbox.pack_start(c, False)
        c.show()
        c.set_editable(True)
        self.connect('delete_event', self.quit)
    def quit(self, *w):
        gtk.main_quit()

if __name__ == '__main__':
    w = TestWin()
    w.show_all()
    gtk.main()
