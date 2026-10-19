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
SPRITE_Y_CODE = bytes.fromhex('5a 20 a7 f1 7a a2 19 a5 00 18 7d dd f0 85 0e a5 01 7d f5 f0 d0 39 a5 02 18 7d 0d f1 85 0f a5 03 69 00 d0 2b a5 0e c9 f0 b0 25 99 00 03 a5 0f 99 01 03 bd c5 f0 99 02 03 bd 25 f1 09 30 99 03 03 5a 98 4a 4a a8 a9 02 99 60 04 7a c8 c8 c8 c8 ca 10 b5 ae de 0d 60')
SPRITE_CODE = bytes.fromhex('20 a7 f1 a0 00 a2 1f a5 00 18 7d ef ef 85 0e a5 01 7d 0f f0 d0 39 a5 02 18 7d 2f f0 85 0f a5 03 69 00 d0 2b a5 0e c9 f0 b0 25 99 00 03 a5 0f 99 01 03 bd cf ef 99 02 03 bd 4f f0 09 30 99 03 03 5a 98 4a 4a a8 a9 02 99 60 04 7a c8 c8 c8 c8 ca 10 b5 ae de 0d 60')
CALLER15_CODE = bytes.fromhex('8a 18 69 10 aa a0 02 20 32 a0 ae de 0d a0 00 bd 65 0e eb bd 35 0e c2 20 38 f9 1a 00 99 00 00 e2 20 60')
CALLER_CODE = bytes.fromhex('8a 18 69 10 aa a0 02 20 c2 f1 ae de 0d a5 02 38 fd 55 0e 85 02 b0 02 c6 03 a0 00 bd 65 0e eb bd 35 0e c2 20 38 f9 1a 00 99 00 00 e2 20 60')
COORDINATE_CODE = bytes.fromhex('bd 65 0e eb bd 35 0e c2 20 38 f9 1a 00 99 00 00 e2 20 60')
PALETTE_LOOPS = {
    'palette80': (0x16, 0x9585, bytes.fromhex('a2 00 bd 94 94 f0 12 8d 21 21 bd 35 95 8d 22 21 bd e5 94 8d 22 21 e8 80 e9 60'), 0x9494, 0x9585, 80),
    'palette30': (0x13, 0xefb2, bytes.fromhex('a2 00 bd 57 ef f0 12 8d 21 21 bd 94 ef 8d 22 21 bd 76 ef 8d 22 21 e8 80 e9 ae de 0d 60'), 0xef57, 0xefb2, 30),
}

BUFFER_FLAGS_CODE = bytes.fromhex('c2 30 a6 08 bf 00 d0 7e 29 ff 00 e2 30 85 08 a2 09 bf 78 90 04 c9 ff f0 0c c5 08 f0 32 da fa e2 20 ca 10 ed 60 c2 20 da ad b3 0d 29 ff 00 aa bd 11 1f 29 ff 00 d0 e7 ae d6 0d bd 19 1f cf 82 90 04 d0 db bd 17 1f cf 84 90 04 d0 d2 fa e2 20 bd 06 a1 05 07 85 07 60')

BUFFER_READ_CODE = bytes.fromhex('a5 04 c9 00 08 b0 18 c2 30 da a6 04 bf 00 c8 7e fa 29 ff 00 f0 09 c9 87 00 b0 04 e2 30 18 60 e2 30 38 60')

BUFFER_INDEX_CODE = bytes.fromhex('a5 00 29 0f 00 85 04 a5 00 29 10 00 0a 0a 0a 0a 65 04 85 04 a5 02 0a 0a 0a 0a 29 ff 00 65 04 85 04 a5 02 29 10 00 f0 08 a5 04 18 69 00 02 85 04 bd 11 1f 29 ff 00 f0 08 a5 04 18 69 00 04 85 04 60')

