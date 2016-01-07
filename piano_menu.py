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

import os
import pickle
import sys

import midi
import piano_output
import piano_input
import piano_input_mock
import waterfall


def GetMidiFiles(path="./"):
  return sorted(
          filter(lambda filename: filename.endswith('.mid'),
                 os.listdir('./')),
          key=lambda f: f.lower())


class Menu(object):
  def __init__(self):
    self.slowdown = 1.0
    self.songs = GetMidiFiles()
    self.current_song = 0
    self.piano_display = piano_output.PianoOutput()
    self.piano_input_obj = piano_input.PianoInput()
    midi_file = midi.MidiFile(self.songs[self.current_song])
    self.waterfall = waterfall.Waterfall(self.piano_input_obj,
                                         self.piano_display, midi_file)
    self.high_scores = self.LoadHighScores()

  def LoadHighScores(self):
    try:
      f = open('highscores.pickle', 'r')
      self.high_scores = pickle.load(f)
    except IOError:
      print 'Warning: Could not open high scores file, creating new.'
      self.high_scores = {}

  def SaveHighScores(self):
    try:
      f = open('highscores.pickle', 'w')
      pickle.dump(self.high_scores, f)
    except IOError:
        print 'Error: Failed to save high scores file highscores.pickle'

  def CheckHighScore(self, score):
    current_song_name = self.songs[self.current_song]
    if current_song_name in self.high_scores:
      self.piano_display.SetKeyText(
          65, self.piano_display.KEYBOARD_HEIGHT + 200,
          "Previous best: %.0f" % self.high_scores[current_song_name][0])

    if (current_song_name in self.high_scores and
        self.high_scores[current_song_name][0] >= score):
      self.piano_display.SetKeyText(
          65, self.piano_display.KEYBOARD_HEIGHT + 150,
          "Your score: %.0f" % score)
      return  # No new high score.

    self.piano_display.SetKeyText(
        65, self.piano_display.KEYBOARD_HEIGHT + 150,
        "New High Score: %.0f" % score)

    self.piano_display.SetKeyText(
        65, self.piano_display.KEYBOARD_HEIGHT + 100,
        "Enter your name:")

    k = keyboard.Keyboard(self.piano_input_obj, self.piano_display)
    your_name = k.GetTypedString()
    self.high_scores[current_song_name] = (score, your_name)
    self.SaveHighScores()

  def MainLoop(self):
    self.piano_input_obj.ClearInput()
    while True:
      self.piano_display.Clear()
      self.piano_display.DrawPiano(False)
      self.piano_display.SetKeyText(36, 20, u"\u2212")
      self.piano_display.SetKeyText(40, 20, u"\u2795")
      self.piano_display.SetKeyText(38, self.piano_display.KEYBOARD_HEIGHT + 50,
                                    "    Slowdown")
      self.piano_display.SetKeyText(38, self.piano_display.KEYBOARD_HEIGHT + 25,
                                    str(self.slowdown))

      self.piano_display.SetKeyText(36 + 12, 20, "<")
      self.piano_display.SetKeyText(40 + 12, 20, ">")
      self.piano_display.SetKeyText(38 + 12,
                                    self.piano_display.KEYBOARD_HEIGHT + 50,
                                    "Select Song")
      self.piano_display.SetKeyText(38 + 12,
                                    self.piano_display.KEYBOARD_HEIGHT + 25,
                                    self.songs[self.current_song][:-4])

      self.piano_display.SetKeyText(38 + 12, 20, u"\u266a")

      self.piano_display.Refresh()
      while not self.piano_input_obj.user_input.empty():
        user_cmd = self.piano_input_obj.user_input.get()
        if user_cmd[1] > 0:
          if user_cmd[0] == 36:
            self.slowdown = max(0.1, self.slowdown - 0.1)
          if user_cmd[0] == 40:
            self.slowdown = self.slowdown + 0.1
          if user_cmd[0] == 40 + 12:
            self.current_song =  (self.current_song + 1) % len(self.songs)
            midi_file = midi.MidiFile(self.songs[self.current_song])
            self.waterfall = waterfall.Waterfall(self.piano_input_obj,
                                                 self.piano_display, midi_file)
          if user_cmd[0] == 36 + 12:
            self.current_song = (self.current_song + len(self.songs) - 1) % (
                len(self.songs))
            midi_file = midi.MidiFile(self.songs[self.current_song])
            self.waterfall = waterfall.Waterfall(self.piano_input_obj,
                                                 self.piano_display, midi_file)
          if user_cmd[0] == 38 + 12:
            score = self.waterfall.Continue(self.slowdown)
            self.CheckHighScore(score)


def main():
  menu = Menu()
  menu.MainLoop()


if __name__ == "__main__":
  main()

