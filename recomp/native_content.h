#ifndef BM_NATIVE_CONTENT_H
#define BM_NATIVE_CONTENT_H
#include <stddef.h>
#include <stdint.h>

/* Native external content.
 *
 * The sprite-gap runtime owns the cartridge map: it builds one backing copy
 * of the image and fills the mapped banks from their pack files. It exposes
 * bm_content_backing so a second provider can write into the same copy.
 *
 * A region provider replaces a run of cartridge bytes with bytes from a pack
 * file. It is identified by the image offset of the run, so every read path
 * that already resolves through cart_getRomPtr sees the external bytes. */
void bm_content_load(uint8_t *rom, size_t size);
void bm_content_clear(const uint8_t *rom);
uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address);
uint8_t *bm_content_backing(uint8_t *rom, size_t size);

void bm_region_load(uint8_t *rom, size_t size);
void bm_region_clear(const uint8_t *rom);
uint8_t *bm_region_resolve(const uint8_t *rom, uint8_t bank, uint16_t address);
#endif
