#!/usr/bin/env python3
"""Review gates for the runtime practice cheats."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import play_native_cheats as cheats


class CheatScriptTests(unittest.TestCase):
    def test_room_teleport_encoding(self):
        text = cheats.build_script(room=0x151)
        self.assertIn("poke 19b8 51", text)
        self.assertIn("poke 19d8 05", text)
        text = cheats.build_script(room=0x0A6)
        self.assertIn("poke 19b8 a6", text)
        self.assertIn("poke 19d8 04", text)
        text = cheats.build_script(room=0x1FF)
        self.assertIn("poke 19b8 ff", text)
        self.assertIn("poke 19d8 05", text)
        text = cheats.build_script(room=0x000)
        self.assertIn("poke 19b8 00", text)
        self.assertIn("poke 19d8 04", text)

    def test_map_teleport_encoding(self):
        text = cheats.build_script(map_pos=(6, 0x128, 0x1E8))
        self.assertIn("poke 1f11 0606", text)
        self.assertIn("poke 1f17 2801e8012801e801", text)
        self.assertIn("poke 1f1f 12001e0012001e00", text)
        self.assertIn("poke 0100 0b", text)

    def test_persistent_cheats(self):
        text = cheats.build_script(invincible=True, air_swim=True)
        self.assertIn("forcepoke 1490 40", text)
        self.assertIn("forcepoke 85 01", text)

    def test_lives_and_complete_all(self):
        text = cheats.build_script(lives=50)
        self.assertIn("poke 0dbe 32", text)
        text = cheats.build_script(complete_all=True)
        self.assertIn("poke 1ea2 9f", text)
        self.assertIn("poke 1f27 01010101", text)

    def test_room_range_is_checked(self):
        with self.assertRaises(ValueError):
            cheats.validate_room(0x200)
        with self.assertRaises(ValueError):
            cheats.validate_map(0x200, 0)

    @unittest.skipUnless((ROOT / "local/captures/cheat-room151/e1.wram.bin").exists(),
                         "requires the room 151 cheat capture")
    def test_room_151_capture_reached_the_room(self):
        wram = (ROOT / "local/captures/cheat-room151/e1.wram.bin").read_bytes()
        room = int.from_bytes(wram[0x10B:0x10D], "little")
        self.assertEqual(room, 0x151)
        customs = [wram[0x1AB9E + s] for s in range(12) if wram[0x14C8 + s]]
        self.assertEqual(customs, [0x9C, 0x9C, 0x9C])

    @unittest.skipUnless((ROOT / "local/captures/cheat-map/m1.wram.bin").exists(),
                         "requires the map teleport capture")
    def test_map_capture_reached_the_position(self):
        wram = (ROOT / "local/captures/cheat-map/m1.wram.bin").read_bytes()
        self.assertEqual(wram[0x1F11], 6)
        self.assertEqual(wram[0x1F17] | (wram[0x1F18] << 8), 0x128)
        self.assertEqual(wram[0x1F19] | (wram[0x1F1A] << 8), 0x1E8)

    @unittest.skipUnless((ROOT / "local/captures/cheat-swim/e1.wram.bin").exists(),
                         "requires the air swim capture")
    def test_air_swim_capture_sets_the_water_flag(self):
        wram = (ROOT / "local/captures/cheat-swim/e1.wram.bin").read_bytes()
        self.assertEqual(wram[0x85], 1)

    def test_fast_room_entry_uses_polling_and_turbo(self):
        text = cheats.build_script(room=0x190, fast=True)
        self.assertIn("turbo on", text)
        self.assertIn("until 0100 == 07", text)
        self.assertIn("until 0100 == 0e", text)
        self.assertIn("until16 10b == 190", text)
        self.assertIn("poke 19b8 90", text)
        self.assertIn("poke 19d8 05", text)
        self.assertIn("turbo off", text)

    def test_legacy_room_entry_stays_fixed_wait(self):
        text = cheats.build_script(room=0x190)
        self.assertIn("wait 600", text)
        self.assertNotIn("until16", text)

    def test_fast_entry_with_existing_save_skips_intro_wait(self):
        text = cheats.build_script(room=0x190, fast=True, existing_save=True)
        self.assertIn("until 0100 == 0e 3000", text)
        self.assertNotIn("wait 780", text)
        self.assertIn("until16 10b == 190", text)


if __name__ == "__main__":
    unittest.main()