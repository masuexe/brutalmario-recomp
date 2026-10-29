#!/usr/bin/env python3
"""Review gates for the r13 product candidate without the C2 type-3 record."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import lorom, sha

R12_SHA = 'd29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552'
C2_OFFSET = 1609362
C2_BEFORE = bytes.fromhex('0000ffffffffffff218001218001ffff')
C2_AFTER = bytes.fromhex('03ffffffffffffff30ddcd34ddcdffff')


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-product-r13/rom.sfc').exists(),
                     'requires the built r13 target')
class ProductR13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r13.json').read_text())
        cls.rom = (ROOT / 'local/restoration/demo11-native-product-r13/rom.sfc').read_bytes()
        cls.r12 = (ROOT / 'local/restoration/demo11-native-product-r12/rom.sfc').read_bytes()

    def test_target_identity(self):
        verify(self.rom, self.cfg['output'], 'r13 ROM')
        self.assertEqual(self.cfg['id'], 'demo11-native-product-r13')
        self.assertEqual(sha(self.r12), R12_SHA)

    def test_rom_equals_r12_without_the_c2_record(self):
        self.assertEqual(len(self.rom), len(self.r12))
        diffs = [i for i in range(len(self.rom)) if self.rom[i] != self.r12[i]]
        expected = [C2_OFFSET + i for i in range(len(C2_BEFORE))
                    if C2_BEFORE[i] != C2_AFTER[i]]
        self.assertEqual(diffs, expected)
        self.assertEqual(self.rom[C2_OFFSET:C2_OFFSET + len(C2_BEFORE)], C2_BEFORE)
        self.assertEqual(self.r12[C2_OFFSET:C2_OFFSET + len(C2_AFTER)], C2_AFTER)

    def test_c2_is_absent_everywhere(self):
        text = json.dumps(self.cfg)
        self.assertNotIn('TYPE3_C2', text)
        self.assertNotIn('type3-c2.bin', text)
        self.assertNotIn(str(C2_OFFSET), text)
        self.assertFalse((ROOT / 'local/restoration/demo11-native-product-r13/type3-c2.bin').exists())

    def test_c0_and_c1_records_remain(self):
        table = 0x318272
        for slot, value in ((0xC0, '03ffffffffffffffe686cbea86cbffff'),
                            (0xC1, '03ffffffffffffff17aecc1baeccffff'),
                            (0xC2, '0000ffffffffffff218001218001ffff')):
            offset = lorom(table + slot * 16)
            self.assertEqual(self.rom[offset:offset + 16].hex(), value)
        packs = {p['variable'] for p in self.cfg['native_sprite_gap']['extra_packs']}
        self.assertIn('BM_SEVEN_CODE_PACK_TYPE3_C0', packs)
        self.assertIn('BM_SEVEN_CODE_PACK_TYPE3_C1', packs)

    def test_other_product_adaptations_remain(self):
        kinds = {a.get('kind') for a in self.cfg.get('native_adaptations', [])}
        self.assertEqual(kinds, {'room-music-override', 'sprite-9c-phase-music'})


if __name__ == '__main__':
    unittest.main()
