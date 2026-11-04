/* Native song player probe: run one song stream against the pinned DSP.
 *
 * The song stream sets the channel registers that the console driver would
 * write. The sample set and its directory come from a real capture of the same
 * ROM, because the song payload alone does not carry the samples.
 *
 * Usage: player <song.bin> <engine-aram.bin> <out.wav> <frames>
 */
#include "snes/dsp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ARAM_SIZE 0x10000u
#define RATE 32040
#define BASE 0x5400u
#define DIRECTORY 0x5B00u

static uint8_t aram[ARAM_SIZE];

static uint16_t word(const uint8_t *data, size_t size, size_t at) {
  if (at + 1 >= size) return 0;
  return (uint16_t)(data[at] | (data[at + 1] << 8));
}

int main(int argc, char **argv) {
  if (argc != 5) {
    fprintf(stderr, "usage: %s <song.bin> <engine-aram.bin> <out.wav> <frames>\n", argv[0]);
    return 2;
  }
  FILE *in = fopen(argv[1], "rb");
  if (!in) { perror("song"); return 1; }
  uint8_t data[0x10000];
  size_t size = fread(data, 1, sizeof(data), in);
  fclose(in);
  if (size < 8) { fprintf(stderr, "song too small\n"); return 1; }

  /* The sample set and the directory come from a console capture. */
  FILE *engine = fopen(argv[2], "rb");
  if (!engine) { perror("engine"); return 1; }
  size_t got = fread(aram, 1, ARAM_SIZE, engine);
  fclose(engine);
  if (got != ARAM_SIZE) { fprintf(stderr, "engine image size differs\n"); return 1; }

  /* Replace the song region with this song's payload. */
  memcpy(aram + BASE, data, size);

  Dsp *dsp = dsp_init(aram);
  if (!dsp) { fprintf(stderr, "dsp init failed\n"); return 1; }
  dsp_reset(dsp);
  dsp_write(dsp, 0x5D, (uint8_t)(DIRECTORY >> 8)); /* DIR */
  /* FLG must clear both reset and mute. A set reset forces gain 0. */
  dsp_write(dsp, 0x6C, 0x00);
  dsp_write(dsp, 0x0C, 0x7F);  /* MVOLL */
  dsp_write(dsp, 0x1C, 0x7F);  /* MVOLR */

  uint32_t frames = (uint32_t)strtoul(argv[4], NULL, 0);
  uint32_t samples = frames * 534u;

  uint16_t patterns[2] = { word(data, size, 0), word(data, size, 2) };
  int voice = 0;
  for (int p = 0; p < 2 && voice < 8; ++p) {
    if (!patterns[p]) continue;
    size_t off = patterns[p] - BASE;
    if (off + 16 > size) continue;
    for (int i = 0; i < 8 && voice < 8; ++i) {
      uint16_t track = word(data, size, off + 2 * i);
      if (!track) continue;
      size_t t = track - BASE;
      if (t >= size) continue;
      int instrument = 0;
      while (t + 1 < size) {
        uint8_t byte = data[t];
        if (byte == 0) { t += 1; continue; }
        if (byte < 0x80) {
          uint8_t pitch = data[t + 1];
          /* Channel registers: pitch, srcn, adsr1, adsr2, gain. */
          dsp_write(dsp, (uint8_t)(0x00 + 10 * voice), (uint8_t)(pitch & 0xFF));
          dsp_write(dsp, (uint8_t)(0x01 + 10 * voice), 0x00);
          dsp_write(dsp, (uint8_t)(0x02 + 10 * voice), 0x7F);  /* VOL(L) */
          dsp_write(dsp, (uint8_t)(0x03 + 10 * voice), 0x7F);  /* VOL(R) */
          dsp_write(dsp, (uint8_t)(0x04 + 10 * voice),
                    (uint8_t)(instrument ? instrument : 1));   /* SRCN */
          dsp_write(dsp, (uint8_t)(0x05 + 10 * voice), 0x00);  /* ADSR1 */
          dsp_write(dsp, (uint8_t)(0x06 + 10 * voice), 0x00);  /* ADSR2 */
          /* GAIN: a value below 0x80 selects direct gain. 0x7F is full. */
          dsp_write(dsp, (uint8_t)(0x07 + 10 * voice), 0x7F);
          voice += 1;
          break;
        }
        if (byte == 0xC6 || byte == 0xC7) { instrument = data[t + 1]; t += 2; continue; }
        t += (byte >= 0xE9 && byte <= 0xF2) ? 4 : ((byte >= 0xCB) ? 3 : 2);
      }
    }
  }
  dsp_write(dsp, 0x4C, (uint8_t)((1u << voice) - 1u));
  fprintf(stderr, "kon=%02X voices=%d dir=%02X\n",
          (unsigned)((1u << voice) - 1u), voice, (unsigned)(DIRECTORY >> 8));
  /* Diagnostic: show the channel registers the probe wrote. */
  for (int c = 0; c < voice; ++c)
    fprintf(stderr, "  ch%d pitch=%02X vol=%02X srcn=%02X\n", c,
            (unsigned)dsp_read(dsp, (uint8_t)(0x00 + 10 * c)),
            (unsigned)dsp_read(dsp, (uint8_t)(0x02 + 10 * c)),
            (unsigned)dsp_read(dsp, (uint8_t)(0x04 + 10 * c)));

  FILE *out = fopen(argv[3], "wb");
  if (!out) { perror("out"); return 1; }
  int16_t *pcm = malloc(sizeof(int16_t) * samples * 2);
  if (!pcm) { fprintf(stderr, "alloc failed\n"); return 1; }
  uint32_t nonzero = 0, first_at = 0;
  for (uint32_t i = 0; i < samples; ++i) {
    dsp_cycle(dsp);
    int16_t l = 0, r = 0;
    dsp_peek(dsp, 0, &l, &r);
    pcm[2 * i] = l;
    pcm[2 * i + 1] = r;
    if (l || r) { if (!nonzero) first_at = i; ++nonzero; }
    dsp_advance(dsp, 1);
  }
  fprintf(stderr, "nonzero samples %u, first at %u\n", nonzero, first_at);
  fprintf(stderr, "gain ch0=%02X state=%02X mute=%d reset=%d mvolL=%02X\n",
          (unsigned)dsp_read(dsp, 0x07), (unsigned)dsp_read(dsp, 0x06),
          (int)dsp->mute, (int)dsp->reset, (unsigned)dsp->masterVolumeL);
  uint32_t data_bytes = samples * 4u;
  fwrite("RIFF", 1, 4, out);
  uint32_t riff = 36u + data_bytes; fwrite(&riff, 4, 1, out);
  fwrite("WAVEfmt ", 1, 8, out);
  uint32_t fmt = 16u; fwrite(&fmt, 4, 1, out);
  uint16_t pcm_fmt = 1u, ch = 2u;
  fwrite(&pcm_fmt, 2, 1, out); fwrite(&ch, 2, 1, out);
  uint32_t rate = RATE; fwrite(&rate, 4, 1, out);
  uint32_t byte_rate = RATE * 4u; fwrite(&byte_rate, 4, 1, out);
  uint16_t block = 4u; fwrite(&block, 2, 1, out);
  uint16_t bits = 16u; fwrite(&bits, 2, 1, out);
  fwrite("data", 1, 4, out); fwrite(&data_bytes, 4, 1, out);
  fwrite(pcm, 4, samples, out);
  fclose(out);
  free(pcm);
  dsp_free(dsp);
  printf("voices=%d frames=%u\n", voice, frames);
  return 0;
}
