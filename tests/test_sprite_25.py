#!/usr/bin/env python3
"""Review gates for the sprite 25 gap recipe and target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_sprite_module as sprite
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/content-versions/7hero/rom.sfc").exists()
                     and (ROOT / "local/restoration/demo11-native-sprite25/rom.sfc").exists(),
                     "requires the pinned 7hero donor and the built target")
class Sprite25ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = sprite.read_recipe(ROOT / "config/native-content/sprite25-module.json")
        cls.donor = sprite.prepare_donor(ROOT / "config/7hero-donor.json")
        cls.base = (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").read_bytes()
        cls.target = (ROOT / "local/restoration/demo11-native-sprite25/rom.sfc").read_bytes()

    def test_review_pins(self):
        code, audit = sprite.build_code(self.donor, self.base, self.recipe)
        self.assertEqual(len(code), 8801)
        self.assertEqual(audit["local_entry_states"], 69)
        self.assertEqual(audit["instruction_variants"], 3040)
        self.assertEqual(audit["reviewed_dispatch_tables"], [])
        self.assertEqual(audit["outside_calls"], self.recipe["external_calls"])

    def test_record_and_native_adaptation(self):
        record = sprite.check_record(self.donor, self.recipe)
        self.assertEqual(record["raw"], "012800073f019944acab2002ac200000")
        self.assertEqual(record["native_raw"], "012800073f019944acaba802aca80000")
        self.assertEqual(record["rooms"], ["154"])

    def test_mapping_keeps_low_bits(self):
        donor = self.recipe["record"]["raw"]
        native = self.recipe["record"]["native_raw"]
        self.assertEqual(len(donor), len(native))
        self.assertEqual(donor[:16], native[:16])
        self.assertEqual(donor[28:], native[28:])
        self.assertEqual(donor[16:22], "acab20")
        self.assertEqual(native[16:22], "acaba8")
        self.assertEqual(self.recipe["code"]["native_address"], "A8AB9D")

    def test_target_carries_the_record(self):
        cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite25.json").read_text())
        verify(self.target, cfg["output"], "sprite 25 target ROM")
        patch = self.recipe["unapplied_rom_patches"][0]
        record = bytes.fromhex(self.recipe["record"]["native_raw"])
        offset = patch["offset"]
        self.assertEqual(offset, 1606850)
        self.assertEqual(self.target[offset:offset+len(record)], record)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite25-final.json").exists(),
                         "requires the sprite 25 qualification report")
    def test_qualification_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite25-final.json").read_text())
        self.assertEqual(report["native_address"], "A8AB9D")
        self.assertGreater(report["module_view"]["page_instructions"], 10000)
        self.assertGreaterEqual(report["fine"]["onset_gap"], 0)
        self.assertLessEqual(report["fine"]["max_abs_y_lag"], 2)
        for tag in ("r1", "r2", "r3"):
            for row in report["samples"][tag]["native"]:
                self.assertEqual(row["custom"], 0x25)
                self.assertEqual(row["sprite"], 0x28)


if __name__ == "__main__":
    unittest.main()
