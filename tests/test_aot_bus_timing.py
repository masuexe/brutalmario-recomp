"""Differential tests of generated leaf code against the pinned interpreter."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'local/upstream/snesrecomp'
sys.path.insert(0, str(ROOT / 'tools'))
from generator_patches import prepare

# Synthetic instruction fixtures, also verified against the user's ROM
# when available. Nothing is copied into a prepared game image.
INDEXED_CODE = bytes.fromhex('bc e5 0d b9 28 f8 85 00 ac d9 13 c0 0a d0 07 ac e8 1d c0 01 d0 11 ad d6 0d 4a 4a a8 b9 11 1f a8 b9 75 f8 25 00 f0 02 a9 01 60')
CODE = bytes.fromhex('a7 8a a6 8a e8 d0 05 a2 00 80 e6 8c 86 8a 60')


@unittest.skipUnless(shutil.which('cc') and (ENGINE / 'recompiler/v2/emit_function.py').is_file(),
                     'requires the pinned engine and a C compiler')
class AotBusTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='aot-bus-')
        cls.path = Path(cls.directory.name)
        cls.generator = prepare('demo-1-1')
        cls.include = ENGINE / 'runner/src'
        source = (cls.include / 'cpu_state.c').read_text()
        parts = ['#include "cpu_state.h"\n#include <stdio.h>\n#include <stdlib.h>\n']
        for name in ('cpu_region_speed', 'cpu_read8_paced', 'cpu_read16_paced',
                     'cpu_write8_paced', 'cpu_write16_paced'):
            start = re.search(r'^(?:uint\w*|void)\s+' + name + r'\(', source, re.M).start()
            brace = source.index('{', start)
            end, depth = brace + 1, 1
            while depth:
                depth += (source[end] == '{') - (source[end] == '}')
                end += 1
            parts.append(source[start:end] + '\n')
        (cls.path / 'paced.c').write_text(''.join(parts))
        rom = ROOT / 'local/roms/demo-1-1.sfc'
        if rom.is_file():
            assert rom.read_bytes()[0x3983:0x3983+len(CODE)] == CODE

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def emit(self, generator, code=CODE, indexed=False):
        bank, pc, m, x = (4, 0xf87c, 1, 1) if indexed else (0, 0xb983, 1, 0)
        offset = bank * 32768 + (pc & 0x7fff)
        script = ('from snes65816 import set_rom_image_size\n'
                  'from v2.emit_function import emit_function\n'
                  f'rom=bytearray(0x28000);rom[{offset}:{offset}+{len(code)}]={code!r}\n'
                  'set_rom_image_size(len(rom))\n'
                  'print(\'#include "cpu_state.h"\\n#include "common_cpu_infra.h"\\n'
                  f'#include "cpu_trace.h"\\n\'+emit_function(bytes(rom),{bank},{pc},{m},{x},func_name="Probe"))\n')
        env = os.environ.copy()
        env['PYTHONPATH'] = str(generator / 'recompiler')
        return subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env,
                              capture_output=True, text=True)

    def build_run(self, generator, indexed=False):
        result = self.emit(generator, INDEXED_CODE if indexed else CODE, indexed)
        self.assertEqual(result.returncode, 0, result.stderr)
        generated = self.path / 'generated.c'
        generated.write_text(result.stdout)
        binary = self.path / 'probe'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I' + str(self.include),
                   '-I' + str(self.include / 'snes'),
                   ROOT / ('tests/aot_indexed_timing_test.c' if indexed else 'tests/aot_bus_timing_test.c'), generated,
                   self.path / 'paced.c', ROOT / 'recomp/aot_timing.c',
                   self.include / 'snes/interp816.c', '-o', binary]
        build = subprocess.run([str(x) for x in command], capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        return subprocess.run([str(binary)], capture_output=True, text=True)

    def test_register_memory_clock_and_deadline_equivalence(self):
        result = self.build_run(self.generator)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_old_generator_reproduces_ten_clock_error(self):
        result = self.build_run(ENGINE)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('clock mismatch: AOT=200 interpreter=190', result.stderr)

    def test_unmodeled_instruction_is_rejected(self):
        result = self.emit(self.generator, CODE[:4] + b'\xea' + CODE[5:])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires a supported native M1 leaf', result.stderr)

    def test_indexed_reads_branches_and_deadlines(self):
        rom = ROOT / 'local/roms/demo-1-1.sfc'
        if rom.is_file():
            self.assertEqual(rom.read_bytes()[0x2787c:0x2787c+len(INDEXED_CODE)], INDEXED_CODE)
        result = self.build_run(self.generator, indexed=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
