#include "native_widescreen.h"
#include "native_mods.h"

#include "config.h"
#include "display_aspect.h"
#include "widescreen.h"
#include "snes/cart.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include "snes/ws_shadow.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Config g_config;
extern Snes *g_snes;
extern Ppu *g_ppu;

/* Default 16:9 margins per side:
 * - 1:1 square pixels (8:7): 72 px/side -> 400x224 (1.7857:1 ~= 16:9).
 * - CRT 7:6 pixels (4:3):    43 px/side -> 342x224 (342*7/6 / 224 = 1.781:1 ~= 16:9). */
enum {
  kBmWsDefaultExtra = 72,
  kBmWsCrtExtra = 43,
};

static int s_ws_env_override = -1; /* -1 = unset, 0 = force off, 1 = force on */
static int s_ws_extra_target = kBmWsDefaultExtra;
static int s_ws_extra_env_set = 0;
static int s_ws_prefill_enabled = 1; /* BM_WS_PREFILL=0 disables Map16 shadow prefill */
static int s_ws_logged_state = -1;
static int s_ws_shadow_active = 0;

static void bm_ws_init_env(void) {
  static int initialized = 0;
  if (initialized) return;
  initialized = 1;

  const char *env = getenv("BM_WIDESCREEN");
  if (env && env[0]) {
    if (env[0] == '0' && env[1] == '\0') s_ws_env_override = 0;
    else s_ws_env_override = 1;
  }

  const char *extra_env = getenv("BM_WIDESCREEN_EXTRA");
  if (extra_env && extra_env[0]) {
    long val = strtol(extra_env, NULL, 10);
    if (val >= 0 && val <= kPpuExtraLeftRight && val <= kWsExtraMax) {
      s_ws_extra_target = (int)val;
      s_ws_extra_env_set = 1;
    }
  }

  const char *prefill_env = getenv("BM_WS_PREFILL");
  if (prefill_env && prefill_env[0] == '0' && prefill_env[1] == '\0') {
    s_ws_prefill_enabled = 0;
  }
}

static int bm_ws_is_enabled(void) {
  bm_ws_init_env();
  if (s_ws_env_override >= 0) return s_ws_env_override;
  if (bm_mod_widescreen_enabled()) return 1;
  return g_config.widescreen ? 1 : 0;
}

int BmWidescreenWindowBaseWidth(int frame_w) {
  int w = 0, h = 0;
  SnesDisplayAspect_ComputePresentationSize(
      frame_w > 0 ? frame_w : 256, 224,
      SnesDisplayAspect_Clamp(g_config.display_aspect), &w, &h);
  return w;
}

int BmWidescreenWindowBaseHeight(void) {
  return 224;
}

void BmWidescreenAfterConfig(void) {
  bm_ws_init_env();
  s_ws_logged_state = -1;
}

void BmWidescreenOnReset(void) {
  if (s_ws_shadow_active) {
    WsShadowReset();
    s_ws_shadow_active = 0;
  }
}

void BmWidescreenPrepareFrame(int drawable_w, int drawable_h,
                              int *frame_w, int *frame_h) {
  (void)drawable_w;
  (void)drawable_h;

  bm_mod_log_summary();
  bm_mod_apply_pack_overrides();
  if (bm_mod_no_sprite_limits_enabled()) {
    g_config.no_sprite_limits = true;
  }

  int enabled = bm_ws_is_enabled();
  int target_extra = s_ws_extra_target;
  if (!s_ws_extra_env_set &&
      SnesDisplayAspect_Clamp(g_config.display_aspect) == kSnesDisplayAspect_Crt4x3) {
    target_extra = kBmWsCrtExtra;
  }
  int extra = enabled ? target_extra : 0;
  if (extra > kPpuExtraLeftRight) extra = kPpuExtraLeftRight;
  if (extra > kWsExtraMax) extra = kWsExtraMax;
  if (extra < 0) extra = 0;

  if (s_ws_logged_state != (enabled ? extra : 0)) {
    s_ws_logged_state = enabled ? extra : 0;
    fprintf(stderr, "[native-widescreen] enabled=%d extra=%d width=%d\n",
            enabled, extra, 256 + 2 * extra);
  }

  *frame_w = 256 + 2 * extra;
  *frame_h = 224;
}

