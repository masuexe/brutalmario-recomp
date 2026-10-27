#!/usr/bin/env python3
"""Review gates for the custom sprite gap inventory."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import audit_sprite_gaps as gaps


@unittest.skipUnless((ROOT / "local/content-versions/7hero/rom.sfc").exists() and
                     (ROOT / "local/content-versions/cheap-demo/rom.sfc").exists() and
                     (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").exists(),
                     "requires pinned local donor and recipient assets")
class SpriteGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT / "local/reports/native-sprite-gaps.json").read_text())
        cls.rows = {row["slot"]: row for row in cls.report["rows"]}

    def test_gap_counts(self):
        self.assertEqual(self.report["slot_count"], 163)
        self.assertEqual(len(self.report["gap_slots"]), 54)
        self.assertEqual(self.report["gap_room_placements"], 94)

    def test_every_gap_slot_is_a_placeholder(self):
        for slot in self.report["gap_slots"]:
            self.assertTrue(self.rows[slot]["recipient_placeholder"])
            self.assertEqual(self.rows[slot]["recipient_record"], gaps.PLACEHOLDER)

    def test_non_gap_slots_are_not_placeholders(self):
        for slot, row in self.rows.items():
            if slot not in self.report["gap_slots"]:
                self.assertFalse(row["recipient_placeholder"])

    def test_type_counts(self):
        type1 = [s for s in self.report["gap_slots"]
                 if any(d["type"] == 1 for d in self.rows[s]["donors"].values())]
        type3 = [s for s in self.report["gap_slots"]
                 if not any(d["type"] == 1 for d in self.rows[s]["donors"].values())
                 and any(d["type"] == 3 for d in self.rows[s]["donors"].values())]
        none = [s for s in self.report["gap_slots"]
                if not any(d["type"] in (1, 3) for d in self.rows[s]["donors"].values())]
        self.assertEqual((len(type1), len(type3), len(none)), (40, 3, 11))
        self.assertEqual(sorted(type3), ["C0", "C1", "C2"])

    def test_slot_95_uses_the_newest_donor(self):
        row = self.rows["95"]
        self.assertEqual(row["room_count"], 7)
        self.assertEqual(row["donors"]["7hero"]["type"], 1)
        self.assertEqual(row["donors"]["cheap-demo"]["type"], 0)
        self.assertEqual(row["donors"]["mazo"]["type"], 0)


if __name__ == "__main__":
    unittest.main()
