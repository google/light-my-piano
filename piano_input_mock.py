"""Mock version of piano_input.PianoInput.
For use when testing on a computer without an actual MIDI input.

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

import Queue
import thread
import time

class PianoInput(object):
  def __init__(self):
    self.user_input = Queue.Queue()
    thread.start_new_thread(self.GetPianoSignal, ())

  def ClearInput(self):
    while not self.user_input.empty():
      self.user_input.get()

  def GetPianoSignal(self):
    while True:
      try:
        print "Important notes: '-'=36 '+'=40  '<'=48 'Play'=50 '>'=52"
        note = int(raw_input("<note> (e.g. '37'): "))
        self.user_input.put((note, 50))
        time.sleep(1)
        self.user_input.put((note, 0))
      except:
        print "Bad input"

