#include "snes/interp816.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  uint8_t ram[0x20000], program[419];
  unsigned cycles, legacy_writes;
} Bus;
int interp816_opcode_hook(uint32_t address) { (void)address; return 0; }
static uint8_t read_bus(void *context, uint32_t address) {
  Bus *b = context;
  unsigned bank = address >> 16, low = address & 65535;
  if ((bank & 0x7f) < 0x40 && low < 0x2000) return b->ram[low];
  if (bank == 0xa1 && low >= 0x8989 && low < 0x8989 + sizeof(b->program))
    return b->program[low - 0x8989];
  static const uint8_t caller[] = {0x22,0x9d,0x89,0xa1,0xdb};
  assert(bank == 0 && low >= 0x8000 && low < 0x8000 + sizeof(caller));
  return caller[low - 0x8000];
}
static void write_bus(void *context, uint32_t address, uint8_t value) {
  Bus *b = context;
  unsigned bank = address >> 16, low = address & 65535;
  assert((bank & 0x7f) < 0x40 && low < 0x2000);
  assert((low >= 0x1f0 && low <= 0x1ff) || low == 0x1eaf || low == 0x1426 ||
         low == 0x1525 || low == 0x14d1);
  if (low == 0x1eaf) ++b->legacy_writes;
  b->ram[low] = value;
}
static Interp816 *run(Bus *b, unsigned p) {
  Interp816 *c = interp816_init(b, read_bus, write_bus);
  c->e = false; interp816_setFlags(c, p | 0x30);
  c->a = 0xa563; c->x = 9; c->y = 0x7f;
  c->sp = 0x1ff; c->db = 5; c->pc = 0x8000;
  for (unsigned i = 0; i < 100 && !c->stopped; ++i)
    b->cycles += interp816_runOpcode(c);
  assert(c->stopped && c->sp == 0x1ff && c->db == 5 && c->k == 0);
  return c;
}
int main(int argc, char **argv) {
  assert(argc == 3);
  uint8_t code[2][419];
  for (unsigned i = 0; i < 2; ++i) {
    FILE *f = fopen(argv[i+1], "rb"); assert(f);
    assert(fread(code[i], 1, 419, f) == 419 && fgetc(f) == EOF); fclose(f);
  }
  unsigned cases = 0;
  const unsigned counters[] = {0,1,255};
  for (unsigned flag = 0; flag < 256; ++flag)
    for (unsigned paused = 0; paused < 2; ++paused)
      for (unsigned counter = 0; counter < 3; ++counter)
        for (unsigned p = 0; p < 256; p += 17) {
          Bus a = {0}, b = {0};
          a.ram[0x10b] = 0x92; a.ram[0x10c] = 1;
          a.ram[0x1eaf] = flag; a.ram[0x9d] = paused;
          a.ram[0x1525] = counters[counter]; a.ram[0x14d1] = 8;
          b = a; memcpy(a.program, code[0], 419); memcpy(b.program, code[1], 419);
          Interp816 *x = run(&a, p), *y = run(&b, p);
          assert(x->a == y->a && x->x == y->x && x->y == y->y && x->dp == y->dp);
          assert(interp816_getFlags(x) == interp816_getFlags(y) && a.cycles == b.cycles);
          assert(a.ram[0x1eaf] == (paused ? flag : flag | 0x80));
          assert(b.ram[0x1eaf] == flag && b.legacy_writes == 0);
          assert(a.legacy_writes == (paused ? 0 : 1));
          assert(b.ram[0x1426] == (paused ? 0 : 1));
          assert(b.ram[0x1525] == (paused ? counters[counter] : (counters[counter] + 1) % 256));
          assert(b.ram[0x14d1] == (!paused && counter == 1 ? 0 : 8));
          for (unsigned i = 0; i < sizeof(a.ram); ++i)
            if (i != 0x1eaf) assert(a.ram[i] == b.ram[i]);
          interp816_free(x); interp816_free(y); ++cases;
        }
  printf("PASS: %u actor cases; same CPU cycles/registers/messages/removal; no foreign progress write\n", cases);
  return 0;
}
