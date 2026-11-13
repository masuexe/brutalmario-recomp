#!/usr/bin/env python3
import array
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_smw_delta
import prepare_product_r45 as p45
import prepare_product_r46 as p46
from restore_star_world_1 import graphics_pointer, lz2


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_bank_counts(log_text: str, bank: str) -> tuple[int, int]:
    match = re.search(
        rf"\[native-seven\] bank={bank} resolutions=(\d+) executed_page_instructions=(\d+)",
        log_text,
    )
    if match is None:
        raise AssertionError(f"missing bank={bank} summary line in run.log")
    return int(match.group(1)), int(match.group(2))


def _load_dump(cap_dir: Path, label: str) -> tuple[bytes, bytes, bytes]:
    wram = (cap_dir / f"{label}.wram.bin").read_bytes()
    vram = (cap_dir / f"{label}.vram.bin").read_bytes()
    cgram = (cap_dir / f"{label}.cgram.bin").read_bytes()
    return wram, vram, cgram


def _bg3_39xx_count(vram: bytes) -> int:
    words = struct.unpack("<" + "H" * 512, vram[0xB200:0xB600])
    return sum(1 for w in words if (w & 0xFF00) == 0x3900 and (w & 0xFF) != 0xFC)


def _wav_rms(wav_path: Path, frame_start: int, frame_end: int) -> float:
    with wave.open(str(wav_path), "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    samples = array.array("h", raw)
    # 32040 Hz / 60 fps = 534 stereo frames/video frame = 1068 int16 samples/frame.
    spf = 534 * 2
    chunk = samples[frame_start * spf : frame_end * spf]
    if not chunk:
        raise AssertionError(f"empty WAV slice for frames {frame_start}..{frame_end}")
    return math.sqrt(sum(s * s for s in chunk) / len(chunk))


class Room1C5IntroCutsceneTest(unittest.TestCase):
    def test_pack_recipe_and_rom_diff(self) -> None:
        pack_dir = ROOT / p46.PACK_SOURCE
        data_path = pack_dir / p46.DATA_PACK_FILE
        code_path = pack_dir / p46.CODE_PACK_FILE
        r45_rom_path = ROOT / "local/restoration" / p46.PARENT / "rom.sfc"
        r46_rom_path = ROOT / "local/restoration" / p46.TARGET / "rom.sfc"
        cheap_rom_path = ROOT / "local/content-versions/cheap-demo/rom.sfc"

        for required in (data_path, code_path, r45_rom_path, r46_rom_path, cheap_rom_path):
            self.assertTrue(required.exists(), f"missing {required}")

        r45_rom = r45_rom_path.read_bytes()
        r46_rom = r46_rom_path.read_bytes()
        cheap_rom = cheap_rom_path.read_bytes()

        self.assertEqual(_sha256(r45_rom), p46.R45_SHA)
        self.assertEqual(_sha256(cheap_rom), p46.CHEAP_DEMO_SHA)

        expected_data = p46.build_data_pack(cheap_rom, r45_rom)
        expected_code = p46.build_code_pack()
        self.assertEqual(data_path.read_bytes(), expected_data)
        self.assertEqual(code_path.read_bytes(), expected_code)
        self.assertEqual(len(expected_data), p46.DATA_PACK_SIZE)
        self.assertEqual(len(expected_code), 123)

        patches = p46.build_patches()
        self.assertEqual(len(patches), 15)
        expected_offsets = sorted(
            patch["offset"] + j
            for patch in patches
            for j, (b, a) in enumerate(
                zip(bytes.fromhex(patch["before"]), bytes.fromhex(patch["after"]))
            )
            if b != a
        )
        diffs = [i for i in range(len(r45_rom)) if r45_rom[i] != r46_rom[i]]
        self.assertEqual(diffs, expected_offsets)
        self.assertEqual(len(diffs), 56)

        manifest = json.loads(
            (ROOT / "config/restorations" / f"{p46.TARGET}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["base_restoration"], p46.PARENT)
        self.assertEqual(manifest["parent_restoration"], p46.PARENT)
        self.assertEqual(manifest["output"]["sha256"], _sha256(r46_rom))
        nsg = manifest["native_sprite_gap"]
        self.assertEqual(len(nsg["frozen_manifests"]), 50)
        self.assertEqual(len(nsg["extra_packs"]), 14)
        self.assertEqual(nsg["extra_packs"][-2]["variable"], p46.DATA_PACK_VAR)
        self.assertEqual(nsg["extra_packs"][-2]["address"], "D48000")
        self.assertFalse(nsg["extra_packs"][-2]["executable"])
        self.assertEqual(nsg["extra_packs"][-1]["variable"], p46.CODE_PACK_VAR)
        self.assertEqual(nsg["extra_packs"][-1]["address"], "89B000")
        self.assertTrue(nsg["extra_packs"][-1]["executable"])
        self.assertEqual(len(nsg["extra_patches"]), 15)
        self.assertEqual(len(manifest["code_patches"]), 15)

        input_manifest = json.loads(
            (ROOT / "local/restoration" / p46.TARGET / "input-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(input_manifest["config"]["output"]["sha256"], _sha256(r46_rom))

    def test_defaults_promoted_to_r46(self) -> None:
        for tool_name in (
            "launch_native.py",
            "play_native_target.py",
            "play_native_cheats.py",
            "build_smw_delta.py",
            "package_public_beta.py",
        ):
            src = (TOOLS_DIR / tool_name).read_text(encoding="utf-8")
            self.assertRegex(
                src,
                r"""--target["']\s*,\s*default\s*=\s*["']demo11-native-product-r(?:4[6-9]|[5-9]\d)["']""",
                f"{tool_name} missing r46+ --target default",
            )
        pkg_src = (TOOLS_DIR / "package_public_beta.py").read_text(encoding="utf-8")
        self.assertRegex(pkg_src, r"""ROOT\s*/\s*["']dist/public-beta-r(?:4[6-9]|[5-9]\d)["']""")
        self.assertRegex(pkg_src, r"""ROOT\s*/\s*["']local/diagnostics/public-beta-r(?:4[6-9]|[5-9]\d)["']""")

        packs = build_smw_delta.collect_target_packs(p46.TARGET)
        self.assertEqual(len(packs), 69)
        by_var = {pack["variable"]: pack for pack in packs}
        self.assertIn(p46.DATA_PACK_VAR, by_var)
        self.assertIn(p46.CODE_PACK_VAR, by_var)
        self.assertEqual(by_var[p46.DATA_PACK_VAR]["size"], p46.DATA_PACK_SIZE)
        self.assertEqual(by_var[p46.CODE_PACK_VAR]["size"], 123)

    def test_capture_r46_room1c5_intro(self) -> None:
        cap = ROOT / "local/captures/r46-room1c5-intro"
        script_path = ROOT / "recomp/inputs/native-room1c5-intro.script"
        r46_rom = (ROOT / "local/restoration" / p46.TARGET / "rom.sfc").read_bytes()
        r45_rom = (ROOT / "local/restoration" / p46.PARENT / "rom.sfc").read_bytes()
        cheap_rom = (ROOT / "local/content-versions/cheap-demo/rom.sfc").read_bytes()

        receipt = json.loads((cap / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["target"], p46.TARGET)
        self.assertEqual(receipt["rom_sha256"], _sha256(r46_rom))
        self.assertEqual(receipt["route_sha256"], _sha256(script_path.read_bytes()))
        self.assertTrue(receipt["audio_diagnostics"])

        run_log = (cap / "run.log").read_text(encoding="utf-8")
        d4_res, d4_exec = _parse_bank_counts(run_log, "D4")
        b89_res, b89_exec = _parse_bank_counts(run_log, "89")
        self.assertGreater(d4_res, 0)
        self.assertEqual(d4_exec, 0)
        self.assertGreater(b89_res, 0)
        self.assertGreater(b89_exec, 0)

        jp_02a, _ = lz2(cheap_rom, graphics_pointer(cheap_rom, 0x2A))
        en_02a, _ = lz2(r45_rom, graphics_pointer(r45_rom, 0x2A))
        dec_23a, _ = lz2(cheap_rom, p46.EXGFX_23A_PTR)
        dec_239, _ = lz2(cheap_rom, p46.EXGFX_239_PTR)
        dec_23c, _ = lz2(cheap_rom, p46.EXGFX_23C_PTR)
        pal_1c5 = cheap_rom[0x2BDA95 + 2 : 0x2BDA95 + 514]

        w_title, v_title, _ = _load_dump(cap, "title")
        self.assertEqual(w_title[0x0100], 0x07)
        self.assertEqual(w_title[0x010B] | (w_title[0x010C] << 8), 0x00C7)
        self.assertEqual(w_title[0x0DDA], 0x02)
        self.assertEqual(v_title[0x9000:0x9800], en_02a)

        w_files, _, _ = _load_dump(cap, "files")
        self.assertEqual(w_files[0x0100], 0x08)

        for lbl, expected_room in (
            ("room1c5", 0x01C5),
            ("room14b", 0x014B),
            ("room14c", 0x014C),
            ("room14d", 0x014D),
        ):
            wram, vram, cgram = _load_dump(cap, lbl)
            self.assertEqual(wram[0x0100], 0x14, lbl)
            self.assertEqual(wram[0x010B] | (wram[0x010C] << 8), expected_room, lbl)
            self.assertEqual(wram[0x0DDA], 0x1E, lbl)
            self.assertEqual(vram[0x9000:0x9800], jp_02a, lbl)
            self.assertGreater(_bg3_39xx_count(vram), 0, lbl)
            if lbl == "room1c5":
                self.assertEqual(vram[0x2000:0x3000], dec_239)
                self.assertEqual(vram[0x3000:0x4000], dec_23a)
                same_23c = sum(
                    1
                    for i in range(128)
                    if vram[0x1000 + i * 32 : 0x1000 + (i + 1) * 32]
                    == dec_23c[i * 32 : (i + 1) * 32]
                )
                self.assertEqual(same_23c, 116)
                cgram_diffs = [
                    i // 2
                    for i in range(0, 512, 2)
                    if cgram[i : i + 2] != pal_1c5[i : i + 2]
                ]
                self.assertEqual(cgram_diffs, [0x64])

        w_ow, v_ow, _ = _load_dump(cap, "ow")
        self.assertEqual(w_ow[0x0100], 0x0E)
        self.assertEqual(w_ow[0x1F11], 0x00)
        self.assertEqual(w_ow[0x0109], 0x00)
        self.assertEqual(v_ow[0x9000:0x9800], en_02a)
        # Row 4 of Overworld BG3 HUD displays "Hey, I am Mario!" (tiles 07 44 58 1d 08 1f 40 4c 1f 0c 40 51 48 4e 1a).
        hud_row4 = [
            x & 0xFF
            for x in struct.unpack("<32H", v_ow[0xA000 + 4 * 64 : 0xA000 + 5 * 64])
        ]
        self.assertEqual(
            hud_row4[11:26],
            [0x07, 0x44, 0x58, 0x1D, 0x08, 0x1F, 0x40, 0x4C, 0x1F, 0x0C, 0x40, 0x51, 0x48, 0x4E, 0x1A],
        )

        w_node, _, _ = _load_dump(cap, "ow_node")
        self.assertEqual(w_node[0x0100], 0x0E)
        self.assertEqual(w_node[0x1F17] | (w_node[0x1F18] << 8), 0x0048)
        self.assertEqual(w_node[0x1F19] | (w_node[0x1F1A] << 8), 0x0198)

        w_course, v_course, _ = _load_dump(cap, "course104")
        self.assertEqual(w_course[0x0100], 0x14)
        self.assertEqual(w_course[0x010B] | (w_course[0x010C] << 8), 0x0105)
        self.assertEqual(v_course[0x9000:0x9800], en_02a)

        w_reload, v_reload, _ = _load_dump(cap, "reload_ow")
        self.assertEqual(w_reload[0x0100], 0x0E)
        self.assertEqual(w_reload[0x1F11], 0x00)
        self.assertEqual(w_reload[0x0109], 0x00)
        self.assertEqual(w_reload[0x1F17] | (w_reload[0x1F18] << 8), 0x0048)
        self.assertEqual(w_reload[0x1F19] | (w_reload[0x1F1A] << 8), 0x0198)
        self.assertEqual(v_reload[0x9000:0x9800], en_02a)

        audio_stats = json.loads((cap / "audio-stats.json").read_text(encoding="utf-8"))
        self.assertEqual(audio_stats["wav_result"], 0)
        self.assertGreater(audio_stats["produced"], 0)
        wav_path = cap / "audio.wav"
        self.assertGreater(_wav_rms(wav_path, 300, 420), 100.0)
        self.assertEqual(_wav_rms(wav_path, 900, 3100), 0.0)
        self.assertGreater(_wav_rms(wav_path, 3400, 3530), 100.0)

    def test_capture_r46_room1c5_skip_and_pause(self) -> None:
        cap = ROOT / "local/captures/r46-room1c5-skip2"
        script_path = ROOT / "recomp/inputs/native-room1c5-skip.script"
        r46_rom = (ROOT / "local/restoration" / p46.TARGET / "rom.sfc").read_bytes()
        r45_rom = (ROOT / "local/restoration" / p46.PARENT / "rom.sfc").read_bytes()
        cheap_rom = (ROOT / "local/content-versions/cheap-demo/rom.sfc").read_bytes()

        receipt = json.loads((cap / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["target"], p46.TARGET)
        self.assertEqual(receipt["rom_sha256"], _sha256(r46_rom))
        self.assertEqual(receipt["route_sha256"], _sha256(script_path.read_bytes()))

        run_log = (cap / "run.log").read_text(encoding="utf-8")
        d4_res, d4_exec = _parse_bank_counts(run_log, "D4")
        b89_res, b89_exec = _parse_bank_counts(run_log, "89")
        self.assertGreater(d4_res, 0)
        self.assertEqual(d4_exec, 0)
        self.assertGreater(b89_res, 0)
        self.assertGreater(b89_exec, 0)

        jp_02a, _ = lz2(cheap_rom, graphics_pointer(cheap_rom, 0x2A))
        en_02a, _ = lz2(r45_rom, graphics_pointer(r45_rom, 0x2A))

        w_paused, v_paused, _ = _load_dump(cap, "paused")
        self.assertEqual(w_paused[0x0100], 0x14)
        self.assertEqual(w_paused[0x010B] | (w_paused[0x010C] << 8), 0x01C5)
        self.assertEqual(w_paused[0x13D4], 0x01)
        self.assertEqual(v_paused[0x9000:0x9800], jp_02a)

        w_unpaused, v_unpaused, _ = _load_dump(cap, "unpaused")
        self.assertEqual(w_unpaused[0x13D4], 0x00)
        self.assertGreater(_bg3_39xx_count(v_unpaused), _bg3_39xx_count(v_paused))

        for lbl, expected_room in (
            ("skip_14b", 0x014B),
            ("skip_14c", 0x014C),
            ("skip_14d", 0x014D),
        ):
            wram, vram, _ = _load_dump(cap, lbl)
            self.assertEqual(wram[0x0100], 0x14, lbl)
            self.assertEqual(wram[0x010B] | (wram[0x010C] << 8), expected_room, lbl)
            self.assertEqual(vram[0x9000:0x9800], jp_02a, lbl)

        w_ow, v_ow, _ = _load_dump(cap, "skip_ow")
        self.assertEqual(w_ow[0x0100], 0x0E)
        self.assertEqual(w_ow[0x1F11], 0x00)
        self.assertEqual(w_ow[0x0109], 0x00)
        self.assertEqual(w_ow[0x1F17] | (w_ow[0x1F18] << 8), 0x0068)
        self.assertEqual(w_ow[0x1F19] | (w_ow[0x1F1A] << 8), 0x0198)
        self.assertEqual(v_ow[0x9000:0x9800], en_02a)

    def test_r45_exgfx_regression_unchanged(self) -> None:
        r45_rom = (ROOT / "local/restoration" / p46.PARENT / "rom.sfc").read_bytes()
        r46_rom = (ROOT / "local/restoration" / p46.TARGET / "rom.sfc").read_bytes()
        for spec in p45.EXGFX_SPECS:
            off = spec["pc_offset"]
            self.assertEqual(r46_rom[off : off + 3], r45_rom[off : off + 3], hex(spec["gid"]))

        cap = ROOT / "local/captures/r46-reg-room175"
        run_log = (cap / "run.log").read_text(encoding="utf-8")
        d3_res, d3_exec = _parse_bank_counts(run_log, "D3")
        self.assertGreater(d3_res, 0)
        self.assertEqual(d3_exec, 0)

        wram, vram, _ = _load_dump(cap, "f512")
        self.assertEqual(wram[0x010B] | (wram[0x010C] << 8), 0x0175)
        do1_rom = (ROOT / "local/content-versions/demo-only-1/rom.sfc").read_bytes()
        dec_18f, _ = lz2(do1_rom, 0x20D41C)
        dec_192, _ = lz2(do1_rom, 0x20DBB6)
        self.assertEqual(vram[0xF000:0x10000], dec_18f)
        self.assertEqual(wram[0xAD00:0xBD00], dec_192)
        same_tiles = sum(
            1
            for i in range(128)
            if vram[0x3000 + i * 32 : 0x3000 + (i + 1) * 32]
            == dec_192[i * 32 : (i + 1) * 32]
        )
        self.assertGreaterEqual(same_tiles, 126)


if __name__ == "__main__":
    unittest.main()
