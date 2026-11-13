#!/usr/bin/env python3
"""Tests for demo11-native-product-r47 bilingual recipe, packs, launchers, and packaging."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import audit_localization
import build_smw_delta
import native_sprite_gap
import package_public_beta as ppb
import prepare_product_r47 as r47
from restoration_targets import RESTORATIONS


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ProductR47MultilangTests(unittest.TestCase):
    def test_r47_config_descends_cleanly_from_r46_with_pinned_packs(self):
        cfg_path = ROOT / "config/restorations/demo11-native-product-r47.json"
        self.assertTrue(cfg_path.is_file(), "run tools/prepare_product_r47.py first")
        cfg = json.loads(cfg_path.read_text())
        self.assertEqual(cfg["id"], "demo11-native-product-r47")
        self.assertEqual(cfg["parent_restoration"], "demo11-native-product-r46")
        self.assertEqual(cfg["base_restoration"], "demo11-native-product-r46")
        self.assertEqual(cfg["base_output"]["sha256"], r47.R46_SHA)

        extra = {p["variable"]: p for p in cfg["native_sprite_gap"]["extra_packs"]}
        self.assertIn("BM_LANG_R47_DATA_PACK", extra)
        self.assertIn("BM_LANG_R47_CODE_PACK", extra)
        self.assertEqual(extra["BM_LANG_R47_DATA_PACK"]["address"], "D58000")
        self.assertEqual(extra["BM_LANG_R47_DATA_PACK"]["source"], r47.PACK_SOURCE)
        self.assertEqual(r47.PACK_SOURCE, "local/native-modules/lang-r47-v2")
        self.assertFalse(extra["BM_LANG_R47_DATA_PACK"]["executable"])
        self.assertEqual(extra["BM_LANG_R47_DATA_PACK"]["size"], r47.EXPECTED_BMLG_SIZE)
        self.assertEqual(extra["BM_LANG_R47_DATA_PACK"]["sha256"], r47.EXPECTED_BMLG_SHA)

        self.assertEqual(extra["BM_LANG_R47_CODE_PACK"]["address"], "908000")
        self.assertTrue(extra["BM_LANG_R47_CODE_PACK"]["executable"])
        self.assertEqual(extra["BM_LANG_R47_CODE_PACK"]["size"], r47.CODE_PACK_SIZE)

        code_blob, entrypoints = r47.build_code_pack_and_entrypoints()
        self.assertEqual(len(code_blob), 4096)
        self.assertEqual(sha(code_blob), extra["BM_LANG_R47_CODE_PACK"]["sha256"])
        self.assertEqual(code_blob[0x0FF0:0x1000], b"\x00" * 16)
        self.assertEqual(len(cfg["code_patches"]), 8)
        patched_addrs = {p["address"] for p in cfg["code_patches"]}
        self.assertEqual(
            patched_addrs,
            {"0005D4", "003A28", "01BB20", "01BB90", "01BBC9", "02B11D", "1FE296", "1FE44D"},
        )
        self.assertTrue(set(entrypoints).issuperset({
            "nmi_upload_ja_gfx02a",
            "nmi_upload_en_gfx02a",
            "hook_ow_level_name",
            "hook_msg_entry",
            "hook_msg_render",
            "hook_msg_close",
            "hook_room1c5_init",
            "hook_room14d_exit",
            "hook_gfx_decompress",
            "hook_title_stripe",
        }))

    def test_code_pack_uses_nmi_vblank_dma_never_midframe_420b(self):
        code_blob, entrypoints = r47.build_code_pack_and_entrypoints()
        nmi_start = entrypoints["nmi_upload_ja_gfx02a"] - r47.CODE_PACK_ADDRESS
        # Find the single LDA #$04; STA $420B inside the NMI VBlank helper only.
        dma_seq = bytes.fromhex("a9048d0b42")
        hits = []
        pos = 0
        while True:
            idx = code_blob.find(dma_seq, pos)
            if idx < 0:
                break
            hits.append(idx)
            pos = idx + 1
        self.assertEqual(len(hits), 1)
        self.assertGreaterEqual(hits[0], nmi_start)
        self.assertLess(hits[0], entrypoints["hook_ow_level_name"] - r47.CODE_PACK_ADDRESS)
        # Ensure $10:D8D0 NMI queue helper is referenced twice (ja + en).
        self.assertEqual(code_blob.count(bytes.fromhex("22d0d810")), 2)

        # Verify Mazo hook_msg_entry matches 0x191 -> $1426==2 (hdr+0x2E) and 0x192 -> $1426==1 (hdr+0x2C).
        msg_entry_off = entrypoints["hook_msg_entry"] - r47.CODE_PACK_ADDRESS
        msg_render_off = entrypoints["hook_msg_render"] - r47.CODE_PACK_ADDRESS
        msg_entry_slice = code_blob[msg_entry_off:msg_render_off]
        idx_191_cmp = msg_entry_slice.index(bytes.fromhex("e220ad2614c902"))
        idx_191_hdr = msg_entry_slice.index(bytes.fromhex("af2e80d5"))
        idx_192_cmp = msg_entry_slice.index(bytes.fromhex("e220ad2614c901"))
        idx_192_hdr = msg_entry_slice.index(bytes.fromhex("af2c80d5"))
        self.assertLess(idx_191_cmp, idx_191_hdr)
        self.assertLess(idx_191_hdr, idx_192_cmp)
        self.assertLess(idx_192_cmp, idx_192_hdr)

    def test_native_sprite_gap_header_and_lle_only_forbidden_bank_handling(self):
        r47_hdr = native_sprite_gap.header("demo11-native-product-r47")
        self.assertIn("#define BM_LANG_R47_SUPPORT 1", r47_hdr)
        self.assertIn("BM_LANG_R47_DATA_PACK", r47_hdr)
        self.assertIn("BM_LANG_R47_CODE_PACK", r47_hdr)

        r46_hdr = native_sprite_gap.header("demo11-native-product-r46")
        self.assertNotIn("BM_LANG_R47_SUPPORT", r46_hdr)

        # Verify configure() allows lle_only nodes in bank $90 (e.g. 9083B7:M1X1)
        # while still rejecting AOT-compiled nodes in mapped banks ($90, $D5).
        feature = native_sprite_gap.identity("demo11-native-product-r47")
        forged = {int(pack["address"], 16) >> 16 for pack in feature["packs"]}
        self.assertIn(0x90, forged)
        self.assertIn(0xD5, forged)
        with tempfile.TemporaryDirectory(prefix="bm-r47-aot-") as folder:
            exp = Path(folder)
            manifest = exp / "src/gen/program_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({
                "nodes": {
                    "908000:M1X1": {"disposition": "aot"},
                }
            }))
            with self.assertRaisesRegex(ValueError, "forbids AOT"):
                native_sprite_gap.configure(exp, "Synthetic", "demo11-native-product-r47")

    def test_collect_r47_packs_covers_71_unique_variables(self):
        r47_rom = ROOT / "local/restoration/demo11-native-product-r47/rom.sfc"
        if not r47_rom.is_file():
            self.skipTest("demo11-native-product-r47 restoration files not present")
        packs = build_smw_delta.collect_target_packs("demo11-native-product-r47")
        self.assertEqual(len(packs), 71)
        variables = {p["variable"] for p in packs}
        self.assertEqual(len(variables), 71)
        self.assertIn("BM_LANG_R47_DATA_PACK", variables)
        self.assertIn("BM_LANG_R47_CODE_PACK", variables)

    def test_target_promoted_and_launchers_expose_lang_flags(self):
        self.assertIn("demo11-native-product-r47", RESTORATIONS)
        self.assertEqual(
            RESTORATIONS["demo11-native-product-r47"]["binary"],
            "BrutalMarioDemo11ProductR47SNESRecomp",
        )
        for script in ("launch_native.py", "play_native_target.py", "play_native_cheats.py"):
            text = (ROOT / "tools" / script).read_text()
            self.assertIn("demo11-native-product-r47", text, script)
            res = subprocess.run(
                [sys.executable, str(ROOT / "tools" / script), "--help"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("--lang {en,ja,auto}", res.stdout, script)

        for script in ("build_smw_delta.py", "package_public_beta.py"):
            text = (ROOT / "tools" / script).read_text()
            self.assertIn('default="demo11-native-product-r47"', text, script)

    def test_public_beta_config_and_bilingual_readme(self):
        for plat in ("linux", "windows"):
            ini = ppb.format_config_ini(plat)
            self.assertIn("[General]", ini)
            self.assertIn("Language=auto", ini)

        readme = ppb.format_readme("demo11-native-product-r47")
        self.assertIn("全部 71 个原生扩展资源包", readme)
        self.assertIn("all 71 native content packs", readme)
        self.assertIn("lang [en|ja|auto|toggle]", readme)
        self.assertIn("GAME SETTINGS", readme)
        self.assertIn("--lang en|ja|auto", readme)
        self.assertIn("Language=auto", readme)

    def test_built_r47_binary_headless_en_ja_title_vram(self):
        binary = ROOT / "local/build/demo11-native-product-r47/BrutalMarioDemo11ProductR47SNESRecomp"
        rom = ROOT / "local/restoration/demo11-native-product-r47/rom.sfc"
        if not binary.is_file() or not rom.is_file():
            self.skipTest("demo11-native-product-r47 native binary not built yet")

        bmlg = r47.build_data_pack()
        ja_028_off, ja_02a_off, ja_02b_off = struct.unpack_from("<HHH", bmlg, 0x0C)
        en_028_off, en_02a_off, en_02b_off = struct.unpack_from("<HHH", bmlg, 0x12)
        expected_ja_028 = bmlg[ja_028_off : ja_028_off + 2048]
        expected_ja_02a = bmlg[ja_02a_off : ja_02a_off + 2048]
        expected_ja_02b = bmlg[ja_02b_off : ja_02b_off + 2048]
        expected_en_028 = bmlg[en_028_off : en_028_off + 2048]
        expected_en_02a = bmlg[en_02a_off : en_02a_off + 2048]
        expected_en_02b = bmlg[en_02b_off : en_02b_off + 2048]

        env_base = os.environ.copy()
        env_base.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", SNESRECOMP_REWIND="0")
        native_sprite_gap.environment("demo11-native-product-r47", env_base)

        with tempfile.TemporaryDirectory(prefix="bm-r47-smoke-") as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "title.script"
            # Boot 600 frames to settle on Title Screen, dump VRAM/WRAM, then start New Game -> 0x1C5.
            script.write_text(
                "turbo on\nwait 600\ndump title\npress start 2\nwait 180\npress start 2\nwait 180\ndump intro\nquit\n"
            )
            cfg = tmp_path / "config.ini"
            cfg.write_text(ppb.format_config_ini("linux"))

            for lang, exp_028, exp_02a, exp_02b in (
                ("en", expected_en_028, expected_en_02a, expected_en_02b),
                ("ja", expected_ja_028, expected_ja_02a, expected_ja_02b),
            ):
                dump_dir = tmp_path / f"dump_{lang}"
                dump_dir.mkdir()
                env = dict(env_base)
                env["BM_LANG"] = lang
                env["SNESRECOMP_DUMP_DIR"] = str(dump_dir)
                res = subprocess.run(
                    [
                        str(binary),
                        "--no-launcher",
                        "--config",
                        str(cfg),
                        "--rom",
                        str(rom),
                        "--script",
                        str(script),
                    ],
                    cwd=dump_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(res.returncode, 0, f"{lang}: {res.stderr}\n{res.stdout}")
                title_vram_path = dump_dir / "title.vram.bin"
                self.assertTrue(title_vram_path.is_file(), f"missing title.vram.bin for {lang}")
                title_vram = title_vram_path.read_bytes()
                self.assertEqual(len(title_vram), 65536)
                # PPU VRAM byte offsets: word $4000 -> byte $8000, $4800 -> $9000, $4C00 -> $9800.
                self.assertEqual(title_vram[0x8000 : 0x8000 + 2048], exp_028, f"{lang} Title GFX 0x28 mismatch")
                self.assertEqual(title_vram[0x9000 : 0x9000 + 2048], exp_02a, f"{lang} Title GFX 0x2A mismatch")
                self.assertEqual(title_vram[0x9800 : 0x9800 + 2048], exp_02b, f"{lang} Title GFX 0x2B mismatch")

                # Verify Room 0x1C5 intro cutscene loads Japanese GFX 0x2A in BOTH EN and JA modes!
                intro_vram = (dump_dir / "intro.vram.bin").read_bytes()
                intro_wram = (dump_dir / "intro.wram.bin").read_bytes()
                room = intro_wram[0x010B] | (intro_wram[0x010C] << 8)
                self.assertIn(room, (0x01C5, 0x014B, 0x014C, 0x014D), f"{lang}: got 0x{room:03X}")
                self.assertEqual(intro_vram[0x9000 : 0x9000 + 2048], expected_ja_02a, f"{lang} 0x1C5 GFX 0x2A mismatch")

    def test_built_r47_binary_headless_demo7_ow_banner_en_ja(self):
        binary = ROOT / "local/build/demo11-native-product-r47/BrutalMarioDemo11ProductR47SNESRecomp"
        rom = ROOT / "local/restoration/demo11-native-product-r47/rom.sfc"
        if not binary.is_file() or not rom.is_file():
            self.skipTest("demo11-native-product-r47 native binary not built yet")

        bmlg = r47.build_data_pack()
        ja_02a_off = struct.unpack_from("<H", bmlg, 0x0E)[0]
        en_02a_off = struct.unpack_from("<H", bmlg, 0x14)[0]
        ja_ow_off, en_ow_off, ow_flags_off = struct.unpack_from("<HHH", bmlg, 0x18)
        expected_ja_02a = bmlg[ja_02a_off : ja_02a_off + 2048]
        expected_en_02a = bmlg[en_02a_off : en_02a_off + 2048]
        # Starting World 1 Overworld node 0x28 ("Yoshi's House" from demo7-en, needs_jp_font == 0).
        self.assertEqual(bmlg[ow_flags_off + 0x28], 0)
        expected_en_banner_28 = bmlg[en_ow_off + 0x28 * 19 : en_ow_off + 0x29 * 19]
        expected_ja_banner_28 = bmlg[ja_ow_off + 0x28 * 19 : ja_ow_off + 0x29 * 19]
        self.assertNotEqual(expected_en_banner_28, expected_ja_banner_28)

        env_base = os.environ.copy()
        env_base.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", SNESRECOMP_REWIND="0")
        native_sprite_gap.environment("demo11-native-product-r47", env_base)

        ow_script_text = (ROOT / "recomp/inputs/cheat-complete-all.script").read_text() + "\ndump ow28\nquit\n"
        with tempfile.TemporaryDirectory(prefix="bm-r47-ow-") as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "ow28.script"
            script.write_text(ow_script_text)
            cfg = tmp_path / "config.ini"
            cfg.write_text(ppb.format_config_ini("linux"))

            for lang, exp_02a, exp_banner in (
                ("en", expected_en_02a, expected_en_banner_28),
                ("ja", expected_ja_02a, expected_ja_banner_28),
            ):
                dump_dir = tmp_path / f"dump_{lang}"
                dump_dir.mkdir()
                env = dict(env_base)
                env["BM_LANG"] = lang
                env["SNESRECOMP_DUMP_DIR"] = str(dump_dir)
                res = subprocess.run(
                    [
                        str(binary),
                        "--no-launcher",
                        "--config",
                        str(cfg),
                        "--rom",
                        str(rom),
                        "--script",
                        str(script),
                    ],
                    cwd=dump_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(res.returncode, 0, f"{lang}: {res.stderr}\n{res.stdout}")
                ow_wram = (dump_dir / "ow28.wram.bin").read_bytes()
                ow_vram = (dump_dir / "ow28.vram.bin").read_bytes()
                self.assertEqual(ow_wram[0x0100], 0x0E, f"{lang}: mode 0x{ow_wram[0x0100]:02X}")
                self.assertEqual(ow_vram[0x9000 : 0x9000 + 2048], exp_02a, f"{lang} OW GFX 0x2A mismatch")
                # PPU VRAM words 0x508B..0x509D (byte offsets 0xA116..0xA13B) hold 19 (tile, attr=0x39) pairs.
                banner_words = struct.unpack_from("<19H", ow_vram, 0x508B * 2)
                banner_tiles = bytes(w & 0xFF for w in banner_words)
                self.assertEqual(banner_tiles, exp_banner, f"{lang} 0x28 banner tiles mismatch")
                self.assertTrue(all((w >> 8) == 0x39 for w in banner_words))


if __name__ == "__main__":
    unittest.main()
