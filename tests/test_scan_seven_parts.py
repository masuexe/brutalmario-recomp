#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from scan_seven_parts import parts

class ScanSevenPartsTests(unittest.TestCase):
    def test_parts(self):
        data = bytearray(0x20000)
        data[0x1AB9E + 3] = 0x2A
        data[0x14C8 + 3] = 8
        data[0xD8 + 3] = 0x8F
        data[0x14D4 + 3] = 1
        data[0x1528 + 3] = 64
        self.assertEqual(parts(data), [(3, 0x18F, 64)])

if __name__ == '__main__':
    unittest.main()
