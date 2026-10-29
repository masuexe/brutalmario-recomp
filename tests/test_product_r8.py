#!/usr/bin/env python3
"""Review gates for the room 151 tidal-wave graphics restoration."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import graphics_pointer, lz2, pointer_offset, sha

R7_SHA = 'e18964c5b90e53eba2836f293dbb209ee4118af7649b1e7ecc6882a5892fe8b1'


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-product-r8/rom.sfc').exists(),
                     'requires the built r8 target')
class ProductR8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations/demo11-native-product-r8.json').read_text())
        cls.rom = (ROOT / 'local/restoration/demo11-native-product-r8/rom.sfc').read_bytes()
        cls.r7 = (ROOT / 'local/restoration/demo11-native-product-r7/rom.sfc').read_bytes()

    def test_target_rom_identity(self):
        verify(self.rom, self.cfg['output'], 'r8 ROM')
        self.assertEqual(self.cfg['id'], 'demo11-native-product-r8')

    def test_single_extended_graphics_pointer_delta(self):
        self.assertEqual(sha(self.r7), R7_SHA)
        off = pointer_offset(0x27D)
        expected = bytearray(self.r7)
        expected[off:off + 3] = bytes.fromhex('0080d1')
        self.assertEqual(bytes(expected), self.rom)
        self.assertEqual(self.r7[off:off + 3], b'\xff' * 3)
        self.assertEqual(self.rom[off:off + 3], bytes.fromhex('0080d1'))

    def test_wave_pack_carries_the_mazo_stream(self):
        mazo = (ROOT / 'local/content-versions/mazo/rom.sfc').read_bytes()
        data, stream = lz2(mazo, graphics_pointer(mazo, 0x27D), limit=0x10000)
        self.assertEqual(len(data), 4096)
        pack = (ROOT / 'local/restoration/demo11-native-product-r8/corridor-wave.bin').read_bytes()
        self.assertEqual(pack, stream)
        extra = next(p for p in self.cfg['native_sprite_gap']['extra_packs']
                     if p['variable'] == 'BM_CORRIDOR_WAVE_PACK')
        self.assertEqual(extra['address'], 'D18000')
        self.assertEqual(extra['sha256'], sha(pack))
        self.assertFalse(extra['executable'])

    def test_pack_banks_are_unique(self):
        import native_sprite_gap as gap
        packs = gap.packs('demo11-native-product-r8')
        banks = [int(p['address'], 16) >> 16 for p in packs]
        self.assertEqual(len(banks), len(set(banks)))


if __name__ == '__main__':
    unittest.main()
