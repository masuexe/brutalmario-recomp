"""Bounded checks for the Demo 1-1 song parser.

The reference material is the 100 extracted payloads in local/music/demo-1-1.
These checks use synthetic payloads, so they do not need that tree.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import decode_song as song
import parse_song as structure


def payload(patterns, track_bytes, first=0x5467, length=0x80):
    """Build a synthetic payload with one pattern and one track."""
    data = bytearray(length)
    data[0:2] = first.to_bytes(2, 'little')
    data[2:4] = (0).to_bytes(2, 'little')
    data[4:6] = (0x00FF).to_bytes(2, 'little')
    data[6:8] = (0x5402).to_bytes(2, 'little')
    data[0x40:0x40 + len(track_bytes)] = track_bytes
    track = 0x5400 + 0x40
    offset = first - 0x5400
    data[offset:offset + 2] = track.to_bytes(2, 'little')
    return bytes(data)


class StructureTests(unittest.TestCase):
    def test_pattern_pointer_leaves_the_payload(self):
        data = bytearray(0x80)
        data[0:2] = (0xFFFF).to_bytes(2, 'little')
        with self.assertRaisesRegex(ValueError, 'leaves the payload'):
            structure.parse(bytes(data))

    def test_a_single_pattern_reports_one_track(self):
        data = payload(None, bytes.fromhex('00'))
        patterns = structure.parse(data)
        self.assertEqual(len(patterns), 1)
        self.assertEqual(len(patterns[0][1]), 1)


class DecodeTests(unittest.TestCase):
    def test_a_zero_byte_is_a_phrase_break(self):
        # A 0x00 byte separates phrases. It does not end the track, so the
        # decoder reports it as a break event.
        data = payload(None, bytes.fromhex('00 06 90 00'))
        events = song.decode_track(data, 0x5440)
        self.assertEqual(events[0][3], ('break',))
        self.assertEqual(events[1][1], 6)
        self.assertEqual(events[1][2], 0x90)

    def test_a_timed_note_is_read(self):
        # A duration byte takes one following byte as its pitch, including a
        # byte above 0x7F. The track region ends after that pair.
        data = payload(None, bytes.fromhex('06 90'))
        events = song.decode_track(data, 0x5440)
        timed = [event for event in events if event[1]]
        self.assertTrue(timed)
        self.assertEqual(timed[0][1], 6)
        self.assertEqual(timed[0][2], 0x90)

    def test_a_rest_uses_pitch_80(self):
        data = payload(None, bytes.fromhex('06 80'))
        events = song.decode_track(data, 0x5440)
        timed = [event for event in events if event[1]]
        self.assertEqual(timed[0][2], 0x80)

    def test_an_instrument_command_takes_one_argument(self):
        data = payload(None, bytes.fromhex('c7 24 06 90 00'))
        events = song.decode_track(data, 0x5440)
        self.assertEqual(events[0][3], (0xC7, 0x24))

    def test_a_subroutine_call_takes_three_arguments(self):
        data = payload(None, bytes.fromhex('e9 40 54 08 00'))
        events = song.decode_track(data, 0x5440)
        self.assertEqual(events[0][3][0], 0xE9)

    def test_a_cursor_below_the_base_returns_no_events(self):
        # A cursor below the payload base reads no byte, so the track is empty.
        data = payload(None, bytes.fromhex('00'))
        self.assertEqual(song.decode_track(data, 0x9999), [])

if __name__ == '__main__':
    unittest.main()
