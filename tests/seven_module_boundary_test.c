/* Execute pinned donor bytes through the real 65816 interpreter on an isolated
 * test bus. MMIO writes are recorded; this does not simulate DMA/PPU output. */
#include "snes/interp816.h"
#include "native_content.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  uint8_t *rom, *code, *graphics;
  uint8_t ram[0x20000], regs[0x8000], caller[16];
  unsigned dma_triggers;
} Bus;

static uint8_t *read_file(const char *path, size_t size) {
  FILE *file = fopen(path, "rb");
  assert(file);
  uint8_t *data = malloc(size);
  assert(data && fread(data, 1, size, file) == size);
  assert(fgetc(file) == EOF && !ferror(file));
  fclose(file);
  return data;
}

static uint8_t read_bus(void *context, uint32_t address) {
  Bus *bus = context;
  unsigned bank = address >> 16, low = address & 0xffff;
  if (bank == 0x7e || bank == 0x7f) return bus->ram[address & 0x1ffff];
  if ((bank & 0x7f) < 0x40 && low < 0x2000) return bus->ram[low];
  if ((bank & 0x7f) < 0x40 && low < 0x8000) return bus->regs[low];
  if (bank == 0 && low >= 0x8000 && low < 0x8010) return bus->caller[low-0x8000];
  /* Explicit synthetic NMI fixture: PHA; LDA #$77; STA $1529; PLA; RTI. */
  const uint8_t nmi[] = {0x48, 0xa9, 0x77, 0x8d, 0x29, 0x15, 0x68, 0x40};
  if (bank == 0 && low >= 0x8100 && low < 0x8108) return nmi[low-0x8100];
  if (bank == 0 && low == 0xffea) return 0;
  if (bank == 0 && low == 0xffeb) return 0x81;
  uint8_t *mapped = bm_content_resolve(bus->rom, bank, low);
  if (mapped) return *mapped;
  assert(low >= 0x8000 && (bank & 0x7f) < 0x80);
  return bus->rom[((bank & 0x7f) << 15) | (low & 0x7fff)];
}

static void write_bus(void *context, uint32_t address, uint8_t value) {
  Bus *bus = context;
  unsigned bank = address >> 16, low = address & 0xffff;
  if (bank == 0x7e || bank == 0x7f) bus->ram[address & 0x1ffff] = value;
  else if ((bank & 0x7f) < 0x40 && low < 0x2000) bus->ram[low] = value;
  else {
    assert((bank & 0x7f) < 0x40 && low >= 0x2000 && low < 0x8000);
    bus->regs[low] = value;
    if (low == 0x420b) {
      assert(value == 4);
      assert(bus->regs[0x4324] == 0x7e || bus->regs[0x4324] == 0xa6);
      if (bus->regs[0x4324] == 0xa6) {
        assert(bus->regs[0x2116] == 0 && bus->regs[0x2117] == 0x48);
        assert(bus->regs[0x4325] == 0 && bus->regs[0x4326] == 8);
      }
      ++bus->dma_triggers;
    }
  }
}

static Interp816 *fresh(Bus *bus) {
  memset(bus->ram, 0, sizeof(bus->ram));
  memset(bus->regs, 0, sizeof(bus->regs));
  memset(bus->caller, 0xdb, sizeof(bus->caller));
  bus->dma_triggers = 0;
  Interp816 *cpu = interp816_init(bus, read_bus, write_bus);
  assert(cpu);
  cpu->e = false; cpu->mf = cpu->xf = true;
  cpu->pc = 0x8000; cpu->sp = 0x1ff;
  cpu->x = 9;
  return cpu;
}

static void finish(Interp816 *cpu) {
  unsigned steps = 0;
  while (!cpu->stopped && steps++ < 2000) interp816_runOpcode(cpu);
  assert(cpu->stopped && steps < 2000);
  assert(cpu->k == 0 && cpu->sp == 0x1ff);
}

