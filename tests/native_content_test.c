#include "native_content.h"
#include "snes/cart.h"
#include "snes/sdd1.h"
#include "snes/sa1.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Unused coprocessor paths retained by cart_getRomPtr's mapper switch. */
uint32_t sdd1_mmc_offset(Sdd1 *s, uint32_t a) { (void)s; (void)a; return UINT32_MAX; }
uint32_t sdd1_lorom_window_offset(Sdd1 *s, uint8_t b, uint16_t a) {
  (void)s; (void)b; (void)a; return UINT32_MAX;
}
uint8_t *sa1_cpu_memory_ptr(Sa1 *s, uint8_t b, uint16_t a) {
  (void)s; (void)b; (void)a; return NULL;
}

/* The sprite runtime owns the backing map in a real build. This test provides
 * a stub that returns the image itself, so the region provider writes into the
 * bytes every other reader already uses. */
static uint8_t *stub_backing;
uint8_t *bm_content_backing(uint8_t *rom, size_t size) {
  (void)rom; (void)size;
  return stub_backing;
}

/* The sprite-gap runtime owns these entry points in a real build. This test
 * stubs them so only the region provider is exercised. */
void bm_content_load(uint8_t *rom, size_t size) { (void)rom; (void)size; }
void bm_content_clear(const uint8_t *rom) { (void)rom; }
uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address) {
  (void)rom; (void)bank; (void)address;
  return NULL;
}

int main(int argc, char **argv) {
  (void)argc;
  const size_t size = 0x400000, offset = 0x1b0008, second = 0x1b0108;
  uint8_t *rom = malloc(size);
  assert(rom);
  memset(rom, 0x5a, size);
  memset(rom + offset, 0, 16);
  memset(rom + second, 0, 8);
  stub_backing = rom;
  if (argv[1] && !strcmp(argv[1], "occupied")) rom[offset] = 1;
  bm_region_load(rom, size);
  Cart cart = {0};
  cart.type = CART_LOROM;
  cart.rom = rom;
  cart.romSize = size;
  cart.ramSize = 0x2000;
  /* Region one covers bytes 1..16 at bank B6 offset 8008. */
  uint8_t *external = cart_getRomPtr(&cart, 0xb6, 0x8008);
  assert(external);
  for (unsigned i = 0; i < 16; ++i) {
    assert(external[i] == i + 1);
    assert(*cart_getRomPtr(&cart, 0x36, 0x8008 + i) == i + 1);
  }
  /* Region two covers bytes 17..24 at bank B6 offset 8108. */
  uint8_t *other = cart_getRomPtr(&cart, 0xb6, 0x8108);
  assert(other);
  for (unsigned i = 0; i < 8; ++i) assert(other[i] == 17 + i);
  /* A byte outside every region stays an image byte, even in a region bank. */
  assert(*cart_getRomPtr(&cart, 0xb6, 0x8000) == 0x5a);
  assert(*cart_getRomPtr(&cart, 0xb6, 0x8018) == 0x5a);
  assert(*cart_getRomPtr(&cart, 0xb6, 0xffff) == 0x5a);
  assert(cart_getRomPtr(&cart, 0xb6, 0x7fff) == NULL);
  assert(cart_getRomPtr(&cart, 0x7e, 0x8008) == NULL);
  assert(*cart_getRomPtr(&cart, 0xb5, 0x8008) == 0x5a);
  bm_region_clear(rom + 1); /* An unrelated owner cannot clear this mount. */
  assert(bm_region_resolve(rom, 0xb6, 0x8008) == external);
  /* Reload discards the old mount. The image holds the region bytes again
   * because the previous mount wrote them into the shared backing. */
  memset(rom + offset, 0, 16);
  memset(rom + second, 0, 8);
  bm_region_load(rom, size);
  assert(*cart_getRomPtr(&cart, 0xb6, 0x8008) == 1);
  bm_region_clear(rom);
  /* After a clear the region no longer answers. The stub backing is the image
   * itself, so the byte keeps the value the last mount wrote. */
  assert(bm_region_resolve(rom, 0xb6, 0x8008) == NULL);
  free(rom);
  puts("Two regions, exact region bytes and mount lifecycle passed");
  return 0;
}
