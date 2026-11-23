#ifndef BM_NATIVE_MODS_H
#define BM_NATIVE_MODS_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Trusted plugin states driven by snes_mod_runtime (mods/preloaded/state.toml). */
int bm_mod_widescreen_enabled(void);
int bm_mod_no_sprite_limits_enabled(void);
int bm_mod_pack_overrides_enabled(void);

/* Resolve an optional override file for a mounted BM_* pack.
 * Checks BM_MOD_OVERRIDES_DIR first, then active mod package roots under
 * <pkg_root>/overrides/<var_name>.bin or <pkg_root>/overrides/<basename>.
 * Returns 1 if an override file exists and was written to out_path, else 0. */
int bm_mod_resolve_pack_override(const char *var_name,
                                 const char *default_path,
                                 char *out_path,
                                 size_t out_cap);

/* Log installed and active mod packages once per session. */
void bm_mod_log_summary(void);

/* Apply any active .snesmod / BM_MOD_OVERRIDES_DIR overrides for non-executable
 * mounted packs directly onto the shared backing map (idempotent, runs once). */
void bm_mod_apply_pack_overrides(void);

#ifdef __cplusplus
}
#endif

#endif /* BM_NATIVE_MODS_H */
