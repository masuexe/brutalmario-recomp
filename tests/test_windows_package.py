#!/usr/bin/env python3
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))


class WindowsPackageTests(unittest.TestCase):
    def test_package_uses_r14_windows_binary(self):
        import package_windows_product as package
        self.assertEqual(package.TARGET, 'demo11-native-product-r14')
        self.assertEqual(package.WIN_BINARY,
                         'BrutalMarioDemo11NativeProductR14SNESRecomp.exe')

    def test_package_rejects_stale_binary(self):
        source = (ROOT / 'tools/package_windows_product.py').read_text()
        self.assertIn("PRACTICE CHEAT CONSOLE", source)
        self.assertIn('stale', source)


if __name__ == '__main__':
    unittest.main()
