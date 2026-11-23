#!/usr/bin/env python3
"""Verify demo11-native-product-r52 native 16:9 widescreen and SNESRecomp mod runtime."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import native_sprite_gap

TARGET = "demo11-native-product-r52"
BINARY = ROOT / "local/build" / TARGET / "BrutalMarioDemo11ProductR52SNESRecomp"
MODS_STAGE_SRC = ROOT / "local/build" / TARGET / "mods/preloaded"
ROM_PATH = ROOT / "local/restoration" / TARGET / "rom.sfc"
CAPTURE_ROOT = ROOT / "local/captures/r52-widescreen-mods-verify"
REPORTS_DIR = ROOT / "local/reports"

# Boot -> Title -> File Select -> skip 4-scene intro -> Overworld -> walk left to 1-1 -> enter 1-1 -> run right
WIDESCREEN_TOUR_SCRIPT = (
    "turbo on\n"
    "until 0100 == 07 4000\n"
    "wait 30\n"
    "dump title\n"
    "press start 2\n"
    "until 0100 == 08 900\n"
    "wait 180\n"
    "press start 2\n"
    "until16 010b == 01c5 900\n"
    "until 0100 == 14 600\n"
    "wait 60\n"
    "dump intro1c5\n"
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
    "until 0100 == 0e 2400\n"
    "wait 60\n"
    "dump overworld\n"
    "press left 10\n"
    "wait 40\n"
    "press b 4\n"
    "until16 010b == 0105 1200\n"
    "until 0100 == 14 1200\n"
    "wait 30\n"
    "dump course105_start\n"
    "press right 120\n"
    "wait 10\n"
    "dump course105_scrolled\n"
    "quit\n"
)

SHORT_TITLE_SCRIPT = (
    "turbo on\n"
    "until 0100 == 07 4000\n"
    "wait 20\n"
    "dump title\n"
    "quit\n"
)


def _read_framedump_bmp(path: Path) -> tuple[int, int, bytes]:
    """Read FrameDump_Present's 32-bit top-down BGRA BMP."""
    data = path.read_bytes()
    assert data[:2] == b"BM", f"not a BMP: {path}"
    pixel_off = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    height = abs(struct.unpack_from("<i", data, 22)[0])
    pixels = data[pixel_off : pixel_off + width * height * 4]
    assert len(pixels) == width * height * 4
    return width, height, pixels


def _write_png_from_bgra(path: Path, raw: bytes, width: int, height: int) -> None:
    """Write an RGB PNG from 32-bit BGRA pixels."""
    rows = []
    stride = width * 4
    for y in range(height):
        row = bytearray([0])
        base = y * stride
        for x in range(width):
            p = base + x * 4
            b, g, r = raw[p], raw[p + 1], raw[p + 2]
            row.extend((r, g, b))
        rows.append(bytes(row))
    raw_scanlines = b"".join(rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw_scanlines, 6)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def _count_nonblack_in_rect(raw: bytes, width: int, x0: int, x1: int, y0: int, y1: int) -> int:
    count = 0
    stride = width * 4
    for y in range(y0, y1):
        row_off = y * stride
        for x in range(x0, x1):
            p = row_off + x * 4
            if raw[p] or raw[p + 1] or raw[p + 2]:
                count += 1
    return count


def _find_presented_bmp(sdir: Path, tag: str) -> tuple[int, int, bytes]:
    p = sdir / "ws_dumps" / f"{tag}.bmp"
    if p.is_file():
        return _read_framedump_bmp(p)
    raise FileNotFoundError(f"missing widescreen dump BMP: {p}")


