/* Immutable native data/code banks. This pilot deliberately uses interpreter
 * execution for the external code; the build rejects AOT nodes in either alias. */
#include "native_content.h"
#include "native_sprite_manifest.h"
#include "sha256.h"
#include "snes/interp816.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint8_t *owner;
static uint8_t *backing;
static unsigned long long code_resolutions, graphics_resolutions;
static int registered;

static void fail(const char *reason) {
  fprintf(stderr, "[native-sprite] rejected: %s\n", reason);
  exit(EXIT_FAILURE);
}

static int matches(const uint8_t *data, size_t size, const uint8_t expected[32]) {
  uint8_t actual[32];
  sha256_compute(data, size, actual);
  return memcmp(actual, expected, 32) == 0;
}

static void report(void) {
  if (!backing) return;
  unsigned long long instructions = 0;
  for (unsigned page = BM_SPRITE_FIRST_PAGE; page <= BM_SPRITE_LAST_PAGE; ++page)
    instructions += interp816_page_insns(page);
  fprintf(stderr, "[native-sprite] code_resolutions=%llu graphics_resolutions=%llu executed_page_instructions=%llu\n",
          code_resolutions, graphics_resolutions, instructions);
}

void bm_content_clear(const uint8_t *rom) {
  if (owner != rom) return;
  report();
  free(backing);
  backing = NULL;
  owner = NULL;
}

static void load_payload(const char *variable, unsigned offset, unsigned size,
                         const uint8_t expected[32]) {
  const char *path = getenv(variable);
  if (!path || !*path) fail(variable);
  FILE *file = fopen(path, "rb");
  if (!file) fail("cannot open pack");
  if (offset > BM_SPRITE_ROM_SIZE || size > BM_SPRITE_ROM_SIZE - offset)
    fail("payload exceeds backing");
  size_t count = fread(backing + offset, 1, size, file);
  int extra = fgetc(file), error = ferror(file);
  fclose(file);
  if (count != size || extra != EOF || error) fail("pack size differs");
  if (!matches(backing + offset, size, expected)) fail("pack SHA-256 differs");
}

void bm_content_load(uint8_t *rom, size_t size) {
  if (owner) bm_content_clear(owner);
  if (size != BM_SPRITE_ROM_SIZE || !matches(rom, size, bm_sprite_rom_sha))
    fail("ROM identity differs");
  backing = calloc(size + 1, 1);
  if (!backing) fail("backing allocation failed");
  memcpy(backing, rom, size);
  load_payload("BM_NATIVE_GRAPHICS_PACK", BM_SPRITE_GFX_OFFSET,
               BM_SPRITE_GFX_SIZE, bm_sprite_gfx_sha);
  load_payload("BM_NATIVE_SPRITE_PACK", BM_SPRITE_CODE_OFFSET,
               BM_SPRITE_CODE_SIZE, bm_sprite_code_sha);
  owner = rom;
  code_resolutions = graphics_resolutions = 0;
  if (!registered) { atexit(report); registered = 1; }
  fprintf(stderr, "[native-sprite] mounted sprite9e code_bank=A5 graphics_bank=B6\n");
}

uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address) {
  if (rom != owner || !backing || address < 0x8000 ||
      (bank != BM_SPRITE_CODE_BANK && bank != BM_SPRITE_GFX_BANK)) return NULL;
  size_t offset = ((size_t)(bank & 0x7f) << 15) | (address & 0x7fff);
  if (bank == BM_SPRITE_CODE_BANK && offset >= BM_SPRITE_CODE_OFFSET &&
      offset - BM_SPRITE_CODE_OFFSET < BM_SPRITE_CODE_SIZE) ++code_resolutions;
  if (bank == BM_SPRITE_GFX_BANK && offset >= BM_SPRITE_GFX_OFFSET &&
      offset - BM_SPRITE_GFX_OFFSET < BM_SPRITE_GFX_SIZE) ++graphics_resolutions;
  return backing + offset;
}
