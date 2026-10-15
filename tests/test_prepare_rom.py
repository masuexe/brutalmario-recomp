"""Synthetic preparation checks, with no copyrighted inputs."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from inventory import digest
from prepare_rom import prepare_bytes, write_new_or_verify


class PreparationTests(unittest.TestCase):
    def fixture(self):
        base = bytes(0x8000)
        ips = b'PATCH\x00\x81\xd7\x00\x01\x0cEOF'
        expected = bytearray(base)
        expected[0x7fd7] = 12
        pin = lambda b: {'size': len(b), 'sha256': digest(b)}
        manifest = {'base': pin(base), 'ips': pin(ips), 'output': pin(expected),
                    'copier_prefix_bytes': 512}
        return base, ips, manifest, bytes(expected)

    def test_alignment_and_input_validation(self):
        base, ips, manifest, expected = self.fixture()
        self.assertEqual(prepare_bytes(base, ips, manifest), expected)
        for wrong_base, wrong_ips in ((base + b'x', ips), (base, ips + b'x')):
            with self.assertRaisesRegex(ValueError, 'pinned input'):
                prepare_bytes(wrong_base, wrong_ips, manifest)

    def test_wrong_output_pin_rejected(self):
        base, ips, manifest, _ = self.fixture()
        manifest['output']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'target ROM'):
            prepare_bytes(base, ips, manifest)

    def test_no_clobber_and_idempotent_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'rom.sfc'
            self.assertEqual(write_new_or_verify(output, b'first'), 'created')
            self.assertEqual(write_new_or_verify(output, b'first'), 'verified_existing')
            with self.assertRaisesRegex(ValueError, 'refusing overwrite'):
                write_new_or_verify(output, b'second')
            self.assertEqual(output.read_bytes(), b'first')
            link = Path(directory) / 'link.sfc'
            link.symlink_to(output)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                write_new_or_verify(link, b'first')


if __name__ == '__main__':
    unittest.main()
