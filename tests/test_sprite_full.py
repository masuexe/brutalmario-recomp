#!/usr/bin/env python3
"""Review gates for the 31-record gap target."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_sprite_gap as gap
from prepare_rom import verify


@unittest.skipUnless((ROOT / "local/restoration/demo11-native-sprite-full/rom.sfc").exists(),
                     "requires the built 31-record target")
class FullGapTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / "config/restorations/demo11-native-sprite-full.json").read_text())
        cls.pairs = gap.settings("demo11-native-sprite-full")[1]
        cls.rom = (ROOT / "local/restoration/demo11-native-sprite-full/rom.sfc").read_bytes()

    def test_records_are_admitted(self):
        self.assertEqual(len(self.pairs), 33)
        slots = [recipe["record"]["slot"] for _, recipe in self.pairs]
        self.assertEqual(slots[:11], ["10", "11", "12", "13", "14",
                                      "0F", "19", "22", "3B", "55", "92"])
        self.assertEqual(len(set(slots)), 33)
        self.assertEqual(slots[-2:], ["9B", "9C"])

    def test_pack_layout_holds_thirty_five_packs(self):
        packs = gap.packs("demo11-native-sprite-full")
        self.assertEqual(len(packs), 35)
        banks = [int(pack["address"], 16) >> 16 for pack in packs]
        self.assertEqual(len(set(banks)), 35)
        self.assertEqual(packs[-1]["variable"], "BM_NATIVE_GRAPHICS_PACK")

    def test_every_record_is_installed(self):
        verify(self.rom, self.cfg["output"], "31-record target ROM")
        for _, recipe in self.pairs:
            record = bytes.fromhex(recipe["record"]["native_raw"])
            offset = recipe["unapplied_rom_patches"][0]["offset"]
            self.assertEqual(self.rom[offset:offset+len(record)], record)

    def test_every_recipe_keeps_low_bits(self):
        for _, recipe in self.pairs:
            self.assertEqual(int(recipe["code"]["native_address"], 16) & 0xffff,
                             int(recipe["code"]["source_address"], 16) & 0xffff)
            for patch in recipe["code_patches"]:
                self.assertEqual(patch["before"][:6], patch["after"][:6])
                self.assertEqual(len(patch["before"]), 8)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite-full-final.json").exists(),
                         "requires the 31-record qualification report")
    def test_qualification_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite-full-final.json").read_text())
        self.assertEqual(report["records"], 33)
        self.assertEqual(report["packs"], 35)
        self.assertEqual(sorted(report["exact_rooms"]),
                         ["05D", "083", "087", "142", "147", "155", "15D"])
        self.assertGreaterEqual(report["module_views"], 35)
        self.assertEqual(sorted(report["open_rooms"]),
                         ["001", "091", "0A3", "14E", "151", "190"])
        self.assertFalse(report["open_rooms"]["151"]["rows_equal"])
        self.assertEqual(sorted(report["room_lists"]["different_rooms"]),
                         ["001", "075", "086", "15E"])
        self.assertEqual(report["rooms"]["155"]["matched"], 4)


    @unittest.skipUnless((ROOT / "local/reports/native-sprite-full-regression.json").exists(),
                         "requires the unchanged-route regression report")
    def test_unchanged_routes_match_the_baseline(self):
        report = json.loads((ROOT / "local/reports/native-sprite-full-regression.json").read_text())
        self.assertEqual(report["baseline"], "demo11-native-sprite9e")
        self.assertEqual(report["gap"], "demo11-native-sprite-full")
        self.assertEqual(sorted(report["routes"]),
                         ["demo11-forest-attack", "demo11-s004-entry",
                          "demo11-sky-visuals"])
        self.assertEqual(report["equal"], report["total"])
        self.assertGreaterEqual(report["total"], 30)
        for route, entry in report["routes"].items():
            self.assertEqual(entry["equal"], entry["total"], route)


if __name__ == "__main__":
    unittest.main()