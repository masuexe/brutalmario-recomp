import configparser
import hashlib
import os
import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import runtime_patches


def _sdl_cflags() -> list[str]:
  return subprocess.check_output(["sdl2-config", "--cflags"], text=True).split()


def _runtime_include_flags() -> list[str]:
  return [
      f"-I{ROOT / 'local/runtime/runner/src/desktop'}",
      f"-I{ROOT / 'local/runtime/runner/src'}",
      f"-I{ROOT / 'local/upstream/snesrecomp/runner/src/desktop'}",
      f"-I{ROOT / 'local/upstream/snesrecomp/runner/src'}",
      f"-I{ROOT / 'local/upstream/snesrecomp/runner/third_party'}",
  ]


class LanguageRuntimeTests(unittest.TestCase):

  def test_runtime_patches_prepare_and_config_layout(self):
    out = runtime_patches.prepare_runtime()
    self.assertTrue(len(out) >= 13)

    cfg_h = (ROOT / "local/runtime/runner/src/desktop/config.h").read_text()
    self.assertIn("  uint8 has_keyboard_controls;\n  char language[16];\n} Config;", cfg_h)

    host_c = (ROOT / "local/runtime/runner/src/desktop/host_main.c").read_text()
    self.assertIn('"Language = auto\\n"', host_c)
    self.assertIn("GAME SETTINGS", host_c)
    self.assertIn("lang en|ja|auto", host_c)

    mmx_c = (ROOT / "local/runtime/runner/src/desktop/mmx_config.c").read_text()
    self.assertNotIn("SDLK_o", mmx_c)
    self.assertNotIn("SDLK_ESCAPE", mmx_c)

  def test_config_language_persistence_roundtrip(self):
    runtime_patches.prepare_runtime()
    with tempfile.TemporaryDirectory() as td:
      td_path = pathlib.Path(td)
      harness = td_path / "cfg_test.c"
      exe = td_path / "cfg_test"
      harness.write_text(r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "sdl_compat.h"

void NORETURN Die(const char *error) {
  fprintf(stderr, "Die: %s\n", error ? error : "");
  exit(1);
}

int main(int argc, char **argv) {
  const char *ini = argv[1];
  ParseConfigFile(ini);
  printf("parsed=%s\n", g_config.language);
  if (argc >= 3) {
    snprintf(g_config.language, sizeof(g_config.language), "%s", argv[2]);
    WriteConfigFile(ini);
  }
  return 0;
}
''')
      # Minimal stub for SDL_GetKeyFromName so util.c + mmx_config.c link without libSDL2
      sdl_stub = td_path / "sdl_stub.c"
      sdl_stub.write_text('''
int SDL_GetKeyFromName(const char *name) { (void)name; return 0; }
''')
      cmd = (
          ["gcc", "-O2", "-Wall", "-Wextra", "-std=c11"]
          + _runtime_include_flags()
          + _sdl_cflags()
          + [
              str(harness),
              str(sdl_stub),
              str(ROOT / "local/runtime/runner/src/desktop/mmx_config.c"),
              str(ROOT / "local/upstream/snesrecomp/runner/src/util.c"),
              "-o",
              str(exe),
          ]
      )
      subprocess.run(cmd, check=True)

      ini_path = td_path / "config.ini"
      ini_path.write_text("[General]\n# Keep comment\nAutosave = 0\n\n[Graphics]\nWindowScale = 3\n")
      r = subprocess.run([str(exe), str(ini_path)], check=True, text=True, capture_output=True)
      self.assertEqual(r.stdout.strip(), "parsed=auto")

      # Write language = ja and verify roundtrip + comment preservation
      r = subprocess.run([str(exe), str(ini_path), "ja"], check=True, text=True, capture_output=True)
      text = ini_path.read_text()
      self.assertIn("# Keep comment", text)
      self.assertIn("Language = ja", text)

      r = subprocess.run([str(exe), str(ini_path)], check=True, text=True, capture_output=True)
      self.assertEqual(r.stdout.strip(), "parsed=ja")

      # Aliases & unknown fallback
      for raw, expected in [("JP", "ja"), ("Japanese", "ja"), ("English", "en"), ("unknown", "auto")]:
        ini_path.write_text(f"[General]\nLanguage = {raw}\n")
        r = subprocess.run([str(exe), str(ini_path)], check=True, text=True, capture_output=True)
        self.assertEqual(r.stdout.strip(), f"parsed={expected}")

  def test_release_launcher_lang_cli(self):
    with tempfile.TemporaryDirectory() as td:
      td_path = pathlib.Path(td)
      launcher = td_path / "BrutalMarioLauncher"
      subprocess.run(
          [
              "gcc",
              "-O2",
              "-Wall",
              "-Wextra",
              "-Werror",
              "-std=c11",
              f"-I{ROOT / 'local/upstream/snesrecomp/runner/src'}",
              str(ROOT / "recomp/bm_release_launcher.c"),
              str(ROOT / "local/upstream/snesrecomp/runner/src/sha256.c"),
              "-o",
              str(launcher),
          ],
          check=True,
      )
      mock_game_c = td_path / "mock_game.c"
      mock_game_c.write_text('''
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
  const char *v = getenv("BM_LANG");
  printf("BM_LANG=%s\\n", v ? v : "(unset)");
  for (int i = 1; i < argc; i++) printf("ARG=%s\\n", argv[i]);
  return 0;
}
''')
      (td_path / "bin").mkdir()
      (td_path / "config").mkdir()
      (td_path / "data").mkdir()
      (td_path / "patch").mkdir()
      subprocess.run(["gcc", str(mock_game_c), "-o", str(td_path / "bin/BrutalMario")], check=True)
      rom_bytes = b"\x00" * 16
      (td_path / "data/rom.sfc").write_bytes(rom_bytes)
      rom_sha_hex = hashlib.sha256(rom_bytes).hexdigest()
      (td_path / "config/packs.manifest").write_text(
          f"# Brutal Mario Native PC Content Manifest\nROM\tdata/rom.sfc\t{len(rom_bytes)}\t{rom_sha_hex}\n"
      )
      rel_path = b"data/rom.sfc"
      body = (
          b"BMPT\x01\x00\x00\x00"
          + struct.pack("<I", 0)
          + (b"\x00" * 32)
          + struct.pack("<I", 1)
          + struct.pack("<H", len(rel_path))
          + rel_path
          + struct.pack("<I", len(rom_bytes))
          + hashlib.sha256(rom_bytes).digest()
          + struct.pack("<I", 0)
      )
      (td_path / "patch/brutalmario.bmpatch").write_bytes(body + hashlib.sha256(body).digest())

      env = dict(os.environ)
      env.pop("DISPLAY", None)
      env.pop("WAYLAND_DISPLAY", None)
      env.pop("BM_LANG", None)
      env["BM_NO_MSGBOX"] = "1"

      for flag, expected in [
          (["--lang", "ja"], "BM_LANG=ja"),
          (["--lang=en"], "BM_LANG=en"),
          (["--lang", "jp"], "BM_LANG=ja"),
          (["--lang=auto"], "BM_LANG=auto"),
      ]:
        r = subprocess.run(
            [str(launcher)] + flag,
            cwd=td_path,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(r.returncode, 0, f"{flag}: stdout={r.stdout!r} stderr={r.stderr!r}")
        self.assertIn(expected, r.stdout.splitlines())
        self.assertNotIn(f"ARG={flag[0]}", r.stdout)

      bad = subprocess.run(
          [str(launcher), "--lang", "fr"],
          cwd=td_path,
          env=env,
          text=True,
          capture_output=True,
      )
      self.assertEqual(bad.returncode, 2)

  def test_native_seven_compiles_with_and_without_r47_flag(self):
    with tempfile.TemporaryDirectory() as td:
      td_path = pathlib.Path(td)
      (td_path / "native_seven_manifest.h").write_text(
          """
#ifndef TEST_MANIFEST_H
#define TEST_MANIFEST_H
#include <stdint.h>
#define BM_SEVEN_ROM_SIZE 0x400000
#define BM_SEVEN_PACKS 1
static const uint8_t bm_seven_rom_sha[32] = {0};
typedef struct {
  const char *variable;
  uint8_t bank;
  size_t offset;
  size_t size;
  uint8_t executable;
  unsigned first_page;
  unsigned last_page;
  uint8_t sha256[32];
} BmSevenPack;
static const BmSevenPack bm_seven_packs[1] = {
  { "DUMMY", 0x90, 0x080000, 16, 0, 0, 0, {0} }
};
#endif
"""
      )
      for extra in ([], ["-DBM_LANG_R47_SUPPORT"]):
        subprocess.run(
            [
                "gcc",
                "-c",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-std=c11",
                f"-I{td_path}",
                f"-I{ROOT / 'recomp'}",
                f"-I{ROOT / 'local/upstream/snesrecomp/runner/src'}",
                f"-I{ROOT / 'local/upstream/snesrecomp/runner/src/snes'}",
            ]
            + extra
            + [str(ROOT / "recomp/native_seven.c"), "-o", str(td_path / "seven.o")],
            check=True,
        )

  def test_host_locale_settings_cheat_and_bmlg_vram_bridge(self):
    runtime_patches.prepare_runtime()
    with tempfile.TemporaryDirectory() as td:
      td_path = pathlib.Path(td)
      # Build synthetic BMLG v1 pack ($D5:8000) and code pack ($90:8000)
      rom_bytes = b"\x00" * 0x400000
      rom_sha = hashlib.sha256(rom_bytes).digest()
      code_pack = b"\x00" * 4096
      code_sha = hashlib.sha256(code_pack).digest()

      def fill_2kb(tag_byte: int) -> bytes:
        return bytes([(tag_byte + (i & 0x3F)) & 0xFF for i in range(2048)])

      ja_028 = fill_2kb(0x10)
      ja_02a = fill_2kb(0x20)
      ja_02b = fill_2kb(0x30)
      en_028 = fill_2kb(0x40)
      en_02a = fill_2kb(0x50)
      en_02b = fill_2kb(0x60)

      # 96 * 19 OW names
      ja_ow = bytearray(96 * 19)
      en_ow = bytearray(96 * 19)
      ow_flags = bytearray(96)
      for t in range(96):
        for j in range(19):
          ja_ow[t * 19 + j] = (0x80 + (t & 0x1F) + j) & 0xFF
          en_ow[t * 19 + j] = (0x40 + (t & 0x1F) + j) & 0xFF
      ow_flags[0x01] = 1   # JP-only OW translevel
      ow_flags[0x29] = 0   # EN OW translevel

      # Messages (144 slots):
      # slot 0 (translevel 0, msg 1) -> needs_jp_font = 1
      # slot 8 (translevel 4, msg 1, remapped from room 0x106) -> needs_jp_font = 0
      # slot 0x50 (translevel 0x28, $187A=0) and 0x51 ($187A=1)
      ja_blob = bytearray()
      en_blob = bytearray()
      ja_ptrs = []
      en_ptrs = []
      msg_flags = bytearray(144)
      for s in range(144):
        ja_ptrs.append(len(ja_blob))
        ja_blob.extend(bytes([0x90 + (s & 0x1F), 0x91, 0x92, 0xFE]))
        en_ptrs.append(len(en_blob))
        en_blob.extend(bytes([0x0A + (s & 0x1F), 0x0B, 0x0C, 0xFE]))
      msg_flags[0] = 1
      msg_flags[8] = 0

      mazo_192 = bytes([0xA1, 0xA2, 0xA3, 0xFE] + [0x1F] * 66)
      mazo_191 = bytes([0xB1, 0xB2, 0xB3, 0xFE] + [0x1F] * 82)
      room_policy = bytearray(512)
      room_policy[0x1C5] = 1
      remap = bytes([1]) + struct.pack("<HB", 0x0106, 0x04)
      title_stripe = b"\x00" * 64

      cursor = 64
      sections = []
      offs = []
      for chunk in [
          ja_028, ja_02a, ja_02b, en_028, en_02a, en_02b,
          bytes(ja_ow), bytes(en_ow), bytes(ow_flags),
          b"".join(struct.pack("<H", p) for p in ja_ptrs), bytes(ja_blob),
          b"".join(struct.pack("<H", p) for p in en_ptrs), bytes(en_blob),
          bytes(msg_flags), mazo_192, mazo_191, bytes(room_policy), remap, title_stripe,
      ]:
        offs.append(cursor)
        sections.append(chunk)
        cursor += len(chunk)
      total_size = cursor
      header = struct.pack(
          "<4sHHI22H8x",
          b"BMLG", 1, 64, total_size,
          offs[0], offs[1], offs[2], offs[3], offs[4], offs[5],
          offs[6], offs[7], offs[8],
          offs[9], offs[10], len(ja_blob),
          offs[11], offs[12], len(en_blob),
          offs[13], offs[14], offs[15], offs[16], offs[17], offs[18], len(title_stripe),
      )
      data_pack = header + b"".join(sections)
      data_sha = hashlib.sha256(data_pack).digest()

      code_path = td_path / "code.bin"
      data_path = td_path / "data.bin"
      code_path.write_bytes(code_pack)
      data_path.write_bytes(data_pack)

      def c_arr(b: bytes) -> str:
        return "{" + ",".join(str(x) for x in b) + "}"

      (td_path / "native_seven_manifest.h").write_text(f"""
#ifndef TEST_SEVEN_MANIFEST_H
#define TEST_SEVEN_MANIFEST_H
#include <stdint.h>
#define BM_SEVEN_ROM_SIZE 0x400000u
#define BM_SEVEN_PACKS 2
static const uint8_t bm_seven_rom_sha[32] = {c_arr(rom_sha)};
typedef struct {{
  const char *variable;
  uint8_t bank;
  size_t offset;
  size_t size;
  uint8_t executable;
  unsigned first_page;
  unsigned last_page;
  uint8_t sha256[32];
}} BmSevenPack;
static const BmSevenPack bm_seven_packs[2] = {{
  {{ "BM_LANG_R47_CODE_PACK", 0x90, 0x080000u, {len(code_pack)}u, 1, 0, 0, {c_arr(code_sha)} }},
  {{ "BM_LANG_R47_DATA_PACK", 0xD5, 0x2A8000u, {len(data_pack)}u, 0, 0, 0, {c_arr(data_sha)} }}
}};
#endif
""")

      stubs = td_path / "stubs.c"
      stubs.write_text(r'''
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct Snes Snes;
typedef struct Ppu Ppu;

