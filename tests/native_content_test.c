#include "native_content.h"
#include "snes/cart.h"
#include "snes/sdd1.h"
#include "snes/sa1.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* Unused coprocessor paths retained by cart_getRomPtr's mapper switch. */
uint32_t sdd1_mmc_offset(Sdd1 *s, uint32_t a) { (void)s; (void)a; return UINT32_MAX; }
uint32_t sdd1_lorom_window_offset(Sdd1 *s, uint8_t b, uint16_t a) {
  (void)s; (void)b; (void)a; return UINT32_MAX;
}
uint8_t *sa1_cpu_memory_ptr(Sa1 *s, uint8_t b, uint16_t a) {
  (void)s; (void)b; (void)a; return NULL;
}

int main(int argc, char **argv) {
  assert(argc == 2);
  const size_t size = 0x400000, offset = 0x1b0008;
  uint8_t *rom = malloc(size);
  assert(rom);
  memset(rom, 0x5a, size);
  memset(rom + offset, 0, 16);
  if (!strcmp(argv[1], "wrong-rom")) rom[0] ^= 1;
  bm_content_load(rom, size);
  Cart cart = {0};
  cart.type = CART_LOROM;
  cart.rom = rom;
  cart.romSize = size;
  cart.ramSize = 0x2000;
  uint8_t *external = cart_getRomPtr(&cart, 0xb6, 0x8008);
  assert(external && external != rom + offset);
  for (unsigned i = 0; i < 16; ++i) {
    assert(external[i] == i + 1);
    assert(*cart_getRomPtr(&cart, 0x36, 0x8008 + i) == 0);
  }
  /* Pointers on either side of the asset keep contiguous span semantics. */
  uint8_t *before = cart_getRomPtr(&cart, 0xb6, 0x8007);
  assert(before[0] == 0x5a && before[1] == 1);
  assert(external[15] == 16 && external[16] == 0x5a);
  assert(*cart_getRomPtr(&cart, 0xb6, 0x8000) == 0x5a);
  assert(*cart_getRomPtr(&cart, 0xb6, 0xffff) == 0x5a);
  assert(cart_getRomPtr(&cart, 0xb6, 0x7fff) == NULL);
  assert(cart_getRomPtr(&cart, 0x7e, 0x8008) == NULL);
  assert(*cart_getRomPtr(&cart, 0xb5, 0x8008) == 0x5a);
  assert(*cart_getRomPtr(&cart, 0xb7, 0x8008) == 0x5a);
  bm_content_clear(rom + 1); /* An unrelated owner cannot clear this mount. */
  assert(bm_content_resolve(rom, 0xb6, 0x8008) == external);
  bm_content_load(rom, size); /* Reload discards the old backing. */
  assert(*cart_getRomPtr(&cart, 0xb6, 0x8008) == 1);
  bm_content_clear(rom);
  assert(bm_content_resolve(rom, 0xb6, 0x8008) == NULL);
  assert(*cart_getRomPtr(&cart, 0xb6, 0x8008) == 0);
  free(rom);
  puts("Independent native bank, contiguous asset boundaries and mount lifecycle passed");
  return 0;
}
