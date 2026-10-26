/* Compare actual official checkpoint code with a scoped native continuation. */
#define main unused_seven_parent_boundary
#include "seven_module_boundary_test.c"
#undef main

static unsigned rom_offset(unsigned address) {
  return (((address >> 16) & 0x7f) << 15) | (address & 0x7fff);
}

static Interp816 *checkpoint(Bus *bus, unsigned room, unsigned tile, unsigned count) {
  Interp816 *cpu = fresh(bus);
  cpu->y = tile; cpu->x = 6;
  bus->ram[0x10b] = room; bus->ram[0x10c] = room >> 8;
  bus->ram[0x1421] = count; bus->ram[0x13bf] = 0x6a;
  bus->ram[0x94] = 0x60; bus->ram[0x95] = 2;
  bus->ram[0x96] = 0x60; bus->ram[0x97] = 1;
  const uint8_t caller[] = {0x20,0x8c,0xf2,0xdb};
  memcpy(bus->caller,caller,sizeof(caller));
  finish(cpu);
  return cpu;
}

int main(int argc, char **argv) {
  assert(argc == 4);
  Bus *source = calloc(1,sizeof(*source)), *native = calloc(1,sizeof(*native));
  assert(source && native);
  uint8_t *donor = read_file(argv[1],0x400000);
  uint8_t *parent = read_file(argv[2],0x400000);
  source->rom = donor; native->rom = read_file(argv[3],0x400000);
  bm_content_load(native->rom,0x400000);
  const unsigned rooms[] = {0x17b,0x174,0xff,0x7b,0x1ff};
  unsigned cases = 0, spawns = 0;
  for (unsigned r = 0; r < 5; ++r)
    for (unsigned tile = 0x6f; tile <= 0x72; ++tile)
      for (unsigned count = 0; count <= 5; ++count) {
        source->rom = rooms[r] == 0x17b ? donor : parent;
        Interp816 *a = checkpoint(source,rooms[r],tile,count);
        Interp816 *b = checkpoint(native,rooms[r],tile,count);
        assert(a->a == b->a && a->x == b->x && a->y == b->y && a->db == b->db);
        assert(a->sp == b->sp && a->dp == b->dp && a->k == b->k && a->pc == b->pc);
        assert(interp816_getFlags(a) == interp816_getFlags(b));
        /* Discarded stack bytes differ because the room guard saves A/P. */
        memset(source->ram+0x100,0,0x100); memset(native->ram+0x100,0,0x100);
        /* The sprite-property table at $07F4C7 comes from each image's own sprite
         * database. Sprite $78 is $C2 in the official Boss image and $D2 in the
         * recipient. Both bytes are that sprite's property; keep the recipient
         * value in the native run and normalize the reviewed byte only here. */
        if (rooms[r] == 0x17b && tile == 0x72 && count == 3) {
          assert(source->ram[0x1685] == donor[rom_offset(0x07f4c7)+0x78]);
          assert(native->ram[0x1685] == native->rom[rom_offset(0x07f4c7)+0x78]);
          assert(source->ram[0x1685] == 0xc2 && native->ram[0x1685] == 0xd2);
          source->ram[0x1685] = native->ram[0x1685];
        }
        if (memcmp(source->ram,native->ram,sizeof(source->ram))) {
          fprintf(stderr,"case room=%03X tile=%02X count=%u\n",rooms[r],tile,count);
          for (unsigned j=0;j<sizeof(source->ram);++j)
            if (source->ram[j]!=native->ram[j]) fprintf(stderr,"%05X: %02X %02X\n",j,source->ram[j],native->ram[j]);
        }
        assert(!memcmp(source->ram,native->ram,sizeof(source->ram)));
        assert(!memcmp(source->regs,native->regs,sizeof(source->regs)));
        if (rooms[r] == 0x17b && tile == 0x72 && count == 3) {
          assert(native->ram[0x1421] == 4 && native->ram[0x14c8+11] == 8);
          assert(native->ram[0x9e + 11] == 0x78 && native->ram[0x154c+11] == 0x10);
          assert(native->ram[0xe4+11] == 0x60 && native->ram[0x14e0+11] == 2);
          assert(native->ram[0xd8+11] == 0x60 && native->ram[0x14d4+11] == 1);
          ++spawns;
        }
        interp816_free(a); interp816_free(b); ++cases;
      }
  assert(spawns == 1);
  free(donor); free(parent); free(native->rom); free(source); free(native);
  printf("Hidden mushroom: %u paired checkpoint cases; original green sprite 78 spawn verified\n",cases);
  return 0;
}