Snes *g_snes = NULL;
uint8_t g_ram[0x20000];
Ppu *g_ppu = NULL;
void *g_cpu = NULL;
const char *g_last_recomp_func = "";
char g_rtl_game_info[256];
bool dsp_available = false;
int snes_frame_counter = 0;

void FrameDump_Init(void) {}
void FrameDump_Ppu(void) {}
void FrameDump_Present(void) {}
void OpenGLRenderer_Create(void *f) { (void)f; }
void OpenGLRenderer_RequestScreenshot(void) {}
void PpuBeginDrawing(void) {}
void PpuSetExtraSpace(void) {}
void RecompStackDump(void) {}
void RtlAudioSetFastForward(void) {}
uint32_t RtlAudioTrimBacklog(void) { return 0; }
void RtlEnableExtendedFrameTiming(void) {}
void RtlLastFramePeriods(void) {}
void RtlLoadSnapshot(void) {}
int RtlPlayerCount(void) { return 1; }
void RtlReadSram(void) {}
void RtlRegisterGame(void) {}
void RtlRenderAudio(void) {}
void RtlReset(void) {}
void RtlRunFrame(void) {}
bool RtlSaveLoad(void) { return false; }
void RtlSetAudioBufferTarget(void) {}
void RtlSetAudioOutputRate(void) {}
void RtlSetPadState(void) {}
uint64_t RtlStateGeneration(void) { return 0; }
void RtlWidescreenPresent(void) {}
void RtlWriteSram(void) {}
Snes *SnesInit(void) { return NULL; }
void audio_trace_get_stats(void) {}
void audio_trace_on_output_underflow(void) {}
uint32_t crc32_compute(void) { return 0; }
uint32_t crc32_update(void) { return 0; }
void host_report_breadcrumb(void) {}
void host_report_crash_test_tick(void) {}
void host_report_fatal(void) {}
void host_report_init(void) {}
void keybinds_init(void) {}
uint32_t keybinds_read_player_runner(void) { return 0; }
void msu1_set_rom_path(void) {}
void recomp_post_mortem_dump(void) {}
double snes_host_clock_alpha(void) { return 0.0; }
double snes_host_clock_next_deadline(void) { return 0.0; }
void snes_host_clock_presentation_done(void) {}
bool snes_host_clock_presentation_due(void) { return false; }
void snes_host_clock_reset(void) {}
void snes_host_clock_simulation_done(void) {}
bool snes_host_clock_simulation_due(void) { return false; }
const uint32_t *snes_osd_image(int *w, int *h) { *w=0;*h=0; return NULL; }
void snes_osd_note_frame(void) {}
void snes_osd_note_volume(void) {}
void snes_osd_present_done(void) {}
void snes_osd_set_fps_visible(void) {}
void snes_osd_set_turbo(void) {}
void snes_osd_toggle_fps(void) {}
const uint32_t *snes_osd_volume_image(int *w, int *h) { *w=0;*h=0; return NULL; }
void snes_rewind_close(void) {}
void snes_rewind_commit(void) {}
void snes_rewind_configure(void) {}
bool snes_rewind_is_open(void) { return false; }
void snes_rewind_note_frame(void) {}
void snes_rewind_note_framebuffer(void) {}
bool snes_rewind_open(void) { return false; }
bool snes_rewind_overlay_image(const uint32_t **o, int *w, int *h) { (void)o;*w=0;*h=0; return false; }
void snes_rewind_set_defaults(void) {}
void snes_rewind_shutdown(void) {}
void snes_rewind_step(void) {}
void snes_runahead_configure(void) {}
void snes_runahead_run_frame(void) {}
void snes_runahead_set_capture(void) {}
void snes_runahead_set_frames(void) {}
void snes_runahead_shutdown(void) {}
void snes_savestate_menu_close(void) {}
uint32_t snes_savestate_menu_filter_guest_input(uint32_t i) { return i; }
void snes_savestate_menu_handle_key(void) {}
bool snes_savestate_menu_is_open(void) { return false; }
void snes_savestate_menu_note_frame(void) {}
bool snes_savestate_menu_overlay_image(const uint32_t **o, int *w, int *h) { (void)o;*w=0;*h=0; return false; }
void snes_savestate_menu_poll_nav(void) {}
void snes_savestate_menu_poll_open(void) {}
void snes_savestate_menu_set_compose(void) {}
void snes_state_dump(void) {}
int snesrecomp_anchor_to_exe_dir(void) { return 0; }
int snesrecomp_exe_dir_path(void) { return 0; }
void snesrecomp_host_args_parse(void) {}
bool snesrecomp_host_args_reject_unknown(void) { return true; }
void snesrecomp_host_args_usage(void) {}
void snesrecomp_host_relaunch(void) {}
bool snesrecomp_launcher_resolve_rom_sha256(void) { return false; }
void snesrecomp_opengl_set_viewport(void) {}
void snesrecomp_opengl_set_vsync(void) {}
uint64_t interp816_page_insns(unsigned p) { (void)p; return 0; }
void tier2_capture_configure(void) {}
''')

      harness = td_path / "host_bridge_test.c"
      harness.write_text(r'''
