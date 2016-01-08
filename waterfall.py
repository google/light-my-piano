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

import copy
import midi
import sys
import time
import piano_input_mock
import piano_output

class Waterfall(object):
  """Handles waterfall object.

  Attributes:
    midi_file: midi.MidiFile object.
    midi_track: midi.MidiTrack object for which waterfall will be displayed.
    state: List of 256 ints indicating which note is currently pressed.
        -1: note is not currently playing.
        nonnegative: note has been playing since specified time.
    time: Time in midi ticks since start of file.
    n_event: Ordinal of first midi event occurring at or after self.time.
    score: User's current score.
    piano_output: piano_output.PianoOutput object handling output graphics.
    piano_input: piano_input.PianoInput object handling input from piano.
    active_notes: set of currently pressed notes.
  """

  def __init__(self, piano_input, piano_output, midi_file):
    self.midi_file = midi_file
    self.midi_track = self._GetLongestTrack(midi_file)
    self.state = [-1] * 256
    self.time = 0
    self.n_event = 0
    self.score = 0
    self.piano_output = piano_output
    self.piano_input = piano_input
    self.active_notes = set()

    self.TICKS_SHOWN = 300  # Total number of ticks shown simultaneously.
    self.PIXELS_PER_TICK = (
        float(self.piano_output.CANVAS_HEIGHT -
              self.piano_output.KEYBOARD_HEIGHT) / self.TICKS_SHOWN)

  def _GetLongestTrack(self, midi_file):
    longestTrack = midi_file.tracks[0]
    for track in midi_file.tracks:
      if len(longestTrack.events) < len(track.events):
        longestTrack = track
    return longestTrack

  def EndOfSong(self):
    return self.n_event >= len(self.midi_track.events)

  def Advance(self, delta):
    """Advances waterfall by delta ticks.
    Returns False iff EOF reached.
    """
    while not self.EndOfSong():
      event = self.midi_track.events[self.n_event]
      if event.delta >= delta:
        event.delta -= delta
        self.time += delta
        break
      self.time += event.delta
      delta -= event.delta
      self.n_event += 1
      if event.ignore_me:
        continue
      if event.cmd == 0x80:
        self.state[event.note] = -1
      elif event.cmd == 0x90:
        self.state[event.note] = self.time

  def WaterfallNoteColor(self, note):
    if note in self.active_notes:
      if self.state[note] >= 0:
        return '#00ff00'
    if note % 12 in (0,2,4,5,7,9,11):
      return '#8080ff'  # white note
    else:
      return '#80ffff'  # black note

  def Draw(self):
    cur_time = self.time
    cur_n_event = self.n_event
    draw_state = copy.copy(self.state)
    self.piano_output.Clear()
    self.piano_output.DrawPiano(True)
    for note in self.active_notes:
      if self.state[note] < 0:
        self.piano_output.SetKeyColor(note, color='#ff0000', wide=True)
    while cur_n_event < len(self.midi_track.events):
      event = self.midi_track.events[cur_n_event]
      cur_time += event.delta
      cur_n_event += 1
      if cur_time > self.time + self.TICKS_SHOWN:
        break
      if event.ignore_me:
        continue
      if event.cmd == 0x80:
        # Note turned off. Draw rect for it.
        y1 = max(0, (draw_state[event.note] - self.time) * self.PIXELS_PER_TICK)
        y2 = (cur_time - self.time) * self.PIXELS_PER_TICK
        self.piano_output.DrawRect(
            event.note, y1, y2, self.WaterfallNoteColor(event.note))
        draw_state[event.note] = -1
      elif event.cmd == 0x90:
        # Note turned on. Store state.
        if draw_state[event.note] >= 0:
          # Note is already on, do nothing
          print('Warning: Waterfall.Draw ignoring double note-on '
                'for note %d' % event.note)
        draw_state[event.note] = cur_time
      else:
        print 'Warning: Waterfall.Draw ignoring cmd %02X' % event.cmd
    # Everything that's still playing should get a rect to end of screen.
    for note, state in enumerate(draw_state):
      if state >= 0:
        y1 = max(0, (state - self.time) * self.PIXELS_PER_TICK)
        y2 = self.TICKS_SHOWN * self.PIXELS_PER_TICK
        self.piano_output.DrawRect(
            note, y1, y2, self.WaterfallNoteColor(note))

    # Print score
    self.piano_output.SetTitle('Score: %d' % self.score)
    self.piano_output.Refresh()

  def UpdatePianoInput(self):
    while not self.piano_input.user_input.empty():
      user_cmd = self.piano_input.user_input.get()
      if user_cmd[1] == 0 and user_cmd[0] in self.active_notes:
        self.active_notes.remove(user_cmd[0])
      if user_cmd[1] > 0:
          self.active_notes.add(user_cmd[0])

  def UpdateScore(self, slowdown_factor=1.0):
    gain = max(1, int(300.0 / slowdown_factor / slowdown_factor))
    loss = max(1, int(50.0 / slowdown_factor / slowdown_factor))
    for note in xrange(256):
      if self.state[note] >= 0:
        if note in self.active_notes:
          self.score += gain
        else:
          self.score -= loss
      if self.state[note] < 0 and note in self.active_notes:
        self.score -= loss

  def MenuRequested(self):
    return self.active_notes == set([
        self.piano_output.LOWEST_NOTE,
        self.piano_output.HIGHEST_NOTE])

  def Continue(self, slowdown_factor=1.0):
    frames_per_sec = 15
    prev_frame_wall_time = time.time()
    self.active_notes = set()

    while not self.EndOfSong():
      self.UpdatePianoInput()
      if self.MenuRequested():
        break

      self.UpdateScore(slowdown_factor)
      self.Draw()

      elapsed_wall_time = time.time() - prev_frame_wall_time
      wait_time = 1.0 / frames_per_sec - elapsed_wall_time
      if wait_time > 0: time.sleep(wait_time)
      prev_frame_wall_time = time.time()

      delta = int(self.midi_file.GetTicksPerSec(self.time) / frames_per_sec /
                  slowdown_factor)
      if delta < 1:
        delta = 1
      self.Advance(delta)
      prev_frame_wall_time = time.time()

    return self.score


def main():
  midi_file = midi.MidiFile(sys.argv[1])
  waterfall = Waterfall(piano_input_mock.PianoInput(),
          piano_output.PianoOutput(), midi_file)
  waterfall.Continue(slowdown_factor=1)


if __name__ == '__main__':
  main()

