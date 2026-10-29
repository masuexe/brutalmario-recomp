#!/usr/bin/env python3
"""Review gates for the room 151 phase music slots (r12)."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import sha

R10_SHA = 'd29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552'


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-product-r12/rom.sfc').exists(),
                     'requires the built r12 target')
class ProductR12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r12.json').read_text())
        cls.rom = (ROOT / 'local/restoration/demo11-native-product-r12/rom.sfc').read_bytes()
        cls.r10 = (ROOT / 'local/restoration/demo11-native-product-r10/rom.sfc').read_bytes()
        cls.pack = (ROOT / 'local/restoration/demo11-native-product-r12/sprite9c-code.bin').read_bytes()
        cls.pack10 = (ROOT / 'local/restoration/demo11-native-product-r10/sprite9c-code.bin').read_bytes()

    def test_target_rom_equals_r10(self):
        verify(self.rom, self.cfg['output'], 'r12 ROM')
        self.assertEqual(self.cfg['id'], 'demo11-native-product-r12')
        self.assertEqual(sha(self.r10), R10_SHA)
        self.assertEqual(self.rom, self.r10)

    def test_phase_music_adaptation_declared(self):
        items = [a for a in self.cfg.get('native_adaptations', [])
                 if a.get('kind') == 'sprite-9c-phase-music']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['phase2_slot'], '0xA5')
        self.assertEqual(items[0]['defeat_slot'], '0xAD')

    def test_pack_changes_only_the_two_music_bytes(self):
        self.assertEqual(len(self.pack), len(self.pack10))
        diffs = [i for i in range(len(self.pack)) if self.pack[i] != self.pack10[i]]
        self.assertEqual(diffs, [0xE3A, 0x12FA])
        # Second-boss arrival (0x92FA) plays A5; defeat (0x8E3A) plays AD.
        self.assertEqual(self.pack[0xE3A], 0xAD)
        self.assertEqual(self.pack[0x12FA], 0xA5)
        self.assertEqual(self.pack10[0xE3A], 0x23)
        self.assertEqual(self.pack10[0x12FA], 0x22)

    def test_song_slots_are_present(self):
        manifest = json.loads((ROOT / 'local/music/demo-1-1/manifest.json').read_text())
        slots = {str(s['slot']).upper(): s for s in manifest.get('songs', [])}
        self.assertEqual(slots['A5']['payload']['size'], 2881)
        self.assertEqual(slots['AD']['payload']['size'], 2152)


if __name__ == '__main__':
    unittest.main()
