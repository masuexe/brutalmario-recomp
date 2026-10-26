#include "native_content.h"
#include "snes/cart.h"
#include "snes/interp816.h"
#include "snes/sdd1.h"
#include "snes/sa1.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

uint32_t sdd1_mmc_offset(Sdd1 *s, uint32_t a) { (void)s; (void)a; return UINT32_MAX; }
uint32_t sdd1_lorom_window_offset(Sdd1 *s, uint8_t b, uint16_t a) {
  (void)s; (void)b; (void)a; return UINT32_MAX;
}
uint8_t *sa1_cpu_memory_ptr(Sa1 *s, uint8_t b, uint16_t a) {
  (void)s; (void)b; (void)a; return NULL;
}
int interp816_opcode_hook(uint32_t address) { (void)address; return 0; }

typedef struct { Cart cart; uint8_t ram[0x20000]; } TestBus;

static uint8_t read_bus(void *context, uint32_t address) {
  TestBus *bus = context;
  unsigned bank = address >> 16, low = address & 0xffff;
  if (bank == 0x7e || bank == 0x7f) return bus->ram[address & 0x1ffff];
  if ((bank & 0x7f) < 0x40 && low < 0x2000) return bus->ram[low];
  uint8_t *p = cart_getRomPtr(&bus->cart, bank, low);
  assert(p);
  return *p;
}

static void write_bus(void *context, uint32_t address, uint8_t value) {
  TestBus *bus = context;
  unsigned bank = address >> 16, low = address & 0xffff;
  if (bank == 0x7e || bank == 0x7f) bus->ram[address & 0x1ffff] = value;
  else {
    assert((bank & 0x7f) < 0x40 && low < 0x2000);
    bus->ram[low] = value;
  }
}

int main(int argc, char **argv) {
  assert(argc == 2);
  TestBus *bus = calloc(1, sizeof(*bus));
  assert(bus);
  uint8_t *rom = malloc(0x400000);
  assert(rom);
  memset(rom, 0x5a, 0x400000);
  memset(rom + 0x1b0008, 0, 16);
  const uint8_t caller[] = {0x22, 0xcd, 0x95, 0xa5, 0xdb}; /* JSL external; STP */
  const uint8_t nmi[] = {0x48, 0xa9, 0x77, 0x8d, 0x29, 0x15, 0x68, 0x40};
  memcpy(rom, caller, sizeof(caller));
  memcpy(rom + 0x100, nmi, sizeof(nmi));
  rom[0x7fea] = 0x00; rom[0x7feb] = 0x81;
  if (!strcmp(argv[1], "wrong-rom")) rom[123] ^= 1;
  bm_content_load(rom, 0x400000);
  bus->cart.type = CART_LOROM;
  bus->cart.rom = rom;
  bus->cart.romSize = 0x400000;
  bus->cart.ramSize = 0x2000;
  assert(*cart_getRomPtr(&bus->cart, 0x25, 0x95cd) == 0x5a);
  assert(*cart_getRomPtr(&bus->cart, 0xa5, 0x95cd) == 0x8b);
  assert(cart_getRomPtr(&bus->cart, 0xa5, 0x95cd) != cart_getRomPtr(&bus->cart, 0x25, 0x95cd));
  for (unsigned i = 0; i < 16; ++i) {
    assert(*cart_getRomPtr(&bus->cart, 0x36, 0x8008 + i) == 0);
    assert(*cart_getRomPtr(&bus->cart, 0xb6, 0x8008 + i) == i + 1);
  }
  assert(cart_getRomPtr(&bus->cart, 0xa5, 0x7fff) == NULL);
  assert(cart_getRomPtr(&bus->cart, 0x7e, 0x95cd) == NULL);
  Interp816 *cpu = interp816_init(bus, read_bus, write_bus);
  cpu->e = false; cpu->mf = cpu->xf = true;
  cpu->pc = 0x8000; cpu->sp = 0x1ff;
  interp816_runOpcode(cpu); /* JSL */
  assert(cpu->k == 0xa5 && cpu->pc == 0x95cd);
  for (int i = 0; i < 3; ++i) interp816_runOpcode(cpu); /* PHB; PHK; PLB */
  assert(cpu->db == 0xa5);
  cpu->nmiWanted = true;
  interp816_runOpcode(cpu);
  assert(cpu->k == 0 && cpu->pc == 0x8100);
  for (int i = 0; i < 30 && !cpu->stopped; ++i) interp816_runOpcode(cpu);
  assert(cpu->stopped && cpu->k == 0 && cpu->db == 0 && cpu->sp == 0x1ff);
  assert(bus->ram[0x1528] == 0x2a && bus->ram[0x1529] == 0x77);
  assert(interp816_page_insns(0xa595) > 0);
  bm_content_clear(rom);
  assert(*cart_getRomPtr(&bus->cart, 0xa5, 0x95cd) == 0x5a);
  interp816_free(cpu);
  free(rom); free(bus);
  puts("External instruction fetch, low WRAM mirror, NMI/RTI and JSL/RTL return passed");
  return 0;
}
