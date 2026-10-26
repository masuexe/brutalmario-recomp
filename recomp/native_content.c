#include "native_content.h"
#include "native_content_manifest.h"
#include "sha256.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint8_t *owner;
static uint8_t *backing;
static unsigned long long bank_resolutions, asset_resolutions;
static int registered;

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
    fprintf(stderr, "[native-content] bank_resolutions=%llu asset_resolutions=%llu\n",
            bank_resolutions, asset_resolutions);
}

void bm_content_clear(const uint8_t *rom) {
  if (owner != rom) return;
  report();
  free(backing);
  backing = NULL;
  owner = NULL;
}

void bm_content_load(uint8_t *rom, size_t size) {
  if (owner) bm_content_clear(owner);
  if (size != BM_CONTENT_ROM_SIZE ||
      !matches(rom, size, bm_content_rom_sha)) fail("ROM identity differs");
  if (BM_CONTENT_OFFSET > size || BM_CONTENT_SIZE > size - BM_CONTENT_OFFSET)
    fail("payload exceeds backing");
  for (size_t i = 0; i < BM_CONTENT_SIZE; ++i)
    if (rom[BM_CONTENT_OFFSET + i]) fail("ROM still contains payload bytes");

  const char *path = getenv("BM_NATIVE_CONTENT_PACK");
  if (!path || !*path) fail("BM_NATIVE_CONTENT_PACK is required");
  FILE *file = fopen(path, "rb");
  if (!file) fail("cannot open pack");
  uint8_t *payload = malloc(BM_CONTENT_SIZE);
  if (!payload) { fclose(file); fail("payload allocation failed"); }
  size_t count = fread(payload, 1, BM_CONTENT_SIZE, file);
  int extra = fgetc(file);
  int io_error = ferror(file);
  fclose(file);
  if (count != BM_CONTENT_SIZE || extra != EOF || io_error)
    fail("pack size differs");
  if (!matches(payload, BM_CONTENT_SIZE, bm_content_payload_sha))
    fail("pack SHA-256 differs");

  /* A full contiguous view preserves the runtime's pointer-span semantics.
   * Only the selected raw bank uses it. The ordinary bank retains the hole.
   * This deliberately trades PC memory for a bounded first data pilot. */
  backing = calloc(size + 1, 1);
  if (!backing) fail("backing allocation failed");
  memcpy(backing, rom, size);
  memcpy(backing + BM_CONTENT_OFFSET, payload, BM_CONTENT_SIZE);
  free(payload);
  owner = rom;
  bank_resolutions = asset_resolutions = 0;
  if (!registered) { atexit(report); registered = 1; }
  fprintf(stderr, "[native-content] mounted " BM_CONTENT_ID
          " bank=%02X payload_bytes=%u\n", BM_CONTENT_BANK, BM_CONTENT_SIZE);
}

uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address) {
  if (rom != owner || !backing || bank != BM_CONTENT_BANK || address < 0x8000)
    return NULL;
  size_t offset = ((size_t)(bank & 0x7f) << 15) | (address & 0x7fff);
  ++bank_resolutions;
  if (offset >= BM_CONTENT_OFFSET && offset - BM_CONTENT_OFFSET < BM_CONTENT_SIZE) {
    if (!asset_resolutions)
      fprintf(stderr, "[native-content] first_asset_resolution=%02X%04X\n", bank, address);
    ++asset_resolutions;
  }
  return backing + offset;
}
