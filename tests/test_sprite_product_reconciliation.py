"""Reject cumulative recovery that changes the official source or mapping scope."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_sprite_product_reconciliation as recovery


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-seven-product-v1/rom.sfc').exists() and
                     (ROOT / 'local/content-versions/boss/rom.sfc').exists(),
                     'requires pinned cumulative parent and official sources')
class SpriteProductReview(unittest.TestCase):
    def setUp(self):
        self.plan = recovery.load(recovery.PLAN)

    def test_official_programs_and_inherited_packs_preserved(self):
        result = recovery.review(self.plan)
        self.assertEqual(set(result['programs']), {'25', '33', '94'})
        self.assertEqual(len(result['inherited_packs']), 51)
        self.assertEqual(result['rom_sha256'], self.plan['candidate_output']['sha256'])

    def test_wrong_parent_rejected(self):
        self.plan['parent'] = 'demo11-native-product-r14'
        with self.assertRaisesRegex(ValueError, 'lineage'):
            recovery.review(self.plan)

    def test_missing_program_rejected(self):
        self.plan['changes'].pop()
        with self.assertRaisesRegex(ValueError, 'three-slot/mapping'):
            recovery.review(self.plan)

    def test_incompatible_mapping_rejected(self):
        self.plan['changes'][0]['native_bank'] = 'CF'
        with self.assertRaisesRegex(ValueError, 'three-slot/mapping'):
            recovery.review(self.plan)

    def test_unpinned_official_source_rejected(self):
        self.plan['sources']['boss']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'source pin'):
            recovery.review(self.plan)

    def test_other_sprite_recipe_rejected(self):
        self.plan['changes'][0]['qualified_recipe'] = 'config/native-content/sprite33-module.json'
        with self.assertRaisesRegex(ValueError, 'official program changed'):
            recovery.review(self.plan)


if __name__ == '__main__':
    unittest.main()
