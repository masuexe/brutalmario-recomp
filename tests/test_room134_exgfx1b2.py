import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from restore_star_world_1 import graphics_pointer, lorom, lz2

R43_ROM = ROOT / "local/restoration/demo11-native-product-r43/rom.sfc"
R44_ROM = ROOT / "local/restoration/demo11-native-product-r44/rom.sfc"
DO1_ROMS = (
    ROOT / "local/content-versions/demo-only-1/rom.sfc",
    ROOT / "local/roms/demo-only-1.sfc",
)
EXGFX_1B2_BIN = ROOT / "local/native-modules/exgfx-1b2-v1/exgfx-1b2.bin"

STREAM_SHA = "c045d50b8c107e807c9c661177940667f47b8c38ae0674203a035d8ee0f22778"
DECODED_SHA = "23c81a9ae6106d21facd642e54e1a6b9ec338c2f19ca1b03f06548198b14d529"
R44_SHA = "8014c789ac9bf9f79d2972f7100ae2c677d7f7489e49c87801dadd4340d4a69b"


class TestRoom134ExGfx1B2(unittest.TestCase):
    def test_donor_exgfx_1b2_stream_and_tile_delta(self):
        donor_path = next((p for p in DO1_ROMS if p.is_file()), None)
        if donor_path is None or not R43_ROM.is_file():
            self.skipTest("donor or r43 ROM not present")

        donor = donor_path.read_bytes()
        r43 = R43_ROM.read_bytes()

        ptr_do1 = graphics_pointer(donor, 0x1B2)
        self.assertEqual(ptr_do1, 0x20F10C)
        dec_do1, stream_do1 = lz2(donor, ptr_do1, limit=0x10000)
        self.assertEqual(len(stream_do1), 2175)
        self.assertEqual(hashlib.sha256(stream_do1).hexdigest(), STREAM_SHA)
        self.assertEqual(len(dec_do1), 4096)
        self.assertEqual(hashlib.sha256(dec_do1).hexdigest(), DECODED_SHA)

        if EXGFX_1B2_BIN.is_file():
            self.assertEqual(EXGFX_1B2_BIN.read_bytes(), stream_do1)

        ptr_r43 = graphics_pointer(r43, 0x1B2)
        self.assertEqual(ptr_r43, 0x2FF238)
        dec_r43, stream_r43 = lz2(r43, ptr_r43, limit=0x10000)
        self.assertEqual(len(stream_r43), 1930)
        self.assertEqual(len(dec_r43), 4096)

        added, modified, zeroed = [], [], []
        for idx in range(128):
            a = dec_r43[idx * 32 : (idx + 1) * 32]
            b = dec_do1[idx * 32 : (idx + 1) * 32]
            if a == b:
                continue
            if a == b"\x00" * 32 and b != b"\x00" * 32:
                added.append(0x80 + idx)
            elif b == b"\x00" * 32:
                zeroed.append(0x80 + idx)
            else:
                modified.append(0x80 + idx)

        self.assertEqual(modified, [])
        self.assertEqual(zeroed, [])
        self.assertEqual(
            added,
            [
                0xA8, 0xA9, 0xAA, 0xAB,
                0xAE, 0xAF,
                0xB8, 0xB9, 0xBA, 0xBB,
                0xBE, 0xBF,
                0xCE, 0xCF,
                0xDE, 0xDF,
            ],
        )

    def test_product_r44_recipe_and_rom_derivation(self):
        cfg_path = ROOT / "config/restorations/demo11-native-product-r44.json"
        self.assertTrue(cfg_path.is_file())
        cfg = json.loads(cfg_path.read_text())
        self.assertEqual(cfg["id"], "demo11-native-product-r44")
        self.assertEqual(cfg["base_restoration"], "demo11-native-product-r43")
        self.assertEqual(cfg["parent_restoration"], "demo11-native-product-r43")
        self.assertEqual(cfg["output"], {"size": 4194304, "sha256": R44_SHA})
        self.assertEqual(
            cfg["native_sprite_gap"]["frozen_manifests"],
            cfg["native_sprite_gap"]["manifests"],
        )
        self.assertEqual(len(cfg["native_sprite_gap"]["frozen_manifests"]), 50)

        extra_by_var = {p["variable"]: p for p in cfg["native_sprite_gap"]["extra_packs"]}
        self.assertIn("BM_EXGFX_1B2_PACK", extra_by_var)
        self.assertEqual(extra_by_var["BM_EXGFX_1B2_PACK"]["address"], "D28000")
        self.assertEqual(extra_by_var["BM_EXGFX_1B2_PACK"]["size"], 2175)
        self.assertEqual(extra_by_var["BM_EXGFX_1B2_PACK"]["sha256"], STREAM_SHA)
        self.assertFalse(extra_by_var["BM_EXGFX_1B2_PACK"]["executable"])

        if R43_ROM.is_file() and R44_ROM.is_file():
            r43 = R43_ROM.read_bytes()
            r44 = R44_ROM.read_bytes()
            self.assertEqual(hashlib.sha256(r44).hexdigest(), R44_SHA)

            off = lorom(0x14821E)
            self.assertEqual(off, 0x0A021E)
            diffs = [i for i in range(len(r43)) if r43[i] != r44[i]]
            self.assertEqual(diffs, [off, off + 1, off + 2])
            self.assertEqual(r43[off : off + 3], bytes.fromhex("38f22f"))
            self.assertEqual(r44[off : off + 3], bytes.fromhex("0080d2"))

    def test_runtime_captures_room134_sun_and_room174_sp4(self):
        cap_134 = ROOT / "local/captures/r44-room134-sun"
        do1_134 = ROOT / "local/captures/diag-room134-do1-ref"
        cap_174 = ROOT / "local/captures/r44-room174-exgfx1b2"

        if cap_134.is_dir():
            receipt = json.loads((cap_134 / "receipt.json").read_text())
            self.assertEqual(receipt["target"], "demo11-native-product-r44")
            self.assertEqual(receipt["rom_sha256"], R44_SHA)
            r44_bin = (
                ROOT
                / "local/build/demo11-native-product-r44"
                / "BrutalMarioDemo11ProductR44SNESRecomp"
            )
            if r44_bin.is_file():
                self.assertEqual(
                    receipt["host_binary_sha256"],
                    hashlib.sha256(r44_bin.read_bytes()).hexdigest(),
                )

            wram = (cap_134 / "room134_f60.wram.bin").read_bytes()
            self.assertEqual(wram[0x010B] | (wram[0x010C] << 8), 0x134)

            for frame_tag in ("room134_f0", "room134_f60"):
                sp4 = (cap_134 / f"{frame_tag}.vram.bin").read_bytes()[0xF000:0x10000]
                self.assertEqual(hashlib.sha256(sp4).hexdigest(), DECODED_SHA)
                if do1_134.is_dir():
                    do1_sp4 = (do1_134 / f"{frame_tag}.vram.bin").read_bytes()[0xF000:0x10000]
                    self.assertEqual(sp4, do1_sp4)

            fb = (cap_134 / "room134_f60.fb.bgrx").read_bytes()
            i_center = (64 * 256 + 128) * 4
            b, g, r, _ = fb[i_center : i_center + 4]
            self.assertEqual((r, g, b), (255, 255, 156))

            sun_ys, sun_xs = [], []
            for y in range(49, 79):
                row_xs = []
                for x in range(100, 160):
                    idx = (y * 256 + x) * 4
                    pb, pg, pr, _ = fb[idx : idx + 4]
                    if (pr, pg, pb) == (255, 255, 156):
                        row_xs.append(x)
                self.assertTrue(row_xs, f"missing sun pixels on scanline y={y}")
                sun_ys.append(y)
                sun_xs.extend(row_xs)
            self.assertEqual(min(sun_ys), 49)
            self.assertEqual(max(sun_ys), 78)
            self.assertLessEqual(min(sun_xs), 115)
            self.assertGreaterEqual(max(sun_xs), 140)

        if cap_174.is_dir():
            wram = (cap_174 / "room174_f60.wram.bin").read_bytes()
            self.assertEqual(wram[0x010B] | (wram[0x010C] << 8), 0x174)
            sp4 = (cap_174 / "room174_f60.vram.bin").read_bytes()[0xF000:0x10000]
            self.assertEqual(hashlib.sha256(sp4).hexdigest(), DECODED_SHA)

    def test_launchers_mount_product_r44_env(self):
        import launch_native

        r44_bin = (
            ROOT
            / "local/build/demo11-native-product-r44"
            / "BrutalMarioDemo11ProductR44SNESRecomp"
        )
        if R44_ROM.is_file() and r44_bin.is_file():
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/play_native_target.py",
                    "--target",
                    "demo11-native-product-r44",
                    "--print-env",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            env_map = dict(
                line.split("=", 1)
                for line in result.stdout.splitlines()
                if line.startswith("BM_")
            )
            self.assertEqual(len(env_map), 66)
            self.assertIn("BM_EXGFX_1B2_PACK", env_map)
            self.assertTrue(env_map["BM_EXGFX_1B2_PACK"].endswith("/exgfx-1b2.bin"))
            launch_env = {
                k: v
                for k, v in launch_native.environment("demo11-native-product-r44").items()
                if k.startswith("BM_")
            }
            self.assertEqual(env_map, launch_env)


if __name__ == "__main__":
    unittest.main()
