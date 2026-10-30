#!/usr/bin/env python3
"""Review gates for the r14 product candidate without the C2 type-3 record."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_rom import verify
from restore_star_world_1 import sha

V1_SHA = 'bae32d5dc0e02d95d86e856e0ec83264f8be0bdb57796564722ccf7a71e824e6'


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-modern-sprites-v1/rom.sfc').exists(),
                     'requires the built v1 target')
class ModernSpriteV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / 'config/restorations/demo11-native-modern-sprites-v2.json').read_text())
        cls.v1 = (ROOT / 'local/restoration/demo11-native-modern-sprites-v1/rom.sfc').read_bytes()
        cls.recipe = json.loads((ROOT / 'config/native-content/sprite97-modern-module.json').read_text())

    def test_lineage(self):
        self.assertEqual(self.cfg['id'], 'demo11-native-modern-sprites-v2')
        self.assertEqual(self.cfg['parent_restoration'], 'demo11-native-modern-sprites-v1')
        self.assertEqual(self.cfg['parent_output']['sha256'], V1_SHA)
        self.assertEqual(sha(self.v1), V1_SHA)

    def test_only_slot97_record_changes(self):
        rom = (ROOT / 'local/restoration/demo11-native-modern-sprites-v2/rom.sfc').read_bytes()
        verify(rom, self.cfg['output'], 'v2 ROM')
        diffs = [i for i in range(len(rom)) if rom[i] != self.v1[i]]
        patch = self.cfg['native_sprite_gap']['extra_patches'][-1]
        before = bytes.fromhex(patch['before'])
        after = bytes.fromhex(patch['after'])
        expected = [patch['offset'] + i for i in range(16) if before[i] != after[i]]
        self.assertEqual(diffs, expected)

    def test_config_adds_one_manifest_and_record_only(self):
        cfg1 = json.loads((ROOT / 'config/restorations/demo11-native-modern-sprites-v1.json').read_text())
        a, b = cfg1['native_sprite_gap'], self.cfg['native_sprite_gap']
        self.assertEqual(b['manifests'], a['manifests'] + ['config/native-content/sprite97-modern-module.json'])
        self.assertEqual(b['extra_packs'], a['extra_packs'])
        self.assertEqual(len(b['extra_patches']), len(a['extra_patches']) + 1)
        self.assertEqual(b['extra_patches'][-1]['offset'], 1608674)
        self.assertEqual(b['extra_patches'][-1]['after'], self.recipe['record']['native_raw'])

    def test_recipe_pins(self):
        record = self.recipe['record']
        self.assertEqual(record['slot'], '97')
        self.assertEqual(record['rooms'], ['1EF'])
        self.assertEqual(record['raw'], '013600b73503994439a5104ba5100000')
        self.assertEqual(record['native_raw'], '013600b73503994439a58c4ba58c0000')
        code = self.recipe['code']
        self.assertEqual(code['size'], 453)
        self.assertEqual(code['native_address'], '8CA52A')
        self.assertEqual(code['sha256'], 'b1f39a342a0e42eff47844f1f1b48f29fa4dfcddda5d1bc513a3e903897b92fc')
        self.assertEqual(self.recipe['external_calls'], ['01B7B3'])
        self.assertEqual(self.recipe['code_patches'], [])
        self.assertEqual(self.recipe['shared_dependencies'][0]['address'], '01B7B3')


if __name__ == '__main__':
    unittest.main()
