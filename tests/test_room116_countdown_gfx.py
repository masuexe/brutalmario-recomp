#!/usr/bin/env python3
"""Tests for demo11-native-product-r48 Room 0x116 countdown sprite GFX restoration."""
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
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta
import package_public_beta as ppb
import prepare_product_r48 as r48
import native_sprite_gap
from restore_star_world_1 import graphics_pointer, lorom, lz2

R47_SHA = "2123f5e3415364d3a5def92b8ac3ab1f581ec68f0cf6469ffda12f4a9da80b0a"
R48_SHA = "bbd52ff43fe86e872ee2c55da7adf40ca0eb52e117d529bc5449f3aae5b1bc52"

FAST_BOOT_TO_OVERWORLD = (
    "turbo on\n"
    "until 0100 == 07 4000\n"
    "wait 10\n"
    "press start 2\n"
    "until 0100 == 08 900\n"
    "wait 180\n"
    "press start 2\n"
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
    "until 0100 == 0e 2400\n"
)


def _run_room_capture(binary: Path, rom: Path, room: int, *, set_complete_flag: bool) -> dict[str, dict[str, bytes]]:
    """Boot the r48 binary, optionally set $1EA2..$1F01 = $9F, warp to `room`, and dump f1/f2."""
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", SNESRECOMP_REWIND="0")
    native_sprite_gap.environment("demo11-native-product-r48", env)

    with tempfile.TemporaryDirectory(prefix=f"bm-r48-room{room:03x}-") as tmp:
        tp = Path(tmp)
        (tp / "saves").mkdir()
        cfg = tp / "config.ini"
        cfg.write_text(ppb.format_config_ini("linux"), encoding="utf-8")

        parts = [FAST_BOOT_TO_OVERWORLD]
        if set_complete_flag:
            parts.append("poke 1ea2 " + ("9f" * 0x60) + "\n")
        parts.extend([
            "poke 1f11 0606\n",
            "poke 1f17 2801e8012801e801\n",
            "poke 1f1f 12001e0012001e00\n",
            "poke 0100 0b\n",
            "until 0100 == 0e 1600\n",
            "poke d7e2 6a\n",
            "press y 2\n",
            "until 0100 == 14 1200\n",
            f"poke 19b8 {room & 0xFF:02x}\n",
            f"poke 19d8 {4 + (room >> 8):02x}\n",
            "poke 88 0000\n",
            "poke 71 06\n",
            f"until16 10b == {room:x} 1600\n",
            "until 0100 == 14 600\n",
            "wait 10\n",
            "dump f1\n",
            "wait 60\n",
            "dump f2\n",
            "quit\n",
        ])
        sc = tp / "room.script"
        sc.write_text("".join(parts), encoding="utf-8")

        run_env = dict(env)
        run_env["SNESRECOMP_DUMP_DIR"] = str(tp)
        res = subprocess.run(
            [
                str(binary),
                "--no-launcher",
                "--config",
                str(cfg),
                "--rom",
                str(rom),
                "--script",
                str(sc),
            ],
            cwd=tp,
            env=run_env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if res.returncode != 0:
            raise AssertionError(f"room 0x{room:03X} run failed: {res.stderr}\n{res.stdout}")

        dumps: dict[str, dict[str, bytes]] = {}
        for tag in ("f1", "f2"):
            dumps[tag] = {
                ext: (tp / f"{tag}.{ext}").read_bytes()
                for ext in ("wram.bin", "vram.bin", "oam.bin", "cgram.bin", "fb.bgrx")
            }
        return dumps


def _countdown_oam_entries(oam: bytes) -> list[tuple[int, int, int, int]]:
    """Return visible OAM entries matching Room 0x116 countdown digit tiles ($80..$89/$90..$99, prop=$22)."""
    out = []
    for idx in range(128):
        x, y, tile, prop = oam[idx * 4 : idx * 4 + 4]
        if y < 0xE0 and prop == 0x22 and ((0x80 <= tile <= 0x89) or (0x90 <= tile <= 0x99)):
            out.append((x, y, tile, prop))
    return out


class Room116CountdownGfxTests(unittest.TestCase):
    def test_r48_config_lineage_symbols_patches_and_packs(self):
        r47_cfg = json.loads((ROOT / "config/restorations/demo11-native-product-r47.json").read_text())
        r48_cfg = json.loads((ROOT / "config/restorations/demo11-native-product-r48.json").read_text())

        self.assertEqual(r48_cfg["id"], "demo11-native-product-r48")
        self.assertEqual(r48_cfg["target"], "Brutal Mario Demo11 Product R48")
        self.assertEqual(r48_cfg["base_restoration"], "demo11-native-product-r47")
        self.assertEqual(r48_cfg["parent_restoration"], "demo11-native-product-r47")
        self.assertEqual(r48_cfg["base_output"], {"size": 4194304, "sha256": R47_SHA})
        self.assertEqual(r48_cfg["output"], {"size": 4194304, "sha256": R48_SHA})

        self.assertEqual(
            r48_cfg["native_sprite_gap"]["frozen_manifests"],
            r48_cfg["native_sprite_gap"]["manifests"],
        )
        self.assertEqual(len(r48_cfg["native_sprite_gap"]["manifests"]), 50)
        self.assertEqual(
            r48_cfg["native_sprite_gap"]["extra_packs"],
            r47_cfg["native_sprite_gap"]["extra_packs"],
        )

        expected_patches = r48.build_patches()
        self.assertEqual(len(expected_patches), 3)
        self.assertEqual(r48_cfg["native_sprite_gap"]["extra_patches"], expected_patches)
        self.assertEqual(len(r48_cfg["code_patches"]), 3)
        self.assertEqual(
            [p["address"] for p in r48_cfg["code_patches"]],
            ["002A6F", "07F19B", "07F884"],
        )

        r47_sym = (ROOT / "recomp/targets/demo11-native-product-r47/symbols.toml").read_text()
        r48_sym = (ROOT / "recomp/targets/demo11-native-product-r48/symbols.toml").read_text()
        self.assertIn("Product R48", r48_sym.splitlines()[0])
        self.assertEqual(r48_sym.replace("Product R48", "Product R47", 1), r47_sym)
        self.assertEqual(r48_sym.count('name = "r47_'), 11)
        self.assertEqual(r48_sym.count("bank = 144"), 11)
        self.assertEqual(sum(1 for ln in r48_sym.splitlines() if ln.strip() == "emit = false"), 13)

        r47_rom_path = ROOT / "local/restoration/demo11-native-product-r47/rom.sfc"
        r48_rom_path = ROOT / "local/restoration/demo11-native-product-r48/rom.sfc"
        if not r47_rom_path.is_file() or not r48_rom_path.is_file():
            self.skipTest("demo11-native-product-r47/r48 ROM files not present")

        r47_rom = r47_rom_path.read_bytes()
        r48_rom = r48_rom_path.read_bytes()
        self.assertEqual(hashlib.sha256(r47_rom).hexdigest(), R47_SHA)
        self.assertEqual(hashlib.sha256(r48_rom).hexdigest(), R48_SHA)

        patched_ranges = set()
        for patch in expected_patches:
            off = patch["offset"]
            before = bytes.fromhex(patch["before"])
            after = bytes.fromhex(patch["after"])
            self.assertEqual(r47_rom[off : off + len(before)], before)
            self.assertEqual(r48_rom[off : off + len(after)], after)
            patched_ranges.update(range(off, off + len(after)))
        diffs = {i for i in range(len(r47_rom)) if r47_rom[i] != r48_rom[i]}
        self.assertTrue(diffs)
        self.assertTrue(diffs.issubset(patched_ranges))

        packs = build_smw_delta.collect_target_packs("demo11-native-product-r48")
        self.assertEqual(len(packs), 71)
        self.assertEqual(len({p["variable"] for p in packs}), 71)

    def test_static_room_audit_room116_and_512_room_matrix(self):
        r48_rom_path = ROOT / "local/restoration/demo11-native-product-r48/rom.sfc"
        if not r48_rom_path.is_file():
            self.skipTest("demo11-native-product-r48 ROM not present")
        rom = r48_rom_path.read_bytes()

        # Verify all 16 vanilla sprite sets at $00:A8C3 have SP2 (+1) == 0x01.
        a8c3 = lorom(0x00A8C3)
        vanilla_sp2_by_set = [rom[a8c3 + s * 4 + 1] for s in range(16)]
        self.assertEqual(vanilla_sp2_by_set, [0x01] * 16)

        # Room 0x116: vanilla spriteset byte ($192B = hdr[2] & 0x0F) -> vanilla SP2 = $01,
        # while Super GFX Bypass ($14:AD08 + room*32) sets active (w0=0x8001) and SP2 = 0x012A.
        l1_116 = int.from_bytes(rom[lorom(0x05E000 + 0x116 * 3) : lorom(0x05E000 + 0x116 * 3) + 3], "little")
        hdr_116 = rom[lorom(l1_116) : lorom(l1_116) + 5]
        spriteset_116 = hdr_116[2] & 0x0F
        self.assertEqual(spriteset_116, 1)
        self.assertEqual(rom[a8c3 + spriteset_116 * 4 + 1], 0x01)

        super_active = []
        super_inactive = []
        super_non01 = []
        super_01 = []
        for room in range(512):
            base = lorom(0x14AD08 + room * 32)
            w0 = int.from_bytes(rom[base : base + 2], "little")
            sp2 = int.from_bytes(rom[base + 14 : base + 16], "little")
            if w0 & 0x8000:
                super_active.append(room)
                if sp2 == 0x0001:
                    super_01.append(room)
                else:
                    super_non01.append((room, sp2))
            else:
                super_inactive.append(room)

        self.assertEqual(len(super_active), 362)
        self.assertEqual(len(super_inactive), 150)
        self.assertEqual(len(super_non01), 127)
        self.assertEqual(len(super_01), 235)
        self.assertEqual(len(super_01) + len(super_inactive), 385)

        non01_map = dict(super_non01)
        self.assertEqual(non01_map[0x116], 0x012A)
        self.assertEqual(non01_map[0x007], 0x012A)
        self.assertEqual(non01_map[0x105], 0x029F)
        self.assertIn(0x104, super_inactive)
        self.assertIn(0x101, super_01)

        level_index = json.loads((ROOT / "config/demo11-level-index.json").read_text())
        indexed_rooms = {int(entry["level"], 16) for entry in level_index["entries"]}
        self.assertEqual(len(set(non01_map) & indexed_rooms), 43)

    def test_headless_room116_preserves_exgfx12a_and_positive_controls_load_gfx31(self):
        binary = ROOT / "local/build/demo11-native-product-r48/BrutalMarioDemo11ProductR48SNESRecomp"
        rom_path = ROOT / "local/restoration/demo11-native-product-r48/rom.sfc"
        if not binary.is_file() or not rom_path.is_file():
            self.skipTest("demo11-native-product-r48 native build not present")

        rom = rom_path.read_bytes()
        exp_12a, _ = lz2(rom, graphics_pointer(rom, 0x12A), limit=0x10000)
        exp_031, _ = lz2(rom, graphics_pointer(rom, 0x31), limit=0x10000)
        exp_29f, _ = lz2(rom, graphics_pointer(rom, 0x29F), limit=0x10000)
        self.assertEqual(len(exp_12a), 4096)
        self.assertEqual(len(exp_031), 2048)
        self.assertEqual(len(exp_29f), 4096)

        # 1. Room 0x116 both without ($1F01 = 0x1F) and with ($1F01 = 0x9F) complete cheat.
        for set_complete, expected_1f01 in ((False, 0x1F), (True, 0x9F)):
            dumps = _run_room_capture(binary, rom_path, 0x116, set_complete_flag=set_complete)
            f1, f2 = dumps["f1"], dumps["f2"]

            self.assertEqual(f1["wram.bin"][0x010B] | (f1["wram.bin"][0x010C] << 8), 0x116)
            self.assertEqual(f1["wram.bin"][0x1F01], expected_1f01)
            self.assertEqual(f1["vram.bin"][0x6800 * 2 : 0x7000 * 2], exp_12a)
            self.assertNotEqual(f1["vram.bin"][0x6800 * 2 : 0x6800 * 2 + 2048], exp_031)

            digits_f1 = _countdown_oam_entries(f1["oam.bin"])
            digits_f2 = _countdown_oam_entries(f2["oam.bin"])
            self.assertEqual(
                {(t, p) for _, _, t, p in digits_f1},
                {(0x81, 0x22), (0x91, 0x22), (0x80, 0x22), (0x90, 0x22)},
            )
            self.assertEqual(
                {(t, p) for _, _, t, p in digits_f2},
                {(0x80, 0x22), (0x90, 0x22), (0x89, 0x22), (0x99, 0x22)},
            )

            # Verify OBJ palette 1 color 8 ($98) is red (247, 8, 8) and rendered in digit bbox,
            # while GFX 0x31 colors (181, 0, 0) / (255, 90, 0) are absent from digit bbox.
            bgr555 = struct.unpack_from("<H", f1["cgram.bin"], 0x98 * 2)[0]
            r = ((bgr555 & 0x1F) << 3) | ((bgr555 & 0x1F) >> 2)
            g = (((bgr555 >> 5) & 0x1F) << 3) | (((bgr555 >> 5) & 0x1F) >> 2)
            b = (((bgr555 >> 10) & 0x1F) << 3) | (((bgr555 >> 10) & 0x1F) >> 2)
            self.assertEqual((r, g, b), (247, 8, 8))

            xs = [x for x, _, _, _ in digits_f1]
            ys = [y for _, y, _, _ in digits_f1]
            fb = f1["fb.bgrx"]
            bbox_colors: set[tuple[int, int, int]] = set()
            red_pixels = 0
            for py in range(min(ys), max(ys) + 8):
                for px in range(min(xs), max(xs) + 8):
                    pb, pg, pr, _ = fb[(py * 256 + px) * 4 : (py * 256 + px) * 4 + 4]
                    rgb = (pr, pg, pb)
                    bbox_colors.add(rgb)
                    if rgb == (247, 8, 8):
                        red_pixels += 1
            self.assertGreater(red_pixels, 50)
            self.assertNotIn((181, 0, 0), bbox_colors)
            self.assertNotIn((255, 90, 0), bbox_colors)

        # 2. Positive controls where effective SP2 == 0x0001 with $1F01 = 0x9F MUST load GFX 0x31:
        #    - Room 0x104 (Yoshi's House, vanilla path, Super Bypass inactive)
        #    - Room 0x101 (Super GFX Bypass with SP2 == 0x0001)
        for room in (0x104, 0x101):
            dumps = _run_room_capture(binary, rom_path, room, set_complete_flag=True)
            f1 = dumps["f1"]
            self.assertEqual(f1["wram.bin"][0x010B] | (f1["wram.bin"][0x010C] << 8), room)
            self.assertEqual(f1["wram.bin"][0x1F01], 0x9F)
            self.assertEqual(f1["vram.bin"][0x6800 * 2 : 0x6800 * 2 + 2048], exp_031)

        # 3. Extra Super-Bypass preservation check: Room 0x105 (SP2 = 0x029F != 0x0001)
        #    with $1F01 = 0x9F must preserve ExGFX 0x29F instead of overwriting with GFX 0x31.
        dumps_105 = _run_room_capture(binary, rom_path, 0x105, set_complete_flag=True)
        f1_105 = dumps_105["f1"]
        self.assertEqual(f1_105["wram.bin"][0x010B] | (f1_105["wram.bin"][0x010C] << 8), 0x105)
        self.assertEqual(f1_105["wram.bin"][0x1F01], 0x9F)
        self.assertEqual(f1_105["vram.bin"][0x6800 * 2 : 0x7000 * 2], exp_29f)
        self.assertNotEqual(f1_105["vram.bin"][0x6800 * 2 : 0x6800 * 2 + 2048], exp_031)


if __name__ == "__main__":
    unittest.main()
