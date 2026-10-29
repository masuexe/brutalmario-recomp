#!/usr/bin/env python3
"""Review gates for the room 151 phase music slots (r11)."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import sha

R10_SHA = 'd29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552'


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-product-r11/rom.sfc').exists(),
                     'requires the built r11 target')
class ProductR11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r11.json').read_text())
        cls.rom = (ROOT / 'local/restoration/demo11-native-product-r11/rom.sfc').read_bytes()
        cls.r10 = (ROOT / 'local/restoration/demo11-native-product-r10/rom.sfc').read_bytes()
        cls.pack = (ROOT / 'local/restoration/demo11-native-product-r11/sprite9c-code.bin').read_bytes()
        cls.pack10 = (ROOT / 'local/restoration/demo11-native-product-r10/sprite9c-code.bin').read_bytes()

    def test_target_rom_equals_r10(self):
        verify(self.rom, self.cfg['output'], 'r11 ROM')
        self.assertEqual(self.cfg['id'], 'demo11-native-product-r11')
        self.assertEqual(sha(self.r10), R10_SHA)
        self.assertEqual(self.rom, self.r10)

    def test_phase_music_adaptation_declared(self):
        items = self.cfg.get('native_adaptations', [])
        item = [a for a in items if a.get('kind') == 'sprite-9c-phase-music']
        self.assertEqual(len(item), 1)
        self.assertEqual(item[0]['phase2_slot'], '0xA5')
        self.assertEqual(item[0]['defeat_slot'], '0xAD')

    def test_pack_changes_only_the_two_music_bytes(self):
        self.assertEqual(len(self.pack), len(self.pack10))
        diffs = [i for i in range(len(self.pack)) if self.pack[i] != self.pack10[i]]
        self.assertEqual(diffs, [0xE3A, 0x12FA])
        self.assertEqual(self.pack[0xE3A], 0xA5)
        self.assertEqual(self.pack[0x12FA], 0xAD)
        # Original requests were 0x23 (phase 2) and 0x22 (defeat).
        self.assertEqual(self.pack10[0xE3A], 0x23)
        self.assertEqual(self.pack10[0x12FA], 0x22)

    def test_song_slots_are_present(self):
        manifest = json.loads((ROOT / 'local/music/demo-1-1/manifest.json').read_text())
        slots = {str(s['slot']).upper(): s for s in manifest.get('songs', [])}
        self.assertEqual(slots['A5']['payload']['size'], 2881)
        self.assertEqual(slots['AD']['payload']['size'], 2152)


if __name__ == '__main__':
    unittest.main()
