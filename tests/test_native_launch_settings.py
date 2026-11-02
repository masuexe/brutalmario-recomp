"""Exercise map hooks and prohibit environment reads on the ROM bus path."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('cc'), 'requires a C compiler')
class NativeLaunchSettingsTests(unittest.TestCase):
    def test_cached_settings_preserve_hooks_and_refresh_on_load(self):
        with tempfile.TemporaryDirectory(prefix='bm-launch-settings-') as directory:
            work = Path(directory)
            (work / 'native_seven_manifest.h').write_text('''
#include <stdint.h>
#define BM_SEVEN_ROM_SIZE 0x40000u
#define BM_SEVEN_PACKS 1u
typedef struct { const char *variable; unsigned bank, offset, size, executable,
  first_page, last_page; uint8_t sha256[32]; } BmSevenPack;
static const uint8_t bm_seven_rom_sha[32] = {0};
static const BmSevenPack bm_seven_packs[1] = {
  {"TEST_PACK", 0x80, 0, 1, 0, 0, 0, {0}}
};
''')
            pack = work / 'pack.bin'
            pack.write_bytes(b'\0')
            engine = ROOT / 'local/upstream/snesrecomp/runner/src'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-I' + str(work), '-I' + str(ROOT / 'recomp'),
                            '-I' + str(engine),
                            str(ROOT / 'tests/native_launch_settings_test.c'),
                            '-o', str(work / 'probe')], check=True, capture_output=True)
            subprocess.run([str(work / 'probe'), str(pack)], check=True,
                           capture_output=True, timeout=10)
