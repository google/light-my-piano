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

import time

import piano_input
import piano_output

_ALPHABET_POSITIONS = [
    36, 38, 40, 41, 43, 45, 47,
    48, 50, 52, 53, 55, 57, 59,
    60, 62, 64, 65, 67, 69, 71,
    72, 74, 76, 77, 79]

_BACKSPACE_POSITION = 84
_ENTER_POSITION = 89


class Keyboard(object):
  """Uses the piano keyboard to type in alphabet characters."""

  def __init__(self, piano_input_obj, piano_output_obj):
    self.piano_input = piano_input_obj
    self.piano_output = piano_output_obj
    self.typed_string = ''

  def DrawKeyboard(self):
    self.piano_output.DrawPiano(False)
    for pos in xrange(26):
      self.piano_output.SetKeyText(_ALPHABET_POSITIONS[pos], 20,
                                   chr(pos + ord('A')))
    self.piano_output.SetKeyText(_BACKSPACE_POSITION, 20, u"\u2190")
    self.piano_output.SetKeyText(_ENTER_POSITION, 20, u"\u23CE")

  def DrawTypedString(self):
    self.piano_output.SetKeyText(65, self.piano_output.KEYBOARD_HEIGHT + 50,
                                 self.typed_string)

  def GetTypedString(self):
    self.typed_string = ''
    self.piano_input.ClearInput()
    text_widget = self.piano_output.SetKeyText(
        65, self.piano_output.KEYBOARD_HEIGHT + 50, '')
    while True:
      while self.piano_input.user_input.empty():
        time.sleep(0.1)
      user_cmd = self.piano_input.user_input.get()
      if user_cmd[1] == 0:
        continue
      note_pressed = user_cmd[0]
      if note_pressed in _ALPHABET_POSITIONS:
        char_pressed = chr(ord('A') + _ALPHABET_POSITIONS.index(note_pressed))
        self.typed_string += char_pressed
        self.piano_output.canvas.insert(text_widget, len(self.typed_string),
                                        char_pressed)
      elif note_pressed == _BACKSPACE_POSITION:
        if self.typed_string:
          self.typed_string = self.typed_string[:-1]
        self.piano_output.canvas.dchars(
            text_widget, len(self.typed_string), len(self.typed_string))
      elif note_pressed == _ENTER_POSITION:
        return self.typed_string
