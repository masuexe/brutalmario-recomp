#!/usr/bin/env python3
"""Checks for the VRAM graphics slice finder."""
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from check_vram_graphics import find_hits


class VramGraphicsTests(unittest.TestCase):
    def test_find_at_offset(self):
        data = random.Random(0).randbytes(4096)
        vram = b'\xAA' * 100 + data + b'\xBB' * 100
        self.assertEqual(find_hits(data, vram), [2148])

    def test_slice_only_match(self):
        data = random.Random(0).randbytes(4096)
        vram = bytearray(b'\x00' * 64)
        vram += data[2048:2112]
        vram += b'\x00' * 64
        self.assertEqual(find_hits(data, bytes(vram)), [64])


if __name__ == '__main__':
    unittest.main()
