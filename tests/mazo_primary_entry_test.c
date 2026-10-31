#include "snes/interp816.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint8_t ram[0x20000], code[128]; unsigned size; int patched; } Bus;
int interp816_opcode_hook(uint32_t address) { (void)address; return 0; }
static uint8_t read_bus(void *context, uint32_t address) {
  Bus *b = context;
  unsigned bank = address >> 16, low = address & 65535;
  if ((bank & 0x7f) < 0x40 && low < 0x2000) return b->ram[low];
  if (bank == 0 && low >= 0xb987 && low <= 0xb991) {
    static const uint8_t helper[] = {0xe8,0xd0,0x05,0xa2,0x00,0x80,0xe6,0x8c,0x86,0x8a,0x60};
    return helper[low - 0xb987];
  }
  if (bank == 0x88 && low >= 0x8000 && low < 0x8000 + b->size)
    return b->code[low - 0x8000];
  /* Model the helper return NZ flags from A, then execute the original caller. */
  static const uint8_t original[] = {0x22,0xa2,0xed,0x13,0x85,0x0f,0xc2,0x30,0xdb};
  static const uint8_t hook[] = {0x22,0x00,0x80,0x88};
  if (bank == 0x13 && low >= 0xeda2 && low <= 0xeda4) {
    static const uint8_t helper[] = {0x29, 0xff, 0x6b};
    return helper[low - 0xeda2];
  }
  assert(bank == 5 && low >= 0xd8b1 && low <= 0xd8b9);
  if (b->patched && low < 0xd8b5) return hook[low - 0xd8b1];
  return original[low - 0xd8b1];
}
static void write_bus(void *context, uint32_t address, uint8_t value) {
  Bus *b = context;
  assert((address >> 16) == 0 || (address >> 16) == 5 || (address >> 16) == 0xa2);
  unsigned low = address & 65535;
  assert(low == 0x8a || low == 0x8b || low == 0x0e || low == 0x0f || low == 0x17bb || (low >= 0x1f0 && low <= 0x1ff));
  b->ram[low] = value;
}
static Interp816 *run(Bus *b, unsigned a, unsigned flags) {
  Interp816 *c = interp816_init(b, read_bus, write_bus);
  c->e = false; interp816_setFlags(c, flags | 0x20);
  c->a = a; c->x = 0x42; c->y = 0x19; c->sp = 0x1ff;
  c->dp = 0; c->db = 5; c->k = 5; c->pc = 0xd8b1;
  for (unsigned n = 0; n < 100 && !c->stopped; ++n) interp816_runOpcode(c);
  assert(c->stopped && c->k == 5 && c->db == 5 && c->sp == 0x1ff);
  assert(c->x == 0x42 && c->y == 0x19 && c->dp == 0);
  return c;
}
int main(int argc, char **argv) {
  assert(argc == 2);
  Bus initial = {0};
  FILE *f = fopen(argv[1], "rb"); assert(f);
  initial.size = fread(initial.code, 1, sizeof(initial.code), f);
  assert(initial.size && initial.size < sizeof(initial.code)); fclose(f);
  initial.ram[0x1f18] = 1; initial.ram[0x1f19] = 0xf0;
  unsigned cases = 0;
  const unsigned guards[] = {0xdd6,0x1f11,0x1f17,0x1f18,0x1f19,0x1f1a};
  for (unsigned scope = 0; scope <= 6; ++scope) {
    for (unsigned value = 0; value < 256; ++value) {
      for (unsigned flags = 0; flags < 256; flags += 17) {
        Bus a = initial, b = initial;
        if (scope) { a.ram[guards[scope-1]] ^= 1; b = a; }
        a.ram[0x13bf] = b.ram[0x13bf] = value;
        a.ram[0x17bb] = b.ram[0x17bb] = 0x0c;
        a.ram[0x0e] = b.ram[0x0e] = 0x0c;
        a.patched = 1;
        Interp816 *x = run(&a, 0xa500 | (flags & 1), flags);
        Interp816 *y = run(&b, 0xa500 | (value == 0x30 && !scope ? 1 : (flags & 1)), flags);
        if (value == 0x30 && !scope) {
          b.ram[0x17bb] = 0x90; b.ram[0x0e] = 0x90; b.ram[0x0f] = 1;
        }
        assert(x->a == y->a && interp816_getFlags(x) == interp816_getFlags(y));
        assert(a.ram[0x17bb] == b.ram[0x17bb]);
        for (unsigned i = 0; i < sizeof(a.ram); ++i)
          if (i < 0x1f0 || i > 0x1ff) assert(a.ram[i] == b.ram[i]);
        interp816_free(x); interp816_free(y); ++cases;
      }
    }
  }
  printf("PASS: %u selector/flags/scope cases, original CPU semantics retained\n", cases);
  Bus phase = {0};
  phase.ram[0x8a] = 0x38; phase.ram[0x8b] = 0x81; phase.ram[0x8c] = 0xa6;
  phase.ram[0x1c8] = 0x32; phase.ram[0x1c9] = 0xb9;
  Interp816 *c = interp816_init(&phase, read_bus, write_bus);
  c->e = false; interp816_setFlags(c, 0xa1);
  c->a = 0x00fe; c->x = 0x8138; c->y = 0x0300; c->sp = 0x1c7;
  c->db = 0xa2; c->k = 0; c->pc = 0xb987;
  for (unsigned n = 0; n < 4; ++n) interp816_runOpcode(c);
  assert(c->pc == 0xb933 && c->sp == 0x1c9 && c->x == 0x8139);
  assert(c->a == 0xfe && c->y == 0x300 && c->db == 0xa2 && interp816_getFlags(c) == 0xa1);
  assert(phase.ram[0x8a] == 0x39 && phase.ram[0x8b] == 0x81 && phase.ram[0x8c] == 0xa6);
  interp816_free(c);
  puts("PASS: observed decompressor input/return phase replays in four original instructions");
  return 0;
}
