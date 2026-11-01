#!/usr/bin/env python3
"""Review gates for the r14 product candidate."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify

TARGET = 'demo11-native-product-r14'
ROM = ROOT / 'local/restoration' / TARGET / 'rom.sfc'
SOURCE = ROOT / 'recomp/native_seven.c'


@unittest.skipUnless(ROM.exists(), 'requires the built r14 target')
class ProductR14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations' / (TARGET + '.json')).read_text())
        cls.rom = ROM.read_bytes()
        cls.source = SOURCE.read_text()

    def test_target_identity(self):
        verify(self.rom, self.cfg['output'], 'r14 ROM')
        self.assertEqual(self.cfg['id'], TARGET)

    def test_phase_music_recipe_remains(self):
        manifests = self.cfg['native_sprite_gap']['manifests']
        self.assertIn('config/native-content/sprite9c-9f-phasebgm2-module.json', manifests)
        kinds = {a.get('kind') for a in self.cfg.get('native_adaptations', [])}
        self.assertIn('sprite-9c-phase-music', kinds)

    def test_event30_default_and_map_opt_in(self):
        self.assertIn('BM_MAZO_EVENT30', self.source)
        self.assertIn('rom[0x2d638] = 0x30', self.source)
        self.assertIn('BM_MAZO_190_NODE', self.source)
        self.assertIn("node[0] == '1'", self.source)

    def test_yoshi_start_remains(self):
        self.assertIn('BM_YOSHI_START', self.source)


if __name__ == '__main__':
    unittest.main()
