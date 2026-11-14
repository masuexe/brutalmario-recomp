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
import prepare_product_r49 as r49
from restore_star_world_1 import graphics_pointer, lz2
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
        self.assertEqual(r47.PACK_SOURCE, "local/native-modules/lang-r47-v1")
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
        self.assertIn("demo11-native-product-r48", RESTORATIONS)
        self.assertEqual(
            RESTORATIONS["demo11-native-product-r48"]["binary"],
            "BrutalMarioDemo11ProductR48SNESRecomp",
        )
        self.assertIn("demo11-native-product-r49", RESTORATIONS)
        self.assertEqual(
            RESTORATIONS["demo11-native-product-r49"]["binary"],
            "BrutalMarioDemo11ProductR49SNESRecomp",
        )
        for script in ("launch_native.py", "play_native_target.py", "play_native_cheats.py"):
            text = (ROOT / "tools" / script).read_text()
            self.assertIn("demo11-native-product-r49", text, script)
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
            self.assertIn('default="demo11-native-product-r49"', text, script)

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


class ProductR49Demo7OwTests(unittest.TestCase):
    """Verify cumulative r49 target (r48 Room 0x116 fix + 71 Demo 7 EN Overworld names)."""

    def test_r49_config_lineage_symbols_and_lang_v2_packs(self):
        r48_cfg = json.loads((ROOT / "config/restorations/demo11-native-product-r48.json").read_text())
        r49_cfg = json.loads((ROOT / "config/restorations/demo11-native-product-r49.json").read_text())
        self.assertEqual(r49_cfg["id"], "demo11-native-product-r49")
        self.assertEqual(r49_cfg["target"], "Brutal Mario Demo11 Product R49")
        self.assertEqual(r49_cfg["parent_restoration"], "demo11-native-product-r48")
        self.assertEqual(r49_cfg["base_restoration"], "demo11-native-product-r48")
        self.assertEqual(r49_cfg["base_output"], {"size": 4194304, "sha256": r49.R48_SHA})
        self.assertEqual(r49_cfg["output"], {"size": 4194304, "sha256": r49.R48_SHA})
        self.assertEqual(
            r49_cfg["native_sprite_gap"]["frozen_manifests"],
            r49_cfg["native_sprite_gap"]["manifests"],
        )
        self.assertEqual(r49_cfg["native_sprite_gap"]["extra_patches"], [])
        self.assertEqual(r49_cfg["code_patches"], [])

        extra = {p["variable"]: p for p in r49_cfg["native_sprite_gap"]["extra_packs"]}
        self.assertEqual(extra["BM_LANG_R47_DATA_PACK"]["source"], "local/native-modules/lang-r47-v2")
        self.assertEqual(extra["BM_LANG_R47_DATA_PACK"]["size"], r49.EXPECTED_BMLG_SIZE)
        self.assertEqual(extra["BM_LANG_R47_DATA_PACK"]["sha256"], r49.EXPECTED_BMLG_SHA)
        self.assertEqual(extra["BM_LANG_R47_CODE_PACK"]["source"], "local/native-modules/lang-r47-v2")
        self.assertEqual(extra["BM_LANG_R47_CODE_PACK"]["sha256"], r49.EXPECTED_CODE_SHA)

        # Every non-localization pack in r49 must remain identical to r48.
        r48_other = [p for p in r48_cfg["native_sprite_gap"]["extra_packs"] if not p["variable"].startswith("BM_LANG_R47_")]
        r49_other = [p for p in r49_cfg["native_sprite_gap"]["extra_packs"] if not p["variable"].startswith("BM_LANG_R47_")]
        self.assertEqual(r49_other, r48_other)

        r49_hdr = native_sprite_gap.header("demo11-native-product-r49")
        self.assertIn("#define BM_LANG_R47_SUPPORT 1", r49_hdr)
        self.assertIn(",".join(str(b) for b in bytes.fromhex(r49.EXPECTED_BMLG_SHA)), r49_hdr)

        r48_sym = (ROOT / "recomp/targets/demo11-native-product-r48/symbols.toml").read_text()
        r49_sym = (ROOT / "recomp/targets/demo11-native-product-r49/symbols.toml").read_text()
        self.assertEqual(r49_sym.replace("Product R49", "Product R48", 1), r48_sym)

        packs = build_smw_delta.collect_target_packs("demo11-native-product-r49")
        self.assertEqual(len(packs), 71)
        self.assertEqual(len({p["variable"] for p in packs}), 71)

    def test_built_r49_binary_headless_demo7_ow_en_ja_and_jp_fallback(self):
        binary = ROOT / "local/build/demo11-native-product-r49/BrutalMarioDemo11ProductR49SNESRecomp"
        rom = ROOT / "local/restoration/demo11-native-product-r49/rom.sfc"
        if not binary.is_file() or not rom.is_file():
            self.skipTest("demo11-native-product-r49 native binary not built yet")

        bmlg = r49.build_data_pack()
        ja_02a_off = struct.unpack_from("<H", bmlg, 0x0E)[0]
        en_02a_off = struct.unpack_from("<H", bmlg, 0x14)[0]
        ja_ow_off, en_ow_off, ow_flags_off = struct.unpack_from("<HHH", bmlg, 0x18)
        expected_ja_02a = bmlg[ja_02a_off : ja_02a_off + 2048]
        expected_en_02a = bmlg[en_02a_off : en_02a_off + 2048]

        for en_slot in (0x28, 0x2A, 0x13, 0x5E):
            self.assertEqual(bmlg[ow_flags_off + en_slot], 0)
        self.assertEqual(bmlg[ow_flags_off + 0x10], 1)

        env_base = os.environ.copy()
        env_base.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", SNESRECOMP_REWIND="0")
        native_sprite_gap.environment("demo11-native-product-r49", env_base)

        ow_probe_script = (
            (ROOT / "recomp/inputs/cheat-complete-all.script").read_text()
            + "\nturbo on\n"
            + "dump ow28\n"
            + "poke 1f11 0000\npoke 1f17 5800d8015800d801\npoke 1f1f 05001d0005001d00\npoke 0100 0b\nwait 240\nuntil 0100 == 0e 600\nwait 30\ndump ow2a\n"
            + "poke 1f11 0101\npoke 1f17 1800680018006800\npoke 1f1f 0100060001000600\npoke 0100 0b\nwait 240\nuntil 0100 == 0e 600\nwait 30\ndump ow13\n"
            + "poke 1f11 0000\npoke 1f17 1800b8011800b801\npoke 1f1f 01001b0001001b00\npoke 0100 0b\nwait 240\nuntil 0100 == 0e 600\nwait 30\ndump ow10\n"
            + "poke 1f11 0000\npoke 1f17 a8010801a8010801\npoke 1f1f 1a0010001a001000\npoke 0100 0b\nwait 240\nuntil 0100 == 0e 600\nwait 30\ndump ow5e\n"
            + "turbo off\nquit\n"
        )
        ja_script = (ROOT / "recomp/inputs/cheat-complete-all.script").read_text() + "\ndump ow28\nquit\n"

        with tempfile.TemporaryDirectory(prefix="bm-r49-ow-") as tmp:
            tmp_path = Path(tmp)
            cfg = tmp_path / "config.ini"
            cfg.write_text(ppb.format_config_ini("linux"))

            # 1. EN run across 0x28, 0x2A, 0x13, 0x10 (JP auto-fallback), and 0x5E (EN recovery)
            en_dir = tmp_path / "dump_en"
            en_dir.mkdir()
            (en_dir / "saves").mkdir()
            en_script_path = tmp_path / "ow_en.script"
            en_script_path.write_text(ow_probe_script)
            env_en = dict(env_base)
            env_en["BM_LANG"] = "en"
            env_en["SNESRECOMP_DUMP_DIR"] = str(en_dir)
            res_en = subprocess.run(
                [str(binary), "--no-launcher", "--config", str(cfg), "--rom", str(rom), "--script", str(en_script_path)],
                cwd=en_dir,
                env=env_en,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(res_en.returncode, 0, f"en: {res_en.stderr}\n{res_en.stdout}")

            for tag, slot, exp_02a in (
                ("ow28", 0x28, expected_en_02a),
                ("ow2a", 0x2A, expected_en_02a),
                ("ow13", 0x13, expected_en_02a),
                ("ow10", 0x10, expected_ja_02a),
                ("ow5e", 0x5E, expected_en_02a),
            ):
                ow_wram = (en_dir / f"{tag}.wram.bin").read_bytes()
                ow_vram = (en_dir / f"{tag}.vram.bin").read_bytes()
                self.assertEqual(ow_wram[0x0100], 0x0E, f"{tag}: mode 0x{ow_wram[0x0100]:02X}")
                self.assertEqual(ow_vram[0x9000 : 0x9000 + 2048], exp_02a, f"{tag} GFX 0x2A mismatch")
                banner_words = struct.unpack_from("<19H", ow_vram, 0x508B * 2)
                banner_tiles = bytes(w & 0xFF for w in banner_words)
                expected_banner = bmlg[en_ow_off + slot * 19 : en_ow_off + (slot + 1) * 19]
                self.assertEqual(banner_tiles, expected_banner, f"{tag} 0x{slot:02X} banner mismatch")
                self.assertTrue(all((w >> 8) == 0x39 for w in banner_words))

            # 2. JA run confirming 0x28 renders Japanese boss banner + ja_gfx02a
            ja_dir = tmp_path / "dump_ja"
            ja_dir.mkdir()
            (ja_dir / "saves").mkdir()
            ja_script_path = tmp_path / "ow_ja.script"
            ja_script_path.write_text(ja_script)
            env_ja = dict(env_base)
            env_ja["BM_LANG"] = "ja"
            env_ja["SNESRECOMP_DUMP_DIR"] = str(ja_dir)
            res_ja = subprocess.run(
                [str(binary), "--no-launcher", "--config", str(cfg), "--rom", str(rom), "--script", str(ja_script_path)],
                cwd=ja_dir,
                env=env_ja,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(res_ja.returncode, 0, f"ja: {res_ja.stderr}\n{res_ja.stdout}")
            ja_wram = (ja_dir / "ow28.wram.bin").read_bytes()
            ja_vram = (ja_dir / "ow28.vram.bin").read_bytes()
            self.assertEqual(ja_wram[0x0100], 0x0E)
            self.assertEqual(ja_vram[0x9000 : 0x9000 + 2048], expected_ja_02a)
            ja_words = struct.unpack_from("<19H", ja_vram, 0x508B * 2)
            self.assertEqual(
                bytes(w & 0xFF for w in ja_words),
                bmlg[ja_ow_off + 0x28 * 19 : ja_ow_off + 0x29 * 19],
            )
            self.assertTrue(all((w >> 8) == 0x39 for w in ja_words))

    def test_built_r49_preserves_room116_countdown_gfx_when_1f01_bit7_set(self):
        binary = ROOT / "local/build/demo11-native-product-r49/BrutalMarioDemo11ProductR49SNESRecomp"
        rom_path = ROOT / "local/restoration/demo11-native-product-r49/rom.sfc"
        if not binary.is_file() or not rom_path.is_file():
            self.skipTest("demo11-native-product-r49 native binary not built yet")

        rom = rom_path.read_bytes()
        exp_12a, _ = lz2(rom, graphics_pointer(rom, 0x12A), limit=0x10000)
        exp_031, _ = lz2(rom, graphics_pointer(rom, 0x31), limit=0x10000)

        env = os.environ.copy()
        env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", SNESRECOMP_REWIND="0", BM_LANG="en")
        native_sprite_gap.environment("demo11-native-product-r49", env)

        with tempfile.TemporaryDirectory(prefix="bm-r49-room116-") as tmp:
            tp = Path(tmp)
            (tp / "saves").mkdir()
            cfg = tp / "config.ini"
            cfg.write_text(ppb.format_config_ini("linux"))
            script = (
                "turbo on\nuntil 0100 == 07 4000\nwait 10\npress start 2\nuntil 0100 == 08 900\nwait 180\n"
                "press start 2\nuntil16 010b == 01c5 900\nuntil 0100 == 14 600\nwait 60\npress a 2\n"
                "until16 010b == 014b 900\nuntil 0100 == 14 600\nwait 60\npress b 2\n"
                "until16 010b == 014c 900\nuntil 0100 == 14 600\nwait 60\npress a 2\n"
                "until16 010b == 014d 900\nuntil 0100 == 14 600\nwait 60\npress b 2\n"
                "until 0100 == 0e 2400\n"
                + "poke 1ea2 " + ("9f" * 0x60) + "\n"
                + "poke 1f11 0606\npoke 1f17 2801e8012801e801\npoke 1f1f 12001e0012001e00\n"
                + "poke 0100 0b\nuntil 0100 == 0e 1600\npoke d7e2 6a\npress y 2\nuntil 0100 == 14 1200\n"
                + "poke 19b8 16\npoke 19d8 05\npoke 88 0000\npoke 71 06\n"
                + "until16 10b == 116 1600\nuntil 0100 == 14 600\nwait 10\ndump f1\nquit\n"
            )
            sc = tp / "room116.script"
            sc.write_text(script)
            env["SNESRECOMP_DUMP_DIR"] = str(tp)
            res = subprocess.run(
                [str(binary), "--no-launcher", "--config", str(cfg), "--rom", str(rom_path), "--script", str(sc)],
                cwd=tp,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(res.returncode, 0, f"r49 room 0x116 failed: {res.stderr}\n{res.stdout}")
            f1_wram = (tp / "f1.wram.bin").read_bytes()
            f1_vram = (tp / "f1.vram.bin").read_bytes()
            self.assertEqual(f1_wram[0x010B] | (f1_wram[0x010C] << 8), 0x116)
            self.assertEqual(f1_wram[0x1F01], 0x9F)
            self.assertEqual(f1_vram[0x6800 * 2 : 0x7000 * 2], exp_12a)
            self.assertNotEqual(f1_vram[0x6800 * 2 : 0x6800 * 2 + 2048], exp_031)


if __name__ == "__main__":
    unittest.main()
