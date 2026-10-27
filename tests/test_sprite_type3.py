#!/usr/bin/env python3
"""Review gates for the type-3 SpriteTool records."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import audit_sprite_type3 as type3


@unittest.skipUnless((ROOT / 'local/content-versions/7hero/rom.sfc').exists() and
                     (ROOT / 'local/content-versions/boss/rom.sfc').exists() and
                     (ROOT / 'local/restoration/demo11-native-sprite9e/rom.sfc').exists(),
                     'requires pinned local donor and recipient assets')
class SpriteType3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seven = (ROOT / 'local/content-versions/7hero/rom.sfc').read_bytes()
        cls.boss = (ROOT / 'local/content-versions/boss/rom.sfc').read_bytes()
        cls.base = (ROOT / 'local/restoration/demo11-native-sprite9e/rom.sfc').read_bytes()
        cls.report = json.loads((ROOT / 'local/reports/native-sprite-type3.json').read_text())

    def test_records_are_type_3(self):
        for name in ('7hero', 'boss'):
            for slot in ('C0', 'C1', 'C2'):
                record = self.report['donors'][name]['records'][slot]
                self.assertEqual(record['type'], 3)
                self.assertEqual(record['raw'][:2], '03')
                self.assertEqual(record['raw'][2:14], 'ff'*6)
                self.assertEqual(record['raw'][-4:], 'ffff')

    def test_donor_records_match(self):
        self.assertTrue(self.report['donor_records_identical'])
        self.assertTrue(self.report['donor_block_identical'])
        for slot in ('C0', 'C1', 'C2'):
            self.assertEqual(self.report['donors']['7hero']['records'][slot]['raw'],
                             self.report['donors']['boss']['records'][slot]['raw'])
            self.assertEqual(self.report['donors']['7hero']['records'][slot]['block_sha256'],
                             self.report['donors']['boss']['records'][slot]['block_sha256'])

    def test_main_label_precedes_the_stub(self):
        for slot in ('C0', 'C1', 'C2'):
            record = self.report['donors']['7hero']['records'][slot]
            label = int(record['label'], 16)
            stub = int(record['stub'], 16)
            self.assertEqual(stub - label, 4)
            self.assertEqual(record['init_field'], record['label_address'])
            self.assertTrue(record['same_block'])

    def test_recipient_slots_are_placeholders(self):
        for slot in ('C0', 'C1', 'C2'):
            record = self.report['placements'][slot]['recipient_record']
            self.assertEqual(record, '0000ffffffffffff218001218001ffff')
            self.assertEqual(self.report['placements'][slot]['donor'],
                             self.report['placements'][slot]['recipient_slots'])
        self.assertEqual(self.report['placement_differences'], [])

    def test_block_hashes_are_stable(self):
        from restore_star_world_1 import sha
        blocks = {'C0': (0x986D7, 0x987A4), 'C1': (0x9AE08, 0x9AEDD), 'C2': (0xADD21, 0xADE48)}
        for slot, (start, end) in blocks.items():
            self.assertEqual(sha(self.seven[start:end]),
                             self.report['donors']['7hero']['records'][slot]['block_sha256'])
            self.assertEqual(self.boss[start:end], self.seven[start:end])


    def test_constructor_patch_plan_is_recorded(self):
        doc = (ROOT / "docs/native-sprite-type3.md").read_text()
        self.assertIn("## Constructor patch plan", doc)
        self.assertIn("b95db18500c8b95db18501c8b95db18502c8c8c8c8", doc)
        self.assertIn("c220b97a828500e220b97c828502b980829f28ab7fb981829f34ab7f28ab7a6b",
                      doc)


if __name__ == '__main__':
    unittest.main()