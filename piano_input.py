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
import time
import usb.core
import usb.util

class PianoInput(object):
  def __init__(self):
    self.user_input = Queue.Queue()
    endpoint_address = self._attach_device()
    thread.start_new_thread(self.GetPianoSignal, (endpoint_address, ))

  def _attach_device(self):
    self.dev = usb.core.find(custom_match=PianoInput.IsMidiUsbDevice)
    if not self.dev:
      raise IOError('Could not find a USB MIDI Streaming device')
    print self.dev

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

    self.dev.set_configuration()

    # Determine the endpoint address for MIDI Input.
    iface = PianoInput.GetMidiStreamingInterface(self.dev)
    endpoint_address = None
    for endpoint in iface.endpoints():
      if endpoint.bEndpointAddress & 0x80:
        # Found input endpoint.
        endpoint_address = endpoint.bEndpointAddress
        break
    if not endpoint_address:
      raise IOError('Cannot find MIDI Input endpoint in USB MIDI device.')

    return endpoint_address

  @staticmethod
  def IsMidiUsbDevice(dev):
    return PianoInput.GetMidiStreamingInterface(dev) is not None

  @staticmethod
  def GetMidiStreamingInterface(dev):
    for cfg in dev:
      iface = usb.util.find_descriptor(cfg, bInterfaceClass=0x01,
                                       bInterfaceSubClass=0x03)
      if iface:
        return iface
    return None 

  def GetNote(self, note):
    NAMES = ['C-', 'C#', 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-',
             'A#', 'B-']
    return '%s%d' % (NAMES[note % 12], note // 12)

  def ClearInput(self):
    while not self.user_input.empty():
      self.user_input.get()

  def GetPianoSignal(self, endpoint_address):
    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    while True:
      try:
        ret = self.dev.read(endpoint_address, 32, 10000)
      except usb.core.USBError:
        # Attempt to reconnect
        endpoint_address = None
        while not endpoint_address:
          try:
            print('Attempting to reconnect...')
            endpoint_address = self._attach_device()
          except Exception as ex:
            print('Connection failed (%s), waiting 1 second...' % ex)
            time.sleep(1.0)
      midiCmd = ret[1]
      if (midiCmd == NOTE_ON or midiCmd == NOTE_OFF):
          note = ret[2]
          volume = ret[3]
          if midiCmd == NOTE_OFF:
            volume = 0
          print note, (midiCmd, self.GetNote(note).lower(), volume)
          self.user_input.put((note, volume))
