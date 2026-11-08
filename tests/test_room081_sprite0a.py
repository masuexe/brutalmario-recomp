import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_sprite_module as psm
from restore_star_world_1 import lorom

CHEAP_DEMO_ROM = ROOT / "local/content-versions/cheap-demo/rom.sfc"


class TestRoom081Sprite0A(unittest.TestCase):
    def test_sprite0a_module_manifest_and_audit(self):
        manifest_path = ROOT / "config/native-content/sprite0a-module.json"
        self.assertTrue(manifest_path.is_file())
        recipe = json.loads(manifest_path.read_text())
        self.assertEqual(recipe["id"], "sprite0a-module")
        self.assertEqual(recipe["record"]["slot"], "0A")
        self.assertEqual(recipe["record"]["raw"], "013601062f01196c20fc1340fc130000")
        self.assertEqual(recipe["record"]["native_raw"], "013601062f01196c20fc8640fc860000")
        self.assertEqual(recipe["code"]["source_address"], "13FBC5")
        self.assertEqual(recipe["code"]["native_address"], "86FBC5")
        self.assertEqual(recipe["code"]["size"], 885)

        if CHEAP_DEMO_ROM.is_file():
            donor = CHEAP_DEMO_ROM.read_bytes()
            r41_path = ROOT / "local/restoration/demo11-native-product-r41/rom.sfc"
            if r41_path.is_file():
                base = r41_path.read_bytes()
                rec_info = psm.check_record(donor, recipe)
                self.assertEqual(rec_info["slot"], "0A")
                code, audit = psm.build_code(donor, base, recipe)
                self.assertEqual(len(code), 885)
                self.assertEqual(
                    hashlib.sha256(code).hexdigest(),
                    recipe["code"]["adapted_sha256"],
                )
                self.assertEqual(
                    audit["outside_calls"],
                    ["01802A", "018032", "01A7DC", "01B7B3", "02A9DE", "07F7D2"],
                )

    def test_product_r42_recipe_and_rom_derivation(self):
        cfg_path = ROOT / "config/restorations/demo11-native-product-r42.json"
        self.assertTrue(cfg_path.is_file())
        cfg = json.loads(cfg_path.read_text())
        self.assertEqual(cfg["id"], "demo11-native-product-r42")
        self.assertEqual(cfg["parent_restoration"], "demo11-native-product-r41")
        self.assertIn(
            "config/native-content/sprite0a-module.json",
            cfg["native_sprite_gap"]["manifests"],
        )
        self.assertEqual(
            cfg["code_patches"],
            [
                {
                    "address": "188312",
                    "before": "012800003f9bb9c4be8313c283130000",
                    "after": "013601062f01196c20fc8640fc860000",
                    "role": "Point custom sprite slot 0A at the cheap-demo room 081 program block in native bank 86.",
                }
            ],
        )

        r41_rom_path = ROOT / "local/restoration/demo11-native-product-r41/rom.sfc"
        r42_rom_path = ROOT / "local/restoration/demo11-native-product-r42/rom.sfc"
        r42_pack_path = ROOT / "local/restoration/demo11-native-product-r42/sprite0a-code.bin"
        if r41_rom_path.is_file() and r42_rom_path.is_file() and r42_pack_path.is_file():
            r41_rom = r41_rom_path.read_bytes()
            r42_rom = r42_rom_path.read_bytes()
            self.assertEqual(hashlib.sha256(r42_rom).hexdigest(), cfg["output"]["sha256"])

            expected = bytearray(r41_rom)
            rec_off = lorom(0x318272) + 0x0A * 16
            self.assertEqual(rec_off, 0x188312)
            self.assertEqual(
                expected[rec_off : rec_off + 16].hex(),
                "012800003f9bb9c4be8313c283130000",
            )
            expected[rec_off : rec_off + 16] = bytes.fromhex(
                "013601062f01196c20fc8640fc860000"
            )
            self.assertEqual(bytes(expected), r42_rom)

            pack = r42_pack_path.read_bytes()
            self.assertEqual(len(pack), 885)
            self.assertEqual(
                hashlib.sha256(pack).hexdigest(),
                "cf5559f3eaedcf809aeb0fbbeddbabc50b04f334b5b8d40a1c434d507c90abcf",
            )

    def test_runtime_captures_room081_sprite0a(self):
        r41_cap = ROOT / "local/captures/r41-room081"
        r42_cap = ROOT / "local/captures/r42-room081-sprite0a-v2"
        cd_cap = ROOT / "local/captures/cheap-demo-room081-sprite0a"

        if r41_cap.is_dir():
            for name in ("arrived", "later"):
                w = (r41_cap / f"{name}.wram.bin").read_bytes()
                self.assertEqual(w[0x14C8 + 9], 0x08)
                self.assertEqual(w[0x9E + 9], 0x28)
                self.assertEqual(w[0x1AB9E + 9], 0x0A)
                self.assertEqual(w[0x1570 + 9], 0x00)
                self.assertEqual(w[0x1558 + 9], 0x00)
                self.assertEqual(w[0xB6 + 9], 0x00)

        if r42_cap.is_dir() and cd_cap.is_dir():
            for cap in (r42_cap, cd_cap):
                xs, ys = set(), set()
                for name in ("arrived", "approach", "active1", "active2", "active3"):
                    w = (cap / f"{name}.wram.bin").read_bytes()
                    self.assertEqual(w[0x100], 0x14)
                    self.assertEqual(w[0x10B] | (w[0x10C] << 8), 0x081)
                    self.assertEqual(w[0x14C8 + 9], 0x08)
                    self.assertEqual(w[0x9E + 9], 0x36)
                    self.assertEqual(w[0x1AB9E + 9], 0x0A)
                    self.assertIn((w[0x1570 + 9] + w[0x1558 + 9]) & 0xFF, (0xD0, 0x70))
                    self.assertIn(w[0xB6 + 9], (0x08, 0xF8))
                    xs.add(w[0xE4 + 9] | (w[0x14E0 + 9] << 8))
                    ys.add(w[0xD8 + 9] | (w[0x14D4 + 9] << 8))
                self.assertGreater(len(xs), 1)
                self.assertTrue(any(y < 0x0140 for y in ys))

            # Child projectile sprite 0xB3 spawned during jump in r42 approach dump
            w_app = (r42_cap / "approach.wram.bin").read_bytes()
            self.assertEqual(w_app[0x14C8 + 7], 0x08)
            self.assertEqual(w_app[0x9E + 7], 0xB3)

            # Interpreter coverage hits $86:FC20 (INIT) and $86:FC40 (MAIN)
            cov_files = sorted((r42_cap / "coverage").rglob("*.json"))
            self.assertTrue(cov_files)
            cov = json.loads(cov_files[-1].read_text())
            hits = {d["target_pc24"].upper(): d["observed_hits"] for d in cov["discoveries"]}
            self.assertGreater(hits.get("0X86FC20", 0), 0)
            self.assertGreater(hits.get("0X86FC40", 0), 0)


if __name__ == "__main__":
    unittest.main()
