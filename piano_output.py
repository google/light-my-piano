"""
Copyright 2015 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import Tkinter as tk

OCTAVE_WIDTH = 158.0
WHITE_NOTE_WIDTH = OCTAVE_WIDTH / 7.0
BLACK_NOTE_WIDTH = WHITE_NOTE_WIDTH / 2.0
BLACK_NOTE_WIDE_WIDTH = WHITE_NOTE_WIDTH / 1.0
NOTE_IND_TO_PARAMS = {0: (0.0, WHITE_NOTE_WIDTH),
                      1: (12.2, BLACK_NOTE_WIDTH),
                      2: (21.8, WHITE_NOTE_WIDTH),
                      3: (40.5, BLACK_NOTE_WIDTH),
                      4: (44.3, WHITE_NOTE_WIDTH),
                      5: (66.9, WHITE_NOTE_WIDTH),
                      6: (80.2, BLACK_NOTE_WIDTH),
                      7: (90.2, WHITE_NOTE_WIDTH),
                      8: (106.5, BLACK_NOTE_WIDTH),
                      9: (112.4, WHITE_NOTE_WIDTH),
                      10: (132.9, BLACK_NOTE_WIDTH),
                      11: (135.5, WHITE_NOTE_WIDTH)}
NOTE_IND_TO_PARAMS_WIDE = {0: (0.0, WHITE_NOTE_WIDTH),
                           1: (12.2-4, BLACK_NOTE_WIDE_WIDTH),
                           2: (21.8, WHITE_NOTE_WIDTH),
                           3: (40.5-4, BLACK_NOTE_WIDE_WIDTH),
                           4: (44.3, WHITE_NOTE_WIDTH),
                           5: (66.9, WHITE_NOTE_WIDTH),
                           6: (80.2-4, BLACK_NOTE_WIDE_WIDTH),
                           7: (90.2, WHITE_NOTE_WIDTH),
                           8: (106.5-4, BLACK_NOTE_WIDE_WIDTH),
                           9: (112.4, WHITE_NOTE_WIDTH),
                           10: (132.9-4, BLACK_NOTE_WIDE_WIDTH),
                           11: (135.5, WHITE_NOTE_WIDTH)}


def noteToPhysicalInterval(note, wide):
  if wide:
    interval = NOTE_IND_TO_PARAMS_WIDE[int(note) % 12]
  else:
    interval = NOTE_IND_TO_PARAMS[int(note) % 12]
  start = (int(note) / 12) * OCTAVE_WIDTH + interval[0]
  return (start, start + interval[1])


def noteToScreenInterval(note, waterfall, wide):
  MIN_X = noteToPhysicalInterval(waterfall.LOWEST_NOTE, wide)[0]
  MAX_X = noteToPhysicalInterval(waterfall.HIGHEST_NOTE, wide)[1]
  SCALE_X = float(waterfall.CANVAS_WIDTH) / (MAX_X - MIN_X)
  interval = noteToPhysicalInterval(note, wide)
  return ((interval[0] - MIN_X)*SCALE_X, (interval[1] - MIN_X)*SCALE_X)


class PianoOutput(object):
  LOWEST_NOTE = 36
  HIGHEST_NOTE = 96
  WHITE_NOTES = (0,2,4,5,7,9,11)

  def __init__(self):
    self.tk_root = tk.Tk()
    self.tk_root.attributes("-fullscreen", True)
    self.CANVAS_WIDTH = self.tk_root.winfo_screenwidth()
    self.CANVAS_HEIGHT = self.tk_root.winfo_screenheight()
    self.KEYBOARD_HEIGHT = int(self.CANVAS_HEIGHT * 0.22)
    self.CANVAS_HEIGHT = self.KEYBOARD_HEIGHT + 300

    self.canvas = tk.Canvas(self.tk_root,
                            width=self.CANVAS_WIDTH,
                            height=self.CANVAS_HEIGHT)

    self.canvas.pack()

  def Clear(self):
    self.canvas.delete('all')

  def DrawPiano(self, draw_guides):
    for i in xrange(self.LOWEST_NOTE, self.HIGHEST_NOTE+1):
      if i % 12 in self.WHITE_NOTES:
        self.SetKeyColor(i, color='white')
    for i in xrange(self.LOWEST_NOTE, self.HIGHEST_NOTE+1):
      if i % 12 not in self.WHITE_NOTES:
        self.SetKeyColor(i, color='black')

  def DrawRect(self, note, y1, y2, color=None):
    """Draws a rect for the specified note.
    Args:
      y1: start of rect in # of pixels (0 is the top of keyboard)
          max val self.CANVAS_HEIGHT - self.KEYBOARD_HEIGHT
      y2: same as y1 for the end of the rect; y2 > y1
    """
    interval = noteToScreenInterval(note, self, wide=True)
    x1 = interval[0]
    x2 = interval[1]
    # 0 => self.CANVAS_HEIGHT
    # CANVAS_HEIGHT - KEYBOARD_HEIGHT => CANVAS_HEIGHT - KEYBOARD_HEIGHT
    a = float(self.KEYBOARD_HEIGHT) / (self.KEYBOARD_HEIGHT - self.CANVAS_HEIGHT)
    b = self.CANVAS_HEIGHT
    ty1 = a*y1 + b
    ty2 = a*y2 + b

    if y2 > y1:
      self.canvas.create_rectangle(
          x1,
          ty1,
          x2,
          ty2,
          fill=color)

  def SetKeyColor(self, note, color=None, wide=False):
    #fillcolor = ('red' if note in self.active_notes else color) if color else 'green' if note in self.active_notes else 'yellow'
    interval = noteToScreenInterval(note, self, wide)
    x1 = interval[0]
    x2 = interval[1]
    if note%12 in self.WHITE_NOTES:
      bottom = self.CANVAS_HEIGHT
    else:
      bottom = self.CANVAS_HEIGHT - 50
    self.canvas.create_rectangle(x1,
                                 bottom,
                                 x2,
                                 self.CANVAS_HEIGHT - (self.KEYBOARD_HEIGHT),
                                 fill=color)

  def SetTitle(self, text):
    self.canvas.create_rectangle(0,0,240,40,fill='white')
    self.canvas.create_text(120,20,font=(None, 16),
                            text=text)
  def Refresh(self):
    self.canvas.update()

  def SetKeyText(self, note, y, text=""):
    interval = noteToScreenInterval(note, self, False)
    x1 = interval[0]
    x2 = interval[1]
    return self.canvas.create_text((x1+x2)/2,
                                   self.CANVAS_HEIGHT - y,font=(None, 16),
                                   text=text)

