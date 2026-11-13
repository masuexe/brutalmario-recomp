/* Immutable cumulative module views. A2/A6 are independent of 22/26; A5/B6
 * retain the preceding qualified content. No room/PC-dependent bank swapping. */
#include "native_content.h"
#include "native_seven_manifest.h"
#include "sha256.h"
#include "snes/interp816.h"
#ifdef BM_LANG_R47_SUPPORT
#include "snes/snes.h"
#include "snes/ppu.h"
#ifdef _WIN32
#include <windows.h>
#endif
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Weak WRAM binding: the full runner provides the strong g_ram; isolated
 * boundary-test links get a zeroed array so the override is inert. */
#if defined(_MSC_VER)
extern uint8_t g_ram[0x20000];
#else
__attribute__((weak)) uint8_t g_ram[0x20000];
#endif

#ifdef BM_LANG_R47_SUPPORT
#if defined(_MSC_VER)
extern Snes *g_snes;
extern void snes_host_register_lang_sync(void (*fn)(int effective_lang, const char *mode));
extern const char *snes_host_get_language_mode(void);
extern int snes_host_set_language_mode(const char *mode_in);
extern int snes_host_get_effective_language(void);
#else
__attribute__((weak)) Snes *g_snes = NULL;
__attribute__((weak)) void snes_host_register_lang_sync(void (*fn)(int effective_lang, const char *mode)) {
  (void)fn;
}
__attribute__((weak)) const char *snes_host_get_language_mode(void) {
  return NULL;
}
__attribute__((weak)) int snes_host_set_language_mode(const char *mode_in) {
  (void)mode_in;
  return 0;
}
__attribute__((weak)) int snes_host_get_effective_language(void) {
  return -1;
}
#endif
#endif
/* Room-scoped native music adaptation (native-content policy): room 0x190 has
 * no music object of its own and inherits the shared default slot 0x02. Force
 * recipient slot 0x9E whenever the game is in room 0x190. */
static int s_music_room = -1;
static int s_yoshi_start_done;
static int s_seven_return_done;
static int s_seven_return_enabled = 1;
static int s_yoshi_start_enabled = 1;
static int s_mazo_node_enabled;

/* These are launch settings. Resolve them once per content load: this file's
 * resolver runs on ROM bus accesses, where Windows CRT environment lookups
 * can cost far more than the emulated instruction itself. */
static void bm_load_launch_settings(void) {
  const char *flag = getenv("BM_SEVEN_RETURN");
  const char *yoshi = getenv("BM_YOSHI_START");
  const char *node = getenv("BM_MAZO_190_NODE");
  s_seven_return_enabled = !(flag && flag[0] == '0' && flag[1] == 0);
  s_yoshi_start_enabled = !(yoshi && yoshi[0] == '0' && yoshi[1] == 0);
  s_mazo_node_enabled = node && node[0] == '1' && node[1] == 0;
}

