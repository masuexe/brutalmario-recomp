/* HDMA cannot write VRAM during the visible field, even in H-blank.
 * Rejected bytes still advance VMAIN. Keep legacy CPU/DMA uploads working. */
#include <assert.h>
#include <stdio.h>
#include "ppu_test_stubs.h"

static Ppu p;

int main(void) {
    ppu_reset(&p);
    for (int high = 0; high < 2; ++high) {
        ppu_write(&p, 0x00, 0x0f);
        ppu_write(&p, 0x15, (high ? 0x80 : 0) | 1);
        p.vramPointer = 0x2000;
        p.vram[0x2000] = p.vram[0x2020] = 0xabcd;
        unsigned writes = p.vramWriteCount;
        g_ppu_wlog_src = kPpuWlogHdma;
        ppu_write(&p, 0x18, 0x12);
        assert(p.vramPointer == 0x2000 + (high ? 0 : 32));
        ppu_write(&p, 0x19, 0x34);
        assert(p.vramPointer == 0x2020);
        assert(p.vram[0x2000] == 0xabcd && p.vram[0x2020] == 0xabcd);
        assert(p.vramWriteCount == writes);
    }

    /* Forced blank permits the same HDMA port writes. */
    ppu_write(&p, 0x00, 0x80);
    ppu_write(&p, 0x15, 0x80);
    p.vramPointer = 0x2000;
    ppu_write(&p, 0x18, 0x12);
    ppu_write(&p, 0x19, 0x34);
    assert(p.vram[0x2000] == 0x3412 && p.vramPointer == 0x2001);

    /* Preserve accepted scripts that upload graphics outside blanking. */
    ppu_write(&p, 0x00, 0x0f);
    for (int src = kPpuWlogCpu; src <= kPpuWlogDma; ++src) {
        g_ppu_wlog_src = src;
        p.vramPointer = 0x2000;
        ppu_write(&p, 0x18, 0x56);
        ppu_write(&p, 0x19, 0x78);
        assert(p.vram[0x2000] == 0x7856 && p.vramPointer == 0x2001);
    }
    puts("HDMA VRAM rejection, port increment, forced blank and legacy uploads passed");
    return 0;
}
