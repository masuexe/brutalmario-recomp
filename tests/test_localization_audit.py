#!/usr/bin/env python3
"""Unit tests for r47 localization ROM/font/VRAM audit and BMLG pack."""
from __future__ import annotations

import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import audit_localization as al  # noqa: E402
from restore_star_world_1 import sha  # noqa: E402


class LocalizationAuditR47Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit_path = ROOT / "config/native-content/localization-audit-r47.json"
        cls.audit = json.loads(cls.audit_path.read_text())
        cls.local_dir = al.resolve_local_dir()

    def test_pinned_json_matches_deterministic_generation(self) -> None:
        fresh = al.generate_audit(self.local_dir)
        self.assertEqual(fresh, self.audit)

    def test_all_10_roms_verified(self) -> None:
        self.assertEqual(set(self.audit["roms"].keys()), set(al.PINNED_ROMS.keys()))
        for name, (_, expected_sha) in al.PINNED_ROMS.items():
            rec = self.audit["roms"][name]
            self.assertEqual(rec["size"], 4194304)
            self.assertEqual(rec["sha256"], expected_sha)

    def test_gfx_028_029_02a_02b_and_ow_hud_safety(self) -> None:
        for name in ("cheap-demo", "ow", "mazo", "7hero", "boss", "demo-only-1", "demo-1-1", "r46"):
            self.assertEqual(self.audit["gfx_audit"][name]["0x29"]["decoded_sha256"], al.GFX_029_SHA)

        self.assertEqual(self.audit["tile_diffs"]["0x2A"]["boss_vs_r46"].__len__(), 92)
        self.assertEqual(self.audit["tile_diffs"]["0x2B"]["boss_vs_r46"], ["0x71", "0x72", "0x73"])
        self.assertEqual(
            self.audit["tile_diffs"]["0x28"]["boss_vs_r46"],
            ["0x38", "0x39", "0x48", "0x49", "0x55", "0x56", "0x65", "0x66"],
        )

        safety = self.audit["vram_layout"]["ow_hud_switch_safety"]
        self.assertTrue(safety["safe_to_swap_gfx02a_on_ow"])
        identical = set(safety["identical_gfx02a_tiles"])
        self.assertEqual(len(identical), 36)
        self.assertIn("0x1F", identical)
        for digit in range(0x22, 0x2C):
            self.assertIn(f"0x{digit:02X}", identical)

    def test_vram_and_stripe_addresses(self) -> None:
        vl = self.audit["vram_layout"]
        self.assertEqual(vl["gfx_slots"]["0x2A"]["vram_word"], "0x4800..0x4BFF")
        self.assertEqual(vl["ow_level_name_banner"]["vram_words"], "0x508B..0x509D")
        self.assertEqual(vl["ow_level_name_banner"]["tile_count"], 19)
        self.assertEqual(vl["ow_level_name_banner"]["wram_stripe_buffer"], "$7F:837D")
        self.assertEqual(len(vl["smw_message_box"]["row_vram_words"]), 8)

    def test_ow_names_en_and_ja(self) -> None:
        ja_ow = self.audit["ja"]["ow_names"]
        en_ow = self.audit["en"]["ow_names"]
        self.assertEqual(len(ja_ow), 96)
        self.assertEqual(len(en_ow), 96)

        en_slots = [e for e in en_ow if e["needs_jp_font"] == 0 and e["text"]]
        self.assertEqual(len(en_slots), 81)
        by_slot = {e["slot"]: e for e in en_ow}
        self.assertEqual(by_slot[0x29]["text"], "Hey,I am Mario!")
        self.assertEqual(by_slot[0x0A]["text"], "Special Warp Star")
        self.assertEqual(by_slot[0x0C]["text"], "Aqua Special")
        self.assertEqual(by_slot[0x0D]["text"], "End of Special Zone")
        self.assertEqual(by_slot[0x34]["text"], "Milky Way Wishes")
        self.assertEqual(by_slot[0x3A]["text"], "Ghost Special")
        self.assertEqual(by_slot[0x4A]["text"], "Baby Yoshi Hill")
        self.assertEqual(by_slot[0x4E]["text"], "Twinbee Special")
        self.assertEqual(by_slot[0x51]["text"], "Wily's Revenge")
        self.assertEqual(by_slot[0x58]["text"], "Athletic Special")

        # Representative demo7-en Overworld slots (including 0x13 and 0x5E adaptations).
        self.assertEqual(by_slot[0x28]["text"], "Yoshi's House")
        self.assertEqual(by_slot[0x2A]["text"], "Catch Yoshi!")
        self.assertEqual(by_slot[0x37]["text"], "Boss Bass Bridge")
        self.assertEqual(by_slot[0x13]["text"], "Yellow Switch")
        self.assertEqual(by_slot[0x25]["text"], "Careful! Lightning!")
        self.assertEqual(by_slot[0x5E]["text"], "LIFT GO! 1")

        # All 84 non-JP OW entries (81 EN + 3 blank) must use valid EN GFX 0x2A tiles < 0x80.
        for e in en_ow:
            if e["needs_jp_font"] == 0:
                raw = bytes.fromhex(e["hex"])
                self.assertEqual(len(raw), 19)
                for b in raw:
                    self.assertLess(b, 0x80, f"slot {e['slot_hex']} tile 0x{b:02X}")
                    self.assertIn(b, al.EN_GFX02A_CHARS, f"slot {e['slot_hex']} tile 0x{b:02X}")

        # All 12 post-demo7 courses keep boss Japanese bytes with needs_jp_font = 1.
        for jslot in al.POST_DEMO7_JP_OW_SLOTS:
            self.assertEqual(by_slot[jslot]["needs_jp_font"], 1)
            self.assertIsNone(by_slot[jslot]["text"])
            self.assertEqual(by_slot[jslot]["hex"], ja_ow[jslot]["hex"])
        self.assertNotIn("53130011", by_slot[0x5A]["hex"])

        # Blank slots 0x00, 0x4F, 0x5F have needs_jp_font = 0.
        for bslot in al.BLANK_OW_SLOTS:
            self.assertEqual(by_slot[bslot]["needs_jp_font"], 0)
            self.assertEqual(by_slot[bslot]["hex"], "1f" * 19)

        self.assertEqual(sum(e["needs_jp_font"] for e in en_ow), 12)

    def test_messages_en_ja_mazo_and_custom_rooms(self) -> None:
        ja_msgs = self.audit["ja"]["messages"]
        en_msgs = self.audit["en"]["messages"]
        self.assertEqual(len(ja_msgs), 144)
        self.assertEqual(len(en_msgs), 144)

        by_slot = {m["slot"]: m for m in en_msgs}
        for slot in al.DEMO_1_1_EN_MSG_SLOTS:
            self.assertEqual(by_slot[slot]["needs_jp_font"], 0)
            self.assertIsNotNone(by_slot[slot]["text"])
        self.assertIn("Can you throw more", by_slot[6]["text"])
        self.assertIn("With a baby yoshi", by_slot[7]["text"])
        self.assertIn("Moving coin is", by_slot[82]["text"])
        self.assertIn("--CAUTION--", by_slot[83]["text"])

        # Vanilla US SMW tutorial slots cleared in Demo 1-1 must NOT be imported from demo6.
        for vanilla_slot in (10, 16, 42, 43, 74, 75, 76, 77, 78, 79, 81, 126):
            self.assertEqual(by_slot[vanilla_slot]["hex"], "fe")
            self.assertEqual(by_slot[vanilla_slot]["needs_jp_font"], 0)

        # Check Mazo messages match mazo-messages-v2.json.
        mazo = self.audit["mazo_messages"]
        self.assertEqual(mazo["0x192"]["size"], 70)
        self.assertEqual(mazo["0x191"]["size"], 86)
        self.assertEqual(mazo["0x192"]["needs_jp_font"], 1)
        self.assertEqual(mazo["0x191"]["needs_jp_font"], 1)

        # Check $10:B6A6 custom room message remapping.
        remaps = {(r["room_int"], r["message_level_int"]) for r in self.audit["custom_room_messages"]["entries"]}
        self.assertEqual(remaps, {(0x106, 0x04), (0x025, 0x03), (0x168, 0x03)})

    def test_rooms_000_to_1ff_tagged(self) -> None:
        rooms = self.audit["rooms"]
        self.assertEqual(len(rooms), 512)
        by_id = {r["room_int"]: r for r in rooms}
        self.assertEqual(list(sorted(by_id.keys())), list(range(512)))

        for r_id in al.PERSISTENT_JP_ROOMS:
            self.assertEqual(by_id[r_id]["needs_jp_font"], 1)
            self.assertEqual(by_id[r_id]["persistent_jp_font"], 1)
        for r_id in al.MAZO_MSG_ROOMS:
            self.assertEqual(by_id[r_id]["needs_jp_font"], 1)
            self.assertEqual(by_id[r_id]["persistent_jp_font"], 0)
        for r_id in al.SHOP_ROOMS:
            self.assertTrue(by_id[r_id]["has_shop_a2"])
            self.assertEqual(by_id[r_id]["needs_jp_font"], 0)
        # 0x025, 0x168 (remapped to 0x03 EN) and 0x105 (level 0x29 EN) have EN InfoBoxes.
        for en_box_room in (0x025, 0x168, 0x105):
            self.assertEqual(by_id[en_box_room]["needs_jp_font"], 0)
        # 0x106 is remapped by $10:B6A6 to level 0x04 (JP messages).
        self.assertEqual(by_id[0x106]["effective_message_level"], "0x04")

    def test_bmlg_binary_pack_round_trip(self) -> None:
        pack = al.build_bmlg_pack(self.audit, self.local_dir)
        self.assertLessEqual(len(pack), 32768)
        self.assertEqual(len(pack), self.audit["bmlg_pack"]["total_size"])
        self.assertEqual(sha(pack), self.audit["bmlg_pack"]["sha256"])

        (
            magic,
            version,
            hdr_size,
            total_size,
            ja_028_off,
            ja_02a_off,
            ja_02b_off,
            en_028_off,
            en_02a_off,
            en_02b_off,
            ja_ow_off,
            en_ow_off,
            ow_flags_off,
            ja_ptrs_off,
            ja_blob_off,
            ja_blob_sz,
            en_ptrs_off,
            en_blob_off,
            en_blob_sz,
            msg_flags_off,
            mazo_192_off,
            mazo_191_off,
            room_policy_off,
            remap_off,
            ja_title_off,
            ja_title_sz,
        ) = struct.unpack("<4sHHI22H", pack[:56])

        self.assertEqual(magic, b"BMLG")
        self.assertEqual(version, 1)
        self.assertEqual(hdr_size, 64)
        self.assertEqual(total_size, len(pack))

        # Verify all 6 fonts match audited SHA-256s.
        self.assertEqual(sha(pack[ja_028_off : ja_028_off + 2048]), self.audit["gfx_audit"]["boss"]["0x28"]["decoded_sha256"])
        self.assertEqual(sha(pack[ja_02a_off : ja_02a_off + 2048]), self.audit["gfx_audit"]["boss"]["0x2A"]["decoded_sha256"])
        self.assertEqual(sha(pack[ja_02b_off : ja_02b_off + 2048]), self.audit["gfx_audit"]["boss"]["0x2B"]["decoded_sha256"])
        self.assertEqual(sha(pack[en_028_off : en_028_off + 2048]), self.audit["gfx_audit"]["r46"]["0x28"]["decoded_sha256"])
        self.assertEqual(sha(pack[en_02a_off : en_02a_off + 2048]), self.audit["gfx_audit"]["r46"]["0x2A"]["decoded_sha256"])
        self.assertEqual(sha(pack[en_02b_off : en_02b_off + 2048]), self.audit["gfx_audit"]["r46"]["0x2B"]["decoded_sha256"])

        # Round-trip all 96 OW names + flags.
        for i in range(96):
            self.assertEqual(pack[ja_ow_off + i * 19 : ja_ow_off + (i + 1) * 19].hex(), self.audit["ja"]["ow_names"][i]["hex"])
            self.assertEqual(pack[en_ow_off + i * 19 : en_ow_off + (i + 1) * 19].hex(), self.audit["en"]["ow_names"][i]["hex"])
            self.assertEqual(pack[ow_flags_off + i], self.audit["en"]["ow_names"][i]["needs_jp_font"])

        # Round-trip all 144 JA & EN messages + flags.
        for lang, ptrs_off, blob_off, blob_sz in (
            ("ja", ja_ptrs_off, ja_blob_off, ja_blob_sz),
            ("en", en_ptrs_off, en_blob_off, en_blob_sz),
        ):
            blob = pack[blob_off : blob_off + blob_sz]
            for i in range(144):
                rel = struct.unpack_from("<H", pack, ptrs_off + i * 2)[0]
                end = blob.index(0xFE, rel) + 1
                self.assertEqual(blob[rel:end].hex(), self.audit[lang]["messages"][i]["hex"])
                if lang == "en":
                    self.assertEqual(pack[msg_flags_off + i], self.audit["en"]["messages"][i]["needs_jp_font"])

        # Round-trip Mazo, room_font_policy, remaps, and JA title stripe.
        self.assertEqual(pack[mazo_192_off : mazo_192_off + 70].hex(), self.audit["mazo_messages"]["0x192"]["hex"])
        self.assertEqual(pack[mazo_191_off : mazo_191_off + 86].hex(), self.audit["mazo_messages"]["0x191"]["hex"])
        for r in range(512):
            self.assertEqual(pack[room_policy_off + r], self.audit["rooms"][r]["persistent_jp_font"])
        self.assertEqual(pack[remap_off], 3)
        self.assertEqual(sha(pack[ja_title_off : ja_title_off + ja_title_sz]), self.audit["stripe_audit"]["boss_title_stripe_sha256"])


if __name__ == "__main__":
    unittest.main()
