"""Execute the patched console queue with both exit-table halves preseeded."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import runtime_patches

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'local/upstream/snesrecomp'


def build_probe(work):
    manifest = json.loads((ROOT / 'config/runtime-patches.json').read_text())
    source = 'runner/src/desktop/host_main.c'
    path = work / source
    path.parent.mkdir(parents=True)
    shutil.copyfile(ENGINE / source, path)
    for item in manifest['patches']:
        if item['source'] != source:
            continue
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['source_sha256']
        subprocess.run(['git', 'apply', str(ROOT / item['patch'])], cwd=work, check=True)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['result_sha256']
    text = path.read_text()
    function = text[text.index('static void CheatQueueRoom('):text.index('static void CheatExecute(')]
    (work / 'room.inc').write_text(function)
    (work / 'probe.c').write_text(r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint8_t ram[0x20000];
static int g_script_count, emit;
static void CheatQueuePoke(unsigned addr, const uint8_t *data, int count) {
  memcpy(ram + addr, data, count); ++g_script_count;
  if (emit) { printf("poke %x ", addr); for(int i=0;i<count;++i) printf("%02x",data[i]); puts(""); }
}
static void CheatQueueWait(int frames) { if(emit) printf("wait %d\n",frames); }
static void CheatQueuePress(unsigned mask, int frames) { assert(mask == 2); if(emit) printf("press y %d\n",frames); }
static void CheatQueueFinish(int first) { (void)first; }
#include "room.inc"
int main(int argc, char **argv) {
  const int rooms[] = {0x00f,0x10f,0x000,0x100,0x1ff,0x00f};
  memset(ram,0xa5,sizeof(ram));
  for(unsigned i=0;i<sizeof(rooms)/sizeof(rooms[0]);++i) {
    CheatQueueRoom(rooms[i]);
    assert(ram[0x19b8] == (rooms[i]&255));
    assert(ram[0x19d8] == 4+(rooms[i]>>8));
    for(unsigned j=1;j<32;++j) { assert(ram[0x19b8+j]==0xa5); assert(ram[0x19d8+j]==0xa5); }
  }
  if(argc==2) { emit=1; CheatQueueRoom((int)strtol(argv[1],NULL,0)); }
}
''')
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', str(work / 'probe.c'),
                    '-o', str(work / 'probe')], check=True)
    return work / 'probe'


@unittest.skipUnless(shutil.which('cc') and (ENGINE / 'runner/src/desktop/host_main.c').exists(),
                     'requires C compiler and pinned runtime')
class ConsoleTeleportTests(unittest.TestCase):
    def test_low_and_high_rooms_preserve_neighboring_exit_records(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = build_probe(Path(directory))
            subprocess.run([str(executable)], check=True)
            for room in ('00f', '10f'):
                sequence = subprocess.check_output([str(executable), '0x' + room], text=True)
                fixture = ROOT / 'recomp/inputs' / ('console-teleport-' + room + '.script')
                self.assertIn(sequence, fixture.read_text())

    def test_extending_materialized_patch_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            build_probe(work)
            items = [dict(item, patch=str(ROOT / item['patch'])) for item in
                     json.loads((ROOT / 'config/runtime-patches.json').read_text())['patches']
                     if item['source'] == 'runner/src/desktop/host_main.c']
            subprocess.run(['git', 'apply', '-R', items[-1]['patch']], cwd=work, check=True)
            target = work / 'local/runtime/runner/src/desktop/host_main.c'
            target.parent.mkdir(parents=True)
            shutil.copyfile(work / 'runner/src/desktop/host_main.c', target)
            with patch.object(runtime_patches, 'ROOT', work), patch.object(runtime_patches, 'patch_plan', return_value=items):
                runtime_patches.prepare_runtime()
                self.assertEqual(runtime_patches.sha(target.read_bytes()), items[-1]['result_sha256'])
                runtime_patches.prepare_runtime()  # A repeated build is unchanged.
                self.assertEqual(runtime_patches.sha(target.read_bytes()), items[-1]['result_sha256'])
