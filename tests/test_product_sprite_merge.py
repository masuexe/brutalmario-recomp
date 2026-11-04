#!/usr/bin/env python3
"""Review gates for the product sprite merge target r20."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

NEW_MANIFESTS = [
    'config/native-content/type3-shooters-c2-v2.json',
    'config/native-content/type3-c2-boss-lowmirror.json',
    'config/native-content/sprite25-boss-product-module.json',
    'config/native-content/sprite33-boss-product-module.json',
    'config/native-content/sprite94-boss-product-module.json',
    'config/native-content/sprite99-modern-module.json',
    'config/native-content/sprite97-modern-module.json',
]
MERGED = {'25', '33', '94', '97', '99', 'A1', 'C2'}
REMAINING = {'96', 'A5', 'A6', 'E8', 'E9', 'EA', 'F5'}


def load(name):
    return json.loads((ROOT / 'config/restorations' / name).read_text())


class ConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load('demo11-native-product-r20.json')
        cls.base = load('demo11-native-product-r19.json')

    def test_lineage(self):
        self.assertEqual(self.config['base_restoration'], 'demo11-native-product-r19')
        self.assertEqual(self.config['base_output'], self.base['output'])

    def test_frozen_recipes_match_the_parent(self):
        gap = self.config['native_sprite_gap']
        self.assertEqual(gap['frozen_manifests'], self.base['native_sprite_gap']['manifests'])
        self.assertEqual(gap['manifests'][:len(gap['frozen_manifests'])], gap['frozen_manifests'])
        self.assertEqual(gap['manifests'][len(gap['frozen_manifests']):], NEW_MANIFESTS)

    def test_pack_and_patch_delta(self):
        gap = self.config['native_sprite_gap']
        base_gap = self.base['native_sprite_gap']
        extra = {pack['variable'] for pack in gap['extra_packs']}
        self.assertEqual(extra - {pack['variable'] for pack in base_gap['extra_packs']},
                         {'BM_NATIVE_SPRITE_A1_PACK'})
        self.assertEqual(len(gap['extra_patches']), 2)
        self.assertEqual([patch['offset'] for patch in gap['extra_patches']], [1608674, 1608834])
        self.assertEqual(gap['extra_patches'][0]['after'], '013600b73503994439a58c4ba58c0000')
        self.assertEqual(gap['extra_patches'][1]['after'], '013600863587b944f6888a34898a0000')

    def test_music_region_pack_is_inherited(self):
        self.assertEqual(self.config['music_region_pack'], self.base['music_region_pack'])

    def test_scope_names_the_merge(self):
        scope = self.config['scope']
        for slot in sorted(MERGED):
            self.assertIn(slot, scope)


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-product-r20/rom.sfc').exists(),
                     'requires the prepared r20 image')
class PreparedImageTests(unittest.TestCase):
    def test_rom_identity(self):
        import hashlib
        config = load('demo11-native-product-r20.json')
        rom = (ROOT / 'local/restoration/demo11-native-product-r20/rom.sfc').read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(), config['output']['sha256'])
        self.assertEqual(len(rom), config['output']['size'])

    def test_census_delta(self):
        report = json.loads((ROOT / 'local/reports/product-r20-sprite-census.json').read_text())
        self.assertEqual(set(report['placeholder_slots']), REMAINING)
        self.assertEqual(report['custom_slot_count'], 164)
        self.assertEqual(report['rom_sha256'], load('demo11-native-product-r20.json')['output']['sha256'])
        for slot in MERGED:
            self.assertNotIn(slot, report['placeholder_slots'])


@unittest.skipUnless((ROOT / 'local/reports/product-r20-sprite-merge.json').exists(),
                     'requires a fresh merge qualification report')
class QualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / 'local/reports/product-r20-sprite-merge.json').read_text())

    def test_merge_delta(self):
        self.assertEqual(set(self.report['merged_slots']), MERGED)
        self.assertEqual(set(self.report['parent_placeholders']), MERGED | REMAINING)
        self.assertEqual(set(self.report['candidate_placeholders']), REMAINING)
        self.assertEqual(self.report['target'], 'demo11-native-product-r20')

    def test_room_samples_hold_the_new_actors(self):
        for key, row in self.report['samples'].items():
            self.assertTrue(any(row['actors'].values()), key)
            self.assertTrue(all(state['mode'] in (0x0D, 0x13, 0x14)
                                for state in row['states'].values()), key)

    def test_doc_records_the_result(self):
        doc = (ROOT / 'docs/native-product-sprite-merge.md').read_text()
        self.assertIn('Product r20', doc)
        self.assertIn('f4185fe22f57c66c338b800bbe423dcd915860c87cc2ec395baa7236cad5e567', doc)
        self.assertIn('BM_SEVEN_RETURN=0', doc)


if __name__ == '__main__':
    unittest.main()
