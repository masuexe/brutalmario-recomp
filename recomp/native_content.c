#include "native_content.h"
#include "native_content_manifest.h"
#include "sha256.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Every region replaces a run of cartridge bytes with bytes from the pack.
 * The runtime keeps one backing copy of the image, so a resolved pointer
 * stays valid for the lifetime of the cartridge. */
static const uint8_t *owner;
static uint8_t *backing;
static unsigned long long resolutions;
static int registered;
/* Banks that hold a region. A resolve inside such a bank returns the backing
 * pointer, so a read that spans a region boundary stays contiguous. */
static unsigned char active_bank[128];

static void fail(const char *reason) {
  fprintf(stderr, "[native-content] rejected: %s\n", reason);
  exit(EXIT_FAILURE);
}

static int matches(const uint8_t *data, size_t size, const uint8_t expected[32]) {
  uint8_t actual[32];
  sha256_compute(data, size, actual);
  return memcmp(actual, expected, 32) == 0;
}

static void report(void) {
  if (backing)
    fprintf(stderr, "[native-content] resolutions=%llu\n", resolutions);
}

void bm_content_clear(const uint8_t *rom) {
  if (owner != rom) return;
  report();
  free(backing);
  backing = NULL;
  owner = NULL;
}

static const char *pack_path(void) {
  const char *path = getenv("BM_NATIVE_CONTENT_PACK");
  if (!path || !*path) fail("BM_NATIVE_CONTENT_PACK is required");
  return path;
}

void bm_content_load(uint8_t *rom, size_t size) {
  if (owner) bm_content_clear(owner);
  if (size != BM_CONTENT_ROM_SIZE || !matches(rom, size, bm_content_rom_sha))
    fail("ROM identity differs");

  /* Every replaced region must be empty in the image. A non-empty region
   * means the descendant image and the pack disagree. */
  for (unsigned i = 0; i < BM_CONTENT_REGION_COUNT; ++i) {
    size_t offset = bm_content_region_offset[i];
    size_t length = bm_content_region_size[i];
    if (offset > size || length > size - offset) fail("region exceeds the image");
    for (size_t k = 0; k < length; ++k)
      if (rom[offset + k]) fail("image still holds region bytes");
  }

  FILE *file = fopen(pack_path(), "rb");
  if (!file) fail("cannot open pack");
  uint8_t *payload = malloc(BM_CONTENT_PACK_SIZE ? BM_CONTENT_PACK_SIZE : 1);
  if (!payload) { fclose(file); fail("payload allocation failed"); }
  size_t count = fread(payload, 1, BM_CONTENT_PACK_SIZE, file);
  int extra = fgetc(file);
  int io_error = ferror(file);
  fclose(file);
  if (count != BM_CONTENT_PACK_SIZE || extra != EOF || io_error)
    fail("pack size differs");
  if (!matches(payload, BM_CONTENT_PACK_SIZE, bm_content_pack_sha))
    fail("pack SHA-256 differs");

  backing = calloc(size + 1, 1);
  if (!backing) { free(payload); fail("backing allocation failed"); }
  memcpy(backing, rom, size);
  size_t cursor = 0;
  for (unsigned i = 0; i < BM_CONTENT_REGION_COUNT; ++i) {
    memcpy(backing + bm_content_region_offset[i], payload + cursor,
           bm_content_region_size[i]);
    cursor += bm_content_region_size[i];
  }
  free(payload);
  memset(active_bank, 0, sizeof(active_bank));
  for (unsigned i = 0; i < BM_CONTENT_REGION_COUNT; ++i) {
    size_t start = bm_content_region_offset[i];
    for (size_t k = 0; k < bm_content_region_size[i]; ++k) {
      size_t at = start + k;
      if (at < size) active_bank[(at >> 15) & 0x7f] = 1;
    }
  }
  owner = rom;
  resolutions = 0;
  if (!registered) { atexit(report); registered = 1; }
  fprintf(stderr, "[native-content] mounted " BM_CONTENT_ID
          " regions=%u bytes=%u\n", (unsigned)BM_CONTENT_REGION_COUNT,
          (unsigned)BM_CONTENT_PACK_SIZE);
}

uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address) {
  if (rom != owner || !backing || address < 0x8000) return NULL;
  size_t offset = ((size_t)(bank & 0x7f) << 15) | (address & 0x7fff);
  if (offset >= BM_CONTENT_ROM_SIZE) return NULL;
  unsigned char canonical = (unsigned char)((offset >> 15) & 0x7f);
  if (!active_bank[canonical]) return NULL;
  ++resolutions;
  return backing + offset;
}
