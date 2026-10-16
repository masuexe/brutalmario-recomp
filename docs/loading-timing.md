# Loading boundaries and the PPU counter-read protocol

Date: 2026-10-16. The compiled route's first mismatch in mode / `$13` / `$14`
moves from frame **838 to 2154**. This closes the frame-838 investigation;
it does not establish cycle-identical execution or complete fidelity.

## What caused frame 838

The custom handler at `$0FC13C` reads `$2137`, then `$213D`, and compares the
unmasked result against `$E2` and `$E6`. The runtime previously reset both
counter-read selectors whenever it latched the beam, and returned zero for
unused bits of the second counter byte. These are two distinct errors.

Latching must preserve the independent H/V byte selectors. Reading `$213F`
resets them. On the second `$213C/$213D` read, bits 1–7 come from the PPU2 read
bus; only bit 0 comes from the ninth counter bit. PPU2 reads, including CGRAM,
update this bus, independently for each PPU. See the original research in
[Anomie's register document](https://github.com/gilligan/snesdev/blob/master/docs/snes_registers.txt)
and [Nocash's register specifications](https://patrickjohnston.org/ASM/ROM%20data/snestek.htm).
The pinned Snes9x `ppu.cpp` implements these same selector/open-bus rules.

The reference exits this particular wait after one iteration, at actual
V=210: the read selector is on the high byte and the retained bus yields
`$E2`. The old native loop always reads a freshly latched low byte and waits
234 iterations, until actual V=226 in the next host call. It is incorrect to
force a one-frame input offset or write the game counter to hide this delay.
The corrected native interpreter exits after one iteration at V=208. Its
absolute master clock there differs from the reference by only six clocks,
but their beam origins still differ; neither matching frame counters nor
matching absolute clocks prove identical beam timing.

The patch also gates software latching through WRIO bit 7. The existing
`$4201` falling-edge path already calls the latch before lowering its gate.
The reset path previously initialized that gate and controller I/O lines low;
it now initializes both high, matching WRIO's reset state. Applying the gate
without this reset correction prevents the game's first counter wait from
finishing. An intermediate diagnostic capture reproduced that failure; it
is not an accepted build.

## Implementation and state

The existing [PPU patch](../patches/runtime/0001-fix-mosaic-and-raster-restore.patch)
now preserves selectors and implements PPU2 bus bits for counter, CGRAM and
status reads. [The reset patch](../patches/runtime/0005-fix-ppu-counter-latch-reset.patch)
corrects the gate and controller I/O defaults. There are no ROM edits or
forced guest-memory writes. Public `Ppu` layout remains unchanged. A small
per-instance sidecar owns the PPU2 read bus and is reset/freed with its PPU.

A 16-byte optional `PIO2` snapshot extension stores the bus, both counters,
both selectors and the latch flag. Lookahead accepts old snapshots without
consuming the next subsystem's data; missing I/O state starts at zero. Old
executables are not qualified to read new snapshots. Format compatibility
does not qualify old full-machine snapshots that retain the former incorrect
WRIO reset gate; regression sessions start fresh and ordinary SRAM saves are
unchanged. Existing `PPU0` display
register and video-memory payloads are unchanged.

The ROM-free counter test reproduces the one-iteration exit, independent
selectors, WRIO gating, bus changes through palette reads, two PPU instances,
reset/free, a new snapshot round trip, and loading the old payload. The
pre-fix PPU fails the selector assertion. All **21 project tests pass**.

## Measurements and remaining differences

The read-only probes cover frames 820–910. The reference diagnostic copy
matches the stock reference's full WRAM and raw pictures at all 13 samples.
The input script accounts for the release frame included by each `press`;
its scene tags agree with the recorded host-frame numbers.

| Observation | Before | Corrected | Reference |
| --- | ---: | ---: | ---: |
| Mode-18 counter-wait iterations | 234 | 1 | 1 |
| First selected-value mismatch, compiled full route | 838 | 2154 | — |
| Selected values matching, compiled frames 1–910 | 908 | 910 | 910 |
| `$14` at interpreter frame 897 | 0 | 3 | 1 |
| `$14` at frame 898, both native tiers | 8 | 8 | 8 |

The mode-17 load has the same **76,000** filtered PC/M/X entries in all three
traces, excluding the explicitly named main-loop and two APU polling pairs.
The subsequent mode-18 loading block has the same **694,380** entries, and
its finalization block has the same **6,317**, without excluding any polls
inside those blocks. These hashes do not compare registers or all memory.
The custom pre-counter handler still differs in APU polling counts.

Frame 897 exposes progress inside ordinary loading code: `$00A5FB` clears
bits of `$14`, and `$00A604` increments it through eight iterations. Both
native tiers and the reference reach 8 and mode `$13` in frame 898. The
interpreter's block takes 21,072,308 master clocks versus the reference's
21,092,086, so a transient value of 3 versus 1 does not establish a logic
error. The compiled observation matches the reference here. Residual bus,
beam and per-instruction timing differences remain; no arbitrary timing
constant was introduced to make this intermediate counter match.

For the complete 6,104-call compiled route, first mismatches are mode at
2154, `$13` at 2155, and `$14` at 2260. There are no multi-field calls or
beam-origin inconsistencies under the native fixed-field model. The eight
sampled raw pictures are byte-identical to the preceding accepted runtime;
WRAM differences at those samples are 0–8 bytes. The existing later moving
scene differences against Snes9x remain. Short-route pictures at fade/load
boundaries also remain phase-dependent, despite selected counters matching.

The demoOnly1 shop route reaches all four choices and exits with B. Some
same-host-frame pictures now differ because its animation advances one guest
frame earlier. At `menu-first`, the native picture matches the reference's
next idle frame on the RGB5 grid with zero differing pixels. The selector
remains visible; this is not a return of the missing palette highlight.
The old 18-scene zero-difference result describes the preceding runtime,
not this new timing phase. Broader cross-core timing remains unqualified.
The three death-return samples still reach mode `$0E`; `$0DBE` is 3, 2, 1,
identical to the preceding runtime (displayed lives 4, 3, 2). New manual
listening, Windows execution and the deferred boss-victory transition are
outside this automated checkpoint.

## Reproduction

Use fresh capture names and a fresh diagnostic build output directory:

```sh
python3 tools/build_boot_probe.py --output local/diagnostics/loading-probe-new
BM_BOOT_TRACE="$PWD/local/reports/loading-reference-new.csv" \
BM_TRACE_FRAMES=820:910 \
  python3 tools/probe_reference.py --manifest config/inputs.json \
  --rom local/roms/demo-1-1.sfc --script recomp/inputs/loading-timing.script \
  --core local/diagnostics/loading-probe-new/libretro/snes9x_libretro.so \
  --capture loading-reference-new

python3 tools/m1.py build
M1_BOOT_TRACE="$PWD/local/reports/loading-native-new.csv" \
M1_TRACE_FRAMES=820:910 \
  python3 tools/m1.py native --interpreter-only \
  --script recomp/inputs/loading-timing.script --capture loading-native-new
python3 tools/analyze_loading_timing.py \
  local/reports/loading-reference-new.csv local/reports/loading-native-new.csv
python3 tools/m1.py native --capture loading-full-new
python3 -m unittest discover -s tests -v
```

Frame filters are optional; absent filters retain the original mode-3 probe.
Native register columns require publishing the interpreter's local pre-op
registers, which the optional probe now enables. Normal launches do not
install the hook or enable that diagnostic synchronization. The initial
`phase838-native.csv` register columns preceded that change and are not used
as evidence; its PC/M/X, WRAM and clock observations remain applicable.
Capture receipts record the selected trace range. Neither probe advances the
APU or changes guest input/memory to obtain observations.

Local evidence: `loading-counter-full`, `loading-counter-compiled`,
`loading-counter-interpreter`, `loading-reference-stock`,
`loading-reference-probe`, `loading-counter-shop`, `loading-counter-deaths`,
and `loading-counter-shop-next-reference` under `local/captures/`.
Reports: `loading-counter-opcodes.json`, `loading-counter-full-analysis.json`,
`loading-counter-primary-regression.json`, `loading-counter-shop-scenes.json`,
`loading-probe-stock.json`, `loading-counter-negative.json`, and
`loading-counter-tests.log`, and `loading-counter-regressions.json` under
`local/reports/`.

Next work can expand measured static recompilation coverage while retaining
these checks. Frame 2154 and broader cycle timing remain separate research
items; closing this investigation does not close the entire port.
