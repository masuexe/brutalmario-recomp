"""Synthetic execution tests for immutable external code and graphics banks."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'local/upstream/snesrecomp/runner/src'
sys.path.insert(0, str(ROOT / 'tools'))
import native_sprite


@unittest.skipUnless(shutil.which('cc') and (ENGINE / 'snes/interp816.c').is_file(),
                     'requires the pinned runtime and C compiler')
class NativeSpriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='bm-native-sprite-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.path = Path(cls.temp.name)
        cls.code = bytes.fromhex('8b4baba92a8d2815ab6b')
        cls.graphics = bytes(range(1, 17))
        rom = bytearray([0x5a]) * 0x400000
        rom[0x1b0008:0x1b0018] = bytes(16)
        rom[:5] = bytes.fromhex('22cd95a5db')
        rom[0x100:0x108] = bytes.fromhex('48a9778d29156840')
        rom[0x7fea:0x7fec] = bytes.fromhex('0081')
        def digest(name, data):
            return f'static const uint8_t {name}[32] = {{' + ','.join(
                str(v) for v in hashlib.sha256(data).digest()) + '};\n'
        macros = {'ROM_SIZE': 0x400000, 'CODE_OFFSET': 0x1295cd, 'CODE_SIZE': len(cls.code),
                  'CODE_BANK': 0xa5, 'GFX_OFFSET': 0x1b0008, 'GFX_SIZE': 16, 'GFX_BANK': 0xb6,
                  'FIRST_PAGE': 0xa595, 'LAST_PAGE': 0xa595}
        header = '#include <stdint.h>\n' + ''.join(
            f'#define BM_SPRITE_{key} {value}u\n' for key, value in macros.items())
        header += digest('bm_sprite_rom_sha', rom) + digest('bm_sprite_code_sha', cls.code)
        header += digest('bm_sprite_gfx_sha', cls.graphics)
        (cls.path / 'native_sprite_manifest.h').write_text(header)
        source = cls.path / 'runner/src/snes/cart.c'
        source.parent.mkdir(parents=True)
        source.write_bytes((ENGINE / 'snes/cart.c').read_bytes())
        subprocess.run(['git', 'apply', '--unsafe-paths', '--directory=' + str(cls.path),
                        str(ROOT / 'patches/runtime/0008-native-content-bank.patch')], check=True)
        cls.binary = cls.path / 'sprite-test'
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wno-type-limits',
                        '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
                        '-I' + str(cls.path), '-I' + str(ROOT / 'recomp'), '-I' + str(ENGINE),
                        '-I' + str(ENGINE / 'snes'), str(ROOT / 'tests/native_sprite_test.c'),
                        str(ROOT / 'recomp/native_sprite.c'), str(source),
                        str(ENGINE / 'sha256.c'), str(ENGINE / 'snes/interp816.c'),
                        '-o', str(cls.binary)], check=True)

    def run_loader(self, code, graphics, mode='valid'):
        env = os.environ.copy()
        for variable, data, name in (('BM_NATIVE_SPRITE_PACK', code, 'code.bin'),
                                     ('BM_NATIVE_GRAPHICS_PACK', graphics, 'graphics.bin')):
            env.pop(variable, None)
            if data is not None:
                path = self.path / name
                path.write_bytes(data)
                env[variable] = str(path)
        return subprocess.run([str(self.binary), mode], env=env,
                              text=True, capture_output=True, timeout=10)

    def test_external_code_executes_and_returns_across_interrupt(self):
        result = self.run_loader(self.code, self.graphics)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('NMI/RTI and JSL/RTL return passed', result.stdout)

    def test_each_pack_is_required(self):
        for code, graphics, variable in ((None, self.graphics, 'BM_NATIVE_SPRITE_PACK'),
                                         (self.code, None, 'BM_NATIVE_GRAPHICS_PACK')):
            with self.subTest(variable=variable):
                result = self.run_loader(code, graphics)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('rejected: ' + variable, result.stderr)

    def test_each_pack_hash_is_checked(self):
        for code, graphics in ((bytes(len(self.code)), self.graphics),
                               (self.code, bytes(len(self.graphics)))):
            result = self.run_loader(code, graphics)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('pack SHA-256 differs', result.stderr)

    def test_code_size_is_checked(self):
        for code in (self.code[:-1], self.code + b'\0'):
            result = self.run_loader(code, self.graphics)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('pack size differs', result.stderr)

    def test_rom_identity_is_checked(self):
        result = self.run_loader(self.code, self.graphics, 'wrong-rom')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROM identity differs', result.stderr)

    def test_build_rejects_compiled_code_in_split_bank_or_alias(self):
        for bank in (0x25, 0xa5, 0x36, 0xb6):
            with tempfile.TemporaryDirectory(prefix='bm-sprite-aot-') as folder:
                experiment = Path(folder)
                path = experiment / 'src/gen/program_manifest.json'
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'nodes': {f'{bank:02X}95DC:M1X1': {}}}))
                with self.assertRaisesRegex(ValueError, 'forbids AOT nodes'):
                    native_sprite.configure(experiment, 'Synthetic', native_sprite.TARGET)


if __name__ == '__main__':
    unittest.main()
