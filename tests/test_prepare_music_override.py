"""Bounded checks for the room music override.

The fixture is a synthetic image with one level block that holds a music
object, so the checks do not need a game image. A level stream starts at
offset 5, so the fixture pads the first five bytes.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import prepare_music_override as override
from restore_star_world_1 import lorom

BLOCK = 0x080000
POINTER = 0x108008


def image(body):
    """Return an image whose room 0x43 holds the given level stream."""
    rom = bytearray(0x200000)
    count = len(body) - 1
    blob = (b'STAR' + count.to_bytes(2, 'little') +
            (count ^ 0xFFFF).to_bytes(2, 'little') + body)
    rom[BLOCK:BLOCK + len(blob)] = blob
    slot = lorom(0x05E000) + 0x43 * 3
    rom[slot:slot + 3] = POINTER.to_bytes(3, 'little')
    return rom


def with_music(song):
    return bytes(5) + bytes([0x40, 0x60, song + 1, 0xFF])


def without_music():
    return bytes(5) + bytes([0x15, 0xF1, 0x20, 0xFF])


class PlanTests(unittest.TestCase):
    def test_plan_reports_the_song_before_and_after(self):
        patch = override.plan(image(with_music(0x44)), 0x43, 0x41)
        self.assertEqual(patch['before'], '44')
        self.assertEqual(patch['after'], '41')
        self.assertEqual(patch['object_before'], '406045')
        self.assertEqual(patch['object_after'], '406042')

    def test_apply_writes_the_new_song(self):
        rom = image(with_music(0x44))
        override.prepare(rom, [(0x43, 0x41)])
        self.assertEqual(override.plan(rom, 0x43, 0x41)['before'], '41')

    def test_the_level_block_size_does_not_change(self):
        rom = image(with_music(0x44))
        before = bytes(rom[BLOCK - 8:BLOCK + 8])
        override.prepare(rom, [(0x43, 0x41)])
        after = bytes(rom[BLOCK - 8:BLOCK + 8])
        self.assertEqual(len(before), len(after))
        self.assertEqual(before[:5], after[:5])

    def test_a_room_without_a_music_object_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '0 music objects'):
            override.plan(image(without_music()), 0x43, 0x41)

    def test_a_room_without_a_pointer_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no level pointer'):
            override.plan(bytearray(0x200000), 0x43, 0x41)


if __name__ == '__main__':
    unittest.main()