/* Rooms that are authored as single-screen boss arenas, cutscenes, or
 * bounded dialogues where showing extra horizontal margins would expose
 * off-arena tiles. These render cleanly centered (4:3) inside the 16:9 frame. */
static bool bm_ws_is_centered_room(uint16_t room, uint8_t screens) {
  if (screens <= 1) return true;
  switch (room) {
    /* 4-scene New Save intro cutscene */
    case 0x01C5:
    case 0x014B:
    case 0x014C:
    case 0x014D:
    /* Seven Koopalings boss & T test ending */
    case 0x00FF:
    case 0x017B:
    /* Mazo bosses & dialogue corridors */
    case 0x0151:
    case 0x0190:
    case 0x0191:
    case 0x0192:
    /* Special bosses & Center Star */
    case 0x008F:
    case 0x0079:
    /* World castle boss rooms */
    case 0x006E:
    case 0x006F:
    case 0x0070:
    case 0x0071:
    case 0x0072:
      return true;
    default:
      return false;
  }
}

static void bm_ws_clear_unused_margins(Ppu *ppu) {
  if (!ppu || !ppu->renderBuffer || !ppu->renderPitch) return;
  int budget = (int)ppu->extraLeftRight;
  int left_pad = budget - (int)ppu->extraLeftCur;
  int right_pad = budget - (int)ppu->extraRightCur;
  if (left_pad <= 0 && right_pad <= 0) return;
  int total_w = 256 + 2 * budget;
  for (int y = 0; y < 224; ++y) {
    uint8_t *row = ppu->renderBuffer + (size_t)y * (size_t)ppu->renderPitch;
    if (left_pad > 0) {
      memset(row, 0, (size_t)left_pad * 4u);
    }
    if (right_pad > 0) {
      memset(row + (size_t)(total_w - right_pad) * 4u, 0, (size_t)right_pad * 4u);
    }
  }
}

/* Resolve a Lunar Magic / Brutal Mario 16x16 Map16 tile into its four 8x8
 * SNES tilemap words (TL, BL, TR, BR) purely read-only from live WRAM + ROM.
 * Verified 1728/1728 (100%) against live BG1 VRAM in Course 1-1. */
static bool bm_ws_lookup_map16_8x8(const uint8_t *ram, Cart *cart,
                                   uint16_t map16, uint8_t tileset,
                                   uint16_t room, uint16_t out4[4]) {
  uint8_t bank;
  uint16_t addr;
  if (map16 < 0x200u) {
    bank = (tileset < 0x10u) ? 0x0Du : 0x05u;
    size_t ptr_off = 0x0FBEu + (size_t)map16 * 2u;
    addr = (uint16_t)ram[ptr_off] | ((uint16_t)ram[ptr_off + 1u] << 8);
  } else if (map16 < 0x300u) {
    bank = 0x11u;
    addr = (uint16_t)(0x8000u | (((uint16_t)(tileset & 0x0Fu)) << 11) |
                      (((uint16_t)(map16 & 0xFFu)) << 3));
  } else if (map16 < 0x400u) {
    bank = 0x11u;
    addr = (uint16_t)((0xF800u + (((uint16_t)(map16 & 0xFFu)) << 3)) & 0xFFFFu);
  } else {
    bank = (room == 0x0003u) ? 0x41u : 0x12u;
    addr = (uint16_t)((0x6000u + ((uint32_t)map16 << 3)) & 0xFFFFu);
  }
  if (addr < 0x8000u || (uint32_t)addr + 8u > 0x10000u) return false;
  for (int i = 0; i < 4; ++i) {
    uint8_t lo = cart_read(cart, bank, (uint16_t)(addr + i * 2));
    uint8_t hi = cart_read(cart, bank, (uint16_t)(addr + i * 2 + 1));
    out4[i] = (uint16_t)lo | ((uint16_t)hi << 8);
  }
  return true;
}

