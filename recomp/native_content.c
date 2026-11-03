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

static void fail(const char *reason) {
  fprintf(stderr, "[native-region] rejected: %s\n", reason);
  exit(EXIT_FAILURE);
}

static int matches(const uint8_t *data, size_t size, const uint8_t expected[32]) {
  uint8_t actual[32];
  sha256_compute(data, size, actual);
  return memcmp(actual, expected, 32) == 0;
}

static void report(void) {
  if (backing)
    fprintf(stderr, "[native-region] resolutions=%llu\n", resolutions);
}

void bm_region_clear(const uint8_t *rom) {
  if (owner != rom) return;
  report();
  backing = NULL; /* The sprite runtime owns this allocation. */
  owner = NULL;
}

static const char *pack_path(void) {
  const char *path = getenv("BM_NATIVE_CONTENT_PACK");
  if (!path || !*path) fail("BM_NATIVE_CONTENT_PACK is required");
  return path;
}

void bm_region_load(uint8_t *rom, size_t size) {
  if (owner) bm_region_clear(owner);
  /* The sprite runtime already built the image plus its packs. Reuse that map
   * so a region write lands in the same bytes every other reader sees. */
  uint8_t *shared = bm_content_backing(rom, size);
  if (!shared) fail("region pack needs the sprite backing map");

  for (unsigned i = 0; i < BM_CONTENT_REGION_COUNT; ++i) {
    size_t offset = bm_content_region_offset[i];
    size_t length = bm_content_region_size[i];
    if (offset > size || length > size - offset) fail("region exceeds the image");
    for (size_t k = 0; k < length; ++k)
      if (shared[offset + k]) fail("image still holds region bytes");
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

  backing = shared;
  size_t cursor = 0;
  for (unsigned i = 0; i < BM_CONTENT_REGION_COUNT; ++i) {
    memcpy(backing + bm_content_region_offset[i], payload + cursor,
           bm_content_region_size[i]);
    cursor += bm_content_region_size[i];
  }
  free(payload);
  owner = rom;
  resolutions = 0;
  if (!registered) { atexit(report); registered = 1; }
  fprintf(stderr, "[native-region] mounted " BM_CONTENT_ID
          " regions=%u bytes=%u\n", (unsigned)BM_CONTENT_REGION_COUNT,
          (unsigned)BM_CONTENT_PACK_SIZE);
}

uint8_t *bm_region_resolve(const uint8_t *rom, uint8_t bank, uint16_t address) {
  (void)rom;
  if (!backing || address < 0x8000) return NULL;
  size_t offset = ((size_t)(bank & 0x7f) << 15) | (address & 0x7fff);
  /* Only a byte inside a region comes from the pack. A byte in the same bank
   * but outside the region stays an image byte, so a mapped sprite bank that
   * shares no region is untouched. */
  for (unsigned i = 0; i < BM_CONTENT_REGION_COUNT; ++i) {
    size_t start = bm_content_region_offset[i];
    if (offset >= start && offset - start < bm_content_region_size[i]) {
      ++resolutions;
      return backing + offset;
    }
  }
  return NULL;
}
