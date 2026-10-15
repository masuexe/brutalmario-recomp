/* ROM-free regression for visible-line-only scanout and MOSAIC changes.
 * Tile pixels are an analytic two-dimensional pattern, not game assets. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ppu_test_stubs.h"

static Ppu p;
static uint32_t pixels[224 * 256];

static unsigned index_at(int x, int y, int depth) {
    return 1 + ((x & 7) + 2 * (y & 7)) % ((1 << depth) - 1);
}

static uint32_t rgb(unsigned index) {
    unsigned c = p.cgram[index];
    unsigned r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    return (((r << 3) | (r >> 2)) << 16) |
           (((g << 3) | (g >> 2)) << 8) | ((b << 3) | (b >> 2));
}

static void setup(int depth, int optimized) {
    memset(&p, 0, sizeof(p));
    ppu_reset(&p);
    p.inidisp = 15;
    p.bgmode = depth == 4 ? 1 : 0;
    p.bgTileAdr = 1;
    p.screenEnabled[0] = 1;
    for (int i = 0; i < 0x400; ++i) p.vram[i] = 1;
    for (int c = 1; c < 16; ++c) p.cgram[c] = c | ((15 - c) << 5) | ((2 * c) << 10);
    for (int y = 0; y < 8; ++y) {
        for (int x = 0; x < 8; ++x) {
            unsigned c = index_at(x, y, depth);
            for (int bit = 0; bit < depth; ++bit) {
                unsigned address = 0x1000 + depth * 4 + y + (bit / 2) * 8;
                p.vram[address] |= ((c >> bit) & 1) << (7 - x + (bit & 1) * 8);
            }
        }
    }
    memset(pixels, 0, sizeof(pixels));
    PpuBeginDrawing(&p, (uint8_t *)pixels, 256 * 4,
                    optimized ? kPpuRenderFlags_NewRenderer : 0);
}

static void check_line(int line, int size, int depth, int enabled) {
    ppu_runLine(&p, line);
    for (int x = 0; x < 256; ++x) {
        int sx = enabled ? x - x % size : x;
        int sy = enabled ? line - line % size : line;
        uint32_t expected = rgb(index_at(sx, sy, depth));
        uint32_t actual = pixels[(line - 1) * 256 + x] & 0xffffff;
        if (actual != expected) {
            fprintf(stderr, "mosaic depth=%d flags=%u size=%d line=%d x=%d: got %06x expected %06x\n",
                    depth, p.renderFlags, size, line, x, actual, expected);
            exit(1);
        }
    }
}

int main(void) {
    for (int optimized = 0; optimized <= 1; ++optimized) {
        for (int depth = 2; depth <= 4; depth += 2) {
            for (int size = 1; size <= 16; ++size) {
                setup(depth, optimized);
                ppu_write(&p, 6, (uint8_t)(((size - 1) << 4) | 1));
                /* Same entry convention as the beam driver: no line 0. */
                for (int line = 1; line <= 224; ++line) check_line(line, size, depth, 1);
            }
            setup(depth, optimized);
            for (int line = 1; line <= 224; ++line) {
                int size = 1 + ((line / 13) % 16);
                ppu_write(&p, 6, (uint8_t)(((size - 1) << 4) | 1));
                check_line(line, size, depth, 1);
            }
            /* Disabling MOSAIC must immediately restore ordinary scanout. */
            ppu_write(&p, 6, 0);
            check_line(1, 1, depth, 0);
        }
    }
    puts("mosaic: 2bpp/4bpp, both renderers, sizes 1..16, visible-only scanout and size changes passed");
    return 0;
}
