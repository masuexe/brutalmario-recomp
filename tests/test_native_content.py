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
        cls.payload = bytes(range(1, 17))
        rom = bytearray([0x5a]) * 0x400000
        rom[0x1b0008:0x1b0018] = bytes(16)
        def digest(name, data):
            return f'static const uint8_t {name}[32] = {{' + ','.join(
                str(x) for x in hashlib.sha256(data).digest()) + '};\n'
        (cls.path / 'native_content_manifest.h').write_text(
            '#include <stdint.h>\n#define BM_CONTENT_ID "synthetic"\n'
            '#define BM_CONTENT_BANK 0xb6u\n#define BM_CONTENT_OFFSET 0x1b0008u\n'
            '#define BM_CONTENT_SIZE 16u\n#define BM_CONTENT_ROM_SIZE 0x400000u\n' +
            digest('bm_content_rom_sha', rom) + digest('bm_content_payload_sha', cls.payload))
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
        env = os.environ.copy()
        env.pop('BM_NATIVE_CONTENT_PACK', None)
        if payload is not None:
            path = self.path / 'pack.bin'
            path.write_bytes(payload)
            env['BM_NATIVE_CONTENT_PACK'] = str(path)
        return subprocess.run([str(self.binary), mode], env=env,
                              text=True, capture_output=True, timeout=10)

    def test_independent_bank_and_boundaries(self):
        result = self.run_loader(self.payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('mount lifecycle passed', result.stdout)
        self.assertIn('first_asset_resolution=B68008', result.stderr)

    def test_missing_pack_is_fatal(self):
        result = self.run_loader(None)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('BM_NATIVE_CONTENT_PACK is required', result.stderr)

    def test_corrupt_pack_is_fatal(self):
        result = self.run_loader(bytes(16))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('pack SHA-256 differs', result.stderr)

    def test_truncated_or_oversized_pack_is_fatal(self):
        for payload in (self.payload[:-1], self.payload + b'\x00'):
            with self.subTest(size=len(payload)):
                result = self.run_loader(payload)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('pack size differs', result.stderr)

    def test_wrong_rom_is_fatal(self):
        result = self.run_loader(self.payload, 'wrong-rom')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROM identity differs', result.stderr)


if __name__ == '__main__':
    unittest.main()
