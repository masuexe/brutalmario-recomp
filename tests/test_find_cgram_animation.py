#!/usr/bin/env python3
"""Checks for the CGRAM animation helper."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from find_cgram_animation import animated_entries


class CgramAnimationTests(unittest.TestCase):
    def test_entry(self):
        base = bytes([0, 0, 1, 0, 2, 0])
        frames = [('a', bytes([0, 0, 5, 0, 2, 0])), ('b', bytes([0, 0, 9, 0, 2, 0]))]
        self.assertEqual(animated_entries(base, frames), {1: {'a': 5, 'b': 9}})

    def test_static(self):
        base = bytes([0, 0, 1, 0])
        self.assertEqual(animated_entries(base, [('a', base)]), {})


if __name__ == '__main__':
    unittest.main()
