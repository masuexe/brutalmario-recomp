"""Preserve modern sprite bank context, bounded dispatch and data relocations."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_modern_sprite_modules as modern


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-sprite-product-v1/rom.sfc').exists(),
                     'requires the pinned cumulative parent and official source')
class ModernSpriteReview(unittest.TestCase):
    def setUp(self):
        self.plan = modern.load(modern.PLAN)
        self.a1 = modern.load(modern.A1)

    def test_source_programs_and_all_relocations_reviewed(self):
        result = modern.review(self.plan, self.a1)
        self.assertEqual(len(result['inherited_packs']), 54)
        self.assertEqual(len(result['spritea1_audit']['relocated_sites']), 52)
        self.assertEqual(result['spritea1_audit']['instruction_variants'], 2096)
        self.assertEqual(result['sprite99_audit']['instruction_variants'], 655)

    def test_wrong_parent_rejected(self):
        self.plan['parent'] = 'demo11-native-seven-product-v1'
        with self.assertRaisesRegex(ValueError, 'lineage'):
            modern.review(self.plan, self.a1)

    def test_widened_db_exception_rejected(self):
        self.plan['sprite99_db07_operands'].pop()
        with self.assertRaisesRegex(ValueError, 'bank-context exceptions'):
            modern.review(self.plan, self.a1)

    def test_missing_data_relocation_rejected(self):
        self.a1['relocations'] = [p for p in self.a1['relocations'] if p['kind'] == 'call']
        with self.assertRaisesRegex(ValueError, 'relocation coverage'):
            modern.review(self.plan, self.a1)

    def test_opcode_change_rejected(self):
        raw = bytearray.fromhex(self.a1['relocations'][0]['after'])
        raw[0] ^= 1
        self.a1['relocations'][0]['after'] = raw.hex()
        with self.assertRaisesRegex(ValueError, 'one reviewed bank byte'):
            modern.review(self.plan, self.a1)

    def test_spurious_ninth_dispatch_target_rejected(self):
        self.a1['short_dispatches'][1]['count'] = 9
        with self.assertRaisesRegex(ValueError, 'dispatch boundaries'):
            modern.review(self.plan, self.a1)

    def test_incompatible_mirror_mapping_rejected(self):
        self.a1['code']['native_address'] = 'CA88EB'
        with self.assertRaisesRegex(ValueError, 'mirror mapping'):
            modern.review(self.plan, self.a1)


if __name__ == '__main__':
    unittest.main()
