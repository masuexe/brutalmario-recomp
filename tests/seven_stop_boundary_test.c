/* Execute the recipient driver dispatch: 80 stops, FF selects an upload. */
#define main unused_seven_parent_boundary
#include "seven_module_boundary_test.c"
#undef main

static unsigned cartridge_writes;
static void stop_write_bus(void *context, uint32_t address, uint8_t value) {
  /* The driver's STX $C110 with DB=00 targets read-only cartridge space.
   * Model that hardware write as ignored, rather than aliasing it to WRAM. */
  if (address == 0xc110) {
    assert(value == 0);
    ++cartridge_writes;
  } else write_bus(context, address, value);
}

int main(int argc, char **argv) {
  assert(argc == 2);
  Bus *bus = calloc(1, sizeof(*bus));
  assert(bus);
  bus->rom = read_file(argv[1], 0x400000);
  for (unsigned request = 0x80; request <= 0xff; request += 0x7f) {
    Interp816 *cpu = fresh(bus);
    cpu->write = stop_write_bus;
    cpu->k = 0x0f; cpu->pc = 0xc0d0; cpu->a = request;
    bus->ram[0xc110] = 0xac;
    bus->ram[0x1dfb] = bus->ram[0x1dff] = request;
    unsigned steps = 0;
    while (!((cpu->k == 0 && cpu->pc == 0x818f) ||
             (cpu->k == 0x0f && cpu->pc == 0xc0ee)) && steps++ < 100)
      interp816_runOpcode(cpu);
    assert(steps < 100);
    if (request == 0x80) {
      assert(cpu->k == 0 && cpu->pc == 0x818f);
      assert(cartridge_writes == 1 && bus->ram[0xc110] == 0xac);
      assert(!bus->ram[0x1dfb] && bus->ram[0x1dff] == 0x80);
      assert(bus->regs[0x2142] == 0x80 && !bus->regs[0x2141] && !bus->regs[0x4200]);
    } else {
      assert(cpu->k == 0x0f && cpu->pc == 0xc0ee && cpu->a == 0xff);
    }
    interp816_free(cpu);
  }
  free(bus->rom); free(bus);
  puts("Modern music dispatch: 80 stops without upload; FF reaches the song-upload branch");
  return 0;
}