/* Unwrap a 9-bit PPU scroll (0..511) to the nearest world coordinate around
 * a 16-bit WRAM camera mirror (WIDESCREEN_PATTERNS.md P1). */
static int bm_ws_unwrap_scroll_512(int cam, uint16_t ppu_scroll) {
  int phase = (int)(ppu_scroll & 0x1FFu);
  int base = (cam & ~0x1FF) + phase;
  if (base - cam > 256) base -= 512;
  else if (cam - base > 256) base += 512;
  return base < 0 ? 0 : base;
}

static void bm_ws_prefill_bg1_margins(Ppu *ppu, const uint8_t *ram, Cart *cart,
                                      uint16_t room, uint8_t screens,
                                      int cam_x, int cam_y,
                                      int left_extra, int right_extra,
                                      int budget) {
  /* Horizontal level layout only ($5B bit 0 == 0): 27 rows x 16 cols/screen. */
  if (!s_ws_prefill_enabled || !cart || (ram[0x005B] & 1u) != 0 ||
      screens == 0 || screens > 32) {
    if (s_ws_shadow_active) {
      WsShadowReset();
      s_ws_shadow_active = 0;
    }
    return;
  }

  int world_x = bm_ws_unwrap_scroll_512(cam_x, ppu->hScroll[0]);
  int world_y = bm_ws_unwrap_scroll_512(cam_y, ppu->vScroll[0]);

  WsShadowSetWorld(0, (uint32_t)world_x, (uint32_t)world_y);
  WsShadowSetScroll(0, (uint32_t)ppu->hScroll[0], (uint32_t)ppu->vScroll[0]);
  WsShadowSetRetainHistory(0, false);
  WsShadowFrame(ppu);
  s_ws_shadow_active = 1;

  uint8_t tileset = ram[0x1931];
  int max_wx = (int)screens * 256 - 1;
  int min_x = world_x - left_extra - 16;
  int max_x = world_x + 256 + right_extra + 16;
  if (min_x < 0) min_x = 0;
  if (max_x > max_wx) max_x = max_wx;

  int min_row = world_y >> 4;
  int max_row = (world_y + 224 + 16) >> 4;
  if (min_row < 0) min_row = 0;
  if (max_row > 26) max_row = 26;

  int min_col16 = min_x >> 4;
  int max_col16 = max_x >> 4;
  int view_col_l = world_x >> 4;
  int view_col_r = (world_x + 255) >> 4;

  for (int row = min_row; row <= max_row; ++row) {
    uint32_t ty = (uint32_t)(row * 2);
    for (int col16 = min_col16; col16 <= max_col16; ++col16) {
      /* Seed off-native margin columns plus the straddling edge columns;
       * the authentic [0, 256) viewport always reads live VRAM directly. */
      if (col16 > view_col_l && col16 < view_col_r) continue;
      int scr = col16 >> 4;
      int col = col16 & 15;
      if (scr < 0 || scr >= (int)screens) continue;
      size_t idx = (size_t)scr * 0x1B0u + (size_t)row * 16u + (size_t)col;
      if (idx >= 0x3600u) continue;
      uint16_t m16 = (uint16_t)ram[0x0C800u + idx] |
                     ((uint16_t)ram[0x1C800u + idx] << 8);
      uint16_t t4[4];
      if (!bm_ws_lookup_map16_8x8(ram, cart, m16, tileset, room, t4)) continue;
      uint32_t tx = (uint32_t)(col16 * 2);
      WsShadowForceTile(0, tx,      ty,      t4[0]); /* TL */
      WsShadowForceTile(0, tx,      ty + 1u, t4[1]); /* BL */
      WsShadowForceTile(0, tx + 1u, ty,      t4[2]); /* TR */
      WsShadowForceTile(0, tx + 1u, ty + 1u, t4[3]); /* BR */
    }
  }
}

