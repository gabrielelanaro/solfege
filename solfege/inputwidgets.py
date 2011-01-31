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
from __future__ import division

import gtk
import math

from solfege import cfg
from solfege import mpd
from solfege import utils

class CairoCommon(object):
    mark_color = {
        1: (0, 1, 0),
        2: (0.8, 0.6, 0)
    }
    def __init__(self):
        self.m_marks = []
        self.m_clicked_tones = []
    def _redraw(self):
        self.window.invalidate_rect(gtk.gdk.Rectangle(0, 0,
            self.allocation.width, self.allocation.height), True)
        return False
    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        # set a clip region for the expose event
        self.context.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        self.context.clip()
        self.draw(self.context)
        return False
    def clear(self):
        self.m_marks = []
        self.m_clicked_tones = []
    def mark_note(self, midi_int, color):
        """
        color should be 1 to mark the first tone of a question and
        2 to mark the second tone.
        """
        if midi_int not in self.m_marks:
            self.m_marks.append((midi_int, color))
        self._redraw()
    def set_first_note(self, note):
        self.clear()
        self.m_clicked_tones = [int(note)]
        self.mark_note(self.m_clicked_tones[-1], 1)
    def grab_focus_first_sensitive_button(self):
        """
        Dummy function. Only buttons interface implement this.
        """
        pass
    def know_directions(self):
        """
        Return True because this is a inputwidget where the user say
        both interval type _and_ direction.
        """
        return True
    def forget_last_tone(self):
        self.m_clicked_tones.pop()
    def _handle_tone_clicked(self, midi_int, mouse_button):
        if self.m_clicked_tones:
            interval = midi_int - self.m_clicked_tones[-1]
            if mouse_button == 1:
                self.m_clicked_tones.append(midi_int)
            self.m_callback(mouse_button, interval, midi_int)

class PianoKeyboard(gtk.DrawingArea, CairoCommon):
    def __init__(self, num_octaves, lowest_c, key_w=15):
        gtk.DrawingArea.__init__(self)
        CairoCommon.__init__(self)
        self.connect("expose_event", self.expose)
        self.connect("button-press-event", self._on_button_press)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        # Piano stuff
        self.m_num_octaves = num_octaves
        self.m_lowest_c = mpd.MusicalPitch.new_from_notename(lowest_c)
        self.m_lowest_tone = self.m_lowest_c.get_octave_notename()
        self.m_highest_tone = (self.m_lowest_c.clone() + 12 * num_octaves - 1).get_octave_notename()
        self.m_white_h = key_w * 3.4
        self.m_black_h = key_w * 2.0
        self.m_key_w = key_w
        self.m_last_redraw = 0
        self.m_black_w = 0.6
        self.set_size_request(int(num_octaves * 7 * key_w + 1), int(self.m_white_h + 1))
    def _on_button_press(self, drawingarea, event):
        assert event.x >= 0
        if event.x < self.m_pos_x or event.x > self.m_num_octaves * 7 * self.m_key_w + self.m_pos_x:
            # Click outside the keys are ignored.
            return
        click_x = event.x - self.m_pos_x
        x = click_x / self.m_key_w
        octave_w = 7 * self.m_key_w
        clicked_octave = int(click_x / octave_w)
        clicked_white = int((click_x % octave_w) / self.m_key_w)
        black_clicked = 0
        if event.y < self.m_black_h:
            if clicked_white in (0, 1, 3, 4, 5):
                # How many pixels into the white key does the black
                # key start:
                bpos1 = self.m_key_w - self.m_key_w * self.m_black_w / 2
                if click_x % self.m_key_w >= bpos1:
                    black_clicked = 1
            if clicked_white in (1, 2, 4, 5, 6):
                # How many pixels into the white key does the black
                # key end:
                bpos2 = self.m_key_w * self.m_black_w / 2
                if click_x % self.m_key_w <= bpos2:
                    black_clicked = -1
        clicked_on = self.m_lowest_c.clone()
        clicked_on.m_notename_i = clicked_white
        clicked_on.m_accidental_i = black_clicked
        clicked_on.m_octave_i += clicked_octave
        self.on_button_press_event(event, clicked_on.semitone_pitch())
    def draw(self, context):
        num_key = 7 * self.m_num_octaves
        width = num_key * self.m_key_w
        self.m_pos_x = pos_x = int((self.allocation.width - width) / 2) + 0.5
        pos_y = .5
        context.set_line_width(1.2)
        context.save()
        for n in range(num_key):
            context.rectangle(pos_x + n * self.m_key_w, pos_y,
                              self.m_key_w, self.m_white_h)
        context.set_source_rgb(1, 1, 1)
        context.fill_preserve()
        context.set_source_rgb(0, 0, 0)
        context.stroke()
        context.restore()

        # Draw black keys
        context.save()
        for oct in range(self.m_num_octaves):
            for n in (0, 1, 3, 4, 5):
                context.rectangle(pos_x + oct*7*self.m_key_w + (n+1-self.m_black_w/2) * self.m_key_w,
                            pos_y,
                            self.m_key_w * self.m_black_w, self.m_black_h)
                context.set_source_rgb(0, 0, 0)
                context.fill_preserve()
        context.stroke()
        context.restore()
        for midi_int, color in self.m_marks:
            n = mpd.MusicalPitch.new_from_int(midi_int)
            acc = n.m_accidental_i
            step = n.steps() - self.m_lowest_c.steps()
            if acc == 0:
                context.arc(pos_x + (step + 0.5) * self.m_key_w, self.m_white_h-(self.m_white_h - self.m_black_h) / 2,
                            self.m_key_w * 0.35, 0, 2 * math.pi)
            else:
                context.arc(pos_x + (step + 0.5 + 0.5 * acc) * self.m_key_w, self.m_black_h * 0.5,
                            self.m_key_w * 0.25, 0, 2 * math.pi)
            context.set_source_rgb(*self.mark_color[color])
            context.fill_preserve()
            context.stroke()


