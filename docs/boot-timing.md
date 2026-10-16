# Boot-load timing and the APU clock

Date: 2026-10-15. The initial native/reference state divergence at host
frames 225–226 is fixed. This is a clock-model correction, not a claim that
the complete game now has cycle-identical execution.

Later update: the [counter-read investigation](loading-timing.md) fixes the
frame-838 divergence. The compiled route now matches the three selected
values through frame 2153. Measurements below retain the APU-clock checkpoint.

## Investigation

Both cores enter game mode `$03` at host frame 192. Before this fix, Snes9x
finishes that load in frame 225, while both compiled and interpreter-only
native runs finish in frame 226. Their frame-end observations are made near
the same V=225 vblank boundary. A fixed one-frame sampling offset does not
explain the identical earlier mode transitions.

Instruction probes locate most of the delay at `$008082/$008085`: the CPU
compares the APU ports against `$bbaa` and branches until the sound driver
returns to its transfer-ready state. The native run executes 4,999 iterations,
versus 3,307 in the reference. The sound driver is initially waiting around
SPC `$0549/$054c`; timer 0 has target 16 but a different divider phase.

With the main-loop wait, APU-ready wait, and APU-ack wait explicitly separated,
the reference, old native, and fixed native traces have the **same 412,273
nonpoll instruction PCs and M/X states in the same order**. This does not
prove register, bus, or complete-machine equivalence. The original narrower
comparison removed only the first two loops and contained 412,289 instructions;
the corrected clock adds one extra iteration in the separate ack loop, so
the final analyzer reports all three polling loops explicitly.

The reference probe is a fresh copy of the pinned Snes9x source with optional,
read-only logging in `cpuexec.cpp`. It never calls extra APU execution or
memory-read APIs. At frame 350, its full WRAM and raw picture match the stock
reference core byte for byte. `apu_clock=0` in its opcode CSV means that no
absolute SPC-cycle count is exported. Native timer prescaler counts down;
the reference prescaler counts up, so those raw columns are not equivalent.

## Cause and correction

The runtime's old conversion was `17088 / 357368` SPC cycles per master
clock: 32,040 DSP samples/sec times 32 SPC cycles/sample, divided into exactly
60 fields/sec. The beam driver instead advances NTSC fields of 357,368 master
clocks. Those fields occur at approximately 60.0988 Hz under the NTSC master
clock convention, so the old conversion advances the SPC about **0.164% too
fast relative to the beam**. The accumulated phase difference affects the
music driver's timer-based response, making the CPU wait longer at this load.

The corrected conversion retains the runtime's nominal 32,040-Hz DSP rate:

```text
NTSC master:   236250000 / 11 Hz
SPC clock:     32040 * 32 Hz
SPC / master:  15664 / 328125
```

These constants agree with the pinned Snes9x implementation
(`snes9x.h` and `apu/apu.cpp`). This fixes an internal inconsistency between
the runtime's nominal audio rate and its beam timing; it does not assume that
every physical SPC oscillator or historical emulator has this exact rate.

The [runtime patch](../patches/runtime/0004-add-master-clock-apu-timeline.patch)
uses an absolute, integer master-to-SPC conversion for both CPU-port and
frame-boundary synchronization. It also removes the artificial full-field
minimum on the partial RESET field and per-host-call rounding accumulation.
The desktop's elapsed-frame pacing uses the corresponding SPC cycles per NTSC
field, preserving its one-field pacing convention. No input-frame offset,
guest instruction, ROM edit, or forced game-counter write is introduced.

The first control experiment changed only the absolute timeline/minimum while
retaining the old rate. It still completed the load in frame 226 and waited
4,998 iterations. That experiment **did not fix the divergence**; the rate
correction is necessary for the measured improvement.

Both project targets enable `SNESRECOMP_APU_MASTER_CLOCK=1` at startup, even
when launched directly. An explicit `0` selects the old model for diagnostics.
The upstream default remains unchanged. Runtime hashes and capture receipts
record this patch and the selected override. The option is for these NTSC,
beam-driven targets, not a general replacement for frame-driven HLE hosts.

## Results and limits

