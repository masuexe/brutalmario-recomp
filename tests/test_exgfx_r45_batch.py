#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_smw_delta
import launch_native
import package_public_beta
import play_native_cheats
import play_native_target
import prepare_product_r45 as p45
from restore_star_world_1 import lz2


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_bank_counts(log_text: str, bank: str) -> tuple[int, int]:
    match = re.search(
        rf"\[native-seven\] bank={bank} resolutions=(\d+) executed_page_instructions=(\d+)",
        log_text,
    )
    if match is None:
        raise AssertionError(f"missing bank={bank} summary line in run.log")
    return int(match.group(1)), int(match.group(2))


class ExGfxR45BatchTest(unittest.TestCase):
    def test_pack_recipe_and_rom_diff(self) -> None:
        pack_path = ROOT / p45.PACK_SOURCE / p45.PACK_FILE
        r44_rom_path = ROOT / "local/restoration" / p45.PARENT / "rom.sfc"
        r45_rom_path = ROOT / "local/restoration" / p45.TARGET / "rom.sfc"
        boss_rom_path = ROOT / "local/content-versions/boss/rom.sfc"
        do1_rom_path = ROOT / "local/content-versions/demo-only-1/rom.sfc"

        for required in (pack_path, r44_rom_path, r45_rom_path, boss_rom_path, do1_rom_path):
            self.assertTrue(required.exists(), f"missing {required}")

        pack_bytes = pack_path.read_bytes()
        self.assertEqual(len(pack_bytes), p45.PACK_SIZE)
        self.assertEqual(hashlib.sha256(pack_bytes).hexdigest(), p45.PACK_SHA)

        r44_rom = r44_rom_path.read_bytes()
        r45_rom = r45_rom_path.read_bytes()
        boss_rom = boss_rom_path.read_bytes()
        do1_rom = do1_rom_path.read_bytes()

        self.assertEqual(hashlib.sha256(r44_rom).hexdigest(), p45.R44_SHA)
        self.assertEqual(hashlib.sha256(r45_rom).hexdigest(), p45.R45_SHA)
        self.assertEqual(hashlib.sha256(boss_rom).hexdigest(), p45.BOSS_SHA)
        self.assertEqual(hashlib.sha256(do1_rom).hexdigest(), p45.DO1_SHA)

        diffs = [i for i in range(len(r44_rom)) if r44_rom[i] != r45_rom[i]]
        expected_offsets = sorted(
            spec["pc_offset"] + j for spec in p45.EXGFX_SPECS for j in range(3)
        )
        self.assertEqual(len(diffs), 24)
        self.assertEqual(diffs, expected_offsets)

        cursor = 0
        for spec in p45.EXGFX_SPECS:
            donor_rom = boss_rom if spec["donor"] == "boss" else do1_rom
            decoded, compressed = lz2(donor_rom, spec["donor_ptr"])
            self.assertEqual(len(decoded), 4096)
            self.assertEqual(len(compressed), spec["stream_size"])
            stream = pack_bytes[cursor : cursor + len(compressed)]
            self.assertEqual(stream, compressed)
            cursor += len(compressed)

        self.assertEqual(cursor, len(pack_bytes))

        manifest = json.loads(
            (ROOT / "config/restorations" / f"{p45.TARGET}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["base_restoration"], p45.PARENT)
        self.assertEqual(manifest["parent_restoration"], p45.PARENT)
        nsg = manifest["native_sprite_gap"]
        self.assertEqual(len(nsg["frozen_manifests"]), 50)
        self.assertEqual(len(nsg["extra_packs"]), 12)
        self.assertEqual(nsg["extra_packs"][-1]["variable"], p45.PACK_VAR)
        self.assertEqual(nsg["extra_packs"][-1]["address"], "D38000")
        self.assertFalse(nsg["extra_packs"][-1]["executable"])
        self.assertEqual(len(nsg["extra_patches"]), 8)
        self.assertEqual(len(manifest["code_patches"]), 8)
        self.assertEqual(manifest["output"]["sha256"], p45.R45_SHA)

    def test_defaults_promoted_to_r45(self) -> None:
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
                r"""--target["']\s*,\s*default\s*=\s*["']demo11-native-product-r45["']""",
                f"{tool_name} missing r45 --target default",
            )
        pkg_src = (TOOLS_DIR / "package_public_beta.py").read_text(encoding="utf-8")
        self.assertIn('ROOT / "dist/public-beta-r45"', pkg_src)
        self.assertIn('ROOT / "local/diagnostics/public-beta-r45"', pkg_src)

        packs = build_smw_delta.collect_target_packs(p45.TARGET)
        self.assertEqual(len(packs), 67)
        by_var = {pack["variable"]: pack for pack in packs}
        self.assertIn(p45.PACK_VAR, by_var)
        self.assertEqual(by_var[p45.PACK_VAR]["size"], p45.PACK_SIZE)
        self.assertEqual(by_var[p45.PACK_VAR]["sha256"], p45.PACK_SHA)

    def test_capture_r45_room0e4_exgfx1e3(self) -> None:
        cap = ROOT / "local/captures/r45-room0e4-exgfx1e3"
        run_log = (cap / "run.log").read_text(encoding="utf-8")
        d3_res, d3_exec = _parse_bank_counts(run_log, "D3")
        self.assertGreater(d3_res, 0)
        self.assertEqual(d3_exec, 0)

        wram = (cap / "existing_later.wram.bin").read_bytes()
        vram = (cap / "existing_later.vram.bin").read_bytes()
        self.assertEqual(wram[0x010B] | (wram[0x010C] << 8), 0x0E4)
        boss_rom = (ROOT / "local/content-versions/boss/rom.sfc").read_bytes()
        dec_1e3, _ = lz2(boss_rom, 0x32E5D0)
        self.assertEqual(vram[0xF000:0x10000], dec_1e3)

    def test_capture_r45_room175_exgfx18f_192(self) -> None:
        cap = ROOT / "local/captures/r45-room175-exgfx18f-192"
        run_log = (cap / "run.log").read_text(encoding="utf-8")
        d3_res, d3_exec = _parse_bank_counts(run_log, "D3")
        self.assertGreater(d3_res, 0)
        self.assertEqual(d3_exec, 0)

        wram = (cap / "f512.wram.bin").read_bytes()
        vram = (cap / "f512.vram.bin").read_bytes()
        self.assertEqual(wram[0x010B] | (wram[0x010C] << 8), 0x175)
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
        for added_tile in (0x4C, 0x4D, 0x4E, 0x4F, 0x5C, 0x5D, 0x5E, 0x5F):
            self.assertEqual(
                vram[0x3000 + added_tile * 32 : 0x3000 + (added_tile + 1) * 32],
                dec_192[added_tile * 32 : (added_tile + 1) * 32],
            )

    def test_capture_r45_multi_rooms(self) -> None:
        cap = ROOT / "local/captures/r45-multi-rooms"
        run_log = (cap / "run.log").read_text(encoding="utf-8")
        d3_res, d3_exec = _parse_bank_counts(run_log, "D3")
        self.assertGreater(d3_res, 0)
        self.assertEqual(d3_exec, 0)

        boss_rom = (ROOT / "local/content-versions/boss/rom.sfc").read_bytes()
        do1_rom = (ROOT / "local/content-versions/demo-only-1/rom.sfc").read_bytes()
        dec_163, _ = lz2(do1_rom, 0x20C8CA)
        dec_1ae, _ = lz2(do1_rom, 0x20DF53)
        dec_0da, _ = lz2(boss_rom, 0x4A94A6)
        dec_0be, _ = lz2(do1_rom, 0x28DCE8)
        dec_1b2, _ = lz2((ROOT / "local/native-modules/exgfx-1b2-v1/exgfx-1b2.bin").read_bytes(), 0x008000)

        w176 = (cap / "r176.wram.bin").read_bytes()
        v176 = (cap / "r176.vram.bin").read_bytes()
        self.assertEqual(w176[0x010B] | (w176[0x010C] << 8), 0x176)
        self.assertEqual(v176[0xE000:0xF000], dec_163)
        self.assertEqual(v176[0x2000:0x3000], dec_1ae)
        self.assertEqual(v176[0xF000:0x10000], dec_1b2)

        w152 = (cap / "r152.wram.bin").read_bytes()
        v152 = (cap / "r152.vram.bin").read_bytes()
        self.assertEqual(w152[0x010B] | (w152[0x010C] << 8), 0x152)
        self.assertEqual(v152[0x3000:0x4000], dec_0da)

        w062 = (cap / "r062.wram.bin").read_bytes()
        v062 = (cap / "r062.vram.bin").read_bytes()
        self.assertEqual(w062[0x010B] | (w062[0x010C] << 8), 0x062)
        same_0be = sum(
            1
            for i in range(128)
            if v062[0xC000 + i * 32 : 0xC000 + (i + 1) * 32]
            == dec_0be[i * 32 : (i + 1) * 32]
        )
        self.assertGreaterEqual(same_0be, 107)

        w134 = (cap / "r134.wram.bin").read_bytes()
        self.assertEqual(w134[0x010B] | (w134[0x010C] << 8), 0x134)
        bgrx = (cap / "r134.fb.bgrx").read_bytes()
        sun_pixels = sum(
            1
            for i in range(0, len(bgrx), 4)
            if bgrx[i] == 156 and bgrx[i + 1] == 255 and bgrx[i + 2] == 255
        )
        self.assertGreater(sun_pixels, 500)

    def test_capture_r45_room15d_wily257(self) -> None:
        cap = ROOT / "local/captures/r45-room15d-wily257"
        run_log = (cap / "run.log").read_text(encoding="utf-8")
        d3_res, d3_exec = _parse_bank_counts(run_log, "D3")
        b85_res, b85_exec = _parse_bank_counts(run_log, "85")
        self.assertGreater(d3_res, 0)
        self.assertEqual(d3_exec, 0)
        self.assertGreater(b85_res, 0)
        self.assertGreater(b85_exec, 0)

        wram = (cap / "p2_wily257.wram.bin").read_bytes()
        vram = (cap / "p2_wily257.vram.bin").read_bytes()
        self.assertEqual(wram[0x010B] | (wram[0x010C] << 8), 0x15D)
        self.assertEqual(wram[0x1FF90] | (wram[0x1FF91] << 8), 0x0257)
        self.assertEqual(wram[0x00C9], 0x08)

        boss_rom = (ROOT / "local/content-versions/boss/rom.sfc").read_bytes()
        dec_257, _ = lz2(boss_rom, 0x3C921A)
        self.assertEqual(wram[0x0AD00:0x0BD00], dec_257)
        for voff, doff, size in (
            (0x3100, 0x0100, 0x100),
            (0x3300, 0x0300, 0x100),
            (0x3500, 0x0500, 0x100),
            (0x3700, 0x0700, 0x100),
            (0x3900, 0x0900, 0x100),
            (0x3B00, 0x0B00, 0x100),
            (0x38C0, 0x0D00, 0x40),
            (0x3AC0, 0x0F00, 0x40),
            (0x3CC0, 0x0D40, 0x40),
            (0x3EC0, 0x0F40, 0x40),
        ):
            self.assertEqual(vram[voff : voff + size], dec_257[doff : doff + size])


if __name__ == "__main__":
    unittest.main()
