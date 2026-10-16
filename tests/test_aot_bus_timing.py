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

# Synthetic eight-instruction fixture, also verified against the user's ROM
# when available. Nothing is copied into a prepared game image.
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

    def emit(self, generator, code=CODE):
        script = ('from snes65816 import set_rom_image_size\n'
                  'from v2.emit_function import emit_function\n'
                  f'rom=bytearray(32768);rom[0x3983:0x3983+{len(code)}]={code!r}\n'
                  'set_rom_image_size(len(rom))\n'
                  'print(\'#include "cpu_state.h"\\n#include "common_cpu_infra.h"\\n'
                  '#include "cpu_trace.h"\\n\'+emit_function(bytes(rom),0,0xb983,1,0,func_name="Probe"))\n')
        env = os.environ.copy()
        env['PYTHONPATH'] = str(generator / 'recompiler')
        return subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env,
                              capture_output=True, text=True)

    def build_run(self, generator):
        result = self.emit(generator)
        self.assertEqual(result.returncode, 0, result.stderr)
        generated = self.path / 'generated.c'
        generated.write_text(result.stdout)
        binary = self.path / 'probe'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I' + str(self.include),
                   '-I' + str(self.include / 'snes'),
                   ROOT / 'tests/aot_bus_timing_test.c', generated,
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
        self.assertIn('requires a supported native M1/X0 leaf', result.stderr)
