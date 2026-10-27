#!/usr/bin/env python3
"""Review gates for the sprite 2A gap recipe and target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_sprite_module as sprite
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/content-versions/7hero/rom.sfc").exists()
                     and (ROOT / "local/restoration/demo11-native-sprite2a/rom.sfc").exists(),
                     "requires the pinned 7hero donor and the built target")
class Sprite2AModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = sprite.read_recipe(ROOT / "config/native-content/sprite2a-module.json")
        cls.donor = sprite.prepare_donor(ROOT / "config/7hero-donor.json")
        cls.base = (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").read_bytes()
        cls.target = (ROOT / "local/restoration/demo11-native-sprite2a/rom.sfc").read_bytes()

    def test_review_pins(self):
        code, audit = sprite.build_code(self.donor, self.base, self.recipe)
        self.assertEqual(len(code), 28478)
        self.assertEqual(len(audit["reviewed_dispatch_tables"]), 3)
        self.assertEqual([table["count"] for table in audit["reviewed_dispatch_tables"]],
                         [35, 23, 21])
        self.assertEqual(len(audit["source_bank_jsl_sites"]), 39)
        self.assertEqual(audit["outside_calls"], self.recipe["external_calls"])

    def test_record_and_native_adaptation(self):
        record = sprite.check_record(self.donor, self.recipe)
        self.assertEqual(record["raw"], "0136000035a299440f80228d80220000")
        self.assertEqual(record["native_raw"], "0136000035a299440f80a98d80a90000")
        self.assertEqual(record["rooms"], ["0FF"])

    def test_patches_keep_low_bits(self):
        self.assertEqual(len(self.recipe["code_patches"]), 39)
        for patch in self.recipe["code_patches"]:
            self.assertEqual(patch["before"][:6], patch["after"][:6])
            self.assertEqual(patch["before"][6:], "22")
            self.assertEqual(patch["after"][6:], "a9")
        self.assertEqual(self.recipe["code"]["native_address"], "A98000")

    def test_target_carries_the_record(self):
        cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite2a.json").read_text())
        verify(self.target, cfg["output"], "sprite 2A target ROM")
        patch = self.recipe["unapplied_rom_patches"][0]
        record = bytes.fromhex(self.recipe["record"]["native_raw"])
        offset = patch["offset"]
        self.assertEqual(offset, 1606930)
        self.assertEqual(self.target[offset:offset+len(record)], record)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite2a-final.json").exists(),
                         "requires the sprite 2A qualification report")
    def test_qualification_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite2a-final.json").read_text())
        self.assertTrue(report["samples"]["r1"]["rows_equal"])
        self.assertEqual(report["native_address"], "A98000")
        self.assertEqual(report["code_patches"], 39)
        self.assertEqual(report["dispatch_tables"], 3)
        self.assertGreater(report["module_view"]["page_instructions"], 10000)
        for row in report["samples"]["r1"]["native"]:
            self.assertEqual(row["custom"], 0x2A)
            self.assertEqual(row["sprite"], 0x36)


if __name__ == "__main__":
    unittest.main()
