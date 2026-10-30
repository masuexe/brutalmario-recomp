#!/usr/bin/env python3
"""Checks for the falling-WRAM scanner."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from find_falling_wram import scan


class FallingWramTests(unittest.TestCase):
    def test_monotonic_drop(self):
        data = [bytearray(0x2000) for _ in range(5)]
        for index, value in enumerate((10, 8, 6, 4, 2)):
            data[index][0x1000] = value
        for index, value in enumerate((1, 2, 3, 4, 5)):
            data[index][0x1100] = value
        found = scan(data, 0x0800, 0x2000, 2)
        self.assertEqual(found, [(8, 0x1000, 10, 2)])

    def test_threshold(self):
        data = [bytearray(0x2000) for _ in range(4)]
        for index, value in enumerate((5, 4, 4, 3)):
            data[index][0x1200] = value
        self.assertEqual(scan(data, 0x0800, 0x2000, 5), [])


if __name__ == '__main__':
    unittest.main()
