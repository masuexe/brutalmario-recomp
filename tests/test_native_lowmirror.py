"""Reject mappings and record edits that would change source module semantics."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_native_lowmirror as low


@unittest.skipUnless((ROOT / 'local/restoration/demo11-native-product-r14/rom.sfc').exists() and
                     (ROOT / 'local/content-versions/boss/rom.sfc').exists(),
                     'requires pinned official donors and native parent')
class NativeLowMirrorTests(unittest.TestCase):
    def setUp(self):
        self.plan = low.load(low.PLAN)

    def test_reviewed_mapping_and_official_dependency(self):
        result = low.review(self.plan)
        self.assertEqual(len(result['audit']), 11)
        self.assertEqual(result['audit']['95']['instruction_variants'], 2086)
        self.assertEqual(result['rom_sha256'], self.plan['candidate_output']['sha256'])

    def test_bank_without_low_mirrors_rejected(self):
        self.plan['changes'][0]['new_address'] = 'D2' + self.plan['changes'][0]['new_address'][2:]
        with self.assertRaisesRegex(ValueError, 'low-memory mirrors'):
            low.review(self.plan)

    def test_low_address_movement_rejected(self):
        self.plan['changes'][0]['new_address'] = '9CE18E'
        with self.assertRaisesRegex(ValueError, 'low-memory mirrors'):
            low.review(self.plan)

    def test_record_property_change_rejected(self):
        raw = bytearray.fromhex(self.plan['changes'][0]['new_record'])
        raw[1] ^= 1
        self.plan['changes'][0]['new_record'] = raw.hex()
        with self.assertRaisesRegex(ValueError, 'outside bank pointers'):
            low.review(self.plan)

    def test_missing_mapping_review_rejected(self):
        self.plan['changes'].pop()
        with self.assertRaisesRegex(ValueError, 'mapping set differs'):
            low.review(self.plan)

    def test_additional_unreviewed_slot_rejected(self):
        self.plan['additional_restorations'][0]['slot'] = '96'
        with self.assertRaisesRegex(ValueError, 'unreviewed additional'):
            low.review(self.plan)


if __name__ == '__main__':
    unittest.main()
