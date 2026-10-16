/* Counter reads retain independent selectors and PPU2 open-bus bits.
 * Reproduce the Demo 1-1 loop without a ROM, then round-trip its I/O state. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ppu_test_stubs.h"
#include "snes/saveload.h"

typedef struct Stream {
    SaveLoadInfo api;
    unsigned char data[0x20000];
    size_t at, size;
    int load;
} Stream;
static void transfer(SaveLoadInfo *api, void *data, size_t size) {
    Stream *s = (Stream *)api;
    assert(s->at + size <= (s->load ? s->size : sizeof(s->data)));
    if (s->load) memcpy(data, s->data + s->at, size);
    else { memcpy(s->data + s->at, data, size); s->size = s->at + size; }
    s->at += size;
}
static bool peek(SaveLoadInfo *api, size_t offset, void *data, size_t size) {
    Stream *s = (Stream *)api;
    if (s->at + offset + size > s->size) return false;
    memcpy(data, s->data + s->at + offset, size);
    return true;
}
static void latch(Ppu *p, Snes *s, unsigned v, unsigned h) {
    s->vPos = v; s->hPos = h;
    ppu_read(p, 0x37);
}
int main(void) {
    Snes snes = {0};
    Ppu *p = ppu_init(), *other = ppu_init();
    g_snes = &snes; snes.ppu = p; snes.ppuLatch = true;
    ppu_reset(p); ppu_reset(other);
    latch(p, &snes, 226, 400);
    assert(ppu_read(p, 0x3d) == 0xe2);
    assert(p->vCountSecond);
    /* SLHV at line 210 must keep the high-byte selector. Open bus retains E2,
     * so the game's unmasked CMP #E2 succeeds before actual line 226. */
    latch(p, &snes, 210, 404);
    assert(p->vCountSecond);
    assert(ppu_read(p, 0x3d) == 0xe2);
    assert(ppu_read(p, 0x3d) == 210);
    assert(ppu_read(p, 0x3c) == 101);
    latch(p, &snes, 257, 800);
    assert(p->hCountSecond && p->vCountSecond);
    assert(ppu_read(p, 0x3d) == 101); /* bit 0 from V8, bits 1..7 from H read */
    assert(ppu_read(p, 0x3c) == 100);
    assert(ppu_read(other, 0x3d) == 0); /* bus ownership */
    assert(ppu_read(p, 0x3d) == 1);
    snes.ppuLatch = false;
    latch(p, &snes, 55, 88);
    assert(p->vCount == 257 && p->hCount == 200 && p->vCountSecond);
    ppu_read(p, 0x3f);
    assert(!p->hCountSecond && !p->vCountSecond && p->countersLatched);
    snes.ppuLatch = true;
    ppu_read(p, 0x3f);
    assert(!p->countersLatched);

    latch(p, &snes, 226, 400);
    assert(ppu_read(p, 0x3d) == 0xe2);
    ppu_write(p, 0x21, 0);
    p->cgram[0] = 0x1234;
    assert(ppu_read(p, 0x3b) == 0x34);
    assert(ppu_read(p, 0x3b) == 0x12);
    assert(ppu_read(p, 0x3d) == 0x12); /* palette reads drive the same bus */
    ppu_read(p, 0x3d); /* E2; leave selector at high */
    Stream stream = {.api.func = transfer};
    ppu_saveload(p, &stream.api);
    size_t saved = stream.size;
    ppu_reset(p);
    stream.load = 1; stream.at = 0; stream.api.peek = peek;
    ppu_saveload(p, &stream.api);
    assert(stream.at == saved && p->vCountSecond && p->vCount == 226);
    latch(p, &snes, 210, 500);
    assert(ppu_read(p, 0x3d) == 0xe2);
    /* An old PPU0 chunk has no extension. Preserve the following chunk. */
    stream.at = 0; stream.size = saved - 16;
    ppu_saveload(p, &stream.api);
    assert(stream.at == stream.size && !p->vCountSecond && p->vCount == 0);
    assert(ppu_read(p, 0x3d) == 0);
    ppu_free(p); ppu_free(other);
    puts("counter latch: selectors, PPU2 open bus, gating, ownership and save compatibility");
    return 0;
}