void BmWidescreenApplyFramePolicy(void) {
  if (!g_ws_active || g_ws_extra <= 0 || !g_ppu || !g_snes || !g_snes->ram) {
    if (s_ws_shadow_active) {
      WsShadowReset();
      s_ws_shadow_active = 0;
    }
    return;
  }

  const uint8_t *ram = g_snes->ram;
  uint8_t game_mode = ram[0x0100];
  uint16_t room = (uint16_t)ram[0x010B] | ((uint16_t)ram[0x010C] << 8);
  uint8_t screens = ram[0x005E];
  int cam_x = (int)((uint16_t)ram[0x001A] | ((uint16_t)ram[0x001B] << 8));
  int cam_y = (int)((uint16_t)ram[0x001C] | ((uint16_t)ram[0x001D] << 8));
  int budget = g_ws_extra;

  /* Overworld map (0x0E): SMW draws a framed 256x224 starry border around the
   * map window on BG3, so center it cleanly inside the 16:9 buffer rather than
   * bleeding raw map tiles outside the border frame. */
  if (game_mode == 0x0E) {
    if (s_ws_shadow_active) { WsShadowReset(); s_ws_shadow_active = 0; }
    PpuSetExtraSpaceCentered(g_ppu, (uint16_t)budget);
    bm_ws_clear_unused_margins(g_ppu);
    return;
  }

  /* In-level gameplay (0x14): expand scrolling courses with dynamic edge
   * clamping so margins never wrap past [0, screens * 256). Keep BG3 top
   * status bar / custom gauges (y=0..40) centered and crisp, and prefill
   * off-native BG1 margin columns from the live Map16 buffer. */
  if (game_mode == 0x14) {
    if (bm_ws_is_centered_room(room, screens)) {
      if (s_ws_shadow_active) { WsShadowReset(); s_ws_shadow_active = 0; }
      PpuSetExtraSpaceCentered(g_ppu, (uint16_t)budget);
      bm_ws_clear_unused_margins(g_ppu);
      return;
    }

    int level_w = (int)screens * 256;
    int left_extra = cam_x < budget ? cam_x : budget;
    if (left_extra < 0) left_extra = 0;

    int right_avail = level_w - (cam_x + 256);
    if (right_avail < 0) right_avail = 0;
    int right_extra = right_avail < budget ? right_avail : budget;

    PpuSetExtraSpace(g_ppu, (uint16_t)budget);
    PpuSetExtraSideSpace(g_ppu, left_extra, right_extra, 0);
    PpuSetWidescreenLayerClampBand(g_ppu, 2, 0, 40);
    bm_ws_prefill_bg1_margins(g_ppu, ram, g_snes->cart, room, screens,
                              cam_x, cam_y, left_extra, right_extra, budget);
    bm_ws_clear_unused_margins(g_ppu);
    return;
  }

  /* Title (0x07), File Select (0x08), transitions, and fade states:
   * center the authentic 256x224 frame inside the widened buffer. */
  if (s_ws_shadow_active) { WsShadowReset(); s_ws_shadow_active = 0; }
  PpuSetExtraSpaceCentered(g_ppu, (uint16_t)budget);
  bm_ws_clear_unused_margins(g_ppu);
}

static void bm_ws_put_le32(uint8_t *p, uint32_t v) {
  p[0] = (uint8_t)(v & 0xFFu);
  p[1] = (uint8_t)((v >> 8) & 0xFFu);
  p[2] = (uint8_t)((v >> 16) & 0xFFu);
  p[3] = (uint8_t)((v >> 24) & 0xFFu);
}

