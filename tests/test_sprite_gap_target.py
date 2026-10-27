#!/usr/bin/env python3
"""Review gates for the sprite 95 gap target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_sprite_gap as gap
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/content-versions/7hero/rom.sfc").exists() and
                     (ROOT / "local/restoration/demo11-native-sprite95/rom.sfc").exists(),
                     "requires the pinned donor and the built target")
class SpriteGapTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite95.json").read_text())
        cls.recipe = json.loads((ROOT / cls.cfg["native_sprite_gap"]["manifest"]).read_text())
        cls.rom = (ROOT / "local/restoration/demo11-native-sprite95/rom.sfc").read_bytes()

    def test_identity_line_admits_the_recipe(self):
        pair = gap.settings("demo11-native-sprite95")
        self.assertIsNotNone(pair)
        cfg, pairs = pair
        self.assertEqual(cfg["id"], "demo11-native-sprite95")
        self.assertEqual(len(pairs), 1)
        path, recipe = pairs[0]
        self.assertEqual(recipe["id"], "sprite95-module")
        self.assertEqual(path, "config/native-content/sprite95-module.json")

    def test_pack_names_are_stable(self):
        names = [pack["variable"] for pack in gap.packs("demo11-native-sprite95")]
        self.assertEqual(names, ["BM_SEVEN_CODE_PACK", "BM_NATIVE_SPRITE_PACK",
                                 "BM_NATIVE_GRAPHICS_PACK"])
        banks = [int(pack["address"], 16) >> 16 for pack in gap.packs("demo11-native-sprite95")]
        self.assertEqual(banks, [0xA3, 0xA5, 0xB6])

    def test_target_rom_carries_the_installed_record(self):
        verify(self.rom, self.cfg["output"], "sprite 95 target ROM")
        patch = self.recipe["unapplied_rom_patches"][0]
        record = bytes.fromhex(self.recipe["record"]["native_raw"])
        offset = patch["offset"]
        self.assertEqual(record.hex(), patch["after"])
        self.assertEqual(self.rom[offset:offset+len(record)], record)

    def test_other_points_keep_the_type1_layout(self):
        donor = self.recipe["record"]["raw"]
        native = self.recipe["record"]["native_raw"]
        self.assertEqual(len(donor), len(native))
        self.assertEqual(donor[:16], native[:16])
        self.assertEqual(donor[28:], native[28:])
        self.assertEqual(donor[16:22], "1ae420")
        self.assertEqual(native[16:22], "1ae4a3")
        self.assertEqual(donor[22:28], "39e520")
        self.assertEqual(native[22:28], "39e5a3")


    @unittest.skipUnless((ROOT / "local/reports/native-sprite95-final.json").exists(),
                         "requires the sprite 95 qualification report")
    def test_room_and_walk_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite95-final.json").read_text())
        self.assertEqual(sorted(report["rooms"]), ["16B", "16C", "16D", "16F", "172", "1CC"])
        self.assertTrue(report["rooms"]["16B"]["slot_rows_equal"])
        self.assertFalse(report["rooms"]["16C"]["slot_rows_equal"])
        self.assertEqual(len(report["walk_samples"]), 9)
        modes = [sample["mode"] for sample in report["walk_samples"]]
        self.assertEqual(modes[0], 0x14)
        self.assertEqual(modes[2], 0x0B)
        self.assertTrue(all(mode == 0x0E for mode in modes[3:]))


if __name__ == "__main__":
    unittest.main()