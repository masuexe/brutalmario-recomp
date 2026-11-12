#!/usr/bin/env python3
"""Unit tests for BMPT v1 delta patching, bm_launcher, and Public Beta packaging."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_smw_delta as delta


class PublicBetaPackageTests(unittest.TestCase):
    def test_synthetic_bmpt_round_trip_and_smc_header_strip(self):
        fake_base = bytes((i * 37 + 13) & 0xFF for i in range(delta.BASE_SIZE))
        # Patch BASE_SHA256 temporarily for synthetic test
        orig_sha = delta.BASE_SHA256
        delta.BASE_SHA256 = hashlib.sha256(fake_base).hexdigest()
        try:
            idx = delta.build_base_index(fake_base)
            # Construct a target containing: base slice + zero run + literal + another base slice
            target = (
                b"HEADER_LIT_"
                + fake_base[1000:5000]
                + (b"\x00" * 512)
                + b"MID_CUSTOM_BYTES_12345"
                + fake_base[200000:202048]
            )
            ops = delta.encode_stream(target, fake_base, idx)
            kinds = [op[0] for op in ops]
            self.assertIn(delta.OP_COPY, kinds)
            self.assertIn(delta.OP_ZERO, kinds)
            self.assertIn(delta.OP_LITERAL, kinds)

            # Build mini BMPT packet manually using the encoder output
            import struct
            pkt = bytearray()
            pkt += delta.MAGIC
            pkt += struct.pack("<I", delta.BASE_SIZE)
            pkt += bytes.fromhex(delta.BASE_SHA256)
            pkt += struct.pack("<I", 1)
            rel = b"data/rom.sfc"
            pkt += struct.pack("<H", len(rel)) + rel
            pkt += struct.pack("<I", len(target))
            pkt += hashlib.sha256(target).digest()
            pkt += struct.pack("<I", len(ops))
            for op in ops:
                if op[0] == delta.OP_COPY:
                    pkt += struct.pack("<BII", delta.OP_COPY, op[1], op[2])
                elif op[0] == delta.OP_ZERO:
                    pkt += struct.pack("<BI", delta.OP_ZERO, op[1])
                else:
                    pkt += struct.pack("<BI", delta.OP_LITERAL, len(op[1])) + op[1]
            pkt += hashlib.sha256(pkt).digest()

            # Verify headerless and 512-byte SMC headered inputs produce identical output
            out_raw = delta.apply_patch_bytes(fake_base, bytes(pkt))
            out_smc = delta.apply_patch_bytes(b"\xAA" * 512 + fake_base, bytes(pkt))
            self.assertEqual(out_raw["data/rom.sfc"], target)
            self.assertEqual(out_smc["data/rom.sfc"], target)

            # Corrupt 1 byte in patch -> must raise ValueError
            bad = bytearray(pkt)
            bad[60] ^= 0xFF
            with self.assertRaisesRegex(ValueError, "integrity"):
                delta.apply_patch_bytes(fake_base, bytes(bad))
        finally:
            delta.BASE_SHA256 = orig_sha

    def test_collect_r43_packs_covers_all_65_runtime_variables(self):
        r43_rom = ROOT / "local/restoration/demo11-native-product-r43/rom.sfc"
        if not r43_rom.is_file():
            self.skipTest("demo11-native-product-r43 restoration files not present")
        packs = delta.collect_target_packs("demo11-native-product-r43")
        self.assertEqual(len(packs), 65)
        variables = {p["variable"] for p in packs}
        self.assertEqual(len(variables), 65)
        self.assertIn("BM_NATIVE_CONTENT_PACK", variables)
        self.assertIn("BM_SPRITE_GRAPHICS_PACK", variables)
        self.assertIn("BM_SPRITE_GRAPHICS_PACK_2", variables)
        self.assertIn("BM_SEVEN_CODE_PACK_50", variables)

    def test_collect_r44_packs_covers_all_66_runtime_variables(self):
        r44_rom = ROOT / "local/restoration/demo11-native-product-r44/rom.sfc"
        if not r44_rom.is_file():
            self.skipTest("demo11-native-product-r44 restoration files not present")
        packs = delta.collect_target_packs("demo11-native-product-r44")
        self.assertEqual(len(packs), 66)
        variables = {p["variable"] for p in packs}
        self.assertEqual(len(variables), 66)
        self.assertIn("BM_NATIVE_CONTENT_PACK", variables)
        self.assertIn("BM_SPRITE_GRAPHICS_PACK", variables)
        self.assertIn("BM_SPRITE_GRAPHICS_PACK_2", variables)
        self.assertIn("BM_SEVEN_CODE_PACK_50", variables)
        self.assertIn("BM_EXGFX_1B2_PACK", variables)
        import package_public_beta as ppb
        readme = ppb.format_readme("demo11-native-product-r44")
        self.assertIn("全部 66 个原生扩展资源包", readme)
        self.assertIn("all 66 native content packs", readme)

    def test_bm_launcher_c_synthesizes_and_verifies_on_unicode_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "鬼畜马里奥 LauncherTest"
            (pkg / "bin").mkdir(parents=True)
            (pkg / "config").mkdir()
            (pkg / "patch").mkdir()

            launcher = pkg / "bin/bm_launcher"
            subprocess.run(
                [
                    "gcc", "-O2", "-Wall", "-Wextra", "-Werror", "-std=c11",
                    f"-I{ROOT / 'local/upstream/snesrecomp/runner/src'}",
                    str(ROOT / "recomp/bm_release_launcher.c"),
                    str(ROOT / "local/upstream/snesrecomp/runner/src/sha256.c"),
                    "-o", str(launcher),
                ],
                check=True,
            )

            fake_base = bytes(((i * 73) ^ (i >> 3)) & 0xFF for i in range(delta.BASE_SIZE))
            fake_sha = hashlib.sha256(fake_base).hexdigest()
            rom_target = b"SYNTH_ROM_HEADER" + fake_base[4096:16384] + b"\x00" * 1024
            pack_target = b"SYNTH_PACK" + fake_base[32768:36864]

            idx = delta.build_base_index(fake_base)
            import struct
            pkt = bytearray()
            pkt += delta.MAGIC
            pkt += struct.pack("<I", delta.BASE_SIZE)
            pkt += bytes.fromhex(fake_sha)
            pkt += struct.pack("<I", 2)
            for rel_str, content in (("data/rom.sfc", rom_target), ("data/packs/p1.bin", pack_target)):
                ops = delta.encode_stream(content, fake_base, idx)
                rel_b = rel_str.encode()
                pkt += struct.pack("<H", len(rel_b)) + rel_b
                pkt += struct.pack("<I", len(content))
                pkt += hashlib.sha256(content).digest()
                pkt += struct.pack("<I", len(ops))
                for op in ops:
                    if op[0] == delta.OP_COPY:
                        pkt += struct.pack("<BII", delta.OP_COPY, op[1], op[2])
                    elif op[0] == delta.OP_ZERO:
                        pkt += struct.pack("<BI", delta.OP_ZERO, op[1])
                    else:
                        pkt += struct.pack("<BI", delta.OP_LITERAL, len(op[1])) + op[1]
            pkt += hashlib.sha256(pkt).digest()
            (pkg / "patch/brutalmario.bmpatch").write_bytes(bytes(pkt))
            (pkg / "config/packs.manifest").write_text(
                f"ROM\tdata/rom.sfc\t{len(rom_target)}\t{hashlib.sha256(rom_target).hexdigest()}\n"
                f"BM_TEST_PACK\tdata/packs/p1.bin\t{len(pack_target)}\t{hashlib.sha256(pack_target).hexdigest()}\n",
                encoding="utf-8",
            )

            # Without base ROM -> exit code 2
            r_miss = subprocess.run([str(launcher), "--setup-only"], capture_output=True, text=True)
            self.assertEqual(r_miss.returncode, 2)

            # With 512-byte SMC headered base ROM -> exit code 0 & exact bytes synthesized
            (pkg / "any_name_smw.smc").write_bytes(b"\x55" * 512 + fake_base)
            r_ok = subprocess.run([str(launcher), "--setup-only"], capture_output=True, text=True)
            self.assertEqual(r_ok.returncode, 0, r_ok.stderr)
            self.assertEqual((pkg / "data/rom.sfc").read_bytes(), rom_target)
            self.assertEqual((pkg / "data/packs/p1.bin").read_bytes(), pack_target)

            r_ver = subprocess.run([str(launcher), "--verify"], capture_output=True, text=True)
            self.assertEqual(r_ver.returncode, 0, r_ver.stderr)


if __name__ == "__main__":
    unittest.main()
