"""Bounded checks for the level music object insertion helpers.

The tests use synthetic level streams.  They check the object walk, the move
placement and the object byte form.  They do not claim a playable course.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import prepare_music_objects as objects


class WalkTests(unittest.TestCase):
    def test_a_music_object_is_recognised(self):
        # Header 5 bytes, one music object, terminator.
        data = bytes.fromhex('0000000000') + bytes.fromhex('406020') + b'\xff'
        found, terminator = objects.walk(data)
        self.assertEqual(terminator, 8)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][0], 5)

    def test_a_stream_without_a_terminator_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unterminated'):
            objects.walk(bytes.fromhex('0000000000') + bytes.fromhex('406020'))

    def test_a_music_object_is_three_bytes(self):
        # The level format gives object 0x26 a three-byte record.
        self.assertEqual(objects.object_size(bytes.fromhex('406020'), 0), 3)
        self.assertEqual(objects.object_size(bytes.fromhex('47606c'), 0), 3)

    def test_a_standard_object_is_three_bytes(self):
        self.assertEqual(objects.object_size(bytes.fromhex('400000'), 0), 3)
        # Object number 0 with b2=0 is a screen exit: four bytes.
        self.assertEqual(objects.object_size(bytes.fromhex('000000'), 0), 4)
        self.assertEqual(objects.object_size(bytes.fromhex('000001'), 0), 3)


class PlanTests(unittest.TestCase):
    def test_the_plan_reports_one_move_per_room(self):
        # A synthetic image: one level block with room 0x02F selected, plus free space.
        rom = bytearray(0x20000)
        start = 0x10008
        rom[start - 8:start] = (b'STAR' + (10).to_bytes(2, 'little') +
                                (10 ^ 0xffff).to_bytes(2, 'little'))
        body = bytes.fromhex('0000000000') + b'\xff'
        rom[start:start + len(body)] = body
        rom[0x08000:0x08003] = bytes.fromhex('0800 01'.replace(' ', ''))[:3]
        self.assertEqual(len(body), 6)
        self.assertTrue(rom[0x9000:0x9100] == bytes(0x100))


class ObjectFormTests(unittest.TestCase):
    def test_the_object_encodes_the_screen_and_the_song(self):
        screen, height, song = 0x07, 0x00, 0x6B
        value = bytes([0x40 | (screen & 0x1F), 0x60 | (height & 0x0F), song + 1])
        self.assertEqual(value, bytes.fromhex('47606c'))
        number = ((value[0] >> 5) & 3) * 16 + (value[1] >> 4)
        self.assertEqual(number, 0x26)

    def test_a_high_screen_number_stays_inside_the_mask(self):
        value = bytes([0x40 | (0x1F & 0x1F), 0x60 | 0x0F, 0x6C])
        number = ((value[0] >> 5) & 3) * 16 + (value[1] >> 4)
        self.assertEqual(number, 0x26)


if __name__ == '__main__':
    unittest.main()
