#!/usr/bin/env python3
"""Regression checks for the bounded level exit parser."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from inspect_level_exits import exits

TARGET = 'demo11-native-product-r13'


@unittest.skipUnless((ROOT / 'local/restoration' / TARGET / 'rom.sfc').exists(),
                     'requires the r13 product target')
class LevelExitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()

    def screen_exits(self, room):
        return sorted((e['screen'], e['dest'], e['secondary'])
                      for e in exits(self.rom, room)['exits']
                      if e['kind'] == 'screen_exit')

    def test_live_verified_rooms(self):
        expected = {
            0x11F: [(2, 0x039, 0), (3, 0x182, 0)],
            0x114: [(0x11, 0x114, 1)],
            0x121: [(4, 0x1D7, 0)],
            0x123: [(0, 0x123, 0), (4, 0x042, 0)],
            0x124: [(2, 0x027, 0), (3, 0x027, 0), (0x0B, 0x029, 0), (0x0D, 0x030, 0)],
            0x11B: [(0x0B, 0x053, 0)],
            0x11C: [(9, 0x041, 0), (0x0A, 0x11C, 1)],
            0x11E: [(0x13, 0x037, 0)],
            0x129: [(1, 0x045, 0), (2, 0x03F, 1), (3, 0x03E, 0)],
        }
        for room, want in expected.items():
            self.assertEqual(self.screen_exits(room), want, hex(room))

    def test_bounded_streams(self):
        for room in (0x11F, 0x114, 0x11B, 0x11C, 0x11E, 0x129, 0x121, 0x123, 0x124):
            info = exits(self.rom, room)
            self.assertGreater(info['size'], 0)
            self.assertLessEqual(info['size'], 0x8000)


if __name__ == '__main__':
    unittest.main()
