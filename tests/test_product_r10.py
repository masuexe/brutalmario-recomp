#!/usr/bin/env python3
"""Review gates for the room 190 music override (native adaptation)."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import sha

R9_SHA = 'd29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552'


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-product-r10/rom.sfc').exists(),
                     'requires the built r10 target')
class ProductR10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r10.json').read_text())
        cls.rom = (ROOT / 'local/restoration/demo11-native-product-r10/rom.sfc').read_bytes()
        cls.r9 = (ROOT / 'local/restoration/demo11-native-product-r9/rom.sfc').read_bytes()

    def test_target_rom_equals_r9(self):
        verify(self.rom, self.cfg['output'], 'r10 ROM')
        self.assertEqual(self.cfg['id'], 'demo11-native-product-r10')
        self.assertEqual(sha(self.r9), R9_SHA)
        self.assertEqual(self.rom, self.r9)

    def test_room_music_adaptation_declared(self):
        items = self.cfg.get('native_adaptations', [])
        self.assertTrue(any(a.get('kind') == 'room-music-override'
                            and a.get('room') == '0x190'
                            and a.get('music_slot') == '0x9E' for a in items))

    def test_native_seven_holds_override(self):
        text = (ROOT / 'recomp/native_seven.c').read_text()
        self.assertIn('bm_room_music_override', text)
        self.assertIn('g_ram[0x0dda] = 0x9e', text)
        self.assertIn('room == 0x190', text)

    def test_pack_banks_are_unique(self):
        import native_sprite_gap as gap
        packs = gap.packs('demo11-native-product-r10')
        banks = [int(p['address'], 16) >> 16 for p in packs]
        self.assertEqual(len(banks), len(set(banks)))


if __name__ == '__main__':
    unittest.main()
