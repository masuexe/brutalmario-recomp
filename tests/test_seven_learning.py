"""Actual donor/mapped hurt logic with controlled random-state fixtures."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import native_seven_child as seven
from prepare_rom import verify


@unittest.skipUnless(shutil.which('cc') and
    (ROOT / 'local/restoration/demo11-native-seven-child-fight-music/rom.sfc').is_file(),
    'requires the pinned native fight-music target and C compiler')
class SevenLearningTests(unittest.TestCase):
    def test_seeded_hurt_learning_and_specific_immunity(self):
        target = 'demo11-native-seven-child-fight-music'
        directory = ROOT / 'local/restoration' / target
        cfg, _ = seven.settings(target)
        donor = ROOT / 'local/content-versions/boss/rom.sfc'
        fixture = ROOT / 'local/captures/seven-opening-v1-donor/attack1200.wram.bin'
        if not fixture.is_file():
            self.skipTest('requires the pinned donor WRAM fixture')
        verify((directory / 'rom.sfc').read_bytes(), cfg['output'], 'current native target')
        verify(donor.read_bytes(), json.loads((ROOT / 'config/boss-donor.json').read_text())['output'], 'official donor')
        verify(fixture.read_bytes(), {'size': 0x20000,
            'sha256': '74fb4823ead68901af132ef89ce9d5a9508b93a47f3eea780b593e01ca8a2b06'}, 'donor state fixture')
        env = os.environ.copy()
        seven.environment(target, env)
        with tempfile.TemporaryDirectory(prefix='bm-seven-learning-') as temporary:
            path = Path(temporary)
            (path / 'native_seven_manifest.h').write_text(seven.header(target))
            engine = ROOT / 'local/upstream/snesrecomp/runner/src'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-DBOUNDARY_CODE_SIZE=28880', '-DBOUNDARY_GRAPHICS_SIZE=27261',
                '-I'+str(engine), '-I'+str(engine / 'snes'), '-I'+str(ROOT / 'recomp'), '-I'+str(path),
                str(ROOT / 'tests/seven_learning_boundary_test.c'), str(ROOT / 'recomp/native_seven.c'),
                str(engine / 'sha256.c'), str(engine / 'snes/interp816.c'), '-o', str(path / 'learning')], check=True)
            subprocess.run([str(path / 'learning'), str(donor), str(directory / 'rom.sfc'), str(fixture)],
                           env=env, check=True)


if __name__ == '__main__':
    unittest.main()
