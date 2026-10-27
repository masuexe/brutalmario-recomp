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
        self.assertEqual(len(self.pairs), 35)
        slots = [recipe["record"]["slot"] for _, recipe in self.pairs]
        self.assertEqual(slots[:11], ["10", "11", "12", "13", "14",
                                      "0F", "19", "22", "3B", "55", "92"])
        self.assertEqual(len(set(slots)), 35)
        self.assertEqual(slots[-4:], ["9B", "9C", "2C", "7F"])

    def test_pack_layout_holds_thirty_five_packs(self):
        packs = gap.packs("demo11-native-sprite-full")
        self.assertEqual(len(packs), 37)
        banks = [int(pack["address"], 16) >> 16 for pack in packs]
        self.assertEqual(len(set(banks)), 37)
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
                if len(patch["before"]) == 8:
                    self.assertEqual(patch["before"][:6], patch["after"][:6])
                else:
                    self.assertEqual(len(patch["before"]), 6)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite-full-final.json").exists(),
                         "requires the 31-record qualification report")
    def test_qualification_report(self):
        report = json.loads((ROOT / "local/reports/native-sprite-full-final.json").read_text())
        self.assertEqual(report["records"], 35)
        self.assertEqual(report["packs"], 37)
        self.assertEqual(sorted(report["exact_rooms"]),
                         ["00D", "05D", "083", "087", "08B", "0AF", "142",
                          "147", "155", "15D", "160"])
        self.assertGreaterEqual(report["module_views"], 37)
        self.assertEqual(sorted(report["open_rooms"]),
                         ["001", "05B", "075", "096", "0A3", "0A5", "0B1",
                          "0B3", "0B5", "0B6", "110", "13C", "13F", "14E",
                          "151", "15E", "162", "163", "164", "190"])
        self.assertEqual(sorted(report["stalled_rooms"]),
                         ["085", "091", "0A2", "0BA", "0BB", "0F3"])
        for room, entry in report["stalled_rooms"].items():
            self.assertTrue(entry["native_frozen"], room)
            self.assertEqual(entry["native"]["mode"], 0x12, room)
            self.assertEqual(entry["donor"]["mode"], 0x14, room)
            self.assertFalse(entry["donor"]["frozen"], room)
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
            for name, point in entry["points"].items():
                self.assertEqual(point["baseline_sha256"], point["gap_sha256"],
                                 route+"/"+name)


    @unittest.skipUnless((ROOT / "local/reports/native-sprite-emu-freeze.json").exists(),
                         "requires the reference-emulator freeze report")
    def test_the_fixture_freezes_the_unmodified_rom(self):
        report = json.loads((ROOT / "local/reports/native-sprite-emu-freeze.json").read_text())
        self.assertEqual(report["rom"], "local/restoration/demo11-base/rom.sfc")
        self.assertEqual(sorted(report["rooms"]), ["085", "0A2", "0BA", "0BB", "0F3"])
        for room, entry in report["rooms"].items():
            self.assertTrue(entry["frozen"], room)
            self.assertEqual(entry["mode"], 0x12, room)


    def test_pea_operands_are_values_not_addresses(self):
        import prepare_sprite_module as sprite
        recipe = sprite.read_recipe(ROOT / "config/native-content/sprite2c-module.json")
        self.assertEqual(len(recipe["ignored_operands"]), 1)
        entry = recipe["ignored_operands"][0]
        self.assertEqual(entry["address"], "2193D2")
        self.assertEqual(entry["operand"], "C6C0")
        appendix = sprite.read_recipe(ROOT / "config/native-content/sprite7f-module.json")
        self.assertEqual(appendix["code"]["data_appendix"]["size"], 128)
        self.assertEqual(len(appendix["relocated_operands"]), 2)
        donor = sprite.prepare_donor(ROOT / appendix["donor_manifest"])
        base = (ROOT / "local/restoration/demo11-native-sprite9e/rom.sfc").read_bytes()
        payload, _ = sprite.build_code(donor, base, appendix)
        self.assertEqual(len(payload), 1641)


    @unittest.skipUnless((ROOT / "local/reports/native-sprite-full-final.json").exists(),
                         "requires the eleven-record qualification report")
    def test_oneframe_phase_of_room_0a5(self):
        report = json.loads((ROOT / "local/reports/native-sprite-full-final.json").read_text())
        phase = report["oneframe_phase"]["0A5"]
        self.assertEqual(phase["offset"], -29)
        self.assertEqual(phase["residual"], 3)
        self.assertEqual(phase["mismatch_frames"], [489, 490, 491])
        self.assertGreaterEqual(phase["equal"], 25)


    @unittest.skipUnless((ROOT / "local/reports/native-sprite-full-final.json").exists(),
                         "requires the qualification report")
    def test_oneframe_phase_of_room_091(self):
        report = json.loads((ROOT / "local/reports/native-sprite-full-final.json").read_text())
        phase = report["oneframe_phase"]["091"]
        self.assertEqual(phase["offset"], -28)
        self.assertEqual(phase["residual"], 0)
        self.assertEqual(phase["mismatch_frames"], [])
        self.assertEqual(phase["equal"], phase["checked"])

    @unittest.skipUnless((ROOT / "local/reports/native-sprite-full-final.json").exists(),
                         "requires the qualification report")
    def test_oneframe_phase_of_room_190(self):
        report = json.loads((ROOT / "local/reports/native-sprite-full-final.json").read_text())
        phase = report["oneframe_phase"]["190"]
        self.assertEqual(phase["offset"], 18)
        self.assertEqual(phase["residual"], 5)

    @unittest.skipUnless((ROOT / "local/reports/native-sprite-full-final.json").exists(),
                         "requires the qualification report")
    def test_oneframe_phase_of_three_more_rooms(self):
        report = json.loads((ROOT / "local/reports/native-sprite-full-final.json").read_text())
        phase = report["oneframe_phase"]
        self.assertEqual(sorted(phase), ["091", "0A2", "0A5", "0B5", "151", "190"])
        self.assertEqual(phase["0A2"]["residual"], 0)
        self.assertEqual(phase["0A2"]["equal"], phase["0A2"]["checked"])
        self.assertEqual(phase["0B5"]["mismatch_frames"][0], 189)
        self.assertEqual(phase["151"]["offset"], -1)
        self.assertGreaterEqual(phase["151"]["residual"], 10)

if __name__ == "__main__":
    unittest.main()