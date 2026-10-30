"""Admission failures that would corrupt the relocated modern A2 program."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_forest_a2 as a2


@unittest.skipUnless((ROOT / 'local/content-versions/demo-only-1/rom.sfc').exists() and
                     (ROOT / 'local/restoration/demo11-native-product-r13/rom.sfc').exists(),
                     'requires pinned official source and parent')
class ForestA2AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.recipe = a2.load(a2.RECIPE)

    def test_complete_review(self):
        code, audit = a2.build(self.recipe)
        self.assertEqual(len(code), 7400)
        self.assertEqual(audit['local_entry_states'], 32)
        self.assertEqual(audit['instruction_variants'], 868)
        self.assertEqual(len(audit['source_bank_relocations']), 13)

    def test_missing_data_relocation_rejected(self):
        self.recipe['relocations'] = [p for p in self.recipe['relocations'] if p['address'] != '30DAC8']
        with self.assertRaisesRegex(ValueError, 'relocation coverage'):
            a2.build(self.recipe)

    def test_nonbank_code_change_rejected(self):
        patch = self.recipe['relocations'][0]
        patch['after'] = 'ea' + patch['after'][2:]
        with self.assertRaisesRegex(ValueError, 'reviewed bank operand'):
            a2.build(self.recipe)

    def test_truncated_dispatch_rejected(self):
        self.recipe['short_dispatch']['count'] = 3
        with self.assertRaisesRegex(ValueError, 'dispatch table'):
            a2.build(self.recipe)

    def test_unreviewed_helper_change_rejected(self):
        self.recipe['recipient_helper']['changes'].pop()
        with self.assertRaisesRegex(ValueError, 'helper adaptation'):
            a2.build(self.recipe)

    def test_low_address_change_rejected(self):
        self.recipe['code']['native_address'] = '9DD7B5'
        with self.assertRaisesRegex(ValueError, 'mapping changes low addresses'):
            a2.build(self.recipe)

    def test_program_bank_without_low_wram_mirrors_rejected(self):
        self.recipe['code']['native_address'] = 'D2D7B4'
        self.recipe['record']['native_raw'] = self.recipe['record']['native_raw'].replace('9d', 'd2')
        with self.assertRaisesRegex(ValueError, 'WRAM/IO mirrors'):
            a2.build(self.recipe)

    def test_source_record_cannot_change_other_properties(self):
        self.recipe['record']['native_raw'] = '00' + self.recipe['record']['native_raw'][2:]
        with self.assertRaisesRegex(ValueError, 'outside the entry banks'):
            a2.build(self.recipe)

    def test_unreviewed_return_position_rejected(self):
        self.recipe['return_adaptation']['fields'][2]['after'] = '68'
        with self.assertRaisesRegex(ValueError, 'return encoding'):
            a2.build(self.recipe)


if __name__ == '__main__':
    unittest.main()