static void bm_seven_return_override(void) {
  int room = g_ram[0x10b] | (g_ram[0x10c] << 8);
  if (room != 0x174) { s_seven_return_done = 0; return; }
  if (g_ram[0x100] != 0x14) return;
  if (!s_seven_return_enabled) return;
  if (s_seven_return_done) return;
  s_seven_return_done = 1;
  g_ram[0x100] = 0x0b;
  g_ram[0x1f11] = 0;
  g_ram[0x1f12] = 0;
  g_ram[0x1f17] = 0x00;
  g_ram[0x1f18] = 0x01;
  g_ram[0x1f19] = 0xf0;
  g_ram[0x1f1a] = 0x00;
  g_ram[0x1f1f] = 0x10;
  g_ram[0x1f20] = 0;
  g_ram[0x1f21] = 0x0f;
  g_ram[0x1f22] = 0;
}
static void bm_yoshi_start_override(void) {
  if (s_yoshi_start_done || !s_yoshi_start_enabled) return;
  if (g_ram[0x100] != 0x0e || g_ram[0x1f11] != 0) return;
  if ((g_ram[0x1f17] | (g_ram[0x1f18] << 8)) != 72) return;
  if ((g_ram[0x1f19] | (g_ram[0x1f1a] << 8)) != 408) return;
  g_ram[0x1f17] = 104;
  g_ram[0x1f18] = 0;
  g_ram[0x1f1f] = 6;
  g_ram[0x1f20] = 0;
  s_yoshi_start_done = 1;
}
static void bm_mazo_map_node_override(void) {
#ifdef BM_MAZO_PRIMARY_ENTRY
  /* This target redirects primary loading, preserving the original course30
   * node and its completion/save index. The legacy B4 table edit must not run. */
  return;
#else
  if (!s_mazo_node_enabled) return;
  if (g_ram[0x100] != 0x0e || g_ram[0x1f11] != 0) return;
  g_ram[0xd1f0] = 0xb4;
#endif
}
static void bm_room_music_override(void) {
  int room = g_ram[0x10b] | (g_ram[0x10c] << 8);
  if (room == 0x190) {
    if (s_music_room != 0x190 || g_ram[0x0dda] != 0x9e) {
      g_ram[0x0dda] = 0x9e;
      g_ram[0x1dfb] = 0x9e;
    }
  }
  s_music_room = room;
}

static const uint8_t *owner;
static uint8_t *backing;
static unsigned long long resolutions[BM_SEVEN_PACKS];
static int registered;

static void fail(const char *reason) {
  fprintf(stderr, "[native-seven] rejected: %s\n", reason);
  exit(EXIT_FAILURE);
}

static int matches(const uint8_t *data, size_t size, const uint8_t expected[32]) {
  uint8_t actual[32];
  sha256_compute(data, size, actual);
  return memcmp(actual, expected, 32) == 0;
}

static void report(void) {
  if (!backing) return;
  for (unsigned i = 0; i < BM_SEVEN_PACKS; ++i) {
    const BmSevenPack *pack = &bm_seven_packs[i];
    unsigned long long instructions = 0;
    if (pack->executable)
      for (unsigned page = pack->first_page; page <= pack->last_page; ++page)
        instructions += interp816_page_insns(page);
    fprintf(stderr, "[native-seven] bank=%02X resolutions=%llu executed_page_instructions=%llu\n",
            pack->bank, resolutions[i], instructions);
  }
}

#ifdef BM_LANG_R47_SUPPORT
static int s_lang_mounted;
static size_t s_lang_ctrl_offset;
static size_t s_lang_data_offset;
static size_t s_lang_data_size;
static char s_lang_mode_fallback[16] = "auto";
static int s_lang_effective;

static uint16_t bm_rd16(const uint8_t *p) {
  return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}