| Observation | Before | Fixed | Reference |
| --- | ---: | ---: | ---: |
| Mode `$03` completion, interpreter probe | Frame 226 | Frame 225 | Frame 225 |
| APU-ready polling iterations | 4,999 | 3,316 | 3,307 |
| First mismatch in mode / `$13` / `$14`, compiled route | Frame 225 | Frame 838 | — |
| Calls matching all three selected values, out of 6,104 | 335 | 2,253 | — |
| Boot audio sample frames after 350 calls, at 32,040 Hz | Historical model | 186,519 | 186,517 |

All three selected values match throughout the first 837 calls of the full
compiled route. Remaining first mismatches are `$13` at 838, `$14` at 897,
and mode at 2154. No multi-field calls or beam-origin inconsistencies return.
The mode-3 completion instruction is still roughly 9,000 master clocks apart
between the fixed native interpreter probe and the reference; frame-level
agreement is not instruction-level timing equality.

The title, file menu, opening message, and overworld sampled pictures match
on the RGB5 grid. Later moving-scene comparisons still differ, and their
same-host-frame pixel counts are **not uniformly improved**: level entry,
walking, segment, and endurance differ at 368, 507, 292, and 156 pixels versus
122, 480, 246, and 11 before this clock fix. Those samples must be evaluated
with their changed execution phase; no blanket graphics/fidelity pass is claimed.

The transition probe has one fully black handoff picture at frame 2154,
followed by 39 consecutive MARIO START pictures (2155–2193) matching the
reference's stable text picture on the RGB5 grid. The prior alternating stale
background does not recur in these samples. Its duration changes with the
remaining load-phase difference and is not declared fully qualified.

The short audio capture has nonzero PCM, complete history from sample zero,
and no dropped samples. The SDL dummy device reports four underflows; this is
not a clean playback or waveform-equivalence claim. Post-fix manual listening
remains to be confirmed. demoOnly1's three-death regression still returns to
the overworld each time (five lives down to two), and its fast door/air-swim
probe still reaches rooms `$177/$178` with swimming active.

All **19 project tests pass**. The new ROM-free test exercises the actual
patched boundary code with a controlled APU sink: partial RESET field,
1,000 field boundaries without accumulated rounding drift, long-loader elapsed
time, overflow-safe conversion, desktop pacing, and unchanged legacy opt-out.
ZSNES 1.51 remains the user-reported historical baseline and has not been
run locally. The deferred boss-victory black screen remains outside this change.

A direct native launch with `SNESRECOMP_APU_MASTER_CLOCK` absent also reaches
mode `$04` at frame 225, confirming the executable's built-in target default.

## Reproduction

Use fresh capture and diagnostic-copy names:

```sh
python3 tools/build_boot_probe.py
BM_BOOT_TRACE="$PWD/local/reports/reference-boot-new.csv" \
  python3 tools/probe_reference.py --manifest config/inputs.json \
  --rom local/roms/demo-1-1.sfc --script recomp/inputs/boot-timing.script \
  --core local/diagnostics/snes9x-boot-probe/libretro/snes9x_libretro.so \
  --capture boot-reference-new

python3 tools/m1.py build
M1_BOOT_TRACE="$PWD/local/reports/native-boot-new.csv" \
  python3 tools/m1.py native --interpreter-only \
  --script recomp/inputs/boot-timing.script --capture boot-native-new
python3 tools/analyze_boot_timing.py \
  local/reports/reference-boot-new.csv local/reports/native-boot-new.csv

python3 tools/m1.py build --target demo-only-1
python3 -m unittest discover -s tests -v
```

`M1_BOOT_TRACE` observes interpreted instructions only; use `--interpreter-only`
for a complete mode-3 trace. The hook writes observations and never edits guest
state. Normal launches do not install the hook. The reference builder copies
tracked source files, skips optional submodule gitlinks, applies the diagnostic
patch, and records source/patch/binary identities without modifying upstream.

Local evidence includes `timing-boot-stock`, `timing-boot-probe-verified`,
`timing-boot-fixed`, `timing-master-default`, `timing-master-transitions`,
`timing-master-audio`, `timing-master-only1-deaths`, and
`timing-master-only1-swim` under `local/captures/`. Reports include
`boot-timing-opcode-comparison.json`, `boot-probe-stock-comparison.json`,
`timing-master-analysis.json`, `timing-master-scenes.json`, and
`timing-master-audio-summary.json` under `local/reports/`.

The follow-up [loading-boundary investigation](loading-timing.md) isolates
frame 838 and corrects the PPU counter-read protocol.
