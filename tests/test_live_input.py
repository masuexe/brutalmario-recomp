#!/usr/bin/env python3
"""Checks for the live input appender."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from live_input import append


class LiveInputTests(unittest.TestCase):
    def test_append(self):
        with tempfile.TemporaryDirectory() as name:
            play = Path(name)
            (play / 'cheats.script').write_text('dump a\n')
            append(play, ['press right 10', 'dump b'])
            self.assertEqual((play / 'cheats.script').read_text(), 'dump a\npress right 10\ndump b\n')


if __name__ == '__main__':
    unittest.main()
