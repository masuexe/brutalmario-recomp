/* Native song player: run one song stream over time against the pinned DSP.
 *
 * The song stream sets channel registers. This program runs that stream
 * frame by frame, so every note of the song sounds in order, and lets the
 * upstream DSP produce the samples. The sample set and its directory come from
 * a console capture of the same ROM.
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
#define MAX_VOICES 8
#define MAX_DEPTH 4

typedef struct {
  uint16_t cursor;
  uint8_t instrument;
  uint8_t volume;
  uint8_t tuning;
  uint32_t wait;
  uint16_t return_to[MAX_DEPTH];
  int depth;
} Voice;

static uint8_t aram[ARAM_SIZE];
static const uint8_t *song;
static size_t song_size;
static Voice voices[MAX_VOICES];
static int voice_count;

static uint16_t word(size_t at) {
  if (at + 1 >= song_size) return 0;
  return (uint16_t)(song[at] | (song[at + 1] << 8));
}

/* Pitch conversion from the AddmusicK SPC engine.
 *
 * PitchTable spans one octave. SetPitch indexes it by the integer octave,
 * interpolates with the fractional part, and multiplies by the sample base
 * pitch from the instrument tuning byte. Writing the raw note byte gives a
 * sub-audio rate, which sounds like a rumble and not a note. */
/* InstrumentTable from the AddmusicK SPC engine: sample, ADSR1, ADSR2, GAIN,
 * tuning. The song selects this table index, and byte 0 is the real SRCN. */
static const uint8_t kInstrumentTable[20][5] = {
  {0x00, 0xFE, 0x6A, 0xB8, 0x06}, {0x01, 0xFA, 0x6A, 0xB8, 0x03},
  {0x02, 0xAE, 0x2F, 0xB8, 0x04}, {0x03, 0xFE, 0x6A, 0xB8, 0x03},
  {0x04, 0xA9, 0x6A, 0xB8, 0x03}, {0x07, 0xAE, 0x26, 0xB8, 0x07},
  {0x08, 0xFA, 0x6A, 0xB8, 0x03}, {0x09, 0x9E, 0x1F, 0xB8, 0x03},
  {0x05, 0xAE, 0x26, 0xB8, 0x1E}, {0x0A, 0xEE, 0x6A, 0xB8, 0x02},
  {0x0B, 0xFE, 0x6A, 0xB8, 0x08}, {0x01, 0xF7, 0x6A, 0xB8, 0x03},
  {0x10, 0x0E, 0x6A, 0x7F, 0x04}, {0x0C, 0xFE, 0x6A, 0xB8, 0x03},
  {0x0D, 0xAE, 0x26, 0xB8, 0x07}, {0x12, 0x8E, 0xE0, 0xB8, 0x03},
  {0x0C, 0xFE, 0x70, 0xB8, 0x03}, {0x11, 0xFE, 0x6A, 0xB8, 0x05},
  {0x01, 0xE9, 0x6A, 0xB8, 0x03}, {0x0F, 0x0F, 0x6A, 0x7F, 0x03},
};

static const uint16_t kPitchTable[13] = {
  0x085F, 0x08DE, 0x0965, 0x09F4, 0x0A8C, 0x0B2C, 0x0BD6,
  0x0C8B, 0x0D4A, 0x0E14, 0x0EEA, 0x0FCD, 0x10BE};

static uint16_t pitch_register(uint8_t note, uint8_t tuning) {
  int index = note >= 0x80 ? (int)(note - 0x80) : (int)note;
  int octave = index / 12;
  int remainder = index % 12;
  if (octave > 12) octave = 12;
  int low = kPitchTable[octave];
  int high = octave + 1 < 13 ? kPitchTable[octave + 1] : low * 2;
  int value = low + (high - low) * remainder / 12;
  /* The table value is already the rate for this octave at the sample base.
   * The tuning byte adjusts it by a small amount, not a multiple. */
  int scaled = value + (int)tuning;
  if (scaled > 0x3FFF) scaled = 0x3FFF;
  return (uint16_t)scaled;
}

static void write_channel(Dsp *dsp, int index, const Voice *voice, uint8_t pitch) {
  uint8_t base = (uint8_t)(10 * index);
  int entry = voice->instrument < 20 ? voice->instrument : 0;
  uint16_t reg = pitch_register(pitch, kInstrumentTable[entry][4]);
  dsp_write(dsp, (uint8_t)(base + 0x00), (uint8_t)(reg & 0xFF));
  dsp_write(dsp, (uint8_t)(base + 0x01), (uint8_t)(reg >> 8));
  dsp_write(dsp, (uint8_t)(base + 0x02), voice->volume);
  dsp_write(dsp, (uint8_t)(base + 0x03), voice->volume);
  const uint8_t *inst = kInstrumentTable[entry];
  dsp_write(dsp, (uint8_t)(base + 0x04), inst[0]);   /* SRCN */
  dsp_write(dsp, (uint8_t)(base + 0x05), inst[1]);   /* ADSR1 */
  dsp_write(dsp, (uint8_t)(base + 0x06), inst[2]);   /* ADSR2 */
  dsp_write(dsp, (uint8_t)(base + 0x07), inst[3]);   /* GAIN */
}

