#include "native_widescreen.h"
#include "native_mods.h"

#include "config.h"
#include "widescreen.h"
#include "snes/ppu.h"
#include "snes/snes.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Config g_config;
extern Snes *g_snes;
extern Ppu *g_ppu;

/* Default 16:9 margin: 72 px per side -> 256 + 144 = 400x224 (aspect 1.7857). */
enum { kBmWsDefaultExtra = 72 };

static int s_ws_env_override = -1; /* -1 = unset, 0 = force off, 1 = force on */
static int s_ws_extra_target = kBmWsDefaultExtra;
static int s_ws_logged_state = -1;

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
    }
  }
}

static int bm_ws_is_enabled(void) {
  bm_ws_init_env();
  if (s_ws_env_override >= 0) return s_ws_env_override;
  if (bm_mod_widescreen_enabled()) return 1;
  return g_config.widescreen ? 1 : 0;
}

void BmWidescreenAfterConfig(void) {
  bm_ws_init_env();
  s_ws_logged_state = -1;
}

void BmWidescreenOnReset(void) {
  /* Per-frame policy re-evaluates live WRAM every frame; nothing sticky. */
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
  int extra = enabled ? s_ws_extra_target : 0;
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

void BmWidescreenApplyFramePolicy(void) {
  if (!g_ws_active || g_ws_extra <= 0 || !g_ppu || !g_snes || !g_snes->ram) {
    return;
  }

  const uint8_t *ram = g_snes->ram;
  uint8_t game_mode = ram[0x0100];
  uint16_t room = (uint16_t)ram[0x010B] | ((uint16_t)ram[0x010C] << 8);
  uint8_t screens = ram[0x005E];
  int cam_x = (int)((uint16_t)ram[0x001A] | ((uint16_t)ram[0x001B] << 8));
  int budget = g_ws_extra;

  /* Overworld map (0x0E): SMW draws a framed 256x224 starry border around the
   * map window on BG3, so center it cleanly inside the 16:9 buffer rather than
   * bleeding raw map tiles outside the border frame. */
  if (game_mode == 0x0E) {
    PpuSetExtraSpaceCentered(g_ppu, (uint16_t)budget);
    bm_ws_clear_unused_margins(g_ppu);
    return;
  }

  /* In-level gameplay (0x14): expand scrolling courses with dynamic edge
   * clamping so margins never wrap past [0, screens * 256). Keep BG3 top
   * status bar / custom gauges (y=0..40) centered and crisp. */
  if (game_mode == 0x14) {
    if (bm_ws_is_centered_room(room, screens)) {
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
    bm_ws_clear_unused_margins(g_ppu);
    return;
  }

  /* Title (0x07), File Select (0x08), transitions, and fade states:
   * center the authentic 256x224 frame inside the widened buffer. */
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
  }
}
