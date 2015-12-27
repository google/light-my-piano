import Queue
import thread
import usb.core

class PianoInput(object):
  """Class for handling input from a piano connected through a USB MIDI."""
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