class PianoOctaveWithAccelName(PianoKeyboard):
    def __init__(self, callback, keys):
        PianoKeyboard.__init__(self, 1, "c", 40)
        self.m_callback = callback
        self.m_visible_accels = False
        self.m_keys = keys
    def draw(self, context):
        PianoKeyboard.draw(self, context)
        if not self.m_visible_accels:
            return
        context.save()
        context.select_font_face("Sans")
        context.set_font_size(24)
        text_h = context.text_extents('A')[3]
        for idx, n in enumerate((0, 2, 4, 5, 7, 9, 11)):
            context.new_path()
            text_w = context.text_extents(self.m_keys[n])[4]
            context.move_to(self.m_pos_x + idx*self.m_key_w + self.m_key_w / 2 - text_w / 2, self.m_black_h + (self.m_white_h - self.m_black_h) / 2 + text_h / 2)
            context.text_path(self.m_keys[n])
            context.fill()
            context.stroke()
        context.restore()
        context.save()
        context.select_font_face("Sans")
        context.set_font_size(24)
        for idx, n in enumerate((1, 3, None, 6, 8, 10)):
            if n:
                context.new_path()
                text_w = context.text_extents(self.m_keys[n])[4]
                context.move_to(self.m_pos_x + (idx + 1)*self.m_key_w - text_w/2, self.m_black_h * 0.8)
                context.text_path(self.m_keys[n])
                context.set_source_rgb(1, 1, 1)
                context.fill()
                context.stroke()
        context.restore()
    def on_button_press_event(self, event, midi_int):
        if event.button == 3:
            utils.play_note(4, midi_int)
        elif event.button == 1:
            self.m_callback(mpd.int_to_notename(midi_int))


class IntervalPianoWidget(PianoKeyboard):
    def __init__(self, callback):
        PianoKeyboard.__init__(self, 4, "c,", 18)
        self.m_callback = callback
    def on_button_press_event(self, event, midi_int):
        """
        The callback function is only called if we have an interval.
        """
        self._handle_tone_clicked(midi_int, event.button)


