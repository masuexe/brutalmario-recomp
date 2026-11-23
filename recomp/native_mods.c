#include "native_mods.h"
#include "native_content.h"
#include "native_seven_manifest.h"
#include "mod_runtime.h"
#include "snes/cart.h"
#include "snes/snes.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Snes *g_snes;

static int s_mod_widescreen = 0;
static int s_mod_no_sprite_limits = 0;
static int s_mod_pack_overrides = 0;
static int s_mod_summary_logged = 0;

static void bm_mods_reset_cb(void) {
  s_mod_widescreen = 0;
  s_mod_no_sprite_limits = 0;
  s_mod_pack_overrides = 0;
}

static void bm_mod_enable_widescreen_cb(void) {
  s_mod_widescreen = 1;
  fprintf(stderr, "[native-mods] plugin activated: brutalmario.widescreen\n");
}

static void bm_mod_enable_no_sprite_limits_cb(void) {
  s_mod_no_sprite_limits = 1;
  fprintf(stderr, "[native-mods] plugin activated: brutalmario.no_sprite_limits\n");
}

static void bm_mod_enable_pack_overrides_cb(void) {
  s_mod_pack_overrides = 1;
  fprintf(stderr, "[native-mods] plugin activated: brutalmario.pack_overrides\n");
}

SNES_MOD_CONSTRUCTOR(bm_register_trusted_mods) {
  snes_mod_register_reset_callback(bm_mods_reset_cb);
  snes_mod_register_presentation_plugin("brutalmario.widescreen",
                                        bm_mod_enable_widescreen_cb);
  snes_mod_register_presentation_plugin("brutalmario.no_sprite_limits",
                                        bm_mod_enable_no_sprite_limits_cb);
  snes_mod_register_activation_plugin("brutalmario.pack_overrides",
                                      bm_mod_enable_pack_overrides_cb);
}

int bm_mod_widescreen_enabled(void) {
  return s_mod_widescreen;
}

int bm_mod_no_sprite_limits_enabled(void) {
  return s_mod_no_sprite_limits;
}

int bm_mod_pack_overrides_enabled(void) {
  return s_mod_pack_overrides;
}

static int file_exists_readable(const char *path) {
  if (!path || !path[0]) return 0;
  FILE *f = fopen(path, "rb");
  if (!f) return 0;
  fclose(f);
  return 1;
}

static const char *path_basename(const char *path) {
  if (!path) return "";
  const char *slash = strrchr(path, '/');
  const char *bslash = strrchr(path, '\\');
  const char *sep = slash;
  if (bslash && (!sep || bslash > sep)) sep = bslash;
  return sep ? sep + 1 : path;
}

static int try_override_in_dir(const char *dir,
                               const char *var_name,
                               const char *base_name,
                               char *out_path,
                               size_t out_cap) {
  if (!dir || !dir[0] || !out_path || out_cap < 16) return 0;
  if (var_name && var_name[0]) {
    int n = snprintf(out_path, out_cap, "%s/%s.bin", dir, var_name);
    if (n > 0 && (size_t)n < out_cap && file_exists_readable(out_path)) {
      return 1;
    }
  }
  if (base_name && base_name[0]) {
    int n = snprintf(out_path, out_cap, "%s/%s", dir, base_name);
    if (n > 0 && (size_t)n < out_cap && file_exists_readable(out_path)) {
      return 1;
    }
  }
  return 0;
}

int bm_mod_resolve_pack_override(const char *var_name,
                                 const char *default_path,
                                 char *out_path,
                                 size_t out_cap) {
  if (!out_path || out_cap == 0) return 0;
  out_path[0] = '\0';
  const char *base_name = path_basename(default_path);

  /* 1. Explicit directory override (env-gated for dev/testing or portable drop-in). */
  const char *env_dir = getenv("BM_MOD_OVERRIDES_DIR");
  if (env_dir && env_dir[0]) {
    if (try_override_in_dir(env_dir, var_name, base_name, out_path, out_cap)) {
      return 1;
    }
  }

  /* 2. Active .snesmod packages from snes_mod_runtime (plan rows). */
  SnesModPkgRow rows[32];
  int count = snes_mod_runtime_plan_rows_c(rows, 32);
  for (int i = 0; i < count; ++i) {
    char pkg_root[1024];
    if (!snes_mod_runtime_package_root_c(rows[i].id, rows[i].version,
                                         pkg_root, sizeof(pkg_root))) {
      continue;
    }
    char ov_dir[1152];
    int n = snprintf(ov_dir, sizeof(ov_dir), "%s/overrides", pkg_root);
    if (n > 0 && (size_t)n < sizeof(ov_dir)) {
      if (try_override_in_dir(ov_dir, var_name, base_name, out_path, out_cap)) {
        return 1;
      }
    }
  }

  return 0;
}

void bm_mod_log_summary(void) {
  if (s_mod_summary_logged) return;
  s_mod_summary_logged = 1;
  SnesModPkgRow installed[32];
  SnesModPkgRow active[32];
  int n_inst = snes_mod_runtime_installed_rows_c(installed, 32);
  int n_act = snes_mod_runtime_plan_rows_c(active, 32);
  fprintf(stderr, "[native-mods] installed=%d active=%d widescreen=%d no_sprite_limits=%d pack_overrides=%d\n",
          n_inst, n_act, s_mod_widescreen, s_mod_no_sprite_limits, s_mod_pack_overrides);
  for (int i = 0; i < n_act; ++i) {
    fprintf(stderr, "[native-mods] active_pkg=%s@%s features=%s\n",
            active[i].id, active[i].version, active[i].features);
  }
}

void bm_mod_apply_pack_overrides(void) {
  static int s_overrides_applied = 0;
  if (s_overrides_applied) return;
  if (!g_snes || !g_snes->cart || !g_snes->cart->rom) return;
  uint8_t *backing = bm_content_backing(g_snes->cart->rom, g_snes->cart->romSize);
  if (!backing) return;
  s_overrides_applied = 1;

  for (unsigned i = 0; i < BM_SEVEN_PACKS; ++i) {
    const BmSevenPack *pack = &bm_seven_packs[i];
    if (pack->executable) continue;
    const char *def_path = getenv(pack->variable);
    char override_path[1280];
    if (!bm_mod_resolve_pack_override(pack->variable, def_path ? def_path : "",
                                      override_path, sizeof(override_path))) {
      continue;
    }
    FILE *f = fopen(override_path, "rb");
    if (!f) {
      fprintf(stderr, "[native-mods] warning: cannot open override %s\n", override_path);
      continue;
    }
    size_t max_bank_cap = 0x8000u - (pack->offset & 0x7fffu);
    size_t count = fread(backing + pack->offset, 1, max_bank_cap, f);
    int extra = fgetc(f);
    int err = ferror(f);
    fclose(f);
    if (count == 0 || extra != EOF || err) {
      fprintf(stderr, "[native-mods] rejected override pack=%s path=%s (exceeds bank or read error)\n",
              pack->variable, override_path);
      continue;
    }
    fprintf(stderr, "[native-mods] override pack=%s path=%s bytes=%zu\n",
            pack->variable, override_path, count);
  }
}
