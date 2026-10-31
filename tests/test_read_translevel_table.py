#!/usr/bin/env python3
"""Checks for the translevel table reader."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from read_translevel_table import entries


class TranslevelTests(unittest.TestCase):
    def test_entries(self):
        data = bytearray(0x10000)
        data[0xD1F0] = 0x30
        data[0xD001] = 0x05
        self.assertEqual(entries(data), {0x1F0: 0x30, 1: 0x05})


if __name__ == '__main__':
    unittest.main()
