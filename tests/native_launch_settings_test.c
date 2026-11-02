/* Synthetic content isolates launch settings and counts environment queries.
 * Gameplay assertions use the actual project resolver and its WRAM hooks. */
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
static unsigned queries;
static const char *yoshi, *seven, *node, *pack_path;
static char *test_getenv(const char *name) {
  ++queries;
  if (!strcmp(name, "BM_YOSHI_START")) return (char *)yoshi;
  if (!strcmp(name, "BM_SEVEN_RETURN")) return (char *)seven;
  if (!strcmp(name, "BM_MAZO_190_NODE")) return (char *)node;
  if (!strcmp(name, "TEST_PACK")) return (char *)pack_path;
  return NULL;
}
#define getenv test_getenv
#include "../recomp/native_seven.c"
#undef getenv

/* The synthetic manifest has zero digests; no real assets are qualified here. */
void sha256_compute(const uint8_t *data, size_t size, uint8_t out[32]) {
  (void)data; (void)size; memset(out, 0, 32);
}
uint64_t interp816_page_insns(unsigned page) { (void)page; return 0; }

static void resolve(uint8_t *rom) {
  assert(bm_content_resolve(rom, 0, 0x8000) == NULL);
}
static void check(uint8_t *rom, int start_on, int return_on, int node_on) {
  unsigned loaded_queries = queries;
  for (unsigned i = 0; i < 10000; ++i) resolve(rom);
  assert(queries == loaded_queries);
  memset(g_ram, 0, sizeof(g_ram));
  s_yoshi_start_done = s_seven_return_done = 0;
  g_ram[0x100] = 0x0e;
  g_ram[0x1f17] = 72;
  g_ram[0x1f19] = 0x98; g_ram[0x1f1a] = 1; /* Y=408 */
  resolve(rom);
  assert(g_ram[0x1f17] == (start_on ? 104 : 72));
  assert(g_ram[0xd1f0] == (node_on ? 0xb4 : 0));
  g_ram[0x100] = 0x14;
  g_ram[0x10b] = 0x74; g_ram[0x10c] = 1;
  resolve(rom);
  assert(g_ram[0x100] == (return_on ? 0x0b : 0x14));
  assert(queries == loaded_queries);
}
int main(int argc, char **argv) {
  assert(argc == 2); pack_path = argv[1];
  uint8_t *rom = calloc(BM_SEVEN_ROM_SIZE, 1); assert(rom);
  bm_content_load(rom, BM_SEVEN_ROM_SIZE);
  check(rom, 1, 1, 0);
  /* Environment mutations cannot affect an already loaded session. */
  yoshi = seven = "0"; node = "1";
  check(rom, 1, 1, 0);
  bm_content_load(rom, BM_SEVEN_ROM_SIZE);
  check(rom, 0, 0, 1);
  /* Preserve the existing exact-string option semantics. */
  yoshi = seven = "00"; node = "10";
  bm_content_load(rom, BM_SEVEN_ROM_SIZE);
  check(rom, 1, 1, 0);
  bm_content_clear(rom); free(rom);
  return 0;
}
