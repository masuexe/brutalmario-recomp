"""Synthetic tests of the compiled native loader and actual cartridge resolver."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'local/upstream/snesrecomp/runner/src'


@unittest.skipUnless(shutil.which('cc') and (ENGINE / 'sha256.c').is_file(),
                     'requires the pinned runtime and C compiler')
class NativeContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='bm-native-content-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.path = Path(cls.temp.name)
        cls.payload = bytes(range(1, 25))
        rom = bytearray([0x5a]) * 0x400000
        rom[0x1b0008:0x1b0018] = bytes(16)
        rom[0x1b0108:0x1b0110] = bytes(8)
        def digest(name, data):
            return f'static const uint8_t {name}[32] = {{' + ','.join(
                str(x) for x in hashlib.sha256(data).digest()) + '};\n'
        (cls.path / 'native_content_manifest.h').write_text(
            '#include <stdint.h>\n#define BM_CONTENT_ID "synthetic"\n'
            '#define BM_CONTENT_REGION_COUNT 2u\n#define BM_CONTENT_PACK_SIZE 24u\n'
            '#define BM_CONTENT_ROM_SIZE 0x400000u\n'
            'static const size_t bm_content_region_offset[2] = {0x1b0008u, 0x1b0108u};\n'
            'static const size_t bm_content_region_size[2] = {16u, 8u};\n' +
            digest('bm_content_pack_sha', cls.payload))
        source = cls.path / 'runner/src/snes/cart.c'
        source.parent.mkdir(parents=True)
        source.write_bytes((ENGINE / 'snes/cart.c').read_bytes())
        subprocess.run(['git', 'apply', '--unsafe-paths', '--directory=' + str(cls.path),
                        str(ROOT / 'patches/runtime/0008-native-content-bank.patch')], check=True)
        cls.binary = cls.path / 'loader-test'
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-type-limits',  # Existing upstream uint8_t <= 0xff check.
                        '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
                        '-I' + str(cls.path), '-I' + str(ROOT / 'recomp'),
                        '-I' + str(ENGINE), '-I' + str(ENGINE / 'snes'),
                        str(ROOT / 'tests/native_content_test.c'),
                        str(ROOT / 'recomp/native_content.c'), str(source),
                        str(ENGINE / 'sha256.c'), '-o', str(cls.binary)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_loader(self, payload, mode='valid'):
        if mode == 'valid':
            mode = 'plain'
        env = os.environ.copy()
        env.pop('BM_NATIVE_CONTENT_PACK', None)
        if payload is not None:
            path = self.path / 'pack.bin'
            path.write_bytes(payload)
            env['BM_NATIVE_CONTENT_PACK'] = str(path)
        return subprocess.run([str(self.binary), mode], env=env,
                              text=True, capture_output=True, timeout=10)

    def test_two_regions_and_boundaries(self):
        result = self.run_loader(self.payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Two regions, exact region bytes', result.stdout)

    def test_missing_pack_is_fatal(self):
        result = self.run_loader(None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('BM_NATIVE_CONTENT_PACK is required', result.stderr)

    def test_corrupt_pack_is_fatal(self):
        result = self.run_loader(bytes(24))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('pack SHA-256 differs', result.stderr)

    def test_truncated_or_oversized_pack_is_fatal(self):
        for payload in (self.payload[:-1], self.payload + b'\x00'):
            with self.subTest(size=len(payload)):
                result = self.run_loader(payload)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('pack size differs', result.stderr)

    def test_occupied_region_is_fatal(self):
        # A region must be empty in the image, because the pack holds its bytes.
        result = self.run_loader(self.payload, 'occupied')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('image still holds region bytes', result.stderr)


if __name__ == '__main__':
    unittest.main()