def _run_session(
    session_dir: Path,
    script_text: str,
    *,
    widescreen_cfg: bool = False,
    extra_env: dict[str, str] | None = None,
    state_toml: str | None = None,
    mod_overrides: dict[tuple[str, str, str], bytes] | None = None,
    capture_pixels: bool = True,
) -> tuple[subprocess.CompletedProcess, Path]:
    if session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True)
    (session_dir / "saves").mkdir()

    dst_mods = session_dir / "mods/preloaded"
    shutil.copytree(MODS_STAGE_SRC, dst_mods)
    if state_toml is not None:
        (dst_mods / "state.toml").write_text(state_toml, encoding="utf-8")
    if mod_overrides:
        for (pkg_id, pkg_ver, rel_name), payload in mod_overrides.items():
            ov_path = dst_mods / "packages" / pkg_id / pkg_ver / "overrides" / rel_name
            ov_path.parent.mkdir(parents=True, exist_ok=True)
            ov_path.write_bytes(payload)

    cfg_path = session_dir / "config.ini"
    cfg_text = (ROOT / "recomp/m1-config.ini").read_text(encoding="utf-8")
    if widescreen_cfg:
        cfg_text = cfg_text.replace("Widescreen=0", "Widescreen=1")
    cfg_path.write_text(cfg_text, encoding="utf-8")

    script_path = session_dir / "input.script"
    script_path.write_text(script_text, encoding="utf-8")

    env = os.environ.copy()
    env.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        SNESRECOMP_REWIND="0",
        SNESRECOMP_DUMP_DIR=str(session_dir),
        SNESRECOMP_SEPARATE_ECHO="1",
        SNESRECOMP_APU_MASTER_CLOCK="1",
    )
    if capture_pixels:
        ws_dir = session_dir / "ws_dumps"
        ws_dir.mkdir(parents=True, exist_ok=True)
        env["BM_WS_DUMP_DIR"] = str(ws_dir)
    native_sprite_gap.environment(TARGET, env)
    if extra_env:
        env.update(extra_env)

    cmd = [
        str(BINARY),
        "--no-launcher",
        "--config",
        str(cfg_path),
        "--script",
        str(script_path),
        "--rom",
        str(ROM_PATH),
    ]
    proc = subprocess.run(
        cmd,
        cwd=session_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    (session_dir / "run.log").write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
    return proc, session_dir


class ProductR52WidescreenAndModsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not BINARY.is_file():
            raise unittest.SkipTest(f"Missing r52 binary at {BINARY}")

    def test_01_stock_default_is_256x224_zero_regression(self) -> None:
        proc, sdir = _run_session(CAPTURE_ROOT / "stock_default", SHORT_TITLE_SCRIPT)
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
        log = (sdir / "run.log").read_text(encoding="utf-8")
        self.assertIn("[native-mods] installed=2 active=0 widescreen=0", log)
        self.assertIn("[native-widescreen] enabled=0 extra=0 width=256", log)
        w, h, raw = _find_presented_bmp(sdir, "title")
        self.assertEqual((w, h), (256, 224))
        self.assertEqual(len(raw), 256 * 224 * 4)

    def test_02_widescreen_tour_env_and_visual_policies(self) -> None:
        proc, sdir = _run_session(
            CAPTURE_ROOT / "widescreen_tour",
            WIDESCREEN_TOUR_SCRIPT,
            extra_env={"BM_WIDESCREEN": "1"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
        log = (sdir / "run.log").read_text(encoding="utf-8")
        self.assertIn("[native-widescreen] enabled=1 extra=72 width=400", log)

        frames: dict[str, bytes] = {}
        for tag in ("title", "intro1c5", "overworld", "course105_start", "course105_scrolled"):
            w, h, raw = _find_presented_bmp(sdir, tag)
            self.assertEqual((w, h), (400, 224), f"{tag} presented size mismatch")
            frames[tag] = raw
            _write_png_from_bgra(REPORTS_DIR / f"r52-ws-{tag}.png", raw, 400, 224)

        # 1. Title, intro cutscene 0x1C5, and framed Overworld (mode 0x0E) must be cleanly centered 4:3.
        for centered_tag in ("title", "intro1c5", "overworld"):
            raw = frames[centered_tag]
            self.assertEqual(_count_nonblack_in_rect(raw, 400, 0, 72, 0, 224), 0, f"{centered_tag} left margin not black")
            self.assertEqual(_count_nonblack_in_rect(raw, 400, 328, 400, 0, 224), 0, f"{centered_tag} right margin not black")
            self.assertGreater(_count_nonblack_in_rect(raw, 400, 72, 328, 0, 224), 5000, f"{centered_tag} center empty")

        # 3. Course 1-1 at start (cam_x == 0): left margin clamped to black, right margin widened!
        c_start = frames["course105_start"]
        wram_start = (sdir / "course105_start.wram.bin").read_bytes()
        cam_x_start = int.from_bytes(wram_start[0x1A:0x1C], "little")
        self.assertEqual(cam_x_start, 0, f"expected cam_x=0 at course 1-1 start, got {cam_x_start}")
        self.assertEqual(_count_nonblack_in_rect(c_start, 400, 0, 72, 0, 224), 0, "course 1-1 start left edge not clamped")
        self.assertGreater(_count_nonblack_in_rect(c_start, 400, 328, 400, 48, 216), 2000, "course 1-1 start right margin not widened")

        # 4. Course 1-1 after running right (cam_x >= 72): BOTH left and right margins widened!
        c_scroll = frames["course105_scrolled"]
        wram_scroll = (sdir / "course105_scrolled.wram.bin").read_bytes()
        cam_x_scroll = int.from_bytes(wram_scroll[0x1A:0x1C], "little")
        self.assertGreaterEqual(cam_x_scroll, 72, f"expected cam_x>=72 after running right, got {cam_x_scroll}")
        self.assertGreater(_count_nonblack_in_rect(c_scroll, 400, 0, 72, 48, 216), 2000, "course 1-1 scrolled left margin not widened")
        self.assertGreater(_count_nonblack_in_rect(c_scroll, 400, 328, 400, 48, 216), 2000, "course 1-1 scrolled right margin not widened")

    def test_03_mod_runtime_activates_widescreen_and_no_sprite_limits(self) -> None:
        state_toml = (
            'format_version = 1\n\n'
            '[[package]]\n'
            'id = "brutalmario.display"\n'
            'version = "1.0.0"\n\n'
            '[[feature]]\n'
            'package_id = "brutalmario.display"\n'
            'id = "widescreen"\n'
            'enabled = true\n\n'
            '[[feature]]\n'
            'package_id = "brutalmario.display"\n'
            'id = "no_sprite_limits"\n'
            'enabled = true\n'
        )
        proc, sdir = _run_session(
            CAPTURE_ROOT / "mod_display_active",
            SHORT_TITLE_SCRIPT,
            widescreen_cfg=False,
            state_toml=state_toml,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
        log = (sdir / "run.log").read_text(encoding="utf-8")
        self.assertIn("[native-mods] plugin activated: brutalmario.widescreen", log)
        self.assertIn("[native-mods] plugin activated: brutalmario.no_sprite_limits", log)
        self.assertIn("[native-mods] installed=2 active=1 widescreen=1 no_sprite_limits=1", log)
        self.assertIn("[native-widescreen] enabled=1 extra=72 width=400", log)
        w, h, raw = _find_presented_bmp(sdir, "title")
        self.assertEqual((w, h), (400, 224))
        self.assertEqual(len(raw), 400 * 224 * 4)

    def test_04_mod_package_overrides_non_executable_data_pack(self) -> None:
        orig_pack = ROOT / "local/restoration" / TARGET / "lang-r47-data.bin"
        mod_bytes = bytearray(orig_pack.read_bytes())
        mod_bytes.extend(b"\x00" * 16)
        self.assertNotEqual(
            hashlib.sha256(bytes(mod_bytes)).hexdigest(),
            hashlib.sha256(orig_pack.read_bytes()).hexdigest(),
        )

        state_toml = (
            'format_version = 1\n\n'
            '[[package]]\n'
            'id = "brutalmario.data_overlay"\n'
            'version = "1.0.0"\n\n'
            '[[feature]]\n'
            'package_id = "brutalmario.data_overlay"\n'
            'id = "pack_overrides"\n'
            'enabled = true\n'
        )
        proc, sdir = _run_session(
            CAPTURE_ROOT / "mod_data_override",
            SHORT_TITLE_SCRIPT,
            state_toml=state_toml,
            mod_overrides={
                ("brutalmario.data_overlay", "1.0.0", "BM_LANG_R47_DATA_PACK.bin"): bytes(mod_bytes)
            },
            capture_pixels=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
        log = (sdir / "run.log").read_text(encoding="utf-8")
        self.assertIn("[native-mods] plugin activated: brutalmario.pack_overrides", log)
        self.assertIn("[native-mods] override pack=BM_LANG_R47_DATA_PACK", log)
        self.assertIn(f"bytes={len(mod_bytes)}", log)


if __name__ == "__main__":
    unittest.main()
