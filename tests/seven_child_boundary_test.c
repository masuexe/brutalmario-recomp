/* Reuse the frozen parent boundary fixture, then compare actual official child
 * bytes with the mapped child on the same explicit WRAM fixture. No DMA/PPU
 * simulation or ordinary gameplay traversal is claimed by this test bus. */
#define main parent_boundary_main
#include "seven_module_boundary_test.c"
#undef main

static void normalize_child_id(uint8_t *ram) {
  for (unsigned slot = 0; slot < 12; ++slot) {
    if (!(ram[0x1ab10 + slot] & 8)) continue;
    if (ram[0x1ab9e + slot] == 0xe0) ram[0x1ab9e + slot] = 0x6a;
  }
  /* JSL pushes the mapped bank. These popped stack bytes are not live state. */
  memset(ram+0x1e0, 0, 0x20);
}

static Interp816 *child_case(Bus *bus, const uint8_t *fixture, unsigned native,
                            unsigned init, unsigned phase, unsigned timer) {
  Interp816 *cpu = fresh(bus);
  memcpy(bus->ram, fixture, 0x20000);
  for (unsigned slot = 0; slot < 12; ++slot) {
    if (native && bus->ram[0x1ab9e + slot] == 0x6a && bus->ram[0x1ab10 + slot] & 8) {
      bus->ram[0x1ab9e + slot] = 0xe0;
    }
  }
  cpu->x = 6;
  bus->ram[0x15e9] = 6;
  bus->ram[0xc2+6] = phase;
  bus->ram[0x15ac+6] = timer;
  if (init) bus->ram[0x1ab10+6] = init == 2 ? 0x8c : 0x88;
  const uint8_t caller[] = {0x22, init ? 0x1d : 0x65, 0xc2, native ? 0x9e : 0x1e, 0xdb};
  memcpy(bus->caller, caller, sizeof(caller));
  finish(cpu);
  return cpu;
}

int main(int argc, char **argv) {
  assert(argc == 6);
  parent_boundary_main(4, argv);
  Bus *native = calloc(1, sizeof(*native)), *source = calloc(1, sizeof(*source));
  assert(native && source);
  native->rom = read_file(argv[1], 0x400000);
  source->rom = read_file(argv[4], 0x400000);
  uint8_t *fixture = read_file(argv[5], 0x20000);
  bm_content_load(native->rom, 0x400000);
  assert(bm_content_resolve(native->rom, 0x1e, 0xc21d) == NULL);
  assert(bm_content_resolve(native->rom, 0x9e, 0x1fff) == NULL);
  /* The namespace adapter changes only the custom ID and preserves A/P. */
  Interp816 *adapter = fresh(native);
  adapter->k = adapter->db = 0xa2; adapter->pc = 0xf040;
  adapter->x = 6; adapter->a = 0x6a; adapter->c = true;
  adapter->sp = 0x1fd;
  native->ram[0x1fe] = 0x8f; native->ram[0x1ff] = 0xf0;
  native->ram[0x9e + 6] = 0x6a;
  unsigned steps = 0;
  while (!(adapter->k == 0xa2 && adapter->pc == 0xf090) && steps++ < 100)
    interp816_runOpcode(adapter);
  assert(steps < 100 && adapter->sp == 0x1ff && adapter->a == 0x6a && adapter->c);
  assert(adapter->mf && adapter->xf && !adapter->z && !adapter->n);
  assert(native->ram[0x9e + 6] == 0x6a && native->ram[0x1ab9e + 6] == 0xe0);
  interp816_free(adapter);
  /* While dying, the wrapper queues an English-font callback through the real
   * scheduler. Execute the copied callback and check the guest DMA program. */
  Interp816 *lifecycle = fresh(native);
  lifecycle->k = lifecycle->db = 0xa2; lifecycle->pc = 0xf060;
  lifecycle->sp = 0x1fd;
  native->ram[0x1fe] = 0x8f; native->ram[0x1ff] = 0xf0;
  native->ram[0x71] = 9;
  native->ram[0x1ff34] = 1; /* Explicit text-state fixture: original dispatcher returns. */
  steps = 0;
  while (!(lifecycle->k == 0xa2 && lifecycle->pc == 0xf090) && steps++ < 1000)
    interp816_runOpcode(lifecycle);
  assert(steps < 1000 && lifecycle->sp == 0x1ff && native->ram[0xc12f] == 1);
  const uint8_t expected_call[] = {0x22, 0xa0, 0xf0, 0xa2};
  assert(!memcmp(native->ram+0xc134, expected_call, 4));
  const uint8_t caller[] = {0x22, 0x30, 0xc1, 0x7e, 0xdb};
  memcpy(native->caller, caller, sizeof(caller));
  lifecycle->k = 0; lifecycle->pc = 0x8000;
  finish(lifecycle);
  assert(native->dma_triggers == 1);
  assert(native->regs[0x4322] == 0x7d && native->regs[0x4323] == 0xe2);
  assert(native->regs[0x4324] == 0xa6 && native->regs[0x4325] == 0 && native->regs[0x4326] == 8);
  interp816_free(lifecycle);
  unsigned pairs = 0;
  for (unsigned test = 0; test < 14; ++test) {
    unsigned init = test < 2 ? test+1 : 0;
    unsigned phase = init ? 0x15 : 0x10+(test-2)/2;
    unsigned timer = test & 1 ? 0x40 : 0;
    Interp816 *a = child_case(source, fixture, 0, init, phase, timer);
    Interp816 *b = child_case(native, fixture, 1, init, phase, timer);
    assert(a->a == b->a && a->x == b->x && a->y == b->y && a->db == b->db);
    assert(a->mf == b->mf && a->xf == b->xf && a->c == b->c && a->z == b->z);
    assert(a->n == b->n && a->v == b->v && a->sp == b->sp);
    normalize_child_id(source->ram);
    normalize_child_id(native->ram);
    for (unsigned i = 0; i < 0x20000; ++i) {
      if (source->ram[i] != native->ram[i]) {
        fprintf(stderr, "case=%u phase=%02X WRAM[%05X] source=%02X native=%02X\n",
                test, phase, i, source->ram[i], native->ram[i]);
        abort();
      }
    }
    assert(!memcmp(source->regs, native->regs, sizeof(source->regs)));
    interp816_free(a); interp816_free(b);
    ++pairs;
  }
  bm_content_clear(native->rom);
  free(native->rom); free(source->rom); free(native); free(source); free(fixture);
  printf("Seven child: %u donor pairs match after custom-ID/dead-stack normalization; normal ID preserved\n", pairs);
  return 0;
}
