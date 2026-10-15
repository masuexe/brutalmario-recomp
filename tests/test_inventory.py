"""Synthetic parser and archive safety checks; no game files required."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from inventory import ips_info, zip_info, scan
from analyze_m0 import preview


class InventoryTests(unittest.TestCase):
    def test_literal_rle_and_final_size(self):
        data = b'PATCH\x00\x01\x00\x00\x02ab\x00\x02\x00\x00\x00\x00\x03zEOF\x00\x04\x00'
        info, records = ips_info(data)
        self.assertEqual([(o, b) for o, b, _ in records], [(256, b'ab'), (512, b'zzz')])
        self.assertEqual(info['max_end_exclusive'], 515)
        self.assertEqual(info['explicit_final_size'], 1024)

    def test_malformed_ips(self):
        for data in (b'', b'PATCHEO', b'PATCHEOFx',
                     b'PATCH\x00\x00\x01\x00\x03a',
                     b'PATCH\x00\x00\x01\x00\x00\x00\x00zEOF'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                ips_info(data)

    def test_expansion_budget(self):
        with patch('inventory.MAX_ARCHIVE', 2), self.assertRaises(ValueError):
            ips_info(b'PATCH\x00\x02\x00\x00\x00\x00\x03zEOF')

    def test_zip_paths_skipped_and_no_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'example.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('../escape', b'x')
                archive.writestr('C:\\escape', b'y')
                archive.writestr('ok.txt', b'hello')
            result = zip_info(path)
            self.assertEqual(sum(i['unsafe_path_or_symlink'] for i in result['members']), 2)
            self.assertIn('sha256', result['members'][2])
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_symlink_input_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'link').symlink_to('/etc/passwd')
            self.assertEqual(scan(root)['file_count'], 0)

    def test_virtual_headered_patch_keeps_source_immutable(self):
        base = bytes(0x8000)
        # A headered IPS writes to the standard LoROM size byte + 512.
        data = b'PATCH\x00\x81\xd7\x00\x01\x0cEOF'
        corrected = preview(base, data, 512)
        direct = preview(base, data, 0)
        self.assertEqual(corrected[0x7fd7], 12)
        self.assertEqual(direct[0x7fd7], 0)
        self.assertEqual(base, bytes(0x8000))


if __name__ == '__main__':
    unittest.main()
