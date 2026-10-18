# Palette-port event timing and two-loop AOT expansion

Date: 2026-10-18. Demo 1-1 now has **54 eligible AOT variants**, up from 52.
Two palette-upload leaves use a restricted byte-write event model that matches
the interpreter's register-write timestamps as well as its instruction totals.
Automated regressions pass. The user subsequently launched the rebuilt
executable directly and reported no issues, passing the bounded manual
regression checkpoint.
demoOnly1 remains a separate target.

The subsequent [coordinate helper expansion](aot-coordinate.md) produces a
55-variant candidate after mixed-width arithmetic qualification. The accepted
54-variant results below remain its regression baseline.

## Implementation and boundaries

| Project label | Native entry | Observed ROM behavior |
| --- | --- | --- |
| `UploadIndexedPalette80` | $169585, M1/X1 | Reads 80 nonzero palette indices and corresponding low/high color bytes, then RTS |
| `UploadIndexedPalette30` | $13EFB2, M1/X1 | Reads 30 palette entries, reloads X from live DB:$0DDE, then RTS |

These are descriptive project labels. Table counts describe the pinned ROM
data in the normal bank context, rather than a hard-coded loop limit. Generated
code retains the guest's actual zero-terminated loop, live data bank and index.
The instruction model adds `LDA abs,X`, `BRA` and `LDX abs` with the corresponding
read-address guards, width handling and native page-cross costs.

The [previous event probe](aot-mmio-events.md) showed that ordinary paced writes
would expose an event clock 24/30 master clocks later than the interpreter,
despite equal final time. The new path recognizes only native M1 `STA abs` with
the literal operands $2121/$2122. A separate guard permits a **single byte** at
these ports in system banks, or an ordinary WRAM destination if DB resolves
the operand there. Other hardware, cartridge writes and unsupported contexts
retain interpreter fallback. The original WRAM-only guard is unchanged.

For a palette-port store, the prefix checks the deadline and address, computes
the real opcode/operand-fetch costs, and defers this instruction's clock charge.
`M1AotPaletteWrite8` performs the effect at the instruction-start clock, then
charges the fetches and data transfer. CPU cycles are also charged after the
effect. The next instruction boundary handles refresh, beam synchronization and
deadlines. No CPU or beam clock is rolled backward, and no fixed per-loop
timing adjustment is used. A WRAM-resolved operand uses ordinary paced timing.

This preserves the accepted interpreter-visible timing contract; it is not a
claim that instruction-start writes model silicon bus timing. It does not
qualify word writes, APU ports, arbitrary PPU destinations or general MMIO.

Owned sources: [runtime support](../recomp/aot_timing.c),
[instruction model](../recomp/generator/instruction_bus.py),
[target policy](../recomp/targets/demo-1-1/timing.json), and
[symbols](../recomp/targets/demo-1-1/symbols.toml). The generator overlay adds the
helper declarations and per-function fetch-cost temporary through the checked
patch; its patch/result hashes are updated. Tracked upstream files stay clean.

## Differential qualification

The tests compile real generated C against the pinned `interp816` core,
actual paced-accessor and bridge-write bodies, and the bridge's actual
post-instruction clock-accounting code on a controlled bus.

| Probe | Exact-state/event cases |
| --- | ---: |
| Three palette-port writes, including deadline cutoffs | 412 |
| Actual $169585 leaf and pinned 80-entry table data | 15,959 |
| Synthetic relocation of that table across read-page boundaries | 16,031 |
| Actual $13EFB2 leaf and pinned 30-entry table data | 6,067 |
| **Total** | **38,469** |

The old paced-store counterexample remains as a negative control, reproducing
the 24/30-clock differences and 72 modeled scanline crossings. The restricted
path has exact event addresses, values, order and timestamps in those contexts.
Real-loop probes compare CPU registers/flags, stack, full WRAM, guest/master
clocks, complete event streams and yield PCs. They cover slow/fast ROM, mirrored
code banks, system/WRAM data banks, nonzero direct page, empty tables, altered
color data, controlled refresh, and every master-clock cutoff through each full
loop. The synthetic relocation additionally exercises `LDA abs,X` page crossing.

