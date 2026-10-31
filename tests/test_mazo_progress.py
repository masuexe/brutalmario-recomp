"""Qualify the complete protected actor while suppressing one foreign flag write."""
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
from prepare_mazo_progress import RECIPE, build


class MazoProgressTests(unittest.TestCase):
    def test_only_the_reviewed_pack_store_changes(self):
        _, _, _, old, new = build()
        self.assertEqual(len(old), len(new))
        self.assertEqual([i for i in range(len(old)) if old[i] != new[i]], [37, 38, 39])

    def test_unreviewed_patch_and_course_identity_rejected(self):
        r = json.loads(RECIPE.read_text())
        for key, value in [('patch', dict(r['patch'], address='A189B1')),
                           ('recipient_course', copy.deepcopy(r['source_course']))]:
            bad = copy.deepcopy(r); bad[key] = value
            with self.assertRaises(ValueError):
                build(bad)

    @unittest.skipUnless(shutil.which('cc'), 'requires C compiler')
    def test_complete_actor_preserves_cpu_and_message_lifecycle(self):
        _, _, _, old, new = build()
        engine = ROOT / 'local/upstream/snesrecomp/runner/src'
        with tempfile.TemporaryDirectory(prefix='bm-mazo-progress-') as folder:
            p = Path(folder)
            (p / 'old.bin').write_bytes(old); (p / 'new.bin').write_bytes(new)
            subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections', '-I' + str(engine),
                str(ROOT / 'tests/mazo_progress_test.c'), str(engine / 'snes/interp816.c'),
                '-o', str(p / 'test')], check=True)
            result = subprocess.run([str(p / 'test'), str(p / 'old.bin'), str(p / 'new.bin')],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('24576 actor cases', result.stdout)


if __name__ == '__main__':
    unittest.main()