class IntervalButtonsWidget(gtk.Table, cfg.ConfigUtils):
    def __init__(self, exname, name, callback, sensicallback, vars_to_watch):
        gtk.Table.__init__(self, 1, 1, True)
        cfg.ConfigUtils.__init__(self, exname)
        self.m_name = name
        self.get_sensitive_buttons = sensicallback
        self.m_callback = callback
        self.m_buttons = {}
        self.new_int_button(_("Minor Second"), 1, 0, 1, 0, 2)
        self.new_int_button(_("Major Second"),  2, 0, 1, 2, 4)
        self.new_int_button(_("Minor Third"),   3, 0, 1, 4, 6)
        self.new_int_button(_("Major Third"),    4, 0, 1, 6, 8)
        self.new_int_button(_("Perfect Fourth"),    5, 1, 2, 0, 2)
        self.new_int_button(_("Tritone"),    6, 1, 2, 2, 4)
        self.new_int_button(_("Perfect Fifth"),    7, 1, 2, 4, 6)
        self.new_int_button(_("Minor Sixth"),  8, 1, 2, 6, 8)
        self.new_int_button(_("Major Sixth"),   9, 2, 3, 0, 2)
        self.new_int_button(_("Minor Seventh"),10, 2, 3, 2, 4)
        self.new_int_button(_("Major Seventh"), 11, 2, 3, 4, 6)
        self.new_int_button(_("Perfect Octave"),   12, 2, 3, 6, 8)
        self.new_int_button(_("Minor Ninth"),  13, 3, 4, 0, 2)
        self.new_int_button(_("Major Ninth"),   14, 3, 4, 2, 4)
        self.new_int_button(_("Minor Tenth"), 15, 3, 4, 4, 6)
        self.new_int_button(_("Major Tenth"),  16, 3, 4, 6, 8)
        self.m_lowest_tone = mpd.LOWEST_NOTENAME
        self.m_highest_tone = mpd.HIGHEST_NOTENAME
        self.add_watch('disable_unused_intervals', self.intervals_changed)
        for var in vars_to_watch:
            self.add_watch(var, self.intervals_changed)
        self.intervals_changed()
    def intervals_changed(self, s=None):
        if self.get_bool('disable_unused_intervals'):
            self.set_sensitivity(self.get_sensitive_buttons())
        else:
            for x in range(1, 17):
                self.m_buttons[x].set_sensitive(True)
    def set_sensitivity(self, make_active):
        for x in range(1, 17):
            self.m_buttons[x].set_sensitive(x in make_active)
    def new_int_button(self, txt, nr, x1, x2, y1, y2):
        # buttonwidget calls m_callback with None as midi_int because it
        # does not know if you mean interval up or down when you click
        # the buttons
        self.m_buttons[nr] = b = gtk.Button(txt)
        w, h = b.size_request()
        b.set_size_request(w, int(h*1.4))
        l=b.get_child().set_justify(gtk.JUSTIFY_CENTER)
        self.attach(b, x1, x2, y1, y2)
        b.connect('clicked',
                  lambda s, nr=nr, self=self:self.m_callback(1, nr, None))
        b.set_data('interval', nr)
        b.connect('event', self._abc)
    def _abc(self, button, event):
        if event.type == gtk.gdk.BUTTON_RELEASE and event.button == 3:
            self.m_callback(3, button.get_data('interval'), None)
    def set_first_note(self, note):
        self.m_first_note = int(note)
    def know_directions(self):
        return False
    def clear(self):
        pass
    def show(self):
        self.show_all()
    def grab_focus_first_sensitive_button(self):
        if self.get_bool('disable_unused_intervals'):
            self.m_buttons[self.get_sensitive_buttons()[0]].grab_focus()
        else:
            self.m_buttons[1].grab_focus()
    def mark_note(self, midi_int, color):
        """
        Only implemented for buttons that are drawn using cairo.
        """
        pass

