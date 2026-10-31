"""Exercise selector admission and actual 65816 register/flag semantics."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from prepare_mazo_primary_entry import RECIPE, build, program
from restore_star_world_1 import lorom


class PrimaryEntryTests(unittest.TestCase):
    def test_secondary_loader_keeps_its_shared_branch_entry(self):
        _, _, rom, _ = build()
        self.assertEqual(rom[lorom(0x05d83b):lorom(0x05d83e)], bytes.fromhex('4cb7d8'))
        self.assertEqual(rom[lorom(0x05d8b7):lorom(0x05d8b9)], bytes.fromhex('c230'))

    def test_scope_and_hook_admission(self):
        r = json.loads(RECIPE.read_text())
        build(r)
        for key, value in [('scope', dict(r['scope'], translevel=49)),
                           ('address', 'D48000'),
                           ('patch', dict(r['patch'], address='05D89F'))]:
            bad = copy.deepcopy(r)
            bad[key] = value
            with self.assertRaises(ValueError):
                build(bad)

    @unittest.skipUnless(shutil.which('cc'), 'requires C compiler')
    def test_original_cpu_semantics_and_scoped_redirect(self):
        engine = ROOT / 'local/upstream/snesrecomp/runner/src'
        with tempfile.TemporaryDirectory(prefix='bm-primary-entry-') as folder:
            p = Path(folder)
            (p / 'code.bin').write_bytes(program())
            subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                            '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
                            '-I' + str(engine), str(ROOT / 'tests/mazo_primary_entry_test.c'),
                            str(engine / 'snes/interp816.c'), '-o', str(p / 'test')], check=True)
            result = subprocess.run([str(p / 'test'), str(p / 'code.bin')],
                                    text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('28672 selector/flags/scope cases', result.stdout)


if __name__ == '__main__':
    unittest.main()
