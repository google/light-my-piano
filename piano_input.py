"""Class for handling input from a piano connected through a USB MIDI.

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
import usb.core

class PianoInput(object):
  def __init__(self):
    self.user_input = Queue.Queue()
    self.dev = usb.core.find(idVendor=0xfc08, idProduct=0x0101)
    print self.dev
    print self.dev[0].interfaces()[1].endpoints()
    self.reattach0 = False
    self.reattach1 = False
    # detach from kernel device
    if self.dev.is_kernel_driver_active(0):
        print "detaching...0"
        self.reattach0 = True
        self.dev.detach_kernel_driver(0)
    if self.dev.is_kernel_driver_active(1):
        print "detaching...1"
        self.reattach1 = True
        self.dev.detach_kernel_driver(1)

    #In a loop, read midi commands from USB
    self.dev.set_configuration()
    thread.start_new_thread(self.GetPianoSignal, tuple())

  def GetNote(self, note):
    NAMES = [ 'C-', 'C#', 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']
    return '%s%d'%(NAMES[note%12], note/12)

  def ClearInput(self):
    while not self.user_input.empty():
      self.user_input.get()

  def GetPianoSignal(self):
    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    while True:
      ret= self.dev.read(0x81, 32, 10000)
      midiCmd = ret[1]
      if (midiCmd == NOTE_ON or midiCmd == NOTE_OFF):
          note = ret[2]
          volume = ret[3]
          print note, (midiCmd, self.GetNote(note).lower(), volume)
          self.user_input.put((note, volume))
