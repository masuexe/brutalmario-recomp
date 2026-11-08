import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import adapt_song_base as asb
from restore_star_world_1 import lorom

SMW_ROM = Path("/home/harp/projects/sfc/roms/Super Mario World (U) [!].smc")


class TestVanillaSmwMusic(unittest.TestCase):
    def test_command_parameter_lengths(self):
        expected = {
            0xdf: 0, 0xf0: 0,
            0xda: 1, 0xdb: 1, 0xe0: 1, 0xe2: 1, 0xe4: 1, 0xe6: 1, 0xe7: 1, 0xea: 1, 0xee: 1,
            0xdc: 2, 0xe1: 2, 0xe3: 2, 0xe8: 2, 0xed: 2,
            0xdd: 3, 0xde: 3, 0xe5: 3, 0xe9: 3, 0xeb: 3, 0xec: 3, 0xef: 3, 0xf1: 3, 0xf2: 3,
        }
        self.assertEqual(asb.LENGTHS, expected)

    @unittest.skipUnless(SMW_ROM.is_file(), "vanilla SMW ROM not present")
    def test_extract_five_vanilla_songs(self):
        smw = SMW_ROM.read_bytes()
        bank = smw[asb.VANILLA_BANK_OFFSET : asb.VANILLA_BANK_OFFSET + asb.VANILLA_BANK_LENGTH]
        expected_specs = {
            0x02: (2321, "aa684a98384e042f", 70, 1894),
            0x03: (1063, "98b9793f39f2c39e", 74, 781),
            0x05: (1150, "fa5cd901f808fbda", 78, 821),
            0x06: (447, "dfd89b4b9f71f99d", 27, 294),
            0x1A: (924, "68bab6e815feb52e", 89, 574),
        }
        for sid, (exp_len, exp_sha_prefix, exp_fields, exp_walked) in expected_specs.items():
            payload = asb.extract_vanilla_payload(bank, sid)
            self.assertEqual(len(payload), exp_len)
            digest = hashlib.sha256(payload).hexdigest()
            self.assertTrue(digest.startswith(exp_sha_prefix), f"{sid:02X}: {digest}")
            fields, walked = asb._walk(payload, 0x5400)
            self.assertEqual(len(fields), exp_fields)
            self.assertEqual(walked, exp_walked)
            for off in fields:
                ptr = int.from_bytes(payload[off : off + 2], "little")
                self.assertTrue(0x5400 <= ptr < 0x5400 + len(payload))

    def test_edge_cases_and_df_zero_arg_walk(self):
        with self.assertRaises(asb.SongError):
            asb.adapt(b"short")
        with self.assertRaises(asb.SongError):
            asb.extract_vanilla_payload(b"\x00" * 10, 0)
        with self.assertRaises(asb.SongError):
            asb.extract_vanilla_payload(b"\x00" * 10, 20)
        # Synthetic 1-pattern song at 6800 where 0xDF (0-byte) precedes 0xE9 (3-byte subroutine)
        # Sequence header: pat0=6808, 00FF, loop=6800 (6 bytes) + 2 pad = 8 bytes
        # Pattern at +8 (16 bytes): ch0=6818, others=0
        # Track at +24 (6818): DF E9 1E 68 01 00 (6 bytes)
        # Sub at +30 (681E): 20 90 00 (3 bytes)
        song = bytearray(33)
        song[0:2] = (0x6808).to_bytes(2, "little")
        song[2:4] = (0x00FF).to_bytes(2, "little")
        song[4:6] = (0x6800).to_bytes(2, "little")
        song[8:10] = (0x6818).to_bytes(2, "little")
        song[24:30] = bytes([0xDF, 0xE9, 0x1E, 0x68, 0x01, 0x00])
        song[30:33] = bytes([0x20, 0x90, 0x00])
        block = len(song).to_bytes(2, "little") + (0x6800).to_bytes(2, "little") + bytes(song) + bytes(4)
        adapted = asb.adapt(block, 0x5400)
        # Check that E9 target at song offset 26 (block offset 30) relocated from 681E to 541E
        self.assertEqual(int.from_bytes(adapted[30:32], "little"), 0x541E)

    def test_product_r41_recipe_and_rom(self):
        cfg_path = ROOT / "config/restorations/demo11-native-product-r41.json"
        self.assertTrue(cfg_path.is_file())
        cfg = json.loads(cfg_path.read_text())
        self.assertEqual(cfg["id"], "demo11-native-product-r41")
        self.assertEqual(cfg["parent_restoration"], "demo11-native-product-r40")

        slots_sg = [
            0x02, 0x03, 0x05, 0x06, 0x19, 0x1A, 0x1E, 0x2C, 0x2E, 0x2F, 0x35, 0x36,
            0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x3F, 0x42, 0x43, 0x45, 0x46, 0x47, 0x4C,
            0x4F, 0x53, 0x54, 0x55, 0x56, 0x57, 0x5B, 0x5D, 0x6D,
        ]
        patch_addrs = {p["address"] for p in cfg["code_patches"]}
        for slot in slots_sg:
            self.assertIn(f"07CF{slot:02X}", patch_addrs)

        rom_path = ROOT / "local/restoration/demo11-native-product-r41/rom.sfc"
        pack_path = ROOT / "local/restoration/demo11-native-product-r41/music-pack.bin"
        r40_rom_path = ROOT / "local/restoration/demo11-native-product-r40/rom.sfc"
        r40_pack_path = ROOT / "local/restoration/demo11-native-product-r40/music-pack.bin"
        if rom_path.is_file() and pack_path.is_file():
            rom = rom_path.read_bytes()
            pack = pack_path.read_bytes()
            self.assertEqual(hashlib.sha256(rom).hexdigest(), cfg["output"]["sha256"])
            self.assertEqual(hashlib.sha256(pack).hexdigest(), cfg["music_region_pack"]["pack_sha256"])
            # Slot 02 unaliased from Slot 4F
            table = lorom(0x0FE000)
            ptr_02 = rom[table + 0x02 * 3 : table + 0x02 * 3 + 3].hex()
            ptr_4f = rom[table + 0x4F * 3 : table + 0x4F * 3 + 3].hex()
            self.assertEqual(ptr_02, "4dd008")
            self.assertEqual(ptr_4f, "468008")
            # Sample group 02 for all 33 restored slots
            sg_table = lorom(0x0FCF00)
            for slot in slots_sg:
                self.assertEqual(rom[sg_table + slot], 0x02)

            # Walk and verify adapt invariance across all 33 restored song slots
            pack_map = {}
            pos = 0
            for region in cfg["music_region_pack"]["regions"]:
                sz = region["size"]
                pack_map[region["offset"]] = pack[pos : pos + sz]
                pos += sz
            for slot in slots_sg:
                p = rom[table + slot * 3 : table + slot * 3 + 3]
                addr = (p[0] << 16) | (p[1] << 8) | p[2]
                off = lorom(addr)
                star_off = off - 8
                blk = pack_map[star_off][8:] if star_off in pack_map else rom[off:]
                plen = int.from_bytes(blk[0:2], "little")
                pdst = int.from_bytes(blk[2:4], "little")
                self.assertEqual(pdst, 0x5400, f"slot {slot:02X}")
                payload = blk[4 : 4 + plen]
                fields, walked = asb._walk(payload, 0x5400)
                self.assertGreater(walked, 0, f"slot {slot:02X}")
                for f_off in fields:
                    ptr = int.from_bytes(payload[f_off : f_off + 2], "little")
                    self.assertTrue(0x5400 <= ptr < 0x5400 + plen, f"slot {slot:02X} ptr {ptr:04X}")
                upload = blk[: 4 + plen + 4]
                self.assertEqual(asb.adapt(upload, 0x5400), upload)

            # Verify exact byte-for-byte derivation from r40 + vanilla SMW ROM
            if r40_rom_path.is_file() and r40_pack_path.is_file() and SMW_ROM.is_file():
                smw = SMW_ROM.read_bytes()
                bank = smw[asb.VANILLA_BANK_OFFSET : asb.VANILLA_BANK_OFFSET + asb.VANILLA_BANK_LENGTH]
                cand_rom = bytearray(r40_rom_path.read_bytes())
                cand_pack = bytearray(r40_pack_path.read_bytes())
                cand_pack[6144:12288] = asb.wrap_star_block(
                    asb.wrap_upload_block(asb.extract_vanilla_payload(bank, 0x03)), pad_to=6144
                )
                cand_pack[12288:18432] = asb.wrap_star_block(
                    asb.wrap_upload_block(asb.extract_vanilla_payload(bank, 0x05)), pad_to=6144
                )
                cand_pack[18432:24576] = asb.wrap_star_block(
                    asb.wrap_upload_block(asb.extract_vanilla_payload(bank, 0x06)), pad_to=6144
                )
                cand_rom[0x26CBE8:0x26D000] = asb.wrap_star_block(
                    asb.wrap_upload_block(asb.extract_vanilla_payload(bank, 0x1A)),
                    pad_to=0x26D000 - 0x26CBE8,
                )
                cand_rom[0x26D000:0x26E3E8] = asb.wrap_star_block(
                    asb.wrap_upload_block(asb.extract_vanilla_payload(bank, 0x02)),
                    pad_to=0x26E3E8 - 0x26D000,
                )
                cand_rom[0x07E006:0x07E009] = bytes.fromhex("4dd008")
                cand_rom[0x28019A] = 0x56
                for slot in slots_sg:
                    cand_rom[0x07CF00 + slot] = 0x02
                self.assertEqual(bytes(cand_rom), rom)
                self.assertEqual(bytes(cand_pack), pack)


if __name__ == "__main__":
    unittest.main()
