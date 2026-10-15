/* A line-224 write is too late for the completed field's visible scanout,
 * but is already live guest state. It must survive that field's replay. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ppu_test_stubs.h"

#define CHECK(condition) do { if (!(condition)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #condition); exit(1); \
} } while (0)

static Ppu p;
static Snes snes;

int main(void) {
    memset(&p, 0, sizeof(p));
    memset(&snes, 0, sizeof(snes));
    ppu_reset(&p);
    g_snes = &snes;
    snes.ppu = &p;
    snes.vPos = 225;
    ppu_write(&p, 0x2c, 0x15);
    ppu_rasterBegin(&p);

    /* Last visible line: only affects next field's picture. */
    snes.vPos = 224;
    ppu_write(&p, 0x2c, 0x10);
    ppu_write(&p, 0x2d, 0x04);
    snes.vPos = 225;
    ppu_rasterFieldBoundary();
    /* There are no writes in the new field's journal. */
    p.scrollPrev = 0x12;
    p.scrollPrev2 = 0x34;
    p.m7prev = 0x56;
    p.oamAdr = 0x41;
    p.oamSecondWrite = true;
    uint8_t live[PPU_SAVESTATE_REGS_SIZE];
    memcpy(live, &p.inidisp, sizeof(live));

    ppu_rasterRenderBegin(&p);
    ppu_rasterApplyLine(&p, 223);
    CHECK(p.screenEnabled[0] == 0x15); /* completed field, not new state */
    ppu_rasterRenderEnd(&p);
    CHECK(p.screenEnabled[0] == 0x10 && p.screenEnabled[1] == 0x04);
    CHECK(!memcmp(live, &p.inidisp, sizeof(live)));
    CHECK(p.scrollPrev == 0x12 && p.scrollPrev2 == 0x34 && p.m7prev == 0x56);
    CHECK(p.oamAdr == 0x41 && p.oamSecondWrite);

    /* Idle fields must not alternate between the two screen-enable values. */
    for (int frame = 0; frame < 8; ++frame) {
        ppu_rasterFieldBoundary();
        ppu_rasterRenderBegin(&p);
        ppu_rasterApplyLine(&p, 223);
        CHECK(p.screenEnabled[0] == 0x10 && p.screenEnabled[1] == 0x04);
        ppu_rasterRenderEnd(&p);
        CHECK(!memcmp(live, &p.inidisp, sizeof(live)));
    }
    puts("raster: late writes, idle fields, complete register file, latches and OAM port preserved");
    return 0;
}
