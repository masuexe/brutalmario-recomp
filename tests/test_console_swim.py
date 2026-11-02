"""Run console toggles against the recipient's real water-decision program."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from test_console_teleport import build_probe, ROOT, ENGINE

ROM = ROOT / 'local/restoration/demo11-native-product-r14/rom.sfc'


@unittest.skipUnless(shutil.which('cc') and ROM.is_file(), 'requires pinned r14 ROM and C compiler')
class ConsoleSwimTests(unittest.TestCase):
    def test_off_recalculates_land_water_and_partial_water(self):
        expected = json.loads((ROOT / 'config/restorations/demo11-native-product-r14.json').read_text())['output']['sha256']
        self.assertEqual(hashlib.sha256(ROM.read_bytes()).hexdigest(), expected)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            build_probe(work)
            text = (work / 'runner/src/desktop/host_main.c').read_text()
            fragment = text[text.index('static void CheatExecute('):text.index('void NORETURN Die(')]
            (work / 'swim.inc').write_text(fragment)
            (work / 'swim.c').write_text(PREFIX + '\n#include "swim.inc"\n' + BODY)
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-I' + str(ENGINE / 'runner/src'), str(work / 'swim.c'),
                            str(ENGINE / 'runner/src/snes/interp816.c'), '-o', str(work / 'swim')], check=True)
            subprocess.run([str(work / 'swim'), str(ROM)], check=True)
            self.assertIn('      TickCheatHolds();', text)
            self.assertIn('    FinishCheatHolds();', text)
            self.assertLess(text.index('      TickCheatHolds();'), text.index('        RtlRunFrame(word);'))
            self.assertGreater(text.index('    FinishCheatHolds();'), text.index('        RtlRunFrame(word);'))


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "snes/interp816.h"
static uint8_t g_ram[0x20000], rom[0x400000];
static int g_cheat_invincible, g_cheat_swim, g_cheat_console_open;
static char g_cheat_input[64], g_cheat_status[256];
static void CheatQueueMap(int m,int x,int y) { (void)m;(void)x;(void)y; assert(0); }
static void CheatQueueRoom(int room) { (void)room;assert(0); }
static void CheatQueuePoke(unsigned a,const uint8_t *b,int n) { (void)a;(void)b;(void)n;assert(0); }
'''

BODY = r'''
static uint8_t read_bus(void *ctx, uint32_t a) {
  (void)ctx;
  if((a&0xffff)<0x2000) return g_ram[a&0x1fff];
  assert(a>=0x8000 && a<0x10000); return rom[a&0x7fff];
}
static void write_bus(void *ctx,uint32_t a,uint8_t v) {
  (void)ctx; assert(a<0x2000); g_ram[a]=v;
}
static void water_decision(void) {
  Interp816 *cpu=interp816_init(NULL,read_bus,write_bus); assert(cpu);
  cpu->e=false;cpu->mf=cpu->xf=true;cpu->k=cpu->db=0;cpu->dp=0;
  cpu->pc=0xea45;cpu->sp=0x1ff;
  unsigned steps=0;
  while(cpu->pc!=0xfd08 && cpu->pc!=0xeaa5 && steps++<100) interp816_runOpcode(cpu);
  assert(steps<100); interp816_free(cpu);
}
static void toggle(void) { strcpy(g_cheat_input,"swim");CheatExecute(); }
static void fixture(uint8_t level_water,uint8_t tile_water,uint8_t expected) {
  memset(g_ram,0,sizeof(g_ram));g_cheat_swim=0;
  g_ram[0x100]=0x14;g_ram[0x85]=level_water;g_ram[0x75]=1;
  toggle();assert(g_cheat_swim);
  for(int i=0;i<3;++i) {
    g_ram[0x8a]=tile_water;
    TickCheatHolds();assert(g_ram[0x85]==1);
    water_decision();assert(g_ram[0x75]==1);
    FinishCheatHolds();assert(g_ram[0x85]==level_water);
  }
  toggle();assert(!g_cheat_swim && g_ram[0x75]==1);
  g_ram[0x8a]=tile_water;
  TickCheatHolds();assert(g_ram[0x85]==level_water);
  water_decision();FinishCheatHolds();
  assert(g_ram[0x75]==expected && g_ram[0x85]==level_water);
  printf("level_water=%u tile_bits=%u swim_off_player_water=%u\n",level_water,tile_water,g_ram[0x75]);
  if (!level_water && tile_water) {
    g_ram[0x8a]=0; water_decision();assert(g_ram[0x75]==0);
  }
}
int main(int argc,char **argv) {
  assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
  assert(fread(rom,1,sizeof(rom),f)==sizeof(rom));fclose(f);
  assert(rom[0x6a45]==0xa5 && rom[0x6a46]==0x85);
  fixture(0,0,0); /* Dry land: natural collision clears player swimming. */
  fixture(1,0,1); /* Fully submerged course: remain swimming. */
  fixture(0,3,1); /* Local water tiles in a dry course: remain swimming. */
  g_cheat_swim=1;g_ram[0x100]=0x13;g_ram[0x85]=0;
  TickCheatHolds();FinishCheatHolds();assert(g_ram[0x85]==0);
  g_ram[0x100]=0x14;TickCheatHolds();g_ram[0x10b]++;g_ram[0x85]=1;
  FinishCheatHolds();assert(g_ram[0x85]==1); /* New room owns its water flag. */
  g_ram[0x85]=0;TickCheatHolds();g_ram[0x85]=0;
  FinishCheatHolds();assert(g_ram[0x85]==0); /* Preserve guest dry writes. */
}
'''
