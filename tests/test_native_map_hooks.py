#!/usr/bin/env python3
"""Checks the native map start and node hooks stay in the runtime source."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NativeMapHookTests(unittest.TestCase):
    def test_hooks(self):
        text = (ROOT / 'recomp/native_seven.c').read_text()
        self.assertIn('bm_yoshi_start_override', text)
        self.assertIn('g_ram[0x1f17] = 104', text)
        self.assertIn('g_ram[0x1f1f] = 6', text)
        self.assertIn('bm_mazo_map_node_override', text)
        self.assertIn('g_ram[0xd1f0] = 0xb4', text)
        self.assertIn('BM_YOSHI_START', text)
        self.assertIn('BM_MAZO_190_NODE', text)
        self.assertIn('bm_seven_return_override', text)
        self.assertIn('BM_SEVEN_RETURN', text)
        self.assertIn('g_ram[0x100] = 0x0b', text)


if __name__ == '__main__':
    unittest.main()
