import Queue

class PianoInput(object):
  """Mock version of piano_input.PianoInput, for use when testing on a computer
  without an actual MIDI input."""
  def __init__(self):
    self.user_input = Queue.Queue()
    for note in xrange(37,60):
      self.user_input.put((note, 45))