int main(int argc, char **argv) {
  assert(argc == 4);
  Bus *bus = calloc(1, sizeof(*bus));
  assert(bus);
  bus->rom = read_file(argv[1], 0x400000);
  bus->code = read_file(argv[2], BOUNDARY_CODE_SIZE);
  bus->graphics = read_file(argv[3], BOUNDARY_GRAPHICS_SIZE);
  bm_content_load(bus->rom, 0x400000);
  assert(bm_content_resolve(bus->rom+1, 0xa2, 0x8000) == NULL);
  assert(bm_content_resolve(bus->rom, 0xa2, 0x1fff) == NULL);
  assert(bm_content_resolve(bus->rom, 0x22, 0x8000) == NULL);
  assert(!memcmp(bm_content_resolve(bus->rom, 0xa5, 0x95cd), "STAR", 4));
  assert(*bm_content_resolve(bus->rom, 0xb6, 0x8008) != bus->rom[0x1b0008]);
  /* The ordinary source bank stays the recipient's bytes. */
  assert(read_bus(bus, 0x22800f) != read_bus(bus, 0xa2800f));
  for (unsigned extra = 0; extra < 2; ++extra) {
    Interp816 *cpu = fresh(bus);
    uint8_t caller[] = {0x22, 0x0f, 0x80, 0xa2, 0xdb};
    memcpy(bus->caller, caller, sizeof(caller));
    bus->ram[0x1ab10+9] = extra ? 4 : 0;
    finish(cpu);
    if (extra) assert(bus->ram[0x1504+9] == 6 && bus->ram[0x94] == 0);
    else {
      assert(bus->ram[0xc10e] == 0x77 && bus->ram[0x94] == 0xc0);
      assert(bus->ram[0xd8+9] == 0x38 && bus->ram[0x15ac+9] == 0xff);
      assert(bus->ram[0x1fee0] == 1 && bus->ram[0x1fb18] == 8);
      assert(bus->ram[0x1fb1c] == 0xe3 && bus->ram[0x1fb1d] == 0x7f);
      assert(bus->regs[0x212c] == 0x14 && bus->regs[0x212d] == 3);
    }
    interp816_free(cpu);
  }
  /* Run the actual scheduler caller and recipient's byte-identical scheduler,
   * stopping before the parent's RTS. It copies the adapted inline JSL to RAM. */
  for (unsigned interrupt = 0; interrupt < 2; ++interrupt) {
    Interp816 *cpu = fresh(bus);
    cpu->k = cpu->db = 0xa2; cpu->pc = 0x81cf; cpu->a = 0x12;
    unsigned steps = 0;
    while (!(cpu->k == 0xa2 && cpu->pc == 0x81d7) && steps++ < 2000)
      interp816_runOpcode(cpu);
    assert(steps < 2000 && cpu->sp == 0x1ff);
    const uint8_t callback[] = {0xa9, 0x12, 0xa2, 9, 0x22, 0xa5, 0xa5, 0xa2, 0x6b};
    assert(!memcmp(bus->ram+0xc130, callback, sizeof(callback)));
    assert(bus->ram[0xc12f] == 1);
    /* Execute the emitted RAM callback, with a synthetic interrupt inside its
     * relocated callback body. MMIO register programs are checked, not pixels. */
    uint8_t caller[] = {0x22, 0x30, 0xc1, 0x7e, 0xdb};
    memcpy(bus->caller, caller, sizeof(caller));
    cpu->k = 0; cpu->pc = 0x8000;
    unsigned interrupted = 0;
    steps = 0;
    while (!cpu->stopped && steps++ < 2000) {
      if (interrupt && !interrupted && cpu->k == 0xa2 && cpu->pc == 0xa5a5) {
        cpu->nmiWanted = true;
        interrupted = 1;
      }
      interp816_runOpcode(cpu);
    }
    assert(cpu->stopped && steps < 2000 && cpu->k == 0 && cpu->sp == 0x1ff);
    assert(cpu->db == 0xa2 && bus->dma_triggers == 3);
    assert(bus->regs[0x4325] == 0 && bus->regs[0x4326] == 3);
    assert(interrupted == interrupt && bus->ram[0x1529] == (interrupt ? 0x77 : 0));
    interp816_free(cpu);
  }
  bm_content_clear(bus->rom);
  assert(bm_content_resolve(bus->rom, 0xa2, 0x8000) == NULL);
  free(bus->rom); free(bus->code); free(bus->graphics); free(bus);
  puts("Seven module: actual init branches, deferred RAM JSL, MMIO programming and interrupted return passed");
  return 0;
}