class AbstractGuitarWidget(gtk.DrawingArea, CairoCommon):
    def __init__(self, callback, strings,
                string_thickness=(1, 1, 1, 1, 1, 1)):
        gtk.DrawingArea.__init__(self)
        CairoCommon.__init__(self)
        self.m_callback = callback
        self.m_strings = strings
        self.m_string_thickness = string_thickness
        self.m_fretdist = (20, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 30, 30)
        self.m_stringdist = 17
        self.m_numstring = len(self.m_strings)
        self.m_neckborder = 6
        self.m_neckl = 0
        self.m_xlist = []
        self.m_lowest_tone = mpd.int_to_notename(
            min(map(mpd.notename_to_int, self.m_strings)))
        self.m_highest_tone = mpd.int_to_notename(
            len(self.m_fretdist) - 1 + max(map(mpd.notename_to_int, self.m_strings)))
        self.m_stringtuning = map(mpd.notename_to_int, self.m_strings)
        tmp = 0
        for x in self.m_fretdist:
            tmp = tmp + x
            self.m_xlist.append(tmp)
        tmp = self.m_neckborder + self.m_stringdist/2
        self.m_ylist = [tmp]
        for y in range(self.m_numstring-1):
            tmp = tmp + self.m_stringdist
            self.m_ylist.append(tmp)
        for x in self.m_fretdist:
            self.m_neckl = self.m_neckl + x
        self.m_neckl = self.m_neckl + 2
        self.m_neckw = self.m_neckborder \
                       + (self.m_numstring-1)*self.m_stringdist \
                       + 1 + self.m_neckborder
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK)
        self.connect('expose_event', self.expose)
        self.m_mouse_pos = None, None
        self.connect('motion-notify-event', self.on_motion_notify_event)
        self.connect('leave-notify-event', self.on_leave_notify_event)
        self.connect('button-press-event', self.on_button_press_event)
        self.set_size_request(self.m_neckl, self.m_neckw)
    def on_button_press_event(self, widget, event):
        x, y = self.event2xy(event)
        if x is not None and y is not None:
            midi_int = self.m_stringtuning[y] + x
            self._handle_tone_clicked(midi_int, event.button)
    def on_leave_notify_event(self, widget, event):
        self.m_mouse_pos = None, None
        self._redraw()
    def on_motion_notify_event(self, widget, event):
        x, y = self.event2xy(event)
        need_redraw = False
        if x is not None and y is not None:
            if (x, y) != self.m_mouse_pos:
                need_redraw = True
            self.m_mouse_pos = x, y
        else:
            if (x, y) != self.m_mouse_pos:
                need_redraw = True
            self.m_mouse_pos = None, None
        if need_redraw:
            self._redraw()
    def draw(self, context):
        self.m_posx = int((self.allocation.width - self.m_neckl) / 2) + 0.5
        self.m_posy = int((self.allocation.height - self.m_neckw) / 2) + 0.5
        context.set_line_width(1.2)
        context.save()
        LG = 0.75 # white grey
        DG = 0.66 # dark grey
        # fret board
        context.rectangle(self.m_posx, self.m_posy, self.m_neckl, self.m_neckw)
        context.fill_preserve()
        context.stroke()
        context.restore()
        # first fret
        context.save()
        px = self.m_fretdist[0] + self.m_posx
        context.rectangle(px, self.m_posy,
                          5, self.m_neckw)
        context.set_source_rgb(LG, LG, LG)
        context.fill_preserve()
        context.set_source_rgb(LG, LG, LG)
        context.stroke()
        #
        context.set_source_rgb(1, 1, 1)
        context.move_to(px, self.m_posy)
        context.rel_line_to(0, self.m_neckw)
        context.stroke()
        #
        context.set_source_rgb(DG, DG, DG)
        context.move_to(px + 5, self.m_posy)
        context.rel_line_to(0, self.m_neckw)
        context.stroke()
        context.restore()
        #
        #FRETS
        context.save()
        for w in self.m_fretdist[1:]:
            px = px + w
            context.set_source_rgb(1, 1, 1)
            context.move_to(px, self.m_posy)
            context.rel_line_to(0, self.m_neckw)
            context.stroke()
            context.set_source_rgb(LG, LG, LG)
            context.move_to(px + 1, self.m_posy)
            context.rel_line_to(0, self.m_neckw)
            context.stroke()
            context.set_source_rgb(DG, DG, DG)
            context.move_to(px + 2, self.m_posy)
            context.rel_line_to(0, self.m_neckw)
            context.stroke()
        context.restore()
        #
        # String
        context.save()
        for y in range(self.m_numstring):
            if self.m_string_thickness[y] == 1:
                context.set_line_width(self.m_string_thickness[y])
                context.set_source_rgb(LG, LG, LG)
                context.move_to(self.m_posx, self.m_posy + self.m_neckborder \
                                + y * self.m_stringdist)
                context.rel_line_to(self.m_neckl, 0)
                context.stroke()
            if self.m_string_thickness[y] == 2:
                context.set_source_rgb(1, 1, 1)
                context.move_to(self.m_posx, self.m_posy + self.m_neckborder \
                                + y * self.m_stringdist)
                context.rel_line_to(self.m_neckl, 0)
                context.stroke()
                context.set_source_rgb(LG, LG, LG)
                context.move_to(self.m_posx, self.m_posy + self.m_neckborder \
                                + y * self.m_stringdist + 1)
                context.rel_line_to(self.m_neckl, 0)
                context.stroke()
            if self.m_string_thickness[y] == 3:
                context.rectangle(self.m_posx, self.m_posy + self.m_neckborder \
                                + y * self.m_stringdist + 1,
                                self.m_neckl, 1)
                context.set_source_rgb(LG, LG, LG)
                context.fill_preserve()
                context.set_source_rgb(LG, LG, LG)
                context.stroke()
                context.set_source_rgb(1, 1, 1)
                context.move_to(self.m_posx, self.m_posy + self.m_neckborder \
                                + y * self.m_stringdist)
                context.rel_line_to(self.m_neckl, 0)
                context.stroke()
        context.restore()
        if isinstance(self, GuitarWidget):
            # The white dots on a guitar
            context.save()
            for x, y in ((3, 2), (5, 2), (7, 2), (9, 2), (12, 1), (12, 3)):
                context.arc(self.m_posx + self.m_xlist[x] - self.m_fretdist[x]/2,
                            self.m_posy + self.m_ylist[y],
                            4.5, 0, math.pi * 2)
                context.set_source_rgb(1, 1, 1)
                context.fill_preserve()
                context.stroke()
            context.restore()
        # Marks
        context.save()
        for note, color in self.m_marks:
            for idx in range(len(self.m_stringtuning)):
                if self.m_stringtuning[idx] <= note < self.m_stringtuning[idx] + len(self.m_fretdist):
                    x = note - self.m_stringtuning[idx]
                    context.arc(self.m_posx + self.m_xlist[x]-self.m_fretdist[x]/2,
                        self.m_posy + self.m_ylist[idx]-self.m_stringdist/2,
                        7, 0, math.pi * 2)
                    context.set_source_rgb(*self.mark_color[color])
                    context.fill_preserve()
                    context.set_source_rgb(0, 0, 0)
                    context.stroke()
        context.restore()
        # Dot following mouse cursor
        if self.m_mouse_pos != (None, None):
            context.save()
            context.arc(self.m_posx + self.m_xlist[self.m_mouse_pos[0]]-self.m_fretdist[self.m_mouse_pos[0]]/2,
                        self.m_posy + self.m_ylist[self.m_mouse_pos[1]]-self.m_stringdist/2,
                        5, 0, math.pi * 2)
            context.set_source_rgb(1, 0, 0)
            context.fill_preserve()
            context.set_source_rgb(0, 0, 0)
            context.stroke()
            context.restore()
    def event2xy(self, event):
        x = event.x - self.m_posx
        xp = yp = None
        for idx in range(len(self.m_xlist)):
            if 0 <= x < self.m_xlist[idx]:
                xp = idx
                break
        for idx in range(len(self.m_ylist)):
            if 0 <= event.y < self.m_ylist[idx]:
                yp = idx
                break
        return xp, yp


