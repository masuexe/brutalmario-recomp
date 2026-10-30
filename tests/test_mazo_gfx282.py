#!/usr/bin/env python3
"""Checks for the room 151 boss extended graphics 0x282 candidate."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from restore_star_world_1 import graphics_pointer, lz2, sha

TARGET = 'demo11-native-mazo-gfx282-v1'
PARENT = 'demo11-native-product-r14'
MAZO = 'local/content-versions/mazo/rom.sfc'
GFX = 0x282
OFFSET = 0x0A048E


@unittest.skipUnless((ROOT / 'local/restoration' / TARGET / 'rom.sfc').exists(),
                     'requires the built gfx282 candidate')
class MazoGfx282Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
        cls.parent = json.loads((ROOT / 'config/restorations' / (PARENT + '.json')).read_text())
        cls.rom = (ROOT / 'local/restoration' / TARGET / 'rom.sfc').read_bytes()
        cls.parent_rom = (ROOT / 'local/restoration' / PARENT / 'rom.sfc').read_bytes()

    def test_rom_delta_is_one_pointer(self):
        diffs = [i for i in range(len(self.rom)) if self.rom[i] != self.parent_rom[i]]
        self.assertEqual(diffs, [OFFSET, OFFSET + 1, OFFSET + 2])
        self.assertEqual(self.parent_rom[OFFSET:OFFSET + 3], b'\xff' * 3)
        self.assertEqual(int.from_bytes(self.rom[OFFSET:OFFSET + 3], 'little'), 0xD28000)
        self.assertEqual(sha(self.rom), self.cfg['output']['sha256'])
        self.assertEqual(self.parent['output']['sha256'], sha(self.parent_rom))

    def test_pack_is_the_mazo_stream(self):
        mazo = (ROOT / MAZO).read_bytes()
        data, stream = lz2(mazo, graphics_pointer(mazo, GFX), limit=0x10000)
        self.assertEqual(len(data), 4096)
        pack = (ROOT / 'local/native-modules/mazo-gfx282-v1/gfx282.bin').read_bytes()
        self.assertEqual(pack, stream)
        extra = [p for p in self.cfg['native_sprite_gap']['extra_packs']
                 if p['variable'] == 'BM_MAZO_GFX282_PACK']
        self.assertEqual(len(extra), 1)
        self.assertEqual(extra[0]['address'], 'D28000')
        self.assertEqual(extra[0]['sha256'], sha(pack))


if __name__ == '__main__':
    unittest.main()
