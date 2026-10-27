#!/usr/bin/env python3
"""Review gates for the sprite 12 gap recipe and target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import prepare_sprite_module as sprite
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/content-versions/cheap-demo/rom.sfc").exists()
                     and (ROOT / "local/restoration/demo11-native-sprite12/rom.sfc").exists(),
                     "requires the pinned cheap-demo donor and the built target")
class Sprite12ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = sprite.read_recipe(ROOT / "config/native-content/sprite12-module.json")
        cls.donor = sprite.prepare_donor(ROOT / "config/cheap-demo-donor.json")
        cls.base = (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").read_bytes()
        cls.target = (ROOT / "local/restoration/demo11-native-sprite12/rom.sfc").read_bytes()

    def test_review_pins(self):
        code, audit = sprite.build_code(self.donor, self.base, self.recipe)
        self.assertEqual(len(code), 1358)
        self.assertEqual(audit["local_entry_states"], 17)
        self.assertEqual(audit["instruction_variants"], 584)
        self.assertEqual(audit["reviewed_dispatch_tables"], [])
        self.assertEqual(audit["source_bank_jsl_sites"], [])
        self.assertEqual(audit["outside_calls"], self.recipe["external_calls"])

    def test_record_and_native_adaptation(self):
        record = sprite.check_record(self.donor, self.recipe)
        self.assertEqual(record["raw"], "01361080388101046292168092160000")
        self.assertEqual(record["native_raw"], "01361080388101046292ab8092ab0000")
        self.assertEqual(record["rooms"], ["155", "157", "159", "15B", "15C"])

    def test_mapping_keeps_low_bits(self):
        donor = self.recipe["record"]["raw"]
        native = self.recipe["record"]["native_raw"]
        self.assertEqual(len(donor), len(native))
        self.assertEqual(donor[:16], native[:16])
        self.assertEqual(donor[28:], native[28:])
        self.assertEqual(donor[16:22], "629216")
        self.assertEqual(native[16:22], "6292ab")
        self.assertEqual(self.recipe["code"]["native_address"], "AB9253")

    def test_target_carries_the_record(self):
        cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite12.json").read_text())
        verify(self.target, cfg["output"], "sprite 12 target ROM")
        patch = self.recipe["unapplied_rom_patches"][0]
        record = bytes.fromhex(self.recipe["record"]["native_raw"])
        offset = patch["offset"]
        self.assertEqual(offset, 1606546)
        self.assertEqual(self.target[offset:offset+len(record)], record)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite12-final.json").exists(),
                         "requires the sprite 12 qualification report")
    def test_qualification_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite12-final.json").read_text())
        self.assertEqual(report["exact_room"], "155")
        for tag in ("r1", "r2", "r3", "r4"):
            self.assertTrue(report["samples"][tag]["rows_equal"], tag)
            for row in report["samples"][tag]["native"]:
                self.assertEqual(row["custom"], 0x12)
        self.assertEqual(sorted(report["rooms"]), ["155", "157", "159", "15B", "15C"])
        self.assertGreater(report["module_view"]["page_instructions"], 1000)


if __name__ == "__main__":
    unittest.main()