static uint32_t bm_rd32(const uint8_t *p) {
  return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
         ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static char bm_ascii_lower(char c) {
  return (c >= 'A' && c <= 'Z') ? (char)(c + ('a' - 'A')) : c;
}

static int bm_streq_nocase(const char *a, const char *b) {
  if (!a || !b) return 0;
  while (*a && *b) {
    if (bm_ascii_lower(*a) != bm_ascii_lower(*b)) return 0;
    a++;
    b++;
  }
  return *a == 0 && *b == 0;
}

static const char *bm_normalize_lang_mode(const char *s) {
  if (!s || !*s) return NULL;
  if (bm_streq_nocase(s, "en") || bm_streq_nocase(s, "english")) return "en";
  if (bm_streq_nocase(s, "ja") || bm_streq_nocase(s, "jp") ||
      bm_streq_nocase(s, "japanese")) return "ja";
  if (bm_streq_nocase(s, "auto") || bm_streq_nocase(s, "system")) return "auto";
  return NULL;
}

static int bm_starts_ja_nocase(const char *s) {
  return s && bm_ascii_lower(s[0]) == 'j' && bm_ascii_lower(s[1]) == 'a';
}

static int bm_detect_os_lang_fallback(void) {
  const char *test_loc = getenv("BM_LANG_TEST_LOCALE");
  if (test_loc && *test_loc)
    return bm_starts_ja_nocase(test_loc) ? 1 : 0;
#ifdef _WIN32
  return PRIMARYLANGID(GetUserDefaultUILanguage()) == LANG_JAPANESE ? 1 : 0;
#else
  static const char *const kVars[] = { "LC_ALL", "LC_MESSAGES", "LANG" };
  for (size_t i = 0; i < sizeof(kVars) / sizeof(kVars[0]); ++i) {
    const char *v = getenv(kVars[i]);
    if (v && *v)
      return bm_starts_ja_nocase(v) ? 1 : 0;
  }
  return 0;
#endif
}

static int bm_lang_resolve_effective(void) {
  int host_eff = snes_host_get_effective_language();
  if (host_eff >= 0) return host_eff ? 1 : 0;
  const char *env = bm_normalize_lang_mode(getenv("BM_LANG"));
  const char *mode = env ? env : s_lang_mode_fallback;
  if (strcmp(mode, "ja") == 0) return 1;
  if (strcmp(mode, "en") == 0) return 0;
  return bm_detect_os_lang_fallback();
}

static void bm_lang_write_ctrl(int eff) {
  s_lang_effective = eff ? 1 : 0;
  if (!backing || !s_lang_mounted || s_lang_ctrl_offset >= BM_SEVEN_ROM_SIZE) return;
  backing[s_lang_ctrl_offset] = (uint8_t)s_lang_effective;
}

static void bm_vram_write_2kb(Ppu *ppu, uint16_t word_base, const uint8_t *src) {
  for (size_t i = 0; i < 1024u; ++i) {
    ppu->vram[word_base + i] =
        (uint16_t)src[i * 2u] | ((uint16_t)src[i * 2u + 1u] << 8);
  }
}

void bm_lang_apply_live_vram(void) {
  if (!backing || !s_lang_mounted || s_lang_data_size < 64u) return;
  const uint8_t *bmlg = backing + s_lang_data_offset;
  if (memcmp(bmlg, "BMLG", 4) != 0 || bm_rd16(bmlg + 4) != 1u ||
      bm_rd16(bmlg + 6) < 64u) {
    return;
  }
  uint32_t total_size = bm_rd32(bmlg + 8);
  if (total_size < 64u || total_size > s_lang_data_size) return;

  uint16_t ja_028_off = bm_rd16(bmlg + 0x0C);
  uint16_t ja_02a_off = bm_rd16(bmlg + 0x0E);
  uint16_t ja_02b_off = bm_rd16(bmlg + 0x10);
  uint16_t en_028_off = bm_rd16(bmlg + 0x12);
  uint16_t en_02a_off = bm_rd16(bmlg + 0x14);
  uint16_t en_02b_off = bm_rd16(bmlg + 0x16);
  uint16_t ja_ow_off  = bm_rd16(bmlg + 0x18);
  uint16_t en_ow_off  = bm_rd16(bmlg + 0x1A);
  uint16_t ow_flags_off = bm_rd16(bmlg + 0x1C);
  uint16_t ja_msg_ptrs_off = bm_rd16(bmlg + 0x1E);
  uint16_t ja_msg_blob_off = bm_rd16(bmlg + 0x20);
  uint16_t ja_msg_blob_sz  = bm_rd16(bmlg + 0x22);
  uint16_t en_msg_ptrs_off = bm_rd16(bmlg + 0x24);
  uint16_t en_msg_blob_off = bm_rd16(bmlg + 0x26);
  uint16_t en_msg_blob_sz  = bm_rd16(bmlg + 0x28);
  uint16_t msg_flags_off   = bm_rd16(bmlg + 0x2A);
  uint16_t mazo_192_off    = bm_rd16(bmlg + 0x2C);
  uint16_t mazo_191_off    = bm_rd16(bmlg + 0x2E);
  uint16_t room_policy_off = bm_rd16(bmlg + 0x30);
  uint16_t room_remap_off  = bm_rd16(bmlg + 0x32);

  if ((uint32_t)ja_028_off + 2048u > total_size ||
      (uint32_t)ja_02a_off + 2048u > total_size ||
      (uint32_t)ja_02b_off + 2048u > total_size ||
      (uint32_t)en_028_off + 2048u > total_size ||
      (uint32_t)en_02a_off + 2048u > total_size ||
      (uint32_t)en_02b_off + 2048u > total_size ||
      (uint32_t)ja_ow_off + 96u * 19u > total_size ||
      (uint32_t)en_ow_off + 96u * 19u > total_size ||
      (uint32_t)ow_flags_off + 96u > total_size ||
      (uint32_t)ja_msg_ptrs_off + 144u * 2u > total_size ||
      (uint32_t)ja_msg_blob_off + ja_msg_blob_sz > total_size ||
      (uint32_t)en_msg_ptrs_off + 144u * 2u > total_size ||
      (uint32_t)en_msg_blob_off + en_msg_blob_sz > total_size ||
      (uint32_t)msg_flags_off + 144u > total_size ||
      (uint32_t)mazo_192_off + 70u > total_size ||
      (uint32_t)mazo_191_off + 86u > total_size ||
      (uint32_t)room_policy_off + 512u > total_size ||
      (uint32_t)room_remap_off + 1u > total_size) {
    return;
  }
  uint8_t remap_count = bmlg[room_remap_off];
  if ((uint32_t)room_remap_off + 1u + (uint32_t)remap_count * 3u > total_size)
    return;

  if (!g_snes || !g_snes->ppu) return;

  uint8_t game_mode = g_ram[0x0100];
  uint8_t translevel = g_ram[0x13BF];
  uint16_t room = (uint16_t)(g_ram[0x010B] | (g_ram[0x010C] << 8));
  uint8_t msg_flag = g_ram[0x1426];
  int eff = bm_lang_resolve_effective();
  int is_mazo_msg = (msg_flag != 0 && (room == 0x0191u || room == 0x0192u));
  uint16_t msg_slot = 0xFFFFu;

  if (msg_flag != 0 && !is_mazo_msg) {
    if (msg_flag == 3u) {
      msg_slot = 1u;
    } else {
      uint8_t msg_level = translevel;
      for (uint8_t i = 0; i < remap_count; ++i) {
        const uint8_t *entry = bmlg + room_remap_off + 1u + (size_t)i * 3u;
        if (bm_rd16(entry) == room) {
          msg_level = entry[2];
          break;
        }
      }
      if (msg_level == 0x28u) {
        msg_slot = (uint16_t)(0x28u * 2u + (g_ram[0x187A] ? 1u : 0u));
      } else {
        uint8_t slot_y = (msg_flag == 1u) ? 0u : 1u;
        msg_slot = (uint16_t)((uint16_t)msg_level * 2u + slot_y);
      }
    }
  }

  int use_jp_font = eff ? 1 : 0;
  if (!eff) {
    if (game_mode == 0x0Eu) {
      if (translevel < 96u && bmlg[ow_flags_off + translevel] != 0)
        use_jp_font = 1;
    } else if (game_mode >= 0x0Fu) {
      if (room < 512u && bmlg[room_policy_off + room] != 0)
        use_jp_font = 1;
    }
    if (msg_flag != 0) {
      if (is_mazo_msg)
        use_jp_font = 1;
      else if (msg_slot < 144u && bmlg[msg_flags_off + msg_slot] != 0)
        use_jp_font = 1;
    }
  }

  if (game_mode <= 0x0Eu) {
    bm_vram_write_2kb(g_snes->ppu, 0x4000u, bmlg + (use_jp_font ? ja_028_off : en_028_off));
    bm_vram_write_2kb(g_snes->ppu, 0x4800u, bmlg + (use_jp_font ? ja_02a_off : en_02a_off));
    bm_vram_write_2kb(g_snes->ppu, 0x4C00u, bmlg + (use_jp_font ? ja_02b_off : en_02b_off));
  } else if (room != 0x0104u && room != 0x0182u) {
    bm_vram_write_2kb(g_snes->ppu, 0x4800u, bmlg + (use_jp_font ? ja_02a_off : en_02a_off));
  }

  if (game_mode == 0x0Eu && translevel < 96u) {
    const uint8_t *ow_names = bmlg + (eff ? ja_ow_off : en_ow_off);
    const uint8_t *row_tiles = ow_names + (size_t)translevel * 19u;
    for (size_t i = 0; i < 19u; ++i) {
      g_snes->ppu->vram[0x508Bu + i] = (uint16_t)row_tiles[i] | 0x3900u;
    }
  }

  if (msg_flag != 0) {
    const uint8_t *msg_ptr = NULL;
    size_t msg_max = 0;
    if (room == 0x0192u) {
      msg_ptr = bmlg + mazo_192_off;
      msg_max = 70u;
    } else if (room == 0x0191u) {
      msg_ptr = bmlg + mazo_191_off;
      msg_max = 86u;
    } else if (msg_slot < 144u) {
      uint16_t ptrs_off = eff ? ja_msg_ptrs_off : en_msg_ptrs_off;
      uint16_t blob_off = eff ? ja_msg_blob_off : en_msg_blob_off;
      uint16_t blob_sz  = eff ? ja_msg_blob_sz  : en_msg_blob_sz;
      uint16_t rel = bm_rd16(bmlg + ptrs_off + (size_t)msg_slot * 2u);
      if (rel < blob_sz) {
        msg_ptr = bmlg + blob_off + rel;
        msg_max = (size_t)blob_sz - rel;
      }
    }
    if (msg_ptr) {
      size_t pos = 0;
      int ended = 0;
      for (size_t r = 0; r < 8u; ++r) {
        uint16_t vram_row = (uint16_t)(0x50C7u + r * 0x20u);
        for (size_t c = 0; c < 18u; ++c) {
          uint8_t tile = 0x1Fu;
          if (!ended && pos < msg_max) {
            uint8_t b = msg_ptr[pos++];
            if (b == 0xFEu) {
              ended = 1;
            } else {
              tile = b;
            }
          } else {
            ended = 1;
          }
          g_snes->ppu->vram[vram_row + c] = (uint16_t)tile | 0x3900u;
        }
      }
    }
  }

  g_snes->ppu->vramWriteCount++;
}

static void bm_lang_sync_from_host(int eff, const char *mode) {
  (void)mode;
  bm_lang_write_ctrl(eff);
  bm_lang_apply_live_vram();
}

const char *bm_lang_get_mode(void) {
  const char *m = snes_host_get_language_mode();
  if (m && *m) return m;
  return s_lang_mode_fallback;
}

void bm_lang_set_mode(const char *mode) {
  if (snes_host_get_effective_language() >= 0) {
    snes_host_set_language_mode(mode);
    return;
  }
  const char *norm = bm_normalize_lang_mode(mode);
  if (!norm) return;
  snprintf(s_lang_mode_fallback, sizeof(s_lang_mode_fallback), "%s", norm);
  bm_lang_write_ctrl(bm_lang_resolve_effective());
  bm_lang_apply_live_vram();
}
#endif

void bm_content_clear(const uint8_t *rom) {
  if (owner != rom) return;
  report();
  free(backing);
  backing = NULL;
  owner = NULL;
#ifdef BM_LANG_R47_SUPPORT
  s_lang_mounted = 0;
  s_lang_ctrl_offset = 0;
  s_lang_data_offset = 0;
  s_lang_data_size = 0;
  s_lang_effective = 0;
#endif
}

void bm_content_load(uint8_t *rom, size_t size) {
  if (owner) bm_content_clear(owner);
  if (size != BM_SEVEN_ROM_SIZE || !matches(rom, size, bm_seven_rom_sha))
    fail("ROM identity differs");
  bm_load_launch_settings();
  const char *event30 = getenv("BM_MAZO_EVENT30");
  if (!(event30 && event30[0] == '0' && event30[1] == 0)) rom[0x2d638] = 0x30;
  backing = calloc(size+1, 1);
  if (!backing) fail("backing allocation failed");
  memcpy(backing, rom, size);
  for (unsigned i = 0; i < BM_SEVEN_PACKS; ++i) {
    const BmSevenPack *pack = &bm_seven_packs[i];
    if (pack->offset > size || pack->size > size-pack->offset ||
        pack->size > 0x8000-(pack->offset & 0x7fff)) fail("pack mapping exceeds bank");
    for (unsigned previous = 0; previous < i; ++previous)
      if (bm_seven_packs[previous].bank == pack->bank) fail("duplicate mapped bank");
    const char *path = getenv(pack->variable);
    if (!path || !*path) fail(pack->variable);
    FILE *file = fopen(path, "rb");
    if (!file) fail("cannot open pack");
    size_t count = fread(backing+pack->offset, 1, pack->size, file);
    int extra = fgetc(file), error = ferror(file);
    fclose(file);
    if (count != pack->size || extra != EOF || error) fail("pack size differs");
    if (!matches(backing+pack->offset, pack->size, pack->sha256)) fail("pack SHA-256 differs");
    resolutions[i] = 0;
  }
  owner = rom;
#ifdef BM_LANG_R47_SUPPORT
  {
    const BmSevenPack *code_pack = NULL;
    const BmSevenPack *data_pack = NULL;
    for (unsigned i = 0; i < BM_SEVEN_PACKS; ++i) {
      const BmSevenPack *pack = &bm_seven_packs[i];
      if (strcmp(pack->variable, "BM_LANG_R47_CODE_PACK") == 0)
        code_pack = pack;
      else if (strcmp(pack->variable, "BM_LANG_R47_DATA_PACK") == 0)
        data_pack = pack;
    }
    if (code_pack && data_pack) {
      s_lang_ctrl_offset = (((size_t)(code_pack->bank & 0x7fu) << 15) | 0x0FF0u);
      s_lang_data_offset = data_pack->offset;
      s_lang_data_size = data_pack->size;
      s_lang_mounted = 1;
      snes_host_register_lang_sync(&bm_lang_sync_from_host);
      bm_lang_write_ctrl(bm_lang_resolve_effective());
    }
  }
#endif
  if (!registered) { atexit(report); registered = 1; }
  fprintf(stderr, "[native-seven] mounted immutable A2/A5/A6/B6 views\n");
}

/* The region runtime reads the same backing map. It must not copy the image,
 * because that copy would miss the sprite packs mounted above. */
uint8_t *bm_content_backing(uint8_t *rom, size_t size) {
  if (rom != owner || !backing || size != BM_SEVEN_ROM_SIZE) return NULL;
  return backing;
}

uint8_t *bm_content_resolve(const uint8_t *rom, uint8_t bank, uint16_t address) {
  bm_seven_return_override();
  bm_yoshi_start_override();
  bm_mazo_map_node_override();
  bm_room_music_override();
  if (rom != owner || !backing || address < 0x8000) return NULL;
  for (unsigned i = 0; i < BM_SEVEN_PACKS; ++i) {
    const BmSevenPack *pack = &bm_seven_packs[i];
    if (bank != pack->bank) continue;
    size_t offset = ((size_t)(bank & 0x7f) << 15) | (address & 0x7fff);
    if (offset >= pack->offset && offset-pack->offset < pack->size) ++resolutions[i];
    return backing+offset;
  }
  return NULL;
}
