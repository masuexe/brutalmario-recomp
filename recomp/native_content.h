#ifndef BM_NATIVE_CONTENT_H
#define BM_NATIVE_CONTENT_H
#include <stddef.h>
#include <stdint.h>

/* Isolated, fixed-bank data pilot. No executable-module switching. */
void bm_content_load(uint8_t *rom, size_t size);
void bm_content_clear(const uint8_t *rom);
uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address);
#endif
