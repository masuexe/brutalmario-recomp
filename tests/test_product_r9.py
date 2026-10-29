#!/usr/bin/env python3
"""Review gates for the room 151 music retarget (slot A4)."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import lorom, sha

R8_SHA = '4a45955c65c30495940b69fbd4675ed41574e3ae37c4471ecc80c32adf2bd55f'
PARAM = lorom(0x5BBCFF) + 0x3F4


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-product-r9/rom.sfc').exists(),
                     'requires the built r9 target')
class ProductR9Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r9.json').read_text())
        cls.rom = (ROOT / 'local/restoration/demo11-native-product-r9/rom.sfc').read_bytes()
        cls.r8 = (ROOT / 'local/restoration/demo11-native-product-r8/rom.sfc').read_bytes()

    def test_target_rom_identity(self):
        verify(self.rom, self.cfg['output'], 'r9 ROM')
        self.assertEqual(self.cfg['id'], 'demo11-native-product-r9')

    def test_single_music_parameter_delta(self):
        self.assertEqual(sha(self.r8), R8_SHA)
        self.assertEqual(self.r8[PARAM - 2:PARAM], b'\x40\x60')
        self.assertEqual(self.r8[PARAM], 0x61)
        expected = bytearray(self.r8)
        expected[PARAM] = 0xA5
        self.assertEqual(bytes(expected), self.rom)
        self.assertEqual(self.rom[PARAM], 0xA5)

    def test_slot_a4_matches_official_demo_1_1(self):
        official = (ROOT / 'local/content-versions/demo-1-1/rom.sfc').read_bytes()

        def block(rom, slot):
            o = lorom(0x0FE000) + slot * 3
            p = int.from_bytes(rom[o:o + 3], 'little')
            f = lorom(p)
            length = int.from_bytes(rom[f:f + 2], 'little')
            return p, rom[f:f + 2 + length]

        self.assertEqual(block(self.rom, 0xA4), block(official, 0xA4))

    def test_pack_banks_are_unique(self):
        import native_sprite_gap as gap
        packs = gap.packs('demo11-native-product-r9')
        banks = [int(p['address'], 16) >> 16 for p in packs]
        self.assertEqual(len(banks), len(set(banks)))


if __name__ == '__main__':
    unittest.main()
