#!/usr/bin/env python3
"""Checks for the green orb bounds helper."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from find_green_orb import green_bounds


class GreenOrbTests(unittest.TestCase):
    def test_bounds(self):
        rows = [[(0, 0, 0)] * 10 for _ in range(10)]
        rows[2][3] = (0, 255, 0)
        rows[4][6] = (0, 200, 0)
        self.assertEqual(green_bounds(rows), (3, 2, 6, 4, 2))

    def test_none(self):
        rows = [[(0, 0, 0)] * 10 for _ in range(10)]
        self.assertIsNone(green_bounds(rows))


if __name__ == '__main__':
    unittest.main()