class GuitarWidget(AbstractGuitarWidget):
    def __init__(self, callback, strings, string_thickness):
        AbstractGuitarWidget.__init__(self, callback, strings, string_thickness)


class AccordionWidget(gtk.DrawingArea, CairoCommon):
    def __init__(self, callback, keyboard_system):
        gtk.DrawingArea.__init__(self)
        CairoCommon.__init__(self)
        self.m_callback = callback
        self.m_notenames_norwegian = (("g,", "bes,", "des", "e",
                 "g", "bes", "des'", "e'", "g'", "bes'", "des''", "e''",
                 "g''", "bes''", "des'''", "e'''", "g'''", "bes'''", "des''''"),
                ("f,", "aes,", "b,", "d",
                 "f", "aes", "b", "d'", "f'", "aes'", "b'", "d''", "f''",
                 "aes''", "b''", "d'''", "f'''", "aes'''", "b'''", "d''''"),
                ("fis,", "a,", "c", "ees",
                 "fis", "a", "c'", "ees'", "fis'", "a'", "c''", "ees''",
                 "fis''", "a''", "c'''", "ees'''", "fis'''", "a'''", "c''''"),
                ("e,", "g,", "bes,", "des",
                 "e", "g", "bes", "des'", "e'", "g'", "bes'", "des''", "e''",
                 "g''", "bes''", "des'''", "e'''", "g'''", "bes'''", "des''''"),
                ("f,", "aes,", "b,", "d",
                 "f", "aes", "b", "d'", "f'", "aes'", "b'", "d''", "f''",
                 "aes''", "b''", "d'''", "f'''", "aes'''", "b'''"))
        self.m_notenames_swedish = (
                ("e,", "g,", "bes,", "des",
                 "e", "g", "bes", "des'", "e'", "g'", "bes'", "des''", "e''",
                 "g''", "bes''", "des'''", "e'''", "g'''", "bes'''"),
                ("dis,", "fis,", "a,", "c", "ees", "fis", "a", "c'",
                 "ees'", "fis'", "a'", "c''", "ees''", "fis''", "a''",
                 "c'''", "ees'''", "fis'''", "a'''", "c''''"),
                ("f,", "aes,", "b,", "d",
                 "f", "aes", "b", "d'", "f'", "aes'", "b'", "d''", "f''",
                 "aes''", "b''", "d'''", "f'''", "aes'''", "b'''"),
                ("e,", "g,", "bes,", "des",
                 "e", "g", "bes", "des'", "e'", "g'", "bes'", "des''", "e''",
                 "g''", "bes''", "des'''", "e'''", "g'''", "bes'''", "des''''"),
                ("fis,", "a,", "c", "ees",
                 "fis", "a", "c'", "ees'", "fis'", "a'", "c''", "ees''",
                 "fis''", "a''", "c'''", "ees'''", "fis'''", "a'''", "c''''"),
                 )
        self.m_notenames_finnish = (
                ("dis,", "fis,", "a,", "c", "ees", "fis", "a", "c'",
                 "ees'", "fis'", "a'", "c''", "ees''", "fis''", "a''",
                 "c'''", "ees'''", "fis'''", "a'''", "c''''"),
                ("d,", "f,", "aes,", "b,", "d",
                 "f", "aes", "b", "d'", "f'", "aes'", "b'", "d''", "f''",
                 "aes''", "b''", "d'''", "f'''", "aes'''", "b'''"),
                ("e,", "g,", "bes,", "des",
                 "e", "g", "bes", "des'", "e'", "g'", "bes'", "des''", "e''",
                 "g''", "bes''", "des'''", "e'''", "g'''", "bes'''", "des''''"),
                ("dis,", "fis,", "a,", "c", "ees",
                 "fis", "a", "c'", "ees'", "fis'", "a'", "c''", "ees''",
                 "fis''", "a''", "c'''", "ees'''", "fis'''", "a'''", "c''''"),
                ("f,", "aes,", "b,", "d",
                 "f", "aes", "b", "d'", "f'", "aes'", "b'", "d''", "f''",
                 "aes''", "b''", "d'''", "f'''", "aes'''", "b'''", "d''''"),
                 )
        self.m_notenames = {'norwegian': self.m_notenames_norwegian,
                            'swedish': self.m_notenames_swedish,
                       'finnish': self.m_notenames_finnish}[keyboard_system]
        self.m_lowest_tone = mpd.HIGHEST_NOTENAME
        self.m_highest_tone = mpd.LOWEST_NOTENAME
        for v in self.m_notenames:
            if mpd.compare_notenames(self.m_lowest_tone, v[0]) > 0:
                self.m_lowest_tone = v[0]
            if mpd.compare_notenames(self.m_highest_tone, v[-1]) < 0:
                self.m_highest_tone = v[-1]
        self.m_button_radius = 9
        self.m_button_xdist = 20
        self.m_button_ydist = 18

        self.connect('expose_event', self.expose)
        self.connect('button-press-event', self._on_button_press)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK)
    def event_to_button_pos(self, event):
        """
        Return a tuple telling which button on the accordion that
        got clicked.
        Returns (Col. row)
        """
        for y in range(self.m_by):
          if self.m_bb + self.m_posy + y * self.m_button_ydist - self.m_button_radius < event.y < self.m_bb + self.m_posy + (y+1) * self.m_button_ydist - self.m_button_radius :
            for x in range(self.m_bx):
                # button center
                cx = self.m_bb + self.m_posx + x * self.m_button_xdist + (y + 1) % 2 * self.m_button_radius
                cy = self.m_bb + self.m_posy + y * self.m_button_ydist
                if math.sqrt((event.x-cx)**2+(event.y-cy)**2)<self.m_button_radius:
                    return x, y
        return None, None
    def _on_button_press(self, drawingarea, event):
        # This is only set if set_first_note is called
        x, y = self.event_to_button_pos(event)
        if x == None:
            return
        midi_int = mpd.notename_to_int(self.m_notenames[y][x])
        self._handle_tone_clicked(midi_int, event.button)
    def draw(self, context):
        # number of buttons, horiz and vertic.
        self.m_bx = bx = len(self.m_notenames[0])
        self.m_by = by = len(self.m_notenames)
        # how much space between buttons and border
        self.m_bb = bb = 16
        #
        w = bx * self.m_button_xdist + bb * 2
        h = by * self.m_button_ydist + bb * 2
        self.m_posx = posx = int((self.allocation.width - w) / 2) + 0.5
        self.m_posy = posy = int((self.allocation.height - h) / 2) + 0.5
        context.set_line_width(1.2)
        context.save()
        context.move_to(posx, posy)
        for x, y in ((w, 0),
                     (0, self.m_button_ydist * by), # right btn
                     (-self.m_button_xdist, self.m_button_ydist), #right btn
                     (-w + self.m_button_xdist * 2, 0),
                     (-self.m_button_xdist, -self.m_button_ydist),
                     (0, -self.m_button_ydist * by),
                     ):
            context.rel_line_to(x, y)
        context.close_path()
        context.set_source_rgb(0, 0, 0)
        context.fill_preserve()
        context.stroke()
        context.restore()

        # buttons
        context.save()
        for row_idx, row in enumerate(self.m_notenames):
            for col_idx, notename in enumerate(row):
                context.arc(bb + posx + col_idx * self.m_button_xdist + (row_idx+1) % 2 * self.m_button_radius,
                            bb + posy + row_idx * self.m_button_ydist,
                            self.m_button_radius, 0, 2 * math.pi)
                if notename[1:][:2] in ('is', 'es'):
                    context.set_source_rgb(0.4, 0.4, 0.4)
                else:
                    context.set_source_rgb(1, 1, 1)
                context.fill_preserve()
                context.stroke()
        context.restore()

        context.save()
        for row_idx, row in enumerate(self.m_notenames):
            for col_idx, notename in enumerate(row):
                try:
                    mark_idx = [m[0] for m in self.m_marks].index(mpd.notename_to_int(notename))
                except ValueError:
                    mark_idx = -1

                if mark_idx != -1:
                    context.arc(bb + posx + col_idx * self.m_button_xdist + (row_idx+1) % 2 * self.m_button_radius,
                            bb + posy + row_idx * self.m_button_ydist,
                            5, 0, 2 * math.pi)
                    context.set_source_rgb(*self.mark_color[self.m_marks[mark_idx][1]])
                    context.fill_preserve()
                    context.stroke()

        context.restore()
        self.set_size_request(500, self.m_by * self.m_button_ydist + 2 * self.m_bb)


