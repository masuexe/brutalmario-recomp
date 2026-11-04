/* External sprite graphics packs.
 *
 * Each pack holds reviewed VRAM ranges. The runtime writes the ranges when
 * the game enters a room that the pack names. The pack file and the manifest
 * pin a size and a SHA-256; a mismatch stops the process. */
#include "native_content.h"
#include "native_sprite_graphics_manifest.h"
#include "sha256.h"
#include "snes.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Snes *g_snes;
extern int snes_frame_counter;

#if BM_SPRITE_GRAPHICS_PACKS > 0
typedef struct {
  uint8_t *payload;
  unsigned ranges;
  int last_room;
} BmSpriteGraphicsState;

static BmSpriteGraphicsState state[BM_SPRITE_GRAPHICS_PACKS];
static int mounted, registered;
static unsigned long long applied;
#endif

static void fail(const char *reason) {
  fprintf(stderr, "[native-sprite-gfx] rejected: %s\n", reason);
  exit(EXIT_FAILURE);
}

#if BM_SPRITE_GRAPHICS_PACKS > 0
static int matches(const uint8_t *data, size_t size, const uint8_t expected[32]) {
  uint8_t actual[32];
  sha256_compute(data, size, actual);
  return memcmp(actual, expected, 32) == 0;
}

static void report(void) {
  if (mounted)
    fprintf(stderr, "[native-sprite-gfx] applied=%llu\n", applied);
}

static unsigned read16(const uint8_t *data, size_t at) {
  return (unsigned)data[at] | ((unsigned)data[at + 1] << 8);
}

static unsigned read32(const uint8_t *data, size_t at) {
  return (unsigned)data[at] | ((unsigned)data[at + 1] << 8) |
         ((unsigned)data[at + 2] << 16) | ((unsigned)data[at + 3] << 24);
}

static void load_pack(unsigned index) {
  const BmSpriteGraphicsPack *pin = &bm_sprite_graphics_packs[index];
  if (state[index].payload) return;
  const char *path = getenv(pin->variable);
  if (!path || !*path) fail("sprite graphics pack variable is missing");
  FILE *file = fopen(path, "rb");
  if (!file) fail("cannot open sprite graphics pack");
  uint8_t *data = malloc(pin->size ? pin->size : 1);
  if (!data) { fclose(file); fail("sprite graphics allocation failed"); }
  size_t count = fread(data, 1, pin->size, file);
  int extra = fgetc(file), error = ferror(file);
  fclose(file);
  if (count != pin->size || extra != EOF || error) fail("sprite graphics pack size differs");
  if (!matches(data, pin->size, pin->sha256)) fail("sprite graphics pack SHA-256 differs");
  if (pin->size < 4) fail("sprite graphics pack holds no table");
  unsigned ranges = read32(data, 0);
  size_t cursor = 4;
  for (unsigned i = 0; i < ranges; ++i) {
    if (cursor + 4 > pin->size) fail("sprite graphics range header exceeds the pack");
    unsigned address = read16(data, cursor), words = read16(data, cursor + 2);
    cursor += 4;
    if (address + words > 0x8000) fail("sprite graphics range exceeds VRAM");
    if (cursor + (size_t)words * 2 > pin->size) fail("sprite graphics range exceeds the pack");
    cursor += (size_t)words * 2;
  }
  if (cursor != pin->size) fail("sprite graphics pack holds trailing bytes");
  state[index].payload = data;
  state[index].ranges = ranges;
  state[index].last_room = -1;
}

static void apply_pack(unsigned index, unsigned room) {
  BmSpriteGraphicsState *slot = &state[index];
  const uint8_t *data = slot->payload;
  size_t cursor = 4;
  for (unsigned i = 0; i < slot->ranges; ++i) {
    unsigned address = read16(data, cursor), words = read16(data, cursor + 2);
    cursor += 4;
    for (unsigned k = 0; k < words; ++k) {
      g_snes->ppu->vram[(address + k) & 0x7fff] = (uint16_t)read16(data, cursor);
      cursor += 2;
    }
  }
}

void bm_sprite_graphics_mount(void) {
  for (unsigned i = 0; i < BM_SPRITE_GRAPHICS_PACKS; ++i) load_pack(i);
  mounted = 1;
  if (!registered) { atexit(report); registered = 1; }
  fprintf(stderr, "[native-sprite-gfx] mounted packs=%u\n",
          (unsigned)BM_SPRITE_GRAPHICS_PACKS);
}

void bm_sprite_graphics_tick(void) {
  static int last_frame = -1;
  if (!mounted || snes_frame_counter == last_frame) return;
  last_frame = snes_frame_counter;
  if (!g_snes || !g_snes->ram || !g_snes->ppu) return;
  if (g_snes->ram[0x100] != 0x14) return;
  unsigned room = (unsigned)g_snes->ram[0x10b] | ((unsigned)g_snes->ram[0x10c] << 8);
  for (unsigned i = 0; i < BM_SPRITE_GRAPHICS_PACKS; ++i) {
    if (!state[i].payload) continue;
    int wanted = (bm_sprite_graphics_packs[i].rooms[room >> 3] >> (room & 7)) & 1;
    if (!wanted) { state[i].last_room = -1; continue; }
    if (state[i].last_room == (int)room) continue;
    apply_pack(i, room);
    state[i].last_room = (int)room;
    ++applied;
  }
}
#else
void bm_sprite_graphics_mount(void) {}
void bm_sprite_graphics_tick(void) {}
#endif
