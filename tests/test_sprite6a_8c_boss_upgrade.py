import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_sprite_module as psm
from restore_star_world_1 import lorom

BOSS_ROM = ROOT / "local/content-versions/boss/rom.sfc"
R42_ROM = ROOT / "local/restoration/demo11-native-product-r42/rom.sfc"
R43_ROM = ROOT / "local/restoration/demo11-native-product-r43/rom.sfc"


class TestSprite6A8CBossUpgrade(unittest.TestCase):
    def test_sprite6a_boss_module_manifest_and_audit(self):
        manifest_path = ROOT / "config/native-content/sprite6a-boss-module.json"
        self.assertTrue(manifest_path.is_file())
        recipe = json.loads(manifest_path.read_text())
        self.assertEqual(recipe["id"], "sprite6a-boss-module")
        self.assertEqual(recipe["record"]["slot"], "6A")
        self.assertEqual(recipe["record"]["raw"], "013610003bab18401dc21e65c21e0000")
        self.assertEqual(recipe["record"]["native_raw"], "013610003bab18401dc28765c2870000")
        self.assertEqual(recipe["code"]["source_address"], "1EC20E")
        self.assertEqual(recipe["code"]["native_address"], "87C20E")
        self.assertEqual(recipe["code"]["size"], 3385)

        if BOSS_ROM.is_file() and R42_ROM.is_file():
            donor = BOSS_ROM.read_bytes()
            base = R42_ROM.read_bytes()
            rec_info = psm.check_record(donor, recipe)
            self.assertEqual(rec_info["slot"], "6A")
            code, audit = psm.build_code(donor, base, recipe)
            self.assertEqual(len(code), 3385)
            self.assertEqual(
                hashlib.sha256(code).hexdigest(),
                recipe["code"]["adapted_sha256"],
            )
            self.assertEqual(
                audit["outside_calls"],
                [
                    "00F5B7",
                    "01802A",
                    "0187A7",
                    "01A7DC",
                    "01AB99",
                    "01B7B3",
                    "02A9DE",
                    "07F7D2",
                    "27FAF4",
                ],
            )

    def test_sprite8c_boss_module_manifest_and_audit(self):
        manifest_path = ROOT / "config/native-content/sprite8c-boss-module.json"
        self.assertTrue(manifest_path.is_file())
        recipe = json.loads(manifest_path.read_text())
        self.assertEqual(recipe["id"], "sprite8c-boss-module")
        self.assertEqual(recipe["record"]["slot"], "8C")
        self.assertEqual(recipe["record"]["raw"], "013600003503194448ac1362ac130000")
        self.assertEqual(recipe["record"]["native_raw"], "013600003503194448ac8862ac880000")
        self.assertEqual(recipe["code"]["source_address"], "13AC37")
        self.assertEqual(recipe["code"]["native_address"], "88AC37")
        self.assertEqual(recipe["code"]["size"], 465)

        if BOSS_ROM.is_file() and R42_ROM.is_file():
            donor = BOSS_ROM.read_bytes()
            base = R42_ROM.read_bytes()
            rec_info = psm.check_record(donor, recipe)
            self.assertEqual(rec_info["slot"], "8C")
            code, audit = psm.build_code(donor, base, recipe)
            self.assertEqual(len(code), 465)
            self.assertEqual(
                hashlib.sha256(code).hexdigest(),
                recipe["code"]["adapted_sha256"],
            )
            self.assertEqual(
                audit["outside_calls"],
                ["01801A", "019138", "01A7DC", "01B7B3", "0285DF", "27FAF4"],
            )

    def test_product_r43_recipe_and_rom_derivation(self):
        cfg_path = ROOT / "config/restorations/demo11-native-product-r43.json"
        self.assertTrue(cfg_path.is_file())
        cfg = json.loads(cfg_path.read_text())
        self.assertEqual(cfg["id"], "demo11-native-product-r43")
        self.assertEqual(cfg["parent_restoration"], "demo11-native-product-r42")
        self.assertIn(
            "config/native-content/sprite6a-boss-module.json",
            cfg["native_sprite_gap"]["manifests"],
        )
        self.assertIn(
            "config/native-content/sprite8c-boss-module.json",
            cfg["native_sprite_gap"]["manifests"],
        )
        self.assertEqual(
            cfg["code_patches"],
            [
                {
                    "address": "188912",
                    "before": "013610003b8b1840f4be203fbf200000",
                    "after": "013610003bab18401dc28765c2870000",
                    "role": "Upgrade custom sprite slot 6A from older cheap-demo ROM copy ($20:BEF4 / $20:BF3F) to the 7hero/boss program in native bank 87 ($87:C21D / $87:C265).",
                },
                {
                    "address": "188B32",
                    "before": "0136000035031944a79a23c39a230000",
                    "after": "013600003503194448ac8862ac880000",
                    "role": "Upgrade custom sprite slot 8C from older cheap-demo ROM copy ($23:9AA7 / $23:9AC3) to the 7hero/boss program in native bank 88 ($88:AC48 / $88:AC62).",
                },
            ],
        )

        if R42_ROM.is_file() and R43_ROM.is_file():
            r42_rom = R42_ROM.read_bytes()
            r43_rom = R43_ROM.read_bytes()
            self.assertEqual(hashlib.sha256(r43_rom).hexdigest(), cfg["output"]["sha256"])

            expected = bytearray(r42_rom)
            off_6a = lorom(0x318272) + 0x6A * 16
            off_8c = lorom(0x318272) + 0x8C * 16
            self.assertEqual(off_6a, 0x188912)
            self.assertEqual(off_8c, 0x188B32)
            expected[off_6a : off_6a + 16] = bytes.fromhex("013610003bab18401dc28765c2870000")
            expected[off_8c : off_8c + 16] = bytes.fromhex("013600003503194448ac8862ac880000")
            self.assertEqual(bytes(expected), r43_rom)

    def test_runtime_captures_for_r43_6a_8c_and_0a(self):
        cap_0d8 = ROOT / "local/captures/r43-room0d8-sprite6a"
        cap_16b = ROOT / "local/captures/r43-room16b-sprite8c"
        cap_081 = ROOT / "local/captures/r43-room081-sprite0a"
        donor_16b = ROOT / "local/captures/type3-room16b-7hero-v1"
        old_16b = ROOT / "local/captures/type3-room16b-native-v1"

        if cap_0d8.is_dir():
            log_0d8 = (cap_0d8 / "run.log").read_text()
            self.assertIn("bank=87 resolutions=656004 executed_page_instructions=102017", log_0d8)
            w_later = (cap_0d8 / "existing_later.wram.bin").read_bytes()
            self.assertEqual(w_later[0x010B] | (w_later[0x010C] << 8), 0x0D8)
            self.assertEqual(w_later[0x14C8 + 2], 0x08)
            self.assertEqual(w_later[0x1AB9E + 2], 0x6A)
            self.assertEqual(w_later[0xC2 + 2], 0x10)

        if cap_16b.is_dir():
            log_16b = (cap_16b / "run.log").read_text()
            self.assertIn("bank=88 resolutions=248515 executed_page_instructions=41399", log_16b)
            w_r2 = (cap_16b / "r2.wram.bin").read_bytes()
            self.assertEqual(w_r2[0x010B] | (w_r2[0x010C] << 8), 0x16B)
            self.assertEqual(w_r2[0x14C8 + 6], 0x08)
            self.assertEqual(w_r2[0x1AB9E + 6], 0x8C)
            # With the 7hero/boss 8C program, actor 6 stops at ceiling Y=0x00C9 in state C2=0x01
            y_r43 = w_r2[0xD8 + 6] | (w_r2[0x14D4 + 6] << 8)
            self.assertEqual(y_r43, 0x00C9)
            self.assertEqual(w_r2[0xC2 + 6], 0x01)
            self.assertEqual(w_r2[0xAA + 6], 0x00)
            self.assertGreater(w_r2[0x15AC + 6], 0)

            if donor_16b.is_dir():
                w_donor = (donor_16b / "r2.wram.bin").read_bytes()
                y_donor = w_donor[0xD8 + 6] | (w_donor[0x14D4 + 6] << 8)
                self.assertEqual(y_r43, y_donor)
                self.assertEqual(w_r2[0xC2 + 6], w_donor[0xC2 + 6])
                self.assertEqual(w_r2[0xAA + 6], w_donor[0xAA + 6])

            if old_16b.is_dir():
                w_old = (old_16b / "r2.wram.bin").read_bytes()
                y_old = w_old[0xD8 + 6] | (w_old[0x14D4 + 6] << 8)
                self.assertEqual(y_old, 0xFEE9)
                self.assertEqual(w_old[0xC2 + 6], 0x00)

        if cap_081.is_dir():
            log_081 = (cap_081 / "run.log").read_text()
            self.assertIn("bank=86 resolutions=216495 executed_page_instructions=33952", log_081)

    def test_default_launchers_point_to_product_r43(self):
        import subprocess
        import launch_native

        self.assertIn(
            'default="demo11-native-product-r43"',
            (ROOT / "tools/launch_native.py").read_text(),
        )
        self.assertIn(
            "default='demo11-native-product-r43'",
            (ROOT / "tools/play_native_target.py").read_text(),
        )
        self.assertIn(
            "default='demo11-native-product-r43'",
            (ROOT / "tools/play_native_cheats.py").read_text(),
        )

        r43_bin = (
            ROOT
            / "local/build/demo11-native-product-r43"
            / "BrutalMarioDemo11ProductR43SNESRecomp"
        )
        if R43_ROM.is_file() and r43_bin.is_file():
            result = subprocess.run(
                [sys.executable, "tools/play_native_target.py", "--print-env"],
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
            values = set(env_map.values())
            for expected_file in (
                "sprite6a-boss-code.bin",
                "sprite8c-boss-code.bin",
                "sprite0a-code.bin",
                "music-pack.bin",
            ):
                self.assertTrue(
                    any(val.endswith("/" + expected_file) for val in values),
                    f"missing {expected_file} in default launcher env",
                )
            launch_env = {
                k: v
                for k, v in launch_native.environment("demo11-native-product-r43").items()
                if k.startswith("BM_")
            }
            self.assertEqual(env_map, launch_env)


if __name__ == "__main__":
    unittest.main()
