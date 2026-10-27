#!/usr/bin/env python3
"""Review gates for the sprite 94 gap recipe and target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_sprite_module as sprite
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/content-versions/7hero/rom.sfc").exists()
                     and (ROOT / "local/restoration/demo11-native-sprite94/rom.sfc").exists(),
                     "requires the pinned 7hero donor and the built target")
class Sprite94ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = sprite.read_recipe(ROOT / "config/native-content/sprite94-module.json")
        cls.donor = sprite.prepare_donor(ROOT / "config/7hero-donor.json")
        cls.base = (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").read_bytes()
        cls.target = (ROOT / "local/restoration/demo11-native-sprite94/rom.sfc").read_bytes()

    def test_review_pins(self):
        code, audit = sprite.build_code(self.donor, self.base, self.recipe)
        self.assertEqual(len(code), 2096)
        self.assertEqual(audit["local_entry_states"], 25)
        self.assertEqual(audit["instruction_variants"], 898)
        self.assertEqual(audit["reviewed_dispatch_tables"], [])
        self.assertEqual(audit["outside_calls"], self.recipe["external_calls"])

    def test_record_and_native_adaptation(self):
        record = sprite.check_record(self.donor, self.recipe)
        self.assertEqual(record["raw"], "013600073f8319645cb31771b3170000")
        self.assertEqual(record["native_raw"], "013600073f8319645cb3a671b3a60000")
        self.assertEqual(record["rooms"], ["0EF"])

    def test_mapping_keeps_low_bits(self):
        donor = self.recipe["record"]["raw"]
        native = self.recipe["record"]["native_raw"]
        self.assertEqual(len(donor), len(native))
        self.assertEqual(donor[:16], native[:16])
        self.assertEqual(donor[28:], native[28:])
        self.assertEqual(donor[16:22], "5cb317")
        self.assertEqual(native[16:22], "5cb3a6")
        self.assertEqual(self.recipe["code"]["native_address"], "A6B34D")

    def test_target_carries_the_record(self):
        cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite94.json").read_text())
        verify(self.target, cfg["output"], "sprite 94 target ROM")
        patch = self.recipe["unapplied_rom_patches"][0]
        record = bytes.fromhex(self.recipe["record"]["native_raw"])
        offset = patch["offset"]
        self.assertEqual(offset, 1608626)
        self.assertEqual(self.target[offset:offset+len(record)], record)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite94-final.json").exists(),
                         "requires the sprite 94 qualification report")
    def test_qualification_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite94-final.json").read_text())
        self.assertTrue(report["samples"]["r2"]["rows_equal"])
        self.assertTrue(report["samples"]["r3"]["rows_equal"])
        self.assertEqual(report["native_address"], "A6B34D")
        self.assertGreater(report["module_view"]["page_instructions"], 10000)
        for row in report["samples"]["r2"]["native"]:
            self.assertEqual(row["custom"], 0x94)
            self.assertEqual(row["sprite"], 0x36)


if __name__ == "__main__":
    unittest.main()
