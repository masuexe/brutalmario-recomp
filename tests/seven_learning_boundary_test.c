/* Run the official hurt/learning handler and its mapped copy with identical
 * seeded unit fixtures. This checks logic, not ordinary combat or audio parity. */
#define main unused_seven_parent_boundary
#include "seven_module_boundary_test.c"
#undef main

static Interp816 *run_hit(Bus *bus, const uint8_t *fixture, unsigned mapped,
                         unsigned seed, unsigned attack, unsigned learned) {
  Interp816 *cpu = fresh(bus);
  memcpy(bus->ram, fixture, 0x20000);
  cpu->k = cpu->db = mapped ? 0xa2 : 0x22;
  cpu->pc = 0x9beb; cpu->sp = 0x1fd; cpu->x = 9;
  bus->ram[0x1fe] = 0x8f; bus->ram[0x1ff] = 0xf0;
  bus->ram[0x71] = bus->ram[0x19] = bus->ram[0x9d] = 0;
  bus->ram[0x1497] = bus->ram[0x1490] = bus->ram[0x1493] = bus->ram[0x13e3] = 0;
  bus->ram[0x1ffa1] = bus->ram[0x1ffa8] = bus->ram[0x1ffa9] = 0;
  bus->ram[0x1ff15] = bus->ram[0x1ff17] = bus->ram[0x1ff33] = 0;
  bus->ram[0x1febf] = attack;
  memset(bus->ram+0x1fec0, 0, 0x20);
  if (learned) bus->ram[0x1fec0+learned] = 1;
  bus->ram[0xc12f] = 0;
  bus->ram[0x148b] = seed; bus->ram[0x148c] = seed ^ 0xa5;
  bus->ram[0x148d] = 0x11; bus->ram[0x148e] = 0x22;
  unsigned steps = 0;
  while (!(cpu->k == (mapped ? 0xa2 : 0x22) && cpu->pc == 0xf090) && steps++ < 100000)
    interp816_runOpcode(cpu);
  if (!(steps < 100000 && cpu->sp == 0x1ff && cpu->mf && cpu->xf))
    fprintf(stderr, "seed=%u mapped=%u steps=%u pc=%02X:%04X sp=%04X mf=%u xf=%u\n", seed, mapped, steps, cpu->k, cpu->pc, cpu->sp, cpu->mf, cpu->xf);
  assert(steps < 100000 && cpu->sp == 0x1ff && cpu->mf && cpu->xf);
  return cpu;
}

static unsigned classify(const Bus *bus, unsigned attack) {
  if (bus->ram[0x1fec0+attack]) return 0; /* Learned this attack's resistance. */
  if (bus->ram[0x1ff15]) return 1;       /* Learned a general defensive skill. */
  if (bus->ram[0x1ff17]) return 2;
  assert(bus->ram[0x71] == 9);
  return 3;                             /* No learning: normal small-Mario death. */
}

static void compare(Bus *source, Bus *mapped, Interp816 *a, Interp816 *b, unsigned outcome) {
  assert(a->db == 0x22 && b->db == 0xa2 && a->x == b->x && a->y == b->y);
  assert(a->c == b->c && a->z == b->z && a->n == b->n && a->v == b->v);
  if (outcome == 3) {
    /* The recipient intentionally retains its existing shorter death timer. */
    assert(a->a == 0x30 && b->a == 0x2e);
    assert(source->ram[0x9d] == 0x30 && mapped->ram[0x9d] == 0x2e);
    assert(source->ram[0x1496] == 0x30 && mapped->ram[0x1496] == 0x2e);
    source->ram[0x9d] = mapped->ram[0x9d];
    source->ram[0x1496] = mapped->ram[0x1496];
  } else assert(a->a == b->a);
  /* Only newly queued callbacks have intentionally rebased ROM-bank bytes. */
  assert(source->ram[0xc12f] == mapped->ram[0xc12f]);
  if (source->ram[0xc12f]) {
    /* 10:D8D0 saves the caller bank in its 24-bit inline-data pointer. */
    assert(source->ram[0x0e] == 0x22 && mapped->ram[0x0e] == 0xa2);
    source->ram[0x0e] = 0xa2;
  }
  for (unsigned i = 0; i < source->ram[0xc12f]; ++i) {
    unsigned at = 0xc134+i*8;
    assert(source->ram[at] == 0x22 && mapped->ram[at] == 0x22);
    assert(source->ram[at+3] == 0x22 && mapped->ram[at+3] == 0xa2);
    source->ram[at+3] = 0xa2;
  }
  memset(source->ram+0x1e0, 0, 0x20);
  memset(mapped->ram+0x1e0, 0, 0x20);
  unsigned differences = 0;
  for (unsigned i = 0; i < 0x20000; ++i) {
    if (source->ram[i] != mapped->ram[i]) {
      fprintf(stderr, "outcome=%u WRAM[%05X] source=%02X mapped=%02X\n",
              outcome, i, source->ram[i], mapped->ram[i]);
      ++differences;
    }
  }
  assert(!differences);
  assert(!memcmp(source->regs, mapped->regs, sizeof(source->regs)));
}

int main(int argc, char **argv) {
  assert(argc == 4);
  Bus *source = calloc(1, sizeof(*source)), *mapped = calloc(1, sizeof(*mapped));
  assert(source && mapped);
  source->rom = read_file(argv[1], 0x400000);
  mapped->rom = read_file(argv[2], 0x400000);
  uint8_t *fixture = read_file(argv[3], 0x20000);
  bm_content_load(mapped->rom, 0x400000);
  unsigned counts[4] = {0}, death_seed = 0;
  for (unsigned seed = 0; seed < 256; ++seed) {
    Interp816 *a = run_hit(source, fixture, 0, seed, 10, 0);
    Interp816 *b = run_hit(mapped, fixture, 1, seed, 10, 0);
    unsigned outcome = classify(source, 10);
    assert(classify(mapped, 10) == outcome);
    ++counts[outcome];
    if (outcome == 3) death_seed = seed;
    compare(source, mapped, a, b, outcome);
    interp816_free(a); interp816_free(b);
  }
  const unsigned expected[] = {32, 56, 63, 105};
  assert(!memcmp(counts, expected, sizeof(counts)));
  /* A learned attack is blocked without consuming RNG. A different unlearned
   * attack with the same failing seed still reaches the damage branch. */
  for (unsigned attack = 10; attack <= 11; ++attack) {
    Interp816 *a = run_hit(source, fixture, 0, death_seed, attack, 10);
    Interp816 *b = run_hit(mapped, fixture, 1, death_seed, attack, 10);
    if (attack == 10) {
      assert(source->ram[0x71] == 0 && mapped->ram[0x71] == 0);
      assert(source->ram[0x9d] == 0 && mapped->ram[0x9d] == 0);
      assert(source->ram[0x148b] == death_seed && mapped->ram[0x148b] == death_seed);
      assert(source->ram[0x148c] == (death_seed ^ 0xa5));
      assert(source->ram[0x148d] == 0x11 && source->ram[0x148e] == 0x22);
      compare(source, mapped, a, b, 0);
    } else {
      assert(classify(source, attack) == 3 && classify(mapped, attack) == 3);
      compare(source, mapped, a, b, 3);
    }
    interp816_free(a); interp816_free(b);
  }
  bm_content_clear(mapped->rom);
  printf("Seven learning: 258 paired cases; attack-resistance=%u defense-A=%u defense-B=%u no-learning=%u; specific immunity passed\n",
         counts[0], counts[1], counts[2], counts[3]);
  free(source->rom); free(mapped->rom); free(source); free(mapped); free(fixture);
  return 0;
}
