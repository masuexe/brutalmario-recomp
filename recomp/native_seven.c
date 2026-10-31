/* Immutable cumulative module views. A2/A6 are independent of 22/26; A5/B6
 * retain the preceding qualified content. No room/PC-dependent bank swapping. */
#include "native_content.h"
#include "native_seven_manifest.h"
#include "sha256.h"
#include "snes/interp816.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Weak WRAM binding: the full runner provides the strong g_ram; isolated
 * boundary-test links get a zeroed array so the override is inert. */
__attribute__((weak)) uint8_t g_ram[0x20000];
/* Room-scoped native music adaptation (native-content policy): room 0x190 has
 * no music object of its own and inherits the shared default slot 0x02. Force
 * recipient slot 0x9E whenever the game is in room 0x190. */
static int s_music_room = -1;
static void bm_mazo_map_node_override(void) {
  if (!getenv("BM_MAZO_190_NODE")) return;
  if (g_ram[0x100] != 0x0e || g_ram[0x1f11] != 0) return;
  g_ram[0xd1f0] = 0xb4;
}
static void bm_room_music_override(void) {
  int room = g_ram[0x10b] | (g_ram[0x10c] << 8);
  if (room == 0x190) {
    if (s_music_room != 0x190 || g_ram[0x0dda] != 0x9e) {
      g_ram[0x0dda] = 0x9e;
      g_ram[0x1dfb] = 0x9e;
    }
  }
  s_music_room = room;
}

static const uint8_t *owner;
static uint8_t *backing;
static unsigned long long resolutions[BM_SEVEN_PACKS];
static int registered;

static void fail(const char *reason) {
  fprintf(stderr, "[native-seven] rejected: %s\n", reason);
  exit(EXIT_FAILURE);
}

static int matches(const uint8_t *data, size_t size, const uint8_t expected[32]) {
  uint8_t actual[32];
  sha256_compute(data, size, actual);
  return memcmp(actual, expected, 32) == 0;
}

static void report(void) {
  if (!backing) return;
  for (unsigned i = 0; i < BM_SEVEN_PACKS; ++i) {
    const BmSevenPack *pack = &bm_seven_packs[i];
    unsigned long long instructions = 0;
    if (pack->executable)
      for (unsigned page = pack->first_page; page <= pack->last_page; ++page)
        instructions += interp816_page_insns(page);
    fprintf(stderr, "[native-seven] bank=%02X resolutions=%llu executed_page_instructions=%llu\n",
            pack->bank, resolutions[i], instructions);
  }
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
  if (size != BM_SEVEN_ROM_SIZE || !matches(rom, size, bm_seven_rom_sha))
    fail("ROM identity differs");
  backing = calloc(size+1, 1);
  if (!backing) fail("backing allocation failed");
  memcpy(backing, rom, size);
  for (unsigned i = 0; i < BM_SEVEN_PACKS; ++i) {
    const BmSevenPack *pack = &bm_seven_packs[i];
    if (pack->offset > size || pack->size > size-pack->offset ||
        pack->size > 0x8000-(pack->offset & 0x7fff)) fail("pack mapping exceeds bank");
    for (unsigned previous = 0; previous < i; ++previous)
      if (bm_seven_packs[previous].bank == pack->bank) fail("duplicate mapped bank");
    const char *path = getenv(pack->variable);
    if (!path || !*path) fail(pack->variable);
    FILE *file = fopen(path, "rb");
    if (!file) fail("cannot open pack");
    size_t count = fread(backing+pack->offset, 1, pack->size, file);
    int extra = fgetc(file), error = ferror(file);
    fclose(file);
    if (count != pack->size || extra != EOF || error) fail("pack size differs");
    if (!matches(backing+pack->offset, pack->size, pack->sha256)) fail("pack SHA-256 differs");
    resolutions[i] = 0;
  }
  owner = rom;
  if (!registered) { atexit(report); registered = 1; }
  fprintf(stderr, "[native-seven] mounted immutable A2/A5/A6/B6 views\n");
}

uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address) {
  bm_mazo_map_node_override();
  bm_room_music_override();
  if (rom != owner || !backing || address < 0x8000) return NULL;
  for (unsigned i = 0; i < BM_SEVEN_PACKS; ++i) {
    const BmSevenPack *pack = &bm_seven_packs[i];
    if (bank != pack->bank) continue;
    size_t offset = ((size_t)(bank & 0x7f) << 15) | (address & 0x7fff);
    if (offset >= pack->offset && offset-pack->offset < pack->size) ++resolutions[i];
    return backing+offset;
  }
  return NULL;
}
