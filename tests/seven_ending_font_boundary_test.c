/* Execute the ending/death font wrapper through the actual scheduler and DMA. */
#define main unused_seven_parent_boundary
#include "seven_module_boundary_test.c"
#undef main

int main(int argc, char **argv) {
  assert(argc == 2);
  Bus *bus = calloc(1, sizeof(*bus));
  assert(bus);
  bus->rom = read_file(argv[1], 0x400000);
  bm_content_load(bus->rom, 0x400000);
  for (unsigned action = 0; action < 10; ++action) {
    Interp816 *cpu = fresh(bus);
    cpu->k = cpu->db = 0xa2; cpu->pc = 0xf060; cpu->sp = 0x1fd;
    bus->ram[0x1fe] = 0x8f; bus->ram[0x1ff] = 0xf0;
    bus->ram[0x71] = action;
    bus->ram[0x1ff34] = 1; /* Explicit dispatcher-return fixture. */
    unsigned steps = 0;
    while (!(cpu->k == 0xa2 && cpu->pc == 0xf090) && steps++ < 1000)
      interp816_runOpcode(cpu);
    assert(steps < 1000 && cpu->sp == 0x1ff);
    assert(bus->ram[0xc12f] == (action == 6 || action == 9));
    if (action == 6 || action == 9) {
      const uint8_t call[] = {0x22, 0xa0, 0xf0, 0xa2};
      assert(!memcmp(bus->ram+0xc134, call, 4));
      const uint8_t caller[] = {0x22, 0x30, 0xc1, 0x7e, 0xdb};
      memcpy(bus->caller, caller, sizeof(caller)); cpu->k = 0; cpu->pc = 0x8000;
      finish(cpu);
      assert(bus->dma_triggers == 1 && bus->regs[0x4322] == 0x7d);
      assert(bus->regs[0x4323] == 0xe2 && bus->regs[0x4324] == 0xa6);
      assert(bus->regs[0x4325] == 0 && bus->regs[0x4326] == 8);
    }
    interp816_free(cpu);
  }
  free(bus->rom); free(bus);
  puts("Font lifecycle: queues only pipe exit and death, actions 6 and 9");
  return 0;
}
