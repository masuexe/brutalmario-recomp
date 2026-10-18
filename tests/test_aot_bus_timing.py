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
PALETTE_CODE = bytes.fromhex('a9 23 8d 21 21 a9 34 8d 22 21 a9 12 8d 22 21 60')

WRAM_FIXTURES = {
    'clear': (0x16, 0x9f2b, b'\xad\x11\x1f\xc9\x06\xf0\x0b\xa2\x07\xa9\x00\x9f\xa0\xff\x7f\xca\x10\xf7`'),
    'copy': (0x0d, 0xa6ba, b'\xa5\x04\x85k\x85n\xa5\x05\x85l\x85o\xad(\x19\x8d\xa1\x1b`'),
    'copy_mmio': (0x0d, 0xa6ba, b'\xa5\x04\x85k\x85n\xa5\x05\x85l\x85o\xad(\x19\x8d\x00!`'),
}


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

    def emit(self, generator, code=CODE, indexed=False, fixture=None):
        bank, pc, m, x = (4, 0xf87c, 1, 1) if indexed else (0, 0xb983, 1, 0)
        if fixture:
            bank, pc, code = ((0x0d, 0xa6ba, PALETTE_CODE) if fixture == 'palette'
                              else WRAM_FIXTURES[fixture])
            m, x = 1, 1
        offset = bank * 32768 + (pc & 0x7fff)
        script = ('from snes65816 import set_rom_image_size\n'
                  'from v2.emit_function import emit_function\n'
                  f'rom=bytearray(0x100000);rom[{offset}:{offset}+{len(code)}]={code!r}\n'
                  'set_rom_image_size(len(rom))\n'
                  'print(\'#include "cpu_state.h"\\n#include "common_cpu_infra.h"\\n'
                  f'#include "cpu_trace.h"\\n\'+emit_function(bytes(rom),{bank},{pc},{m},{x},func_name="Probe"))\n')
        env = os.environ.copy()
        env['PYTHONPATH'] = str(generator / 'recompiler')
        return subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env,
                              capture_output=True, text=True)

    def build_run(self, generator, indexed=False, fixture=None):
        result = self.emit(generator, INDEXED_CODE if indexed else CODE, indexed, fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        generated = self.path / 'generated.c'
        generated.write_text(result.stdout)
        binary = self.path / 'probe'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I' + str(self.include),
                   '-I' + str(self.include / 'snes'),
                   ROOT / ('tests/aot_wram_timing_test.c' if fixture else
                           'tests/aot_indexed_timing_test.c' if indexed else 'tests/aot_bus_timing_test.c'), generated,
                   self.path / 'paced.c', ROOT / 'recomp/aot_timing.c',
                   self.include / 'snes/interp816.c', '-o', binary]
        if fixture:
            command.insert(1, '-DCLEAR_FIXTURE=1' if fixture=='clear' else
                           '-DCOPY_MMIO_FIXTURE=1' if fixture=='copy_mmio' else '-DCOPY_FIXTURE=1')
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

    def test_long_indexed_wram_clear_and_deadlines(self):
        self.check_wram_fixture('clear')

    def test_direct_page_wram_copy_and_deadlines(self):
        self.check_wram_fixture('copy')

    def test_mmio_store_yields_before_effects(self):
        result = self.build_run(self.generator, fixture='copy_mmio')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_palette_write_events_block_mmio_promotion(self):
        """Total-clock equality must not hide different hardware event times."""
        result = self.emit(self.generator, fixture='palette')
        self.assertEqual(result.returncode, 0, result.stderr)
        generated = self.path / 'palette.c'
        generated.write_text(result.stdout)
        source = (self.include / 'snes/interp_bridge.c').read_text()
        bodies = []
        for name in ('bridge_region_speed', 'bridge_timing_bus', 'bridge_is_apu_port',
                     'bridge_apu_port_diag_enabled', 'bridge_bus_write'):
            start = re.search(r'^static\s+\w+\s+' + name + r'\(', source, re.M).start()
            brace = source.index('{', start)
            end, depth = brace + 1, 1
            while depth:
                depth += (source[end] == '{') - (source[end] == '}')
                end += 1
            bodies.append(source[start:end] + '\n')
        # Reuse the bridge's actual post-op clock accounting as well as its
        # callbacks. Leave cartridge/APU scheduling outside this PPU bus probe.
        start = source.index('            unsigned _internal = (unsigned)_cyc > s_interp_bus_cycles')
        end = source.index('            if (g_snes && g_snes->cart)', start)
        bodies.append('static void bridge_finish_opcode(CpuState *cpu, int _cyc) {\n' +
                      source[start:end] + '}\n')
        (self.path / 'bridge_write.inc').write_text(''.join(bodies))
        # Compile the unmodified production guard under a second name, then
        # bypass it only in this disposable probe's controlled PPU bus.
        wrapper = self.path / 'production_timing.c'
        wrapper.write_text('#define M1AotBusWriteSupported M1ProductionBusWriteSupported\n'
                           f'#include "{ROOT / "recomp/aot_timing.c"}"\n')
        binary = self.path / 'palette-events'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I' + str(self.include),
                   '-I' + str(self.include / 'snes'), '-I' + str(self.path),
                   ROOT / 'tests/aot_mmio_event_test.c', generated,
                   self.path / 'paced.c', wrapper,
                   self.include / 'snes/interp816.c', '-o', binary]
        build = subprocess.run([str(x) for x in command], capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('promotion blocked', result.stdout)
        print(result.stdout, end='')

    def check_wram_fixture(self, fixture):
        bank, pc, code = WRAM_FIXTURES[fixture]
        rom = ROOT / 'local/roms/demo-1-1.sfc'
        if rom.is_file():
            offset=bank*32768+(pc&32767)
            self.assertEqual(rom.read_bytes()[offset:offset+len(code)],code)
        result = self.build_run(self.generator, fixture=fixture)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