HELPER_FIXTURES = {
    'restore_pointer': (0x0d, 0xa6b1, bytes.fromhex('a5 6b 85 04 a5 6c 85 05 60'), 0x6c),
    'advance_row': (0x0d, 0xa97d, bytes.fromhex('a5 57 18 69 10 85 57 a8 90 0a a5 6c 69 00 85 6c 85 6f 85 05 60'), 0x6f),
    'frame_phase': (0x15, 0xa055, bytes.fromhex('a5 13 18 7d 45 a0 60'), 0x13),
}

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

    def emit(self, generator, code=CODE, indexed=False, fixture=None, fixture_code=None):
        bank, pc, m, x = (4, 0xf87c, 1, 1) if indexed else (0, 0xb983, 1, 0)
        if fixture:
            if fixture == 'buffer_flags':
                bank, pc, code = 0x15, 0xa110, BUFFER_FLAGS_CODE
            elif fixture == 'buffer_read':
                bank, pc, code = 0x15, 0xa0e3, BUFFER_READ_CODE
            elif fixture == 'buffer_index':
                bank, pc, code = 0x15, 0xa2fd, BUFFER_INDEX_CODE
            elif fixture == 'caller15':
                bank, pc, code = 0x15, 0xa023, CALLER15_CODE
            elif fixture == 'coordinate15':
                bank, pc, code = 0x15, 0xa032, COORDINATE_CODE
            elif fixture == 'sprite_y':
                bank, pc, code = 0x13, 0xf13d, SPRITE_Y_CODE
            elif fixture == 'sprite':
                bank, pc, code = 0x13, 0xf06f, SPRITE_CODE
            elif fixture == 'caller':
                bank, pc, code = 0x13, 0xf1a7, CALLER_CODE
            elif fixture == 'coordinate':
                bank, pc, code = 0x13, 0xf1c2, COORDINATE_CODE
            elif fixture == 'palette':
                bank, pc, code = 0x0d, 0xa6ba, PALETTE_CODE
            elif fixture in HELPER_FIXTURES:
                bank, pc, code = HELPER_FIXTURES[fixture][:3]
            elif fixture in PALETTE_LOOPS:
                bank, pc, code = PALETTE_LOOPS[fixture][:3]
            else:
                bank, pc, code = WRAM_FIXTURES[fixture]
            m, x = (0 if fixture in ('buffer_index', 'buffer_read') else 1), 1
        if fixture_code is not None:
            code = fixture_code
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
        self.assertIn('requires a supported native width/opcode combination', result.stderr)

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

    def test_sprite_loop_nested_calls_stack_and_deadlines(self):
        self.sprite_probe(False)

    def test_sprite_saved_y_loop_and_wrapping_destinations(self):
        self.sprite_probe(True)

    def sprite_probe(self, saved_y):
        rom_path = ROOT / 'local/roms/demo-1-1.sfc'
        if not rom_path.is_file():
            self.skipTest('requires the verified local ROM for sprite tables')
        rom = rom_path.read_bytes()
        offset = 0x13 * 32768
        pc = 0xf13d if saved_y else 0xf06f
        table_base = 0xf0c5 if saved_y else 0xefcf
        code = rom[offset+(pc&32767):offset+0x71d5]
        expected = SPRITE_Y_CODE if saved_y else SPRITE_CODE
        self.assertEqual(code[:len(expected)], expected)
        table = rom[offset+(table_base&32767):offset+(pc&32767)]
        (self.path / 'sprite_fixture.h').write_text(
            f'#define CODE_PC {pc}\n#define TABLE_BASE {table_base}\n'
            f'#define LOOP_COUNT {26 if saved_y else 32}\n#define SAVED_Y {int(saved_y)}\n'
            'static const uint8_t code[] = {' + ','.join(map(str, code)) + '};\n'
            'static const uint8_t table_bytes[] = {' + ','.join(map(str, table)) + '};\n')
        sources = []
        declarations = ''.join(f'RecompReturn bank_13_{pc}_M{m}X{x}(CpuState *);\n'
                               for pc in ('F1A7','F1C2') for m in range(2) for x in range(2))
        for fixture, name in (('sprite_y' if saved_y else 'sprite','Sprite'), ('caller','Caller'), ('coordinate','Callee')):
            result = self.emit(self.generator, fixture=fixture)
            self.assertEqual(result.returncode, 0, result.stderr)
            source = self.path / ('sprite_' + name + '.c')
            source.write_text('#include "cpu_state.h"\n' + declarations +
                              result.stdout.replace('Probe_', name + '_'))
            sources.append(source)
        binary = self.path / 'sprite'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I' + str(self.include),
                   '-I' + str(self.include / 'snes'), '-I' + str(self.path),
                   ROOT / 'tests/aot_sprite_timing_test.c', *sources,
                   self.path / 'paced.c', ROOT / 'recomp/aot_timing.c',
                   self.include / 'snes/interp816.c', '-o', binary]
        build = subprocess.run(list(map(str, command)), capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout, end='')

    def test_buffer_flags_lookup_predicate_masks_and_deadlines(self):
        self.buffer_flags_probe(None)

    def test_buffer_flags_long_compare_hardware_guard(self):
        self.buffer_flags_probe(0x001fff)

    def test_buffer_flags_long_compare_bank_endpoint_guard(self):
        self.buffer_flags_probe(0x7effff)

    def test_buffer_flags_long_compare_last_safe_word(self):
        self.buffer_flags_probe(0x7efffe)

    def buffer_flags_probe(self, compare_address):
        rom_path = ROOT / 'local/roms/demo-1-1.sfc'
        if not rom_path.is_file():
            self.skipTest('requires the verified local ROM for lookup tables')
        rom = rom_path.read_bytes(); offset = 0x15*32768+0x2110
        self.assertEqual(rom[offset:offset+len(BUFFER_FLAGS_CODE)], BUFFER_FLAGS_CODE)
        code = BUFFER_FLAGS_CODE
        if compare_address is not None:
            code = code.replace(bytes.fromhex('cf 82 90 04'),
                                bytes([0xcf])+compare_address.to_bytes(3, 'little'))
        (self.path/'buffer_flags_fixture.h').write_text(
            '#define CODE_BANK 0x15\n#define CODE_PC 0xa110\n' +
            (f'#define RELOCATED_FIXTURE 1\n#define COMPARE_GUARD {0 if compare_address==0x7efffe else 0xa14d}\n' if compare_address is not None else '') +
            'static const uint8_t code[] = {' + ','.join(map(str, code)) + '};\n' +
            'static const uint8_t table_bytes[] = {' + ','.join(map(str, rom[0x21078:0x21086])) + '};\n' +
            'static const uint8_t mask_bytes[] = {' + ','.join(map(str, rom[0xaa106:0xaa110])) + '};\n')
        result = self.emit(self.generator, fixture='buffer_flags', fixture_code=code)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = self.path/'buffer_flags.c'; source.write_text(result.stdout)
        binary = self.path/'buffer_flags'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I'+str(self.include),
                   '-I'+str(self.include/'snes'), '-I'+str(self.path),
                   ROOT/'tests/aot_buffer_flags_timing_test.c', source,
                   self.path/'paced.c', ROOT/'recomp/aot_timing.c',
                   self.include/'snes/interp816.c', '-o', binary]
        build = subprocess.run(list(map(str, command)), capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout+build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        print(result.stdout, end='')

    def test_buffer_read_width_stack_predicate_and_deadlines(self):
        self.buffer_read_probe('original', 0x7ec800)

    def test_buffer_read_hardware_boundary_yields_with_saved_x(self):
        self.buffer_read_probe('hardware', 0x001ffe)

    def test_buffer_read_bank_endpoint_yields_with_saved_x(self):
        self.buffer_read_probe('bank_end', 0x7efffe)

    def buffer_read_probe(self, variant, table_base):
        rom_path = ROOT / 'local/roms/demo-1-1.sfc'
        if rom_path.is_file():
            offset = 0x15*32768+0x20e3
            self.assertEqual(rom_path.read_bytes()[offset:offset+len(BUFFER_READ_CODE)], BUFFER_READ_CODE)
        code = BUFFER_READ_CODE.replace(bytes.fromhex('bf 00 c8 7e'),
                                        bytes([0xbf])+table_base.to_bytes(3, 'little'))
        (self.path/'buffer_read_fixture.h').write_text(
            '#define CODE_BANK 0x15\n#define CODE_PC 0xa0e3\n' +
            f'#define TABLE_BASE {table_base}\n' +
            ('#define RELOCATED_FIXTURE 1\n' if variant != 'original' else '') +
            'static const uint8_t code[] = {' + ','.join(map(str, code)) + '};\n')
        result = self.emit(self.generator, fixture='buffer_read', fixture_code=code)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = self.path/'buffer_read.c'; source.write_text(result.stdout)
        binary = self.path/'buffer_read'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I'+str(self.include),
                   '-I'+str(self.include/'snes'), '-I'+str(self.path),
                   ROOT/'tests/aot_buffer_read_timing_test.c', source,
                   self.path/'paced.c', ROOT/'recomp/aot_timing.c',
                   self.include/'snes/interp816.c', '-o', binary]
        build = subprocess.run(list(map(str, command)), capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout+build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        print(result.stdout, end='')

    def test_buffer_index_words_flags_and_deadlines(self):
        self.buffer_index_probe(False)

    def test_buffer_index_bank_endpoint_yields_before_word_read(self):
        self.buffer_index_probe(True)

    def buffer_index_probe(self, bank_wrap):
        rom_path = ROOT / 'local/roms/demo-1-1.sfc'
        if rom_path.is_file():
            offset = 0x15*32768+0x22fd
            self.assertEqual(rom_path.read_bytes()[offset:offset+len(BUFFER_INDEX_CODE)], BUFFER_INDEX_CODE)
        code = BUFFER_INDEX_CODE
        if bank_wrap:
            code = code.replace(bytes.fromhex('bd 11 1f'), bytes.fromhex('bd ff ff'))
        (self.path/'buffer_index_fixture.h').write_text(
            '#define CODE_BANK 0x15\n#define CODE_PC 0xa2fd\n'
            f'#define TABLE_OPERAND {0xffff if bank_wrap else 0x1f11}\n' +
            ('#define BANK_WRAP_FIXTURE 1\n' if bank_wrap else '') +
            'static const uint8_t code[] = {' + ','.join(map(str, code)) + '};\n')
        result = self.emit(self.generator, fixture='buffer_index', fixture_code=code)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = self.path/'buffer_index.c'; source.write_text(result.stdout)
        binary = self.path/'buffer_index'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I'+str(self.include),
                   '-I'+str(self.include/'snes'), '-I'+str(self.path),
                   ROOT/'tests/aot_buffer_index_timing_test.c', source,
                   self.path/'paced.c', ROOT/'recomp/aot_timing.c',
                   self.include/'snes/interp816.c', '-o', binary]
        build = subprocess.run(list(map(str, command)), capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout+build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        print(result.stdout, end='')

    def test_restore_pointer_bytes_flags_and_deadlines(self):
        self.helper_probe('restore_pointer')

    def test_advance_row_carry_decimal_flags_and_deadlines(self):
        self.helper_probe('advance_row')

    def test_frame_phase_indexed_adc_flags_and_deadlines(self):
        self.helper_probe('frame_phase')

    def helper_probe(self, fixture):
        bank, pc, code, max_dp = HELPER_FIXTURES[fixture]
        rom_path = ROOT / 'local/roms/demo-1-1.sfc'
        table = bytes((i*17+3)&255 for i in range(256))
        if rom_path.is_file():
            rom = rom_path.read_bytes()
            offset = bank*32768+(pc&32767)
            self.assertEqual(rom[offset:offset+len(code)], code)
            table = rom[0x15*32768+0x2045:0x15*32768+0x2145]
        elif fixture == 'frame_phase':
            self.skipTest('requires the verified local ROM for the indexed table span')
        header = (f'#define CODE_BANK {bank}\n#define CODE_PC {pc}\n'
                  f'#define LAST_DP {0x1fff-max_dp}\n'
                  f'#define HELPER_{fixture.upper()} 1\n'
                  'static const uint8_t code[] = {' + ','.join(map(str, code)) + '};\n'
                  'static const uint8_t table_bytes[] = {' + ','.join(map(str, table)) + '};\n')
        (self.path/'helper_fixture.h').write_text(header)
        result = self.emit(self.generator, fixture=fixture)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = self.path/'helper.c'; source.write_text(result.stdout)
        binary = self.path/'helper'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I'+str(self.include),
                   '-I'+str(self.include/'snes'), '-I'+str(self.path),
                   ROOT/'tests/aot_helpers_timing_test.c', source, self.path/'paced.c',
                   ROOT/'recomp/aot_timing.c', self.include/'snes/interp816.c', '-o', binary]
        build = subprocess.run(list(map(str, command)), capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout+build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        print(result.stdout, end='')

    def test_bank15_coordinate_caller_and_deadline_continuations(self):
        self.caller_probe(bank15=True)

    def test_nested_coordinate_caller_and_deadline_continuations(self):
        self.caller_probe()

    def caller_probe(self, bank15=False):
        rom = ROOT / 'local/roms/demo-1-1.sfc'
        if rom.is_file():
            offset = 0x15 * 32768 + 0x2023 if bank15 else 0x13 * 32768 + 0x71a7
            code = CALLER15_CODE if bank15 else CALLER_CODE
            self.assertEqual(rom.read_bytes()[offset:offset+len(code)], code)
        sources = []
        target = 'bank_15_A032' if bank15 else 'bank_13_F1C2'
        declarations = ''.join(f'RecompReturn {target}_M{m}X{x}(CpuState *);\n'
                               for m in range(2) for x in range(2))
        for fixture, name in (('caller15' if bank15 else 'caller', 'Caller'),
                              ('coordinate15' if bank15 else 'coordinate', 'Callee')):
            result = self.emit(self.generator, fixture=fixture)
            self.assertEqual(result.returncode, 0, result.stderr)
            source = self.path / (name + '.c')
            source.write_text('#include "cpu_state.h"\n' + declarations +
                              result.stdout.replace('Probe_', name + '_'))
            sources.append(source)
        binary = self.path / 'caller'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I' + str(self.include),
                   '-I' + str(self.include / 'snes'),
                   ROOT / 'tests/aot_caller_timing_test.c', *sources,
                   self.path / 'paced.c', ROOT / 'recomp/aot_timing.c',
                   self.include / 'snes/interp816.c', '-o', binary]
        if bank15:
            command.insert(1, '-DBANK15_FIXTURE=1')
        build = subprocess.run(list(map(str, command)), capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout, end='')

    def test_unqualified_nested_callee_is_rejected(self):
        code = bytearray(CALLER_CODE)
        code[8:10] = bytes.fromhex('00 f0')
        result = self.emit(self.generator, fixture='caller', fixture_code=bytes(code))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('require a qualified callee', result.stderr)

    def test_coordinate_word_arithmetic_widths_flags_and_deadlines(self):
        rom = ROOT / 'local/roms/demo-1-1.sfc'
        if rom.is_file():
            offset = 0x13 * 32768 + (0xf1c2 & 32767)
            self.assertEqual(rom.read_bytes()[offset:offset+len(COORDINATE_CODE)], COORDINATE_CODE)
        self.coordinate_probe()

    def test_bank15_coordinate_word_arithmetic_widths_flags_and_deadlines(self):
        rom = ROOT / 'local/roms/demo-1-1.sfc'
        if rom.is_file():
            offset = 0x15 * 32768 + 0x2032
            self.assertEqual(rom.read_bytes()[offset:offset+len(COORDINATE_CODE)], COORDINATE_CODE)
        self.coordinate_probe(bank15=True)

    def test_bank15_coordinate_word_endpoints_and_unsafe_contexts_yield(self):
        self.coordinate_guards(bank15=True)

    def test_coordinate_byte_arithmetic_flags_and_deadlines(self):
        self.coordinate_probe(narrow=True)

    def test_coordinate_word_endpoints_and_unsafe_contexts_yield(self):
        self.coordinate_guards()

    def coordinate_guards(self, bank15=False):
        cases = (
            ('read-bank-end', 11, 0xffff, 0xf1cc, (0x7e, 0x7f), 0),
            ('store-bank-end', 14, 0xffff, 0xf1cf, (0x7e, 0x7f), 0),
            ('read-hardware', 11, 0x1fff, 0xf1cc, (0, 0x80), 0),
            ('store-hardware', 14, 0x1f00, 0xf1cf, (0, 0x80), 0xff),
            ('store-last-safe', 14, 0x1ffe, 0, (0, 0x80, 0x7e, 0x7f), 0),
            ('unsafe-data-bank', 14, 0, 0xf1c2, (0x40, 0xc0), 0),
        )
        for name, *guard in cases:
            with self.subTest(fixture=name):
                self.coordinate_probe(guard=guard, bank15=bank15)

    def coordinate_probe(self, narrow=False, guard=None, bank15=False):
        code = bytearray(COORDINATE_CODE)
        if narrow:
            code[7:9] = code[16:18] = b'\x38\x38'
        if guard:
            at, address, pc, dbs, y = guard
            if bank15 and pc:
                pc += 0xa032 - 0xf1c2
            code[at:at+2] = address.to_bytes(2, 'little')
            (self.path / 'coordinate_guard_fixture.h').write_text(
                f'#define EXPECTED_GUARD_PC {pc}\n#define GUARD_Y {y}\n'
                'static const unsigned guard_dbs[] = {' + ','.join(map(str, dbs)) + '};\n'
                'static uint8_t code[] = {' + ','.join(map(str, code)) + '};\n')
        result = self.emit(self.generator, fixture='coordinate15' if bank15 else 'coordinate', fixture_code=bytes(code))
        self.assertEqual(result.returncode, 0, result.stderr)
        generated = self.path / 'coordinate.c'
        generated.write_text(result.stdout)
        binary = self.path / 'coordinate'
        command = ['cc', '-std=c11', '-O2', '-DSNESRECOMP_TRACE=0',
                   '-DSNESRECOMP_REVERSE_DEBUG=0', '-I' + str(self.include),
                   '-I' + str(self.include / 'snes'), '-I' + str(self.path),
                   ROOT / 'tests/aot_coordinate_timing_test.c', generated,
                   self.path / 'paced.c', ROOT / 'recomp/aot_timing.c',
                   self.include / 'snes/interp816.c', '-o', binary]
        if bank15:
            command.insert(1, '-DBANK15_FIXTURE=1')
        if narrow:
            command.insert(1, '-DNARROW_FIXTURE=1')
        if guard:
            command.insert(1, '-DCOORDINATE_OVERRIDE=1')
        build = subprocess.run([str(x) for x in command], capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout, end='')

    def test_palette_write_events_match_with_legacy_counterexample(self):
        """Total-clock equality must not hide different hardware event times."""
        result = self.palette_probe()
        self.assertIn('412 exact-event cases', result.stdout)
        print(result.stdout, end='')

    def test_real_palette_loops_and_complete_deadline_sweeps(self):
        rom_path = ROOT / 'local/roms/demo-1-1.sfc'
        if not rom_path.is_file():
            self.skipTest('requires the verified local ROM for the two palette tables')
        rom = rom_path.read_bytes()
        for fixture, (bank, pc, code, base, end, count) in PALETTE_LOOPS.items():
            with self.subTest(fixture=fixture):
                offset = bank * 32768 + (pc & 32767)
                self.assertEqual(rom[offset:offset+len(code)], code)
                table = rom[bank*32768+(base&32767):bank*32768+(end&32767)]
                self.assertEqual(table.index(0), count)
                header = (f'#define CODE_BANK {bank}\n#define CODE_PC {pc}\n'
                          f'#define TABLE_BASE {base}\n#define INDEX_BASE {base}\n'
                          f'#define COLOR_COUNT {count}\n'
                          'static const uint8_t code[] = {' + ','.join(map(str, code)) + '};\n'
                          'static const uint8_t table_bytes[] = {' + ','.join(map(str, table)) + '};\n')
                (self.path / 'palette_loop_fixture.h').write_text(header)
                result = self.palette_probe(fixture, loop=True)
                self.assertIn(f'{count} colors;', result.stdout)
                print(result.stdout, end='')
                if fixture == 'palette80':
                    # Synthetic relocation of the verified tables crosses an
                    # absolute-indexed read page without changing the ROM.
                    relocated = bytearray(code)
                    for at in (3, 11, 17):
                        address = int.from_bytes(code[at:at+2], 'little')
                        relocated[at:at+2] = (address-base+0xa0f0).to_bytes(2, 'little')
                    relocated_header = header.replace(f'#define TABLE_BASE {base}', '#define TABLE_BASE 41200').replace(
                        f'#define INDEX_BASE {base}', '#define INDEX_BASE 41200').replace(
                        'static const uint8_t code[] = {' + ','.join(map(str, code)),
                        'static const uint8_t code[] = {' + ','.join(map(str, relocated)))
                    (self.path / 'palette_loop_fixture.h').write_text(relocated_header)
                    result = self.palette_probe(fixture, loop=True, code_override=bytes(relocated))
                    print('Relocated page-crossing fixture: ' + result.stdout, end='')

    def palette_probe(self, fixture='palette', loop=False, code_override=None):
        result = self.emit(self.generator, fixture=fixture, fixture_code=code_override)
        self.assertEqual(result.returncode, 0, result.stderr)
        generated = self.path / 'palette.c'
        generated.write_text(result.stdout)
        legacy = self.path / 'legacy-palette.c'
        legacy.write_text(result.stdout.replace('Probe_M1X1', 'LegacyProbe_M1X1').replace(
            'M1AotPaletteWrite8', 'LegacyPaletteWrite8').replace(
            'M1AotPaletteWriteSupported', 'M1AotBusWriteSupported'))
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
                   ROOT / ('tests/aot_palette_loop_test.c' if loop else 'tests/aot_mmio_event_test.c'),
                   generated, legacy,
                   self.path / 'paced.c', wrapper,
                   self.include / 'snes/interp816.c', '-o', binary]
        build = subprocess.run([str(x) for x in command], capture_output=True, text=True)
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def check_wram_fixture(self, fixture):
        bank, pc, code = WRAM_FIXTURES[fixture]
        rom = ROOT / 'local/roms/demo-1-1.sfc'
        if rom.is_file():
            offset=bank*32768+(pc&32767)
            self.assertEqual(rom.read_bytes()[offset:offset+len(code)],code)
        result = self.build_run(self.generator, fixture=fixture)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