static void bm_ws_write_bmp(const char *dir, const char *name, const Ppu *ppu) {
  if (!dir || !dir[0] || !ppu || !ppu->renderBuffer || !ppu->renderPitch) return;
  uint32_t w = (uint32_t)(256 + 2 * (int)ppu->extraLeftRight);
  uint32_t h = 224u;
  if (ppu->renderPitch < w * 4u) return;
  char path[1024];
  int n = snprintf(path, sizeof(path), "%s/%s.bmp", dir, name);
  if (n <= 0 || (size_t)n >= sizeof(path)) return;
  FILE *f = fopen(path, "wb");
  if (!f) return;
  uint8_t hdr[54] = {'B', 'M'};
  uint32_t sz = w * h * 4u;
  bm_ws_put_le32(hdr + 2, 54u + sz);
  bm_ws_put_le32(hdr + 10, 54u);
  bm_ws_put_le32(hdr + 14, 40u);
  bm_ws_put_le32(hdr + 18, w);
  bm_ws_put_le32(hdr + 22, 0u - h); /* top-down */
  hdr[26] = 1;
  hdr[28] = 32;
  bm_ws_put_le32(hdr + 34, sz);
  fwrite(hdr, 1, sizeof(hdr), f);
  for (uint32_t y = 0; y < h; ++y) {
    fwrite(ppu->renderBuffer + (size_t)y * (size_t)ppu->renderPitch, 4u, w, f);
  }
  fclose(f);
  fprintf(stderr, "[native-widescreen] dumped %s (%ux%u, left=%u right=%u)\n",
          name, w, h, (unsigned)ppu->extraLeftCur, (unsigned)ppu->extraRightCur);
}

void BmWidescreenAfterDraw(void) {
  static int init = 0;
  static const char *dump_dir = NULL;
  static unsigned mask = 0;
  static int title_f = 0, intro_f = 0, ow_f = 0, c105_f = 0;
  if (!init) {
    init = 1;
    dump_dir = getenv("BM_WS_DUMP_DIR");
    if (dump_dir && !dump_dir[0]) dump_dir = NULL;
  }
  if (!dump_dir || !g_ppu || !g_snes || !g_snes->ram) return;

  const uint8_t *ram = g_snes->ram;
  uint8_t mode = ram[0x0100];
  uint16_t room = (uint16_t)ram[0x010B] | ((uint16_t)ram[0x010C] << 8);
  int cam_x = (int)((uint16_t)ram[0x001A] | ((uint16_t)ram[0x001B] << 8));

  if (!(mask & 1u) && mode == 0x07) {
    if (++title_f >= 20) { mask |= 1u; bm_ws_write_bmp(dump_dir, "title", g_ppu); }
  }
  if (!(mask & 2u) && mode == 0x14 && room == 0x01C5) {
    if (++intro_f >= 20) { mask |= 2u; bm_ws_write_bmp(dump_dir, "intro1c5", g_ppu); }
  }
  if (!(mask & 4u) && mode == 0x0E) {
    if (++ow_f >= 20) { mask |= 4u; bm_ws_write_bmp(dump_dir, "overworld", g_ppu); }
  }
  if (!(mask & 8u) && mode == 0x14 && room == 0x0105 && cam_x == 0) {
    if (++c105_f >= 15) { mask |= 8u; bm_ws_write_bmp(dump_dir, "course105_start", g_ppu); }
  }
  if (!(mask & 16u) && mode == 0x14 && room == 0x0105 && cam_x >= 72) {
    mask |= 16u;
    bm_ws_write_bmp(dump_dir, "course105_scrolled", g_ppu);
    WsShadowMarginStat st;
    WsShadowGetMarginStats(0, &st);
    fprintf(stderr,
            "[native-widescreen] bg1_shadow westHit=%llu westMiss=%llu eastHit=%llu eastMiss=%llu "
            "prefillSeed=%llu westRawFallback=%llu eastRawFallback=%llu\n",
            (unsigned long long)st.westHit, (unsigned long long)st.westMiss,
            (unsigned long long)st.eastHit, (unsigned long long)st.eastMiss,
            (unsigned long long)st.prefillSeed,
            (unsigned long long)st.westRawFallback,
            (unsigned long long)st.eastRawFallback);
  }
}
