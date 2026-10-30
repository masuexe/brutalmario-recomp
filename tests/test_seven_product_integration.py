"""Reject cumulative integrations that lose the pinned Seven feature boundary."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_seven_product as seven


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-type3-c2-v2/rom.sfc').exists(),
                     'requires pinned cumulative and qualified Seven inputs')
class SevenProductReview(unittest.TestCase):
    def test_bounded_official_feature_integration(self):
        result = seven.review()
        self.assertEqual(len(result['patches']), 7)
        self.assertEqual(result['child_source_sha256'],
                         '8301000a2fed1e9c534958f06ef1d82eeb7e62f92cce9ef674b1f369c4fd0dbb')

    def test_unrelated_patch_rejected(self):
        plan = seven.load(seven.PLAN)
        plan['patches'][0]['offset'] += 1
        with self.assertRaisesRegex(ValueError, 'qualified feature delta'):
            seven.review(plan=plan)

    def test_wrong_parent_rejected(self):
        plan = seven.load(seven.PLAN)
        plan['parent'] = 'demo11-native-product-r14'
        with self.assertRaisesRegex(ValueError, 'lineage'):
            seven.review(plan=plan)

    def test_modified_child_rejected(self):
        child = seven.load(seven.CHILD)
        raw = bytearray.fromhex(child['code']['raw_payload'])
        raw[32] ^= 1
        child['code']['raw_payload'] = raw.hex()
        with self.assertRaisesRegex(ValueError, 'qualified official source'):
            seven.review(child=child)

    def test_incompatible_child_bank_rejected(self):
        child = seven.load(seven.CHILD)
        child['code']['native_address'] = 'D0C20E'
        with self.assertRaisesRegex(ValueError, 'low-mirror mapping'):
            seven.review(child=child)


if __name__ == '__main__':
    unittest.main()