#define _POSIX_C_SOURCE 200809L
#define main host_orig_main
#include "host_main.c"
#undef main
#include "native_content.h"

extern Snes *g_snes;

static uint8 s_draw_buf[1024 * 896 * 4];
static void TestBeginDraw(int w, int h, uint8 **pixels, int *pitch) {
  (void)h;
  *pixels = s_draw_buf;
  *pitch = w * 4;
}
static void TestEndDraw(void) {}
static bool TestInit(SDL_Window *w) { (void)w; return true; }
static void TestDestroy(void) {}
static void TestGetOut(int *w, int *h) { *w = 512; *h = 448; }

static void AssertEqInt(int got, int exp, const char *msg) {
  if (got != exp) {
    fprintf(stderr, "FAIL %s: got=%d exp=%d\n", msg, got, exp);
    exit(1);
  }
}
static void AssertEqStr(const char *got, const char *exp, const char *msg) {
  if (!got || strcmp(got, exp) != 0) {
    fprintf(stderr, "FAIL %s: got=%s exp=%s\n", msg, got ? got : "(null)", exp);
    exit(1);
  }
}

int main(int argc, char **argv) {
  const char *ini_path = argv[1];
  const char *ppm_path = argv[2];
  (void)argc;

  /* 1. Locale detection matrix */
  g_active_config_file = ini_path;
  snprintf(g_config.language, sizeof(g_config.language), "auto");
  g_lang_boot_override[0] = 0;
  g_settings_script_active = 0;

  setenv("BM_LANG_TEST_LOCALE", "ja_JP.UTF-8", 1);
  AssertEqInt(snes_host_get_effective_language(), 1, "test_locale ja_JP");
  setenv("BM_LANG_TEST_LOCALE", "zh_CN.UTF-8", 1);
  AssertEqInt(snes_host_get_effective_language(), 0, "test_locale zh_CN -> en");
  setenv("BM_LANG_TEST_LOCALE", "en_US.UTF-8", 1);
  AssertEqInt(snes_host_get_effective_language(), 0, "test_locale en_US");
  unsetenv("BM_LANG_TEST_LOCALE");

  setenv("LC_ALL", "C", 1);
  setenv("LANG", "ja_JP.UTF-8", 1);
  AssertEqInt(snes_host_get_effective_language(), 0, "LC_ALL=C beats LANG=ja");
  unsetenv("LC_ALL");
  setenv("LC_MESSAGES", "ja_JP.UTF-8", 1);
  setenv("LANG", "en_US.UTF-8", 1);
  AssertEqInt(snes_host_get_effective_language(), 1, "LC_MESSAGES=ja beats LANG=en");
  unsetenv("LC_MESSAGES");

  /* --script determinism */
  setenv("BM_LANG_TEST_LOCALE", "ja_JP.UTF-8", 1);
  g_settings_script_active = 1;
  AssertEqInt(snes_host_get_effective_language(), 0, "script auto defaults to en");
  snprintf(g_lang_boot_override, sizeof(g_lang_boot_override), "auto");
  AssertEqInt(snes_host_get_effective_language(), 1, "script explicit BM_LANG=auto honors locale");
  g_lang_boot_override[0] = 0;
  g_settings_script_active = 0;

  /* 2. Mount BMLG + code pack via bm_content_load */
  static uint8_t rom[0x400000];
  memset(rom, 0, sizeof(rom));
  Snes snes = {0};
  Ppu ppu = {0};
  snes.ppu = &ppu;
  g_snes = &snes;

  snprintf(g_config.language, sizeof(g_config.language), "ja");
  bm_content_load(rom, sizeof(rom));
  uint8_t *ctrl = bm_content_resolve(rom, 0x90, 0x8FF0);
  if (!ctrl) { fprintf(stderr, "FAIL ctrl resolve\n"); return 1; }
  AssertEqInt(*ctrl, 1, "initial $90:8FF0 = ja (1)");

  /* 3. Settings overlay + PPM dump + config.ini persistence */
  g_renderer_funcs.Initialize = TestInit;
  g_renderer_funcs.Destroy = TestDestroy;
  g_renderer_funcs.GetOutputSize = TestGetOut;
  g_renderer_funcs.BeginDraw = TestBeginDraw;
  g_renderer_funcs.EndDraw = TestEndDraw;
  g_frozen_w = 256;
  g_frozen_h = 224;
  setenv("SNESRECOMP_OVERLAY_DUMP", ppm_path, 1);

  /* Switch to EN via SettingsExecuteCommand, dump and close */
  g_settings_menu_open = 1;
  SettingsExecuteCommand("en");
  AssertEqStr(bm_lang_get_mode(), "en", "bm_lang_get_mode en");
  AssertEqInt(*ctrl, 0, "$90:8FF0 updated to 0");
  SettingsExecuteCommand("close");
  AssertEqInt(g_settings_menu_open, 0, "settings closed");

  /* Re-verify key controls and CheatExecute lang */
  g_settings_menu_open = 1;
  SettingsKeyDown(SDLK_2, 0);
  AssertEqStr(snes_host_get_language_mode(), "ja", "key 2 -> ja");
  AssertEqInt(*ctrl, 1, "$90:8FF0 -> 1");
  SettingsKeyDown(SDLK_LEFT, 0);
  AssertEqStr(snes_host_get_language_mode(), "en", "key LEFT -> en");
  SettingsKeyDown(SDLK_ESCAPE, 0);
  AssertEqInt(g_settings_menu_open, 0, "key ESC closes");

  snprintf(g_cheat_input, sizeof(g_cheat_input), "lang ja");
  CheatExecute();
  AssertEqInt(*ctrl, 1, "cheat lang ja");
  snprintf(g_cheat_input, sizeof(g_cheat_input), "lang toggle");
  CheatExecute();
  AssertEqInt(*ctrl, 0, "cheat lang toggle -> en");
  snprintf(g_cheat_input, sizeof(g_cheat_input), "lang jp");
  CheatExecute();
  AssertEqInt(*ctrl, 1, "cheat lang jp -> ja");

  /* 4. Live VRAM hot-swap tests */
  uint32_t vc = ppu.vramWriteCount;
  /* Title mode 0x07: writes 0x28/0x2A/0x2B */
  g_ram[0x0100] = 0x07;
  bm_lang_set_mode("en");
  AssertEqInt((int)(ppu.vramWriteCount > vc), 1, "vramWriteCount bumped title");
  AssertEqInt(ppu.vram[0x4000] & 0xFF, 0x40, "title EN 0x28 tile0");
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x50, "title EN 0x2A tile0");
  AssertEqInt(ppu.vram[0x4C00] & 0xFF, 0x60, "title EN 0x2B tile0");

  /* OW mode 0x0E: EN translevel 0x29 vs JP-only translevel 0x01 */
  g_ram[0x0100] = 0x0E;
  g_ram[0x13BF] = 0x29;
  bm_lang_apply_live_vram();
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x50, "OW 0x29 EN font");
  AssertEqInt(ppu.vram[0x508B], 0x3900 | ((0x40 + (0x29 & 0x1F)) & 0xFF), "OW 0x29 EN name");

  g_ram[0x13BF] = 0x01; /* needs_jp_font = 1 even in EN mode */
  memset(&ppu.vram[0x508B], 0, 19 * sizeof(uint16_t));
  bm_lang_apply_live_vram();
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x20, "OW 0x01 EN falls back to JA font");

  bm_lang_set_mode("ja");
  AssertEqInt(ppu.vram[0x508B], 0x3900 | ((0x80 + (0x01 & 0x1F)) & 0xFF), "OW 0x01 JA name");

  /* Hovered OW banner mismatch with $13BF (e.g. $03:BB20 drew 0x29 while $13BF == 0x00) */
  bm_lang_set_mode("en");
  g_ram[0x13BF] = 0x29;
  memset(&ppu.vram[0x508B], 0, 19 * sizeof(uint16_t));
  bm_lang_apply_live_vram();
  g_ram[0x13BF] = 0x00; /* stale $13BF while VRAM still displays 0x29 banner */
  bm_lang_set_mode("ja");
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x20, "hovered OW 0x29 JA font");
  AssertEqInt(ppu.vram[0x508B], 0x3900 | ((0x80 + (0x29 & 0x1F)) & 0xFF), "hovered OW 0x29 JA name");
  bm_lang_set_mode("en");
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x50, "hovered OW 0x29 EN font restored");
  AssertEqInt(ppu.vram[0x508B], 0x3900 | ((0x40 + (0x29 & 0x1F)) & 0xFF), "hovered OW 0x29 EN name restored");

  /* Hovered JP-only OW 0x01 with stale $13BF == 0x00 still activates JP font in EN mode */
  g_ram[0x13BF] = 0x01;
  memset(&ppu.vram[0x508B], 0, 19 * sizeof(uint16_t));
  bm_lang_apply_live_vram();
  g_ram[0x13BF] = 0x00;
  bm_lang_set_mode("en");
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x20, "hovered OW 0x01 EN falls back to JA font");
  AssertEqInt(ppu.vram[0x508B], 0x3900 | ((0x40 + (0x01 & 0x1F)) & 0xFF), "hovered OW 0x01 EN name");

  /* Level mode 0x14: room policy + ExGFX shop + open Message Box */
  bm_lang_set_mode("en");
  g_ram[0x0100] = 0x14;
  g_ram[0x010B] = 0xC5; g_ram[0x010C] = 0x01; /* room 0x1C5 persistent_jp_font=1 */
  g_ram[0x1426] = 0;
  bm_lang_apply_live_vram();
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x20, "room 0x1C5 EN falls back to JA font");

  /* ExGFX Shop 0x104 should NOT clobber 0x4800 */
  ppu.vram[0x4800] = 0xABCD;
  g_ram[0x010B] = 0x04; g_ram[0x010C] = 0x01;
  bm_lang_apply_live_vram();
  AssertEqInt(ppu.vram[0x4800], 0xABCD, "shop 0x104 ExGFX preserved");

  /* Remapped room 0x106 -> msg level 0x04 -> slot 8 (needs_jp_font=0), msg open */
  g_ram[0x010B] = 0x06; g_ram[0x010C] = 0x01;
  g_ram[0x13BF] = 0x00;
  g_ram[0x1426] = 1;
  bm_lang_set_mode("en");
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x50, "room 0x106 msg8 EN font");
  AssertEqInt(ppu.vram[0x50C7], 0x3900 | (0x0A + 8), "room 0x106 msg8 EN byte 0");
  AssertEqInt(ppu.vram[0x50CA], 0x391F, "room 0x106 msg8 FE pad");
  bm_lang_set_mode("ja");
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x20, "room 0x106 msg8 JA font");
  AssertEqInt(ppu.vram[0x50C7], 0x3900 | (0x90 + 8), "room 0x106 msg8 JA byte 0");

  /* Mazo 0x192 ($1426==1) and 0x191 ($1426==2) message-scoped in EN mode */
  bm_lang_set_mode("en");
  g_ram[0x010B] = 0x92; g_ram[0x010C] = 0x01;
  g_ram[0x13BF] = 0x00;
  g_ram[0x1426] = 1;
  bm_lang_apply_live_vram();
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x20, "mazo 0x192 $1426=1 EN falls back to JA font");
  AssertEqInt(ppu.vram[0x50C7], 0x39A1, "mazo 0x192 byte 0");

  g_ram[0x010B] = 0x91; g_ram[0x010C] = 0x01;
  g_ram[0x1426] = 2;
  bm_lang_apply_live_vram();
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x20, "mazo 0x191 $1426=2 EN falls back to JA font");
  AssertEqInt(ppu.vram[0x50C7], 0x39B1, "mazo 0x191 byte 0");

  /* Mazo $1426 mismatch (room 0x191 with $1426==1 uses normal msg_slot, NOT mazo_191) */
  g_ram[0x010B] = 0x91; g_ram[0x010C] = 0x01;
  g_ram[0x13BF] = 0x04; /* msg_slot 8 has msg_flags[8]=0 */
  g_ram[0x1426] = 1;
  bm_lang_apply_live_vram();
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x50, "mazo 0x191 $1426=1 mismatch keeps EN font");
  AssertEqInt(ppu.vram[0x50C7], 0x3900 | (0x0A + 8), "mazo 0x191 $1426=1 does not load mazo_191");

  /* Room 0x192 with $1426==2 mismatch does NOT load mazo_192 */
  g_ram[0x010B] = 0x92; g_ram[0x010C] = 0x01;
  g_ram[0x13BF] = 0x04;
  g_ram[0x1426] = 2;
  bm_lang_apply_live_vram();
  AssertEqInt(ppu.vram[0x4800] & 0xFF, 0x50, "mazo 0x192 $1426=2 mismatch keeps EN font");
  AssertEqInt(ppu.vram[0x50C7], 0x3900 | (0x0A + 9), "mazo 0x192 $1426=2 does not load mazo_192");

  bm_content_clear(rom);
  printf("ALL_HOST_BRIDGE_CHECKS_OK\n");
  return 0;
}
''')

      ini_path = td_path / "config.ini"
      ini_path.write_text("[General]\nAutosave = 0\n")
      ppm_path = td_path / "settings.ppm"
      exe = td_path / "host_bridge_test"

      sdl_libs = subprocess.check_output(["sdl2-config", "--libs"], text=True).split()
      cmd = (
          ["gcc", "-O2", "-std=c11", "-DBM_LANG_R47_SUPPORT"]
          + _runtime_include_flags()
          + [f"-I{td_path}", f"-I{ROOT / 'recomp'}"]
          + _sdl_cflags()
          + [
              str(harness),
              str(stubs),
              str(ROOT / "local/runtime/runner/src/desktop/mmx_config.c"),
              str(ROOT / "local/upstream/snesrecomp/runner/src/util.c"),
              str(ROOT / "local/upstream/snesrecomp/runner/src/sha256.c"),
              str(ROOT / "local/upstream/snesrecomp/runner/src/snes_overlay_draw.c"),
              str(ROOT / "recomp/native_seven.c"),
          ]
          + sdl_libs
          + ["-o", str(exe)]
      )
      subprocess.run(cmd, check=True)

      env = dict(os.environ)
      env["BM_LANG_R47_CODE_PACK"] = str(code_path)
      env["BM_LANG_R47_DATA_PACK"] = str(data_path)
      env.pop("BM_LANG", None)
      env.pop("LC_ALL", None)
      env.pop("LC_MESSAGES", None)
      env["LANG"] = "en_US.UTF-8"

      r = subprocess.run(
          [str(exe), str(ini_path), str(ppm_path)],
          env=env,
          text=True,
          capture_output=True,
      )
      self.assertEqual(r.returncode, 0, f"stdout={r.stdout}\nstderr={r.stderr}")
      self.assertIn("ALL_HOST_BRIDGE_CHECKS_OK", r.stdout)
      self.assertTrue(ppm_path.is_file())
      ppm_bytes = ppm_path.read_bytes()
      self.assertTrue(ppm_bytes.startswith(b"P6\n512 448\n255\n"))
      self.assertEqual(len(ppm_bytes), len(b"P6\n512 448\n255\n") + 512 * 448 * 3)
      self.assertIn("Language = en", ini_path.read_text())


if __name__ == "__main__":
  unittest.main()