/* Run one command. Return the frames to wait, or -1 when the voice is done. */
static int step(Dsp *dsp, int index) {
  Voice *voice = &voices[index];
  for (int guard = 0; guard < 64; ++guard) {
    size_t at = voice->cursor - BASE;
    if (at >= song_size) return -1;
    uint8_t byte = song[at];
    if (byte == 0) {
      /* A zero byte ends a subroutine and returns to the caller. In the
       * caller stream it separates phrases and the stream continues. */
      if (voice->depth > 0) {
        voice->cursor = voice->return_to[--voice->depth];
        continue;
      }
      voice->cursor += 1;
      continue;
    }
    if (byte < 0x80) {
      if (at + 1 >= song_size) return -1;
      uint8_t pitch = song[at + 1];
      write_channel(dsp, index, voice, pitch);
      dsp_write(dsp, 0x4C, (uint8_t)(1u << index));
      voice->cursor += 2;
      /* The duration is in engine ticks. One tick is one frame at the
       * console tempo, so a note of 96 ticks holds for 96 frames. */
      return byte ? byte : 1;
    }
    switch (byte) {
      case 0xC6: case 0xC7:
        voice->instrument = song[at + 1];
        voice->cursor += 2;
        continue;
      case 0xDA:
        voice->cursor += 2;
        continue;
      case 0xE0:
        voice->volume = song[at + 1];
        voice->cursor += 2;
        continue;
      case 0xE1:
        voice->volume = song[at + 1];
        voice->cursor += 3;
        continue;
      case 0xE9: {
        uint16_t target = (uint16_t)(song[at + 1] | (song[at + 2] << 8));
        if (voice->depth < MAX_DEPTH) {
          voice->return_to[voice->depth++] = (uint16_t)(voice->cursor + 4);
          voice->cursor = target;
        } else {
          voice->cursor += 4;
        }
        continue;
      }
      default:
        voice->cursor += (byte >= 0xE9 && byte <= 0xF2) ? 4
                       : ((byte >= 0xCB) ? 3 : 2);
        continue;
    }
  }
  return -1;
}

int main(int argc, char **argv) {
  if (argc != 5) {
    fprintf(stderr, "usage: %s <song.bin> <engine-aram.bin> <out.wav> <frames>\n", argv[0]);
    return 2;
  }
  FILE *in = fopen(argv[1], "rb");
  if (!in) { perror("song"); return 1; }
  static uint8_t data[0x10000];
  size_t size = fread(data, 1, sizeof(data), in);
  fclose(in);
  if (size < 8) { fprintf(stderr, "song too small\n"); return 1; }
  song = data;
  song_size = size;

  FILE *engine = fopen(argv[2], "rb");
  if (!engine) { perror("engine"); return 1; }
  if (fread(aram, 1, ARAM_SIZE, engine) != ARAM_SIZE) {
    fprintf(stderr, "engine image size differs\n");
    return 1;
  }
  fclose(engine);
  memcpy(aram + BASE, data, size);

  Dsp *dsp = dsp_init(aram);
  if (!dsp) { fprintf(stderr, "dsp init failed\n"); return 1; }
  dsp_reset(dsp);
  dsp_write(dsp, 0x5D, (uint8_t)(DIRECTORY >> 8));
  dsp_write(dsp, 0x6C, 0x00);
  dsp_write(dsp, 0x0C, 0x7F);
  dsp_write(dsp, 0x1C, 0x7F);

  memset(voices, 0, sizeof(voices));
  voice_count = 0;
  for (int pattern_index = 0; pattern_index < 2; ++pattern_index) {
    uint16_t pattern = word((size_t)(2 * pattern_index));
    if (!pattern) continue;
    size_t off = pattern - BASE;
    if (off + 16 > size) continue;
    for (int i = 0; i < 8 && voice_count < MAX_VOICES; ++i) {
      uint16_t track = word(off + 2 * i);
      if (!track) continue;
      Voice *voice = &voices[voice_count];
      voice->cursor = track;
      voice->instrument = 1;
      voice->volume = 0x7F;
      voice->tuning = 0x03;
      voice->wait = 0;
      voice->depth = 0;
      voice_count += 1;
    }
  }

  uint32_t frames = (uint32_t)strtoul(argv[4], NULL, 0);
  uint32_t samples = frames * 534u;
  int16_t *pcm = malloc(sizeof(int16_t) * samples * 2);
  if (!pcm) { fprintf(stderr, "alloc failed\n"); return 1; }

  uint32_t notes = 0;
  for (uint32_t frame = 0; frame < frames; ++frame) {
    for (int index = 0; index < voice_count; ++index) {
      if (voices[index].wait) { voices[index].wait -= 1; continue; }
      int wait = step(dsp, index);
      if (wait < 0) continue;
      voices[index].wait = (uint32_t)wait;
      notes += 1;
    }
    for (uint32_t i = 0; i < 534u; ++i) {
      dsp_cycle(dsp);
      int16_t l = 0, r = 0;
      dsp_peek(dsp, 0, &l, &r);
      uint32_t at = frame * 534u + i;
      if (at < samples) { pcm[2 * at] = l; pcm[2 * at + 1] = r; }
      dsp_advance(dsp, 1);
    }
  }

  uint32_t data_bytes = samples * 4u;
  FILE *out = fopen(argv[3], "wb");
  if (!out) { perror("out"); return 1; }
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
  printf("voices=%d frames=%u notes=%u\n", voice_count, frames, notes);
  return 0;
}
