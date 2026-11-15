#!/usr/bin/env python3
"""Verify demo11-native-product-r50 true New-Save Yoshi's House InitialSaveData and 1-1 teleport removal."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import native_sprite_gap
import package_public_beta as ppb
import prepare_product_r49 as r49
import prepare_product_r50 as r50

TARGET = "demo11-native-product-r50"
BINARY = ROOT / "local/build" / TARGET / "BrutalMarioDemo11ProductR50SNESRecomp"
ROM_PATH = ROOT / "local/restoration" / TARGET / "rom.sfc"
CAPTURE_ROOT = ROOT / "local/captures/r50-yoshi-start-verify"

SKIP_INTRO_SCRIPT = (
    "until16 010b == 01c5 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "press a 2\n"
    "until16 010b == 014b 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "press b 2\n"
    "until16 010b == 014c 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "press a 2\n"
    "until16 010b == 014d 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "press b 2\n"
)

BOOT_TO_FILE_SELECT = (
    "until 0100 == 07 4000\n"
    "wait 10\n"
    "press start 2\n"
    "until 0100 == 08 900\n"
    "wait 180\n"
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_wram_vram(session_dir: Path, tag: str) -> tuple[bytes, bytes]:
    return (
        (session_dir / f"{tag}.wram.bin").read_bytes(),
        (session_dir / f"{tag}.vram.bin").read_bytes(),
    )


def _ow_state(wram: bytes) -> dict[str, int | tuple[int, int]]:
    return {
        "mode": wram[0x0100],
        "room": wram[0x010B] | (wram[0x010C] << 8),
        "map": wram[0x1F11],
        "intro_flag": wram[0x0109],
        "mario_px": struct.unpack_from("<HH", wram, 0x1F17),
        "luigi_px": struct.unpack_from("<HH", wram, 0x1F1B),
        "mario_tile": struct.unpack_from("<HH", wram, 0x1F1F),
        "luigi_tile": struct.unpack_from("<HH", wram, 0x1F23),
    }


def _hud_banner_words(vram: bytes) -> tuple[int, ...]:
    return struct.unpack_from("<19H", vram, 0x508B * 2)


def _run_session(session_dir: Path, script_text: str, seed_srm: Path | None = None) -> dict:
    """Execute one isolated OS process of the r50 binary inside `session_dir`."""
    if session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True)
    saves_dir = session_dir / "saves"
    saves_dir.mkdir()
    if seed_srm is not None:
        shutil.copy2(seed_srm, saves_dir / "save.srm")

    cfg_path = session_dir / "config.ini"
    cfg_path.write_text(ppb.format_config_ini("linux"), encoding="utf-8")

    script_path = session_dir / "route.script"
    script_path.write_text(script_text, encoding="utf-8")

    env = {k: v for k, v in os.environ.items() if not k.startswith(("BM_", "SNESRECOMP_", "M1_"))}
    env.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        SNESRECOMP_REWIND="0",
        BM_LANG="en",
        SNESRECOMP_DUMP_DIR=str(session_dir),
    )
    native_sprite_gap.environment(TARGET, env)

    res = subprocess.run(
        [
            str(BINARY),
            "--no-launcher",
            "--config",
            str(cfg_path),
            "--rom",
            str(ROM_PATH),
            "--script",
            str(script_path),
        ],
        cwd=session_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    (session_dir / "run.log").write_text(res.stdout + res.stderr, encoding="utf-8")
    if res.returncode != 0:
        raise AssertionError(
            f"session {session_dir.name} failed (rc={res.returncode}):\n{res.stderr}\n{res.stdout}"
        )
    if "exit: script quit" not in res.stderr:
        raise AssertionError(f"session {session_dir.name} missing script quit exit marker")
    return {
        "session": session_dir.name,
        "script_sha256": _sha256(script_path.read_bytes()),
        "sram_sha256": _sha256((saves_dir / "save.srm").read_bytes()) if (saves_dir / "save.srm").is_file() else None,
    }


class ProductR50YoshiStartTests(unittest.TestCase):
    _captures_ready = False

    @classmethod
    def _ensure_captures(cls) -> None:
        if cls._captures_ready:
            return
        if not BINARY.is_file() or not ROM_PATH.is_file():
            raise unittest.SkipTest("demo11-native-product-r50 binary or ROM not built yet")

        CAPTURE_ROOT.mkdir(parents=True, exist_ok=True)

        # Session 1: Scenarios (b) + (c) — fresh saves/, File A New Save -> Yoshi's House -> walk to 1-1 -> enter 0x105.
        s1_dir = CAPTURE_ROOT / "session1_new_save_and_1_1"
        s1_meta = _run_session(
            s1_dir,
            "turbo on\n"
            + BOOT_TO_FILE_SELECT
            + "press start 2\n"
            + SKIP_INTRO_SCRIPT
            + "until 0100 == 0e 2400\n"
            + "dump b_ow0\n"
            + "wait 60\n"
            + "dump b_ow60\n"
            + "press left 30\n"
            + "wait 30\n"
            + "dump c_11_start\n"
            + "wait 120\n"
            + "dump c_11_hold120\n"
            + "press y 2\n"
            + "until 0100 == 14 600\n"
            + "wait 30\n"
            + "dump c_enter105\n"
            + "quit\n",
        )
        s1_srm = s1_dir / "saves/save.srm"

        # Session 2: Scenario (d) Case A — fresh OS process loading File A saved at 1-1 (72, 408).
        s2_dir = CAPTURE_ROOT / "session2_reload_from_1_1"
        s2_meta = _run_session(
            s2_dir,
            "turbo on\n"
            + BOOT_TO_FILE_SELECT
            + "press start 2\n"
            + "until 0100 == 0e 1200\n"
            + "dump da_start\n"
            + "wait 120\n"
            + "dump da_hold120\n"
            + "press right 30\n"
            + "wait 30\n"
            + "dump da_yoshi\n"
            + "press left 30\n"
            + "wait 120\n"
            + "dump da_back11_120\n"
            + "press right 30\n"
            + "wait 30\n"
            + "dump da_yoshi2\n"
            + "press y 2\n"
            + "until 0100 == 14 600\n"
            + "dump da_enter_yoshi\n"
            + "wait 60\n"
            + "quit\n",
            seed_srm=s1_srm,
        )
        s2_srm = s2_dir / "saves/save.srm"

        # Session 3: Scenario (d) Case B — fresh OS process loading File A saved at Yoshi's House (104, 408).
        s3_dir = CAPTURE_ROOT / "session3_reload_from_yoshi"
        s3_meta = _run_session(
            s3_dir,
            "turbo on\n"
            + BOOT_TO_FILE_SELECT
            + "press start 2\n"
            + "until 0100 == 0e 1200\n"
            + "dump db_start\n"
            + "wait 60\n"
            + "press left 30\n"
            + "wait 30\n"
            + "dump db_11_start\n"
            + "wait 120\n"
            + "dump db_11_120\n"
            + "quit\n",
            seed_srm=s2_srm,
        )

        # Session 4: Scenario (e) — same session after File A at (72, 408), soft reset -> New Save File B.
        s4_dir = CAPTURE_ROOT / "session4_file_b_same_session"
        s4_meta = _run_session(
            s4_dir,
            "turbo on\n"
            + BOOT_TO_FILE_SELECT
            + "press start 2\n"
            + "until 0100 == 0e 1200\n"
            + "wait 30\n"
            + "dump e_filea_11\n"
            + "reset\n"
            + BOOT_TO_FILE_SELECT
            + "press down 2\n"
            + "wait 20\n"
            + "press start 2\n"
            + SKIP_INTRO_SCRIPT
            + "until 0100 == 0e 2400\n"
            + "dump e_fileb_ow0\n"
            + "wait 60\n"
            + "dump e_fileb_ow60\n"
            + "quit\n",
            seed_srm=s1_srm,
        )

        receipt = {
            "target": TARGET,
            "rom_sha256": _sha256(ROM_PATH.read_bytes()),
            "binary_sha256": _sha256(BINARY.read_bytes()),
            "bmlg_sha256": r49.EXPECTED_BMLG_SHA,
            "sessions": [s1_meta, s2_meta, s3_meta, s4_meta],
        }
        (CAPTURE_ROOT / "receipt.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        cls._captures_ready = True

    def _expected_ow_banners(self) -> tuple[bytes, bytes]:
        bmlg = r49.build_data_pack()
        en_ow_off = struct.unpack_from("<H", bmlg, 0x1A)[0]
        banner_28 = bmlg[en_ow_off + 0x28 * 19 : en_ow_off + 0x29 * 19]
        banner_29 = bmlg[en_ow_off + 0x29 * 19 : en_ow_off + 0x2A * 19]
        return banner_28, banner_29

    def _assert_banner(
        self,
        vram: bytes,
        expected: bytes,
        other: bytes,
        label: str,
        *,
        full: bool = True,
    ) -> None:
        words = _hud_banner_words(vram)
        tiles = bytes(w & 0xFF for w in words)
        if full:
            self.assertEqual(tiles, expected, f"{label}: expected full 19-tile banner")
            self.assertNotEqual(tiles, other, f"{label}: unexpected banner match")
            self.assertTrue(all((w >> 8) == 0x39 for w in words), f"{label}: expected 0x39 attrs")
        else:
            # Initial Overworld HUD draw clears trailing columns 28-29 to 0x38FE, leaving the 17-tile name intact.
            self.assertEqual(tiles[:17], expected[:17], f"{label}: expected 17-tile banner prefix")
            self.assertNotEqual(tiles[:17], other[:17], f"{label}: unexpected banner prefix match")

    def test_a_recipe_rom_diff_and_runtime_hook_removed(self) -> None:
        native_seven_src = (ROOT / "recomp/native_seven.c").read_text(encoding="utf-8")
        self.assertNotIn("bm_yoshi_start_override", native_seven_src)
        self.assertNotIn("BM_YOSHI_START", native_seven_src)

        r49_cfg = json.loads((ROOT / "config/restorations/demo11-native-product-r49.json").read_text())
        r50_cfg = json.loads((ROOT / "config/restorations/demo11-native-product-r50.json").read_text())
        self.assertEqual(r50_cfg["id"], TARGET)
        self.assertEqual(r50_cfg["parent_restoration"], "demo11-native-product-r49")
        self.assertEqual(r50_cfg["base_restoration"], "demo11-native-product-r49")
        self.assertEqual(r50_cfg["output"], {"size": 4194304, "sha256": r50.EXPECTED_R50_ROM_SHA})
        self.assertEqual(
            r50_cfg["native_sprite_gap"]["extra_packs"],
            r49_cfg["native_sprite_gap"]["extra_packs"],
        )
        self.assertEqual(len(r50_cfg["code_patches"]), 4)
        self.assertEqual(
            [p["address"] for p in r50_cfg["code_patches"]],
            ["001EF6", "001EFA", "001EFE", "001F02"],
        )

        r49_sym = (ROOT / "recomp/targets/demo11-native-product-r49/symbols.toml").read_text()
        r50_sym = (ROOT / "recomp/targets/demo11-native-product-r50/symbols.toml").read_text()
        self.assertEqual(r50_sym.replace("Product R50", "Product R49", 1), r49_sym)

        packs = build_smw_delta.collect_target_packs(TARGET)
        self.assertEqual(len(packs), 71)
        self.assertEqual(len({p["variable"] for p in packs}), 71)

        r49_rom_path = ROOT / "local/restoration/demo11-native-product-r49/rom.sfc"
        demo7_rom_path = ROOT / "local/content-versions/demo7/rom.sfc"
        if not r49_rom_path.is_file() or not ROM_PATH.is_file() or not demo7_rom_path.is_file():
            self.skipTest("local restoration or demo7 ROM files not present")

        r49_rom = r49_rom_path.read_bytes()
        r50_rom = ROM_PATH.read_bytes()
        demo7_rom = demo7_rom_path.read_bytes()
        self.assertEqual(_sha256(r49_rom), r50.R49_SHA)
        self.assertEqual(_sha256(r50_rom), r50.EXPECTED_R50_ROM_SHA)
        self.assertEqual(_sha256(demo7_rom), r50.DEMO7_SHA)

        diffs = [i for i in range(len(r49_rom)) if r49_rom[i] != r50_rom[i]]
        self.assertEqual(diffs, [0x1EF6, 0x1EFA, 0x1EFE, 0x1F02])
        self.assertEqual(r50_rom[0x1EF0:0x1F06], demo7_rom[0x1EF0:0x1F06])

        manifest_path = ROOT / "local/restoration" / TARGET / "input-manifest.json"
        self.assertTrue(manifest_path.is_file())
        input_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            input_manifest["content"]["files"]["recomp/native_seven.c"],
            _sha256((ROOT / "recomp/native_seven.c").read_bytes()),
        )

    def test_b_new_save_initial_position_and_hud_banner(self) -> None:
        self._ensure_captures()
        banner_28, banner_29 = self._expected_ow_banners()
        s1_dir = CAPTURE_ROOT / "session1_new_save_and_1_1"

        w0, v0 = _load_wram_vram(s1_dir, "b_ow0")
        st0 = _ow_state(w0)
        self.assertEqual(st0["mode"], 0x0E)
        self.assertEqual(st0["map"], 0x00)
        self.assertEqual(st0["intro_flag"], 0x00)
        self.assertEqual(st0["mario_px"], (104, 408))
        self.assertEqual(st0["luigi_px"], (104, 408))
        self.assertEqual(st0["mario_tile"], (6, 25))
        self.assertEqual(st0["luigi_tile"], (6, 25))
        self._assert_banner(v0, banner_28, banner_29, "b_ow0", full=True)

        w60, v60 = _load_wram_vram(s1_dir, "b_ow60")
        st60 = _ow_state(w60)
        self.assertEqual(st60["mode"], 0x0E)
        self.assertEqual(st60["mario_px"], (104, 408))
        self.assertEqual(st60["luigi_px"], (104, 408))
        self.assertEqual(st60["mario_tile"], (6, 25))
        self.assertEqual(st60["luigi_tile"], (6, 25))
        self._assert_banner(v60, banner_28, banner_29, "b_ow60", full=False)

    def test_c_walk_onto_1_1_stays_without_teleport_and_saves(self) -> None:
        self._ensure_captures()
        banner_28, banner_29 = self._expected_ow_banners()
        s1_dir = CAPTURE_ROOT / "session1_new_save_and_1_1"

        for tag in ("c_11_start", "c_11_hold120"):
            w, v = _load_wram_vram(s1_dir, tag)
            st = _ow_state(w)
            self.assertEqual(st["mode"], 0x0E, tag)
            self.assertEqual(st["mario_px"], (72, 408), tag)
            self.assertEqual(st["mario_tile"], (4, 25), tag)
            self._assert_banner(v, banner_29, banner_28, tag, full=True)

        w_enter, _ = _load_wram_vram(s1_dir, "c_enter105")
        st_enter = _ow_state(w_enter)
        self.assertEqual(st_enter["mode"], 0x14)
        self.assertEqual(st_enter["room"], 0x0105)

        srm = (s1_dir / "saves/save.srm").read_bytes()
        self.assertEqual(len(srm), 32768)
        # File A SRAM slot starts at 0x006F ($1F11 - $1EA2); +6/+10 are pixel X, +14/+18 are tile X.
        self.assertEqual(struct.unpack_from("<HHHH", srm, 0x75), (72, 408, 72, 408))
        self.assertEqual(struct.unpack_from("<HHHH", srm, 0x7D), (4, 25, 4, 25))

    def test_d_fresh_process_existing_save_reload_case_a_and_case_b(self) -> None:
        self._ensure_captures()
        banner_28, banner_29 = self._expected_ow_banners()

        # Case A: reload File A saved at 1-1 (72, 408) -> stays on 1-1 -> walk to Yoshi's House -> back to 1-1 -> save at Yoshi's House.
        s2_dir = CAPTURE_ROOT / "session2_reload_from_1_1"
        for tag, full in (("da_start", True), ("da_hold120", False), ("da_back11_120", True)):
            w, v = _load_wram_vram(s2_dir, tag)
            st = _ow_state(w)
            self.assertEqual(st["mode"], 0x0E, tag)
            self.assertEqual(st["mario_px"], (72, 408), tag)
            self.assertEqual(st["mario_tile"], (4, 25), tag)
            self._assert_banner(v, banner_29, banner_28, tag, full=full)

        for tag in ("da_yoshi", "da_yoshi2"):
            w, v = _load_wram_vram(s2_dir, tag)
            st = _ow_state(w)
            self.assertEqual(st["mode"], 0x0E, tag)
            self.assertEqual(st["mario_px"], (104, 408), tag)
            self.assertEqual(st["mario_tile"], (6, 25), tag)
            self._assert_banner(v, banner_28, banner_29, tag, full=True)

        w_yenter, _ = _load_wram_vram(s2_dir, "da_enter_yoshi")
        st_yenter = _ow_state(w_yenter)
        self.assertEqual(st_yenter["mode"], 0x14)
        self.assertEqual(st_yenter["room"], 0x0104)

        s2_srm = (s2_dir / "saves/save.srm").read_bytes()
        self.assertEqual(struct.unpack_from("<HHHH", s2_srm, 0x75), (104, 408, 104, 408))
        self.assertEqual(struct.unpack_from("<HHHH", s2_srm, 0x7D), (6, 25, 6, 25))

        # Case B: reload File A saved at Yoshi's House (104, 408) -> walk onto 1-1 -> stays at (72, 408).
        s3_dir = CAPTURE_ROOT / "session3_reload_from_yoshi"
        wb0, vb0 = _load_wram_vram(s3_dir, "db_start")
        stb0 = _ow_state(wb0)
        self.assertEqual(stb0["mode"], 0x0E)
        self.assertEqual(stb0["mario_px"], (104, 408))
        self.assertEqual(stb0["mario_tile"], (6, 25))
        self._assert_banner(vb0, banner_28, banner_29, "db_start", full=True)

        for tag in ("db_11_start", "db_11_120"):
            wb11, vb11 = _load_wram_vram(s3_dir, tag)
            stb11 = _ow_state(wb11)
            self.assertEqual(stb11["mode"], 0x0E, tag)
            self.assertEqual(stb11["mario_px"], (72, 408), tag)
            self.assertEqual(stb11["mario_tile"], (4, 25), tag)
            self._assert_banner(vb11, banner_29, banner_28, tag, full=True)

    def test_e_second_new_save_file_b_same_session(self) -> None:
        self._ensure_captures()
        banner_28, banner_29 = self._expected_ow_banners()
        s4_dir = CAPTURE_ROOT / "session4_file_b_same_session"

        wa, _ = _load_wram_vram(s4_dir, "e_filea_11")
        sta = _ow_state(wa)
        self.assertEqual(sta["mode"], 0x0E)
        self.assertEqual(sta["mario_px"], (72, 408))
        self.assertEqual(sta["mario_tile"], (4, 25))

        wb0, vb0 = _load_wram_vram(s4_dir, "e_fileb_ow0")
        stb0 = _ow_state(wb0)
        self.assertEqual(stb0["mode"], 0x0E)
        self.assertEqual(stb0["map"], 0x00)
        self.assertEqual(stb0["intro_flag"], 0x00)
        self.assertEqual(stb0["mario_px"], (104, 408))
        self.assertEqual(stb0["luigi_px"], (104, 408))
        self.assertEqual(stb0["mario_tile"], (6, 25))
        self.assertEqual(stb0["luigi_tile"], (6, 25))
        self._assert_banner(vb0, banner_28, banner_29, "e_fileb_ow0", full=True)

        wb60, vb60 = _load_wram_vram(s4_dir, "e_fileb_ow60")
        stb60 = _ow_state(wb60)
        self.assertEqual(stb60["mode"], 0x0E)
        self.assertEqual(stb60["mario_px"], (104, 408))
        self.assertEqual(stb60["luigi_px"], (104, 408))
        self.assertEqual(stb60["mario_tile"], (6, 25))
        self.assertEqual(stb60["luigi_tile"], (6, 25))
        self._assert_banner(vb60, banner_28, banner_29, "e_fileb_ow60", full=False)


if __name__ == "__main__":
    unittest.main()
