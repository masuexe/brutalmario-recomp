#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from compare_mazo_event_table import collisions

class CompareEventTests(unittest.TestCase):
    def test_collisions(self):
        table = [0, 0x30, 1, 0x30, 2]
        self.assertEqual(collisions(table), [1, 3])

if __name__ == '__main__':
    unittest.main()
