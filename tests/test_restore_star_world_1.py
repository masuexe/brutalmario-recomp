"""Bounded graphics decoding and immutable restoration-output safeguards."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from restore_star_world_1 import lorom, lz2, write_verified


class RestorationSafetyTests(unittest.TestCase):
    def test_overflow_is_rejected_before_a_write_outside_the_graphics_buffer(self):
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            lz2(bytes.fromhex('e7ff00ff'), 0x008000, limit=100)

    def test_invalid_backreference_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'backreference'):
            lz2(bytes.fromhex('800100ff'), 0x008000)

    def test_stream_crosses_a_lorom_bank_without_consumption_gaps(self):
        rom = bytearray(0x8002)
        rom[0x7ffe:] = bytes.fromhex('010102ff')
        decoded, source = lz2(rom, 0x00fffe)
        self.assertEqual(decoded, b'\x01\x02')
        self.assertEqual(source, bytes.fromhex('010102ff'))

    def test_rom_mirrors_are_distinct_from_wram_banks(self):
        self.assertEqual(lorom(0xff8000), 0x3f8000)
        with self.assertRaises(ValueError):
            lorom(0x7f8000)

    def test_existing_conflicting_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rom.sfc'
            write_verified(path, b'original')
            write_verified(path, b'original')
            with self.assertRaisesRegex(ValueError, 'refusing'):
                write_verified(path, b'different')
            self.assertEqual(path.read_bytes(), b'original')
