/* A selected row uses a temporary HDMA palette color, then restores it.
 * Exercise real pixel output, CPU uploads, half-written CGRAM, and replay. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ppu_test_stubs.h"

static Ppu p;
static Snes snes;
static uint32_t pixels[256 * 224];

static void color(unsigned line, unsigned index, unsigned value, uint8_t source) {
    snes.vPos = line;
    g_ppu_wlog_src = source;
    ppu_write(&p, 0x21, index);
    ppu_write(&p, 0x22, value);
    ppu_write(&p, 0x22, value >> 8);
    g_ppu_wlog_src = kPpuWlogCpu;
}

int main(void) {
    for (int renderer = 0; renderer <= 1; ++renderer) {
        memset(&p, 0, sizeof(p));
        memset(&snes, 0, sizeof(snes));
        g_snes = &snes; snes.ppu = &p;
        ppu_reset(&p); ppu_rasterReset();
        p.inidisp = 15;
        p.cgram[0] = 0x7c00;
        PpuBeginDrawing(&p, (uint8_t *)pixels, 256 * 4,
                        renderer ? kPpuRenderFlags_NewRenderer : 0);
        snes.vPos = 225;
        ppu_rasterBegin(&p);
        color(225, 0, 0x03e0, kPpuWlogDma); /* normal vblank upload */
        snes.vPos = 20;
        ppu_write(&p, 0x21, 1);
        ppu_write(&p, 0x22, 0x56); /* high byte arrives on the next line */
        snes.vPos = 21;
        ppu_write(&p, 0x22, 0x34);
        color(50, 0, 0x001f, kPpuWlogHdma);
        color(66, 0, 0x03e0, kPpuWlogHdma);
        snes.vPos = 225;
        ppu_rasterFieldBoundary();
        /* New-field writes must stay live without coloring the old picture. */
        color(225, 0, 0x7c00, kPpuWlogCpu);
        ppu_write(&p, 0x21, 2);
        ppu_write(&p, 0x22, 0x9a);
        uint16_t live[256];
        memcpy(live, p.cgram, sizeof(live));
        for (int replay = 0; replay < 3; ++replay) {
            ppu_rasterRenderBegin(&p);
            for (unsigned line = 1; line <= 224; ++line) {
                ppu_rasterApplyLine(&p, line - 1);
                if (line == 21) assert(p.cgram[1] == 0 && p.cgramSecondWrite);
                if (line == 22) assert(p.cgram[1] == 0x3456 && !p.cgramSecondWrite);
                ppu_runLine(&p, line);
                uint32_t expected = line >= 51 && line <= 66 ? 0xff0000 : 0x00ff00;
                for (unsigned x = 0; x < 256; ++x)
                    assert((pixels[(line - 1) * 256 + x] & 0xffffff) == expected);
            }
            ppu_rasterRenderEnd(&p);
            assert(!memcmp(live, p.cgram, sizeof(live)));
            assert(p.cgramPointer == 2 && p.cgramBuffer == 0x9a && p.cgramSecondWrite);
        }
        for (int idle = 0; idle < 3; ++idle) {
            ppu_rasterFieldBoundary();
            ppu_rasterRenderBegin(&p);
            ppu_rasterApplyLine(&p, 223);
            assert(p.cgram[0] == 0x7c00);
            ppu_rasterRenderEnd(&p);
            assert(!memcmp(live, p.cgram, sizeof(live)));
            assert(p.cgramPointer == 2 && p.cgramSecondWrite);
        }
    }
    puts("palette raster: both renderers, temporary color, CPU DMA, port latches and repeated replay");
    return 0;
}