The existing non-palette MMIO-store fallback test still passes. Explicit guard
tests reject neighboring ports, non-system I/O addresses and two-byte accesses.
All **57 project tests pass**. These controlled probes do not replace actual
beam/IRQ/HDMA co-simulation or full hardware fidelity testing.

## Full-route and transition regression

| Same 6,104-call route | Accepted 52 variants | Candidate 54 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 276,494 | 283,424 |
| Interpreted opcodes | 75,424,920 | 71,949,915 |
| Interpreted opcodes in $169585..$16959E | 2,530,380 | 0 |
| Interpreted opcodes in $13EFB2..$13EFCE | 944,625 | 0 |

The two promoted spans remove **3,475,005 interpreted instructions**. The 6,930
additional bridge entries equal their observed 3,495 and 3,435 calls. These
different units do not define an AOT percentage or a measured speed gain.

All eight full-WRAM/raw-framebuffer samples match the preceding build exactly.
Mode, $13/$14, CPU clock, beam clock and beam position match at every one of
the 6,104 calls. All 85 dense-transition WRAM/framebuffer samples also match.
No multi-field calls or beam-origin mismatches were introduced. Existing first
selected reference differences remain at calls 2154 (mode), 2155 ($13) and
2260 ($14); cross-core timing parity remains incomplete.

The pure-interpreter run has zero compiled-body entries and matches the previous
pure-interpreter route's eight memory/image samples and all 6,104 selected
clock/state observations. Its earlier transient $14 difference at call 897 is
retained. Compiled versus pure-interpreter runs retain the previous 2–9-byte
WRAM differences at six samples, with identical images; full-state equivalence
between these execution modes is not claimed.

## Audio regression

At the matched 32,000-Hz SDL dummy device rate, all **1,719,253 generated stereo
PCM frames** are byte-identical to the accepted 52-variant audio capture, with
the WAV at the native 32,040-Hz rate. Both retain 4 output underflows, 2,132
missing output frames, no priming and no ring-overflow drops. Device-consumed
tail counts vary with shutdown scheduling and are not treated as PCM identity.
This qualifies generated audio and the matched dummy-device regression, not a
new physical listening or ZSNES audio comparison.

## Manual checkpoint and reproduction

Following the requested map movement, Entry loading/play, pipe/underground
return, map return, palette/transition and ordinary music/effects checks, the
user reported no issues after running:

```sh
local/build/demo-1-1/BrutalMarioDemo11SNESRecomp
```

This passes the 54-variant build's bounded manual regression checkpoint,
together with the automated evidence above. The executable at that path has
SHA-256 `14218a4054260558b6437889a8f1452c926f0dfcf3446a5c30ffe9e6d21eb231`,
matching the final full-route capture. That hash is workspace verification,
not a hash independently supplied by the user. Exact duration and individual
subtest outcomes were not separately reported. This does not establish a full
natural clear or whole-port fidelity. The deferred subjective star-music
concern and demoOnly1 spotlight seams remain separate.

Reproduction:

```sh
python3 tools/m1.py generate
python3 tools/m1.py build
python3 -m unittest discover -s tests -v
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
```

The accepted pre-change configuration, generated sources, regular executable
and receipt are archived in `local/probes/aot-palette-baseline/` with hashes.
Final captures are `aot-palette-final-full`, `aot-palette-final-transitions`,
`aot-palette-interpreter` and `aot-palette-audio` under `local/captures/`.

Reports under `local/reports/`: `aot-palette-differential.log`,
`aot-palette-tests.log`, `aot-palette-final-scenes.json`,
`aot-palette-final-transition-scenes.json`, `aot-palette-final-state.json`,
`aot-palette-floor-regression.json`, `aot-palette-floor-scenes.json`,
`aot-palette-coverage.json`, `aot-palette-previous-coverage.json`,
`aot-palette-timing.json` and `aot-palette-audio-comparison.json`.
