# Windows cheat console performance repair

## Current finding (2026-11-02)

The roughly 3 FPS regression is resolved in isolated Linux and Windows
candidates. The cause was repeated CRT `getenv` calls in
`recomp/native_seven.c`, on the ROM bus resolution path. The Yoshi-start and
Mazo-node helpers queried launch settings on every access; the Seven-return
helper did so in its selected room. These calls were especially expensive on
Windows. The console overlay was not the cause.

The repair reads the three settings once during `bm_content_load`, then keeps
the existing hook conditions, write ordering and values. Settings refresh on a
subsequent content load. Changing the process environment while content is
already loaded no longer changes these settings; these are launcher options,
not runtime cheat commands. Defaults and exact-string option semantics remain.
The hooks still execute at their original ROM access boundaries.

This finding supersedes the earlier attribution to the build host. Matching
selected generated objects did not exclude the project content resolver.

## Fresh measurements

All runs use isolated saves and headless SDL. These are mean **guest-stage
milliseconds per simulated frame**, not displayed FPS. Turbo is enabled.

| Probe | Before | Repaired |
| --- | ---: | ---: |
| Windows, first 60 frames | 471.193 | 3.320 |
| Linux, first 60 frames | 25.664 | 3.112 |
| Windows, console `help;close`, first 60 frames | — | 3.508 |
| Linux, console `help;close`, first 60 frames | 25.432 | 3.011 |
| Linux, 3,122-frame room190 fixture | 25.144 | 3.115 |
| Windows, same room190 fixture | — | 3.652 |

The Windows and Linux 60-frame before/after checks each retain 12 byte-identical
files: complete WRAM/SRAM/VRAM/CGRAM/OAM, framebuffers and register/trace dumps.
The Linux gameplay regression retains 36 byte-identical files at three samples.
The repaired Windows gameplay run matches all binary dumps and the text dumps
after explicit CRLF/LF normalization against repaired Linux. Room 190 is in
mode 14 and requests slot 9E at all three samples. The map/pipe placement is an
assisted diagnostic fixture; it does not prove ordinary traversal or a win.

The Windows console actually logs OPEN and CLOSED and completes the script.
The C regression checks all three hooks, exact option strings, refresh on load,
and no environment queries across 10,000 resolver calls per case. All 439 tests
pass; the two packaging tests also pass after the packaging tool update.

## Identities and evidence

- Target: `demo11-native-product-r14`.
- ROM: `393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b`.
- Windows candidate: `4f9250135e28f49fe28f441df4bba7ca051619b804d8326d784620d0146598cc`.
- Linux candidate: `bee36989fa7719890c41d8c2c4efe67531faf45a8cea515836d23fa95be28ae8`.
- Evidence: `local/diagnostics/console-perf-20261102/`, with fresh capture
  directories, input identities, scripts, profiles, qualification reports,
  compile/relink commands and unit-test output. Existing builds were preserved;
  each candidate reuses its platform's old link objects, replacing only the
  content resolver object with the patched source.
- Gameplay input: `recomp/inputs/native-console-runtime-smoke.script`.
- Qualifier: `tools/qualify_console_performance.py BEFORE AFTER --output REPORT`.
  Use `--normalize-text-newlines` only for explicit cross-platform comparisons.
- Windows bundle: `local/release/product-r14-console-fixed-windows-qualified-20261102.zip`,
  SHA-256 `c8466922d52938b1379c394712b650d6354948841a5c715cce1290d5db45868c`.
- Linux bundle: `local/release/product-r14-console-fixed-linux-20261102.zip`,
  SHA-256 `fa11dbd9cead16d06e0e9237f5e302ce2bb5e4042e47fd355487f297de9d0c1f`.

Rebuilds use the ordinary project runtime source. To package an isolated Windows
candidate without overwriting old artifacts:

```
python3 tools/package_windows_product.py --binary PATH_TO_EXE --out-dir FRESH_DIRECTORY
```

These bundles carry r14 and its console, not the separately qualified overworld
music ROM fix. Normal desktop presentation, audible output, every console
command and a whole-game playthrough are not qualified by these headless runs.
The broader content restoration remains open.

## Historical investigation (superseded where it conflicts above)

### Earlier performance investigation

## Finding

The built-in cheat console is present in the new Windows r14 package. The game
starts at about 3 FPS.

The console is not the cause. These cases stay at about 3 FPS:

- r14 Windows build with the console code removed.
- old runtime objects relinked with the current host.
- VSync off, audio off and window scale 1.
- `SNESRECOMP_LLE_BOUNCE=0`.
- a script with `turbo on`.

The old package executable runs the same 60-frame script in about 2 seconds.
The new executable takes about 21 seconds.

## Evidence

- Old package: `product-r14-event30-v2.zip`.
- New package: `product-r14-cheat-console-win.zip`.
- New Windows binary: `local/build-windows/demo11-native-product-r14/`.
- Test script: `wait 60 / dump / quit`.
- Logs: `tmp/old60.log`, `tmp/new60.log`, `tmp/fresh.log`.

Both runs report the same guest frame and master clock at frame 60. The new
build reports `aot_bridge_entries=3974` and `interpreted_opcodes=8037440`
before the bounce override. the old build reports 60 and 817753. With
`SNESRECOMP_LLE_BOUNCE=0` the new build reports 0 and 820072, but remains slow.

## Status

Open. The Windows package with the console is not a normal-play package until
the new build matches the old executable's speed.
## Host profile

`SNESRECOMP_HOST_PROFILE=1` isolates the slow stage on the new Windows build.

- Old package: guest mean 3.36 ms per frame.
- New package: guest mean 351 ms per frame.
- Raster, compose, upload and deadline wait stay below 2 ms.

The guest stage is about 100 times slower in the new build. Audio off and
`SNESRECOMP_APU_MASTER_CLOCK=0` do not change it. The next step is a compiled
object and link comparison, not a presentation fix.
## CPU load

A Windows process counter sampled the new executable at about 100 percent of
one CPU core during the slow guest stage. The guest stage is compute-bound, not
a sleep or deadline wait.
## Object comparison

The old and new Windows objects for `bank00_v2.c`, `interp_bridge.c`,
`common_rtl.c` and `snes.c` have the same instruction stream. Only the
`.debug$S` section and the embedded source path differ.

The 100 times guest slowdown is therefore not in the generated guest code.
The remaining difference is the host call path or the link inputs.
## Render and SDL exclusion

A test build forced `g_snes->disableRender = true` on every frame. The guest
stage stayed at 487 ms per frame. A test build linked the old SDL3 library. The
guest stage stayed at 443 ms per frame.

The guest slowdown does not come from PPU rendering or the SDL3 library.

## Local rebuild exclusion

A local Windows rebuild of the same target shows the same slow rate. This
result excludes the console patch as the cause.

| Binary | Guest stage mean |
| --- | --- |
| Shipped package executable | 3.6 ms per frame |
| Local rebuild, optimized flags | 592 ms per frame |
| Relinked fast build directory | 547 ms per frame |

The local rebuild uses the same compiler, the same flags and the same generated
guest code. The shipped executable stays fast. The slowdown therefore comes from
the build host, not from the cheat console patch.

The 60-frame script reports the same guest state in every case. The difference
is the time to reach it.