inputwidget_names = [_("Buttons"),
                 _("Piano"), _("Guitar"), _("Bass"),
                 _("5 string bass"), _("6 string bass"),
                 _("Accordion B griff"), _("Accordion C griff"),
                 _("Accordion (system used in Finland)")]

def name_to_inputwidget(name, callback):
    if name == _("Piano"):
        w = IntervalPianoWidget(callback)
    elif name == _("Accordion B griff"):
        w = AccordionWidget(callback, 'norwegian')
    elif name == _("Accordion C griff"):
        w = AccordionWidget(callback, 'swedish')
    elif name == _("Accordion (system used in Finland)"):
        w = AccordionWidget(callback, 'finnish')
    elif name == _("Guitar"):
        w = GuitarWidget(callback, ["e'", "b", "g", "d", "a,", "e,"],
                                   (1, 1, 1, 2, 2, 3))
    elif name == _("Bass"):
        w = AbstractGuitarWidget(callback, ["g,", "d,", "a,,", "e,,"],
                                 (1, 1, 2, 3))
    elif name == _("5 string bass"):
        w = AbstractGuitarWidget(callback, ["g,", "d,", "a,,", "e,,", "b,,,"],
                                 (1, 1, 2, 3, 3))
    else:
        assert name == _("6 string bass")
        w = AbstractGuitarWidget(callback, ["c", "g,", "d,", "a,,", "e,,", "b,,,"],
                                 (1, 1, 2, 2, 3, 3))
    return w

