"""Execute the real coordinate command and check its WRAM write boundary."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from test_console_teleport import build_probe, ENGINE
from test_console_swim import PREFIX


@unittest.skipUnless(shutil.which('cc') and ENGINE.exists(), 'requires compiler and pinned runtime')
class ConsoleXYTests(unittest.TestCase):
    def test_coordinates_and_gameplay_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            build_probe(work)
            text = (work / 'runner/src/desktop/host_main.c').read_text()
            fragment = text[text.index('static void CheatExecute('):text.index('void NORETURN Die(')]
            (work / 'xy.inc').write_text(fragment)
            (work / 'xy.c').write_text(PREFIX.replace(', rom[0x400000]', '') + '\n#include "xy.inc"\n' + BODY)
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-I' + str(ENGINE / 'runner/src'), str(work / 'xy.c'),
                            '-o', str(work / 'xy')], check=True)
            subprocess.run([str(work / 'xy')], check=True)


BODY = r'''
static uint8_t before[0x20000], expected[0x20000];
static void active(void) {
  memset(g_ram,0xa5,sizeof(g_ram));
  g_ram[0x100]=0x14;
  g_ram[0x71]=g_ram[0x9d]=g_ram[0x13d4]=g_ram[0x1493]=0;
  memcpy(before,g_ram,sizeof(g_ram));
}
static void execute(const char *s) { snprintf(g_cheat_input,sizeof(g_cheat_input),"%s",s);CheatExecute(); }
static void valid(const char *command,unsigned x,unsigned y) {
  active();memcpy(expected,g_ram,sizeof(g_ram));
  expected[0x94]=expected[0xd1]=x&255; expected[0x95]=expected[0xd2]=x>>8;
  expected[0x96]=expected[0xd3]=y&255; expected[0x97]=expected[0xd4]=y>>8;
  expected[0x7a]=expected[0x7b]=expected[0x7c]=expected[0x7d]=0;
  expected[0x13da]=expected[0x13dc]=0;
  execute(command);assert(!memcmp(g_ram,expected,sizeof(g_ram)));
  assert(!strncmp(g_cheat_status,"xy ",3));
}
int main(void) {
  TickCheatHolds();FinishCheatHolds();
  valid("xy 256 240",256,240);valid("tp 0x1234 0XABCD",0x1234,0xabcd);
  valid("xy 0 65535",0,65535);valid("xy 65535 0",65535,0);
  valid("xy 010 008",10,8);
  const char *bad[]={"xy","xy 1","xy 1 2 3","xy -1 2","xy 1 -2",
    "xy 65536 2","xy 1 65536","xy 1x 2","xy x 2","xy 0x 2",
    "xy 999999999999999999999999 2"};
  for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);++i) {
    active();execute(bad[i]);assert(!memcmp(g_ram,before,sizeof(g_ram)));
    assert(strstr(g_cheat_status,"usage:"));
  }
  for(unsigned mode=0;mode<256;++mode) if(mode!=0x14) {
    active();g_ram[0x100]=mode;memcpy(before,g_ram,sizeof(g_ram));execute("xy 256 240");
    assert(!memcmp(g_ram,before,sizeof(g_ram)));assert(strstr(g_cheat_status,"active level"));
  }
  const unsigned guards[]={0x71,0x9d,0x13d4,0x1493};
  for(unsigned i=0;i<sizeof(guards)/sizeof(guards[0]);++i) {
    active();g_ram[guards[i]]=1;memcpy(before,g_ram,sizeof(g_ram));execute("tp 1 2");
    assert(!memcmp(g_ram,before,sizeof(g_ram)));
  }
  puts("XY command: exact writes, decimal/hex bounds, all mode gates and action locks pass");
}
'''
