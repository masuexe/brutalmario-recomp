#ifndef BM_NATIVE_CONTENT_H
#define BM_NATIVE_CONTENT_H
#include <stddef.h>
#include <stdint.h>

/* Native external content. Each region replaces a run of cartridge bytes
 * with a payload file. A region is identified by its bank and offset, so
 * every read path that already resolves through cart_getRomPtr sees the
 * external bytes without a code change. */
void bm_content_load(uint8_t *rom, size_t size);
void bm_content_clear(const uint8_t *rom);
uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address);
#endif
