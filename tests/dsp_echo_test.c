#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "snes/dsp.h"
#include "snes/dsp_shadow.h"

DspShadow *dsp_shadow_create(void) { return NULL; }
void dsp_shadow_free(DspShadow *p) { (void)p; }
void dsp_shadow_process(DspShadow *s, Dsp *d, int l, int r, int *ol, int *or) {
    (void)s; (void)d; *ol = l; *or = r;
}
void audio_trace_on_sample(int16_t l, int16_t r, int drop, uint32_t fill) {
    (void)l; (void)r; (void)drop; (void)fill;
}
void audio_trace_on_reg_write(uint8_t a, uint8_t v) { (void)a; (void)v; }
void audio_trace_on_consume(uint64_t i, uint32_t n, uint32_t a) { (void)i; (void)n; (void)a; }

typedef struct {
    SaveLoadInfo info;
    unsigned char bytes[300000];
    size_t position, size;
    int loading;
} Stream;
static void transfer(SaveLoadInfo *info, void *data, size_t size) {
    Stream *s = (Stream*)info;
    assert(s->position + size <= sizeof(s->bytes));
    if (s->loading) {
        assert(s->position + size <= s->size);
        memcpy(data, s->bytes + s->position, size);
    } else {
        memcpy(s->bytes + s->position, data, size);
        s->size = s->position + size;
    }
    s->position += size;
}
static bool peek(SaveLoadInfo *info, size_t off, void *out, size_t size) {
    Stream *s = (Stream*)info;
    if (s->position + off + size > s->size) return false;
    memcpy(out, s->bytes + s->position + off, size); return true;
}
static Dsp *create(uint8_t *ram, int separate) {
    setenv("SNESRECOMP_SEPARATE_ECHO", separate ? "1" : "0", 1);
    Dsp *d = dsp_init(ram); assert(d); dsp_reset(d); return d;
}
static void wrap_echo(Dsp *d) {
    /* Reproduce the measured death transition: new ESA + old ring offset
     * wraps into the SPC engine around $0ac8. */
    dsp_write(d, 0x6c, 0);
    dsp_write(d, 0x6d, 0xef);
    dsp_write(d, 0x7d, 2);
    d->echoBufferIndex = 1778;
    d->echoRemain = 270;
    dsp_cycle(d);
}
int main(void) {
    static uint8_t shared[65536], isolated[65536];
    static Stream old, current;
    memset(shared, 0xa5, sizeof(shared)); memset(isolated, 0xa5, sizeof(isolated));
    Dsp *hardware = create(shared, 0), *compat = create(isolated, 1);
    wrap_echo(hardware); wrap_echo(compat);
    assert(shared[0xac8] != 0xa5); /* Default still models actual shared RAM. */
    for (size_t i = 0; i < sizeof(isolated); ++i) assert(isolated[i] == 0xa5);

    current.info.func = transfer;
    dsp_saveload(compat, &current.info);
    size_t plain_size = sizeof(Dsp) - offsetof(Dsp, ram);
    assert(current.size == plain_size + 8 + 65536);
    assert(memcmp(current.bytes + plain_size, "ECHO", 4) == 0);
    /* Known separate feedback samples, independent of CPU program RAM. */
    memset(current.bytes + plain_size + 8, 0x10, 65536);
    current.loading = 1; current.position = 0; current.info.peek = peek;
    dsp_saveload(compat, &current.info);
    compat->echoBufferAdr = 0; compat->echoBufferIndex = 0;
    dsp_cycle(compat);
    assert(compat->firBufferL[(compat->firBufferIndex - 1) & 7] == 0x808);
    assert(isolated[0] == 0xa5);

    old.info.func = transfer;
    dsp_saveload(hardware, &old.info);
    assert(old.size == plain_size);
    old.loading = 1; old.position = 0; old.info.peek = peek;
    dsp_saveload(compat, &old.info); /* Legacy state: no extra bytes consumed. */
    assert(old.position == plain_size);
    compat->echoBufferAdr = 0; compat->echoBufferIndex = 0;
    dsp_cycle(compat);
    assert(compat->firBufferL[(compat->firBufferIndex - 1) & 7] == 0);
    dsp_free(hardware); dsp_free(compat);
    puts("shared/default and isolated echo, wrapped writes and save history passed");
    return 0;
}
