#!/usr/bin/env python3
"""Checks the exit scanner helper."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from scan_level_exits import filter_exits


class ScanTests(unittest.TestCase):
    def test_filter(self):
        table = {3: [{'dest': 0x129, 'screen': 1}], 4: [{'dest': 2, 'screen': 0}], 5: []}
        self.assertEqual(filter_exits(table, 0x129), [(3, {'dest': 0x129, 'screen': 1})])


if __name__ == '__main__':
    unittest.main()
