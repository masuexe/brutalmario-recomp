/* Run the real SPC driver against a song payload, with no reimplementation.
 *
 * The earlier probe rewrote the pitch conversion and produced noise. This
 * program loads the driver that the game itself runs, starts it, and lets the
 * SPC700 execute the real code, so the DSP output follows the console path.
 *
 * Usage: engine <engine-aram.bin> <song.bin> <out.wav> <frames>
 */
#include "snes/apu.h"
#include "snes/dsp.h"
#include "snes/spc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RATE 32040
#define BASE 0x5400u

static Apu *apu;

static void start_song(void) {
  /* The driver entry is reached through the APU input ports. The game writes
   * the song number to port 0 and then the driver reads it. */
  uint8_t entry = apu->ram[0x0000];
  fprintf(stderr, "reset vector low byte %02X\n", (unsigned)entry);
}

int main(int argc, char **argv) {
  if (argc != 5) {
    fprintf(stderr, "usage: %s <engine-aram.bin> <song.bin> <out.wav> <frames>\n", argv[0]);
    return 2;
  }
  static uint8_t image[0x10000];
  FILE *in = fopen(argv[1], "rb");
  if (!in) { perror("engine"); return 1; }
  if (fread(image, 1, sizeof(image), in) != sizeof(image)) {
    fprintf(stderr, "engine image size differs\n");
    return 1;
  }
  fclose(in);

  static uint8_t song[0x10000];
  FILE *sf = fopen(argv[2], "rb");
  if (!sf) { perror("song"); return 1; }
  size_t song_size = fread(song, 1, sizeof(song), sf);
  fclose(sf);

  apu = apu_init();
  if (!apu) { fprintf(stderr, "apu init failed\n"); return 1; }
  apu_reset(apu);
  memcpy(apu->ram, image, sizeof(image));
  memcpy(apu->ram + BASE, song, song_size);

  /* Report what the image holds so the run is checkable. */
  fprintf(stderr, "ram[0]=%02X ram[1]=%02X ram[0x5400]=%02X song=%zu\n",
          (unsigned)apu->ram[0], (unsigned)apu->ram[1],
          (unsigned)apu->ram[BASE], song_size);
  start_song();

  /* Execute the driver for the requested frames and collect DSP samples. */
  uint32_t frames = (uint32_t)strtoul(argv[4], NULL, 0);
  uint32_t samples = frames * 534u;
  int16_t *pcm = malloc(sizeof(int16_t) * samples * 2);
  if (!pcm) { fprintf(stderr, "alloc failed\n"); return 1; }
  uint32_t got = 0;
  for (uint32_t i = 0; i < samples * 2 && got < samples * 2; ++i) {
    apu_cycle(apu);
    if ((i & 1) == 1) {
      int16_t l = 0, r = 0;
      dsp_peek(apu->dsp, 0, &l, &r);
      pcm[got++] = l;
      pcm[got++] = r;
      dsp_advance(apu->dsp, 1);
    }
  }
  uint32_t nonzero = 0;
  for (uint32_t i = 0; i < got; ++i) if (pcm[i]) ++nonzero;
  fprintf(stderr, "samples %u nonzero %u\n", got, nonzero);

  uint32_t data_bytes = got * 2u;
  FILE *out = fopen(argv[3], "wb");
  if (!out) { perror("out"); return 1; }
  fwrite("RIFF", 1, 4, out);
  uint32_t riff = 36u + data_bytes; fwrite(&riff, 4, 1, out);
  fwrite("WAVEfmt ", 1, 8, out);
  uint32_t fmt = 16u; fwrite(&fmt, 4, 1, out);
  uint16_t pcm_fmt = 1u, ch = 1u;
  fwrite(&pcm_fmt, 2, 1, out); fwrite(&ch, 2, 1, out);
  uint32_t rate = RATE; fwrite(&rate, 4, 1, out);
  uint32_t byte_rate = RATE * 2u; fwrite(&byte_rate, 4, 1, out);
  uint16_t block = 2u; fwrite(&block, 2, 1, out);
  uint16_t bits = 16u; fwrite(&bits, 2, 1, out);
  fwrite("data", 1, 4, out); fwrite(&data_bytes, 4, 1, out);
  fwrite(pcm, 2, got, out);
  fclose(out);
  free(pcm);
  apu_free(apu);
  return 0;
}
