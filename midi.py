"""Classes for reading MIDI files.

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

import struct


def ReadInt32(b):
  return struct.unpack('>i', b)[0]


def ReadInt24(b):
  return struct.unpack('>i', '\0'+b)[0]


def ReadInt16(b):
  return struct.unpack('>h', b)[0]


def ReadInt8(b):
  return ord(b[0])


def ReadVarLen(b):
  """Reads a MIDI variable-length int.
  Returns a tuple specifying the int, and the number of bytes read."""
  val = ReadInt8(b[0])
  bytes_read = 1
  if val & 0x80:
    val &= 0x7f
    while True:
      next_byte = ReadInt8(b[bytes_read])
      bytes_read += 1
      val = (val << 7) | (next_byte & 0x7f)
      if not next_byte & 0x80:
        break
  return val, bytes_read


class MidiChunk(object):
  """A chunk is either a file header, or a music track.
  Each of these is implemented as a subclass (MidiHeader and MidiTrack,
  respectively).

  Attributes:
    id: 4-byte string identifying the type of chunk:
        'MThd' for header, 'MTrk' for track.
    data: string containing the chunk data.
  """

  def __init__(self, file):
    """Read the chunk from a file stream."""
    self.id = file.read(4)
    byte_len = ReadInt32(file.read(4))
    print 'Reading chunk of type [%s], length %d' % (self.id, byte_len)
    self.data = file.read(byte_len)

  def Validate(self):
    """Throws an assertion if the chunk has invalid structure."""
    pass


class MidiHeader(MidiChunk):
  def __init__(self, file):
    super(MidiHeader, self).__init__(file)
    self.format = ReadInt16(self.data[0:2])
    self.num_tracks = ReadInt16(self.data[2:4])
    print 'This is a Format %d MIDI file' % self.format
    division = ReadInt16(self.data[4:])
    if division & 0x8000:
      self.ticks_per_note = (division & 0x00ff)
      self.notes_per_sec = (division & 0x7f00) >> 8
      print 'Ticks per frame: %d' % self.ticks_per_note
      print 'Frames per sec: %d' % self.notes_per_sec
    else:
      self.ticks_per_note = division
      self.notes_per_sec = 2
      print 'Ticks per quarter note: %d' % self.ticks_per_note

  def Validate(self):
    assert self.id == 'MThd'


class MidiTrack(MidiChunk):
  """Contains a music track (a list of events).

  Attributes (in addition to inherited attributes):
    events: List of MidiEvent objects.
  """

  def __init__(self, file, skip_ignores=True):
    super(MidiTrack, self).__init__(file)
    self.events = []
    bytes_read = 0
    prev_event = None
    while bytes_read < len(self.data):
      event = MidiEvent()
      if skip_ignores:
        bytes_read += event.ReadSkippingIgnores(self.data[bytes_read:],
                                                prev_event)
      else:
        bytes_read += event.Read(self.data[bytes_read:], prev_event)
      if len(self.events) == 0:
        event.delta += 300  # Add a delay before the song starts.
      self.events.append(event)
      prev_event = event
    print 'Read track with %d events' % len(self.events)

  def Validate(self):
    assert self.id == 'MTrk'


class MidiEvent(object):
  """Represents a single event, such as note-on or note-off.

  Attributes:
    delta: (int) Time since previous event.
    note: (int) MIDI code for note pressed. 0-255.
    volume: (int) Volume (velocity), 0-255
    cmd: (int) MIDI command. 0x80: note off, 0x90: note on.
    raw_cmd: (int) Actual MIDI command byte, including channel.
    channel: (int) Midi channel for this event.
    ignore_me: (bool) If true, this is a system event or some other
        uninteresting stuff.
  """

  def __init__(self):
    self.delta = -1
    self.note = -1
    self.volume = -1
    self.cmd = -1
    self.raw_cmd = -1
    self.channel = -1
    self.ignore_me = True

  def __str__(self):
    if self.cmd == 0xff:
      return 'Delta %5d   Cmd %02x   Type %02x   ' % (
          self.delta, self.cmd, self.type)
    return 'Delta %5d   Channel %2x   Cmd %s   Note %s   Volume %2x  %s' % (
        self.delta, self.channel, MidiEvent.CmdName(self.cmd),
        MidiEvent.NoteName(self.note), self.volume,
        '(IGNORE)' if self.ignore_me else '')

  @staticmethod
  def NoteName(note):
    NAMES = [
        'C-', 'C#', 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']
    return '%s%d' % (NAMES[note%12], note/12 - 1)

  @staticmethod
  def CmdName(cmd):
    NAMES = {0x80: 'NoteOFF', 0x90: 'NoteON '}
    if cmd in NAMES:
      return NAMES[cmd]
    return '  %02X   ' % cmd

  def ReadSkippingIgnores(self, b, prev_event):
    """Read event from byte string, skipping ignore_me events, but keeping
    their delta. Returns total number of bytes read."""
    total_bytes_read = self.Read(b, prev_event)
    while self.ignore_me and total_bytes_read < len(b):
      total_bytes_read += self.Read(b[total_bytes_read:], self)
    return total_bytes_read

  def Read(self, b, prev_event):
    """Read event from byte string. Returns the number of bytes read."""
    self.delta, bytes_read = ReadVarLen(b)
    self.raw_cmd = ReadInt8(b[bytes_read])
    bytes_read += 1

    # Parse ordinary events
    self.ignore_me = False
    if not self.raw_cmd & 0x80:
      # Push back the command, as we are actually using the command from the
      # previous event.
      bytes_read -= 1
      self.raw_cmd = prev_event.raw_cmd

    self.cmd = self.raw_cmd

    if self.cmd == 0xff:
      self.ignore_me = True
      self.type = ReadInt8(b[bytes_read])
      bytes_read += 1
      cmd_len, l = ReadVarLen(b[bytes_read:])
      bytes_read += l
      self.data = b[bytes_read:bytes_read+cmd_len]
      bytes_read += cmd_len  # Skip entire message
      return bytes_read
    if self.cmd == 0xf0:
      self.ignore_me = True
      while not (ReadInt8(b[bytes_read]) == 0xF7):
        bytes_read += 1
      return bytes_read

    if (self.cmd & 0xf0) in (0xd0, 0xc0):
      self.ignore_me = True
      bytes_read += 1  # Skip one byte
    elif (self.cmd & 0xf0) in (0x80, 0x90):
      # Note-off (0x80) or note-on (0x90) command
      self.channel = self.cmd & 0x0f;
      self.cmd = self.cmd & 0xf0;
      self.note = ReadInt8(b[bytes_read])
      self.volume = ReadInt8(b[bytes_read + 1])
      bytes_read += 2
      if self.volume == 0:
        self.cmd = 0x80  # Some midi files use volume 0 to indicate note-off
    else:
      # Unknown command - ignored
      bytes_read += 2
      self.ignore_me = True

    return bytes_read


class MidiFile(object):
  """Represents a MIDI file loaded in memory.

  Attributes:
    header: The header chunk.
    tracks: List of (non-header) tracks.
    tempo_map: List of (time, tempo) where |time| is in ticks and |tempo| is the
        number of ticks per second. Each tempo is valid starting at the time
        specified by |time|.
  """

  def __init__(self, fname):
    """Read a midi file to memory."""
    with open(fname) as file:
      self.header = MidiHeader(file)
      self.header.Validate()
      self.tracks = []
      self.tempo_map = [
          (0, self.header.ticks_per_note*self.header.notes_per_sec)]
      print 'Midi file contains %d tracks' % self.header.num_tracks
      for i in xrange(self.header.num_tracks):
        skip_ignores = True
        if self.header.format == 1 and i == 0:
          skip_ignores = False
        track = MidiTrack(file, skip_ignores=skip_ignores)
        track.Validate()
        self.tracks.append(track)
      if self.header.format == 1:
        tempo_map_track = self.tracks[0]
        cur_time = 0
        for event in tempo_map_track.events:
          cur_time += event.delta
          if event.cmd == 0xff and event.type == 0x51:
            tempo = ReadInt24(event.data) / 1.e6
            notes_per_sec = 1.0 / tempo
            print 'Time %d: Found tempo %.6f' % (cur_time, tempo)
            print 'Deduced notes per sec: %.2f' % notes_per_sec
            self.tempo_map.append(
                (cur_time, self.header.ticks_per_note*notes_per_sec))
    print 'Tempo map:'
    for start_time, tempo in self.tempo_map:
      print '  %7d ticks: Tempo=%f' % (start_time, tempo)

  def GetTicksPerSec(self, time):
    """Get the tempo (in ticks per sec) at the specified time (in ticks)."""
    for start_time, tempo in self.tempo_map[::-1]:
      if start_time <= time:
        return tempo
    return self.tempo_map[0][1]

