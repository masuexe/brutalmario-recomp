#!/usr/bin/env python3
"""Review gates for the all-levels completion cheat."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

SCRIPT = ROOT / "recomp/inputs/cheat-complete-all.script"
DOC = ROOT / "docs/completion-cheat-product.md"


class CompletionCheatTests(unittest.TestCase):
    def test_script_writes_the_pinned_fields(self):
        text = SCRIPT.read_text()
        self.assertIn("poke 1ea2 " + "9f" * 0x60, text)
        self.assertIn("poke 1f02 " + "ff" * 0x0f, text)
        self.assertIn("poke 1f27 01010101", text)
        self.assertIn("poke 1f2e 60", text)
        self.assertIn("poke 1f2f " + "ff" * 12, text)
        self.assertIn("poke 1182c " + "00" * 24, text)

    def test_script_waits_for_the_map_and_reloads(self):
        text = SCRIPT.read_text()
        self.assertLess(text.index("until 0100 == 0e"), text.index("poke 1ea2"))
        self.assertIn("poke 0100 0b", text)
        self.assertNotIn("quit", text)

    def test_launcher_offers_the_cheat(self):
        text = (ROOT / "tools/play_native_target.py").read_text()
        self.assertIn("--complete-all", text)
        self.assertIn("cheat-complete-all.script", text)
        self.assertIn("save.srm.before-cheat", text)

    def test_document_records_the_measured_result(self):
        doc = DOC.read_text()
        self.assertIn("23964 pixels", doc)
        self.assertIn("cheat-verify2", doc)
        self.assertIn("mode `$14`", doc)


    def test_special_zone_script_uses_map_five(self):
        text = (ROOT / "recomp/inputs/cheat-special-zone.script").read_text()
        self.assertIn("poke 1f11 0505", text)
        self.assertIn("poke 1f17 1801280118012801", text)
        self.assertIn("until 1f11 == 05 600", text)
        self.assertNotIn("quit", text)

    def test_launcher_offers_special_zone(self):
        text = (ROOT / "tools/play_native_target.py").read_text()
        self.assertIn("--special-zone", text)
        self.assertIn("cheat-special-zone.script", text)

    def test_document_explains_center_versus_warp(self):
        doc = DOC.read_text()
        self.assertIn("## The Special Zone map", doc)
        self.assertIn("$0178/$01A8", doc)
        self.assertIn("$0178/$01C8", doc)
        self.assertIn("--special-zone", doc)

    def test_r47_cheat_scripts_reach_overworld_and_special_zone(self):
        binary = ROOT / "local/build/demo11-native-product-r47/BrutalMarioDemo11ProductR47SNESRecomp"
        rom = ROOT / "local/restoration/demo11-native-product-r47/rom.sfc"
        if not binary.is_file() or not rom.is_file():
            self.skipTest("demo11-native-product-r47 native build not present")

        import native_sprite_gap
        import package_public_beta as ppb

        env_base = os.environ.copy()
        env_base.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", SNESRECOMP_REWIND="0")
        native_sprite_gap.environment("demo11-native-product-r47", env_base)

        cases = [
            ("cheat-complete-all.script", "en", None),
            ("cheat-special-zone.script", "en", 5),
            ("cheat-special-zone.script", "ja", 5),
        ]
        for sname, lang, expected_map in cases:
            with tempfile.TemporaryDirectory(prefix=f"bm-cheat-{lang}-") as tmp:
                tp = Path(tmp)
                (tp / "saves").mkdir()
                cfg = tp / "config.ini"
                cfg.write_text(ppb.format_config_ini("linux"), encoding="utf-8")
                sc = tp / sname
                sc.write_text(
                    (ROOT / "recomp/inputs" / sname).read_text(encoding="utf-8")
                    + "\ndump end\nquit\n",
                    encoding="utf-8",
                )
                env = dict(env_base)
                env["BM_LANG"] = lang
                env["SNESRECOMP_DUMP_DIR"] = str(tp)
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
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
                self.assertEqual(
                    res.returncode, 0, f"{sname} ({lang}) failed: {res.stderr}\n{res.stdout}"
                )
                wram = (tp / "end.wram.bin").read_bytes()
                self.assertEqual(wram[0x0100], 0x0E)
                self.assertEqual(wram[0x1EA2], 0x9F)
                if expected_map is not None:
                    self.assertEqual(wram[0x1F11], expected_map)
                    self.assertEqual(wram[0x1F17] | (wram[0x1F18] << 8), 0x118)
                    self.assertEqual(wram[0x1F19] | (wram[0x1F1A] << 8), 0x128)

if __name__ == "__main__":
    unittest.main()