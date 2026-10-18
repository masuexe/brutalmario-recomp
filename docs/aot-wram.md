# WRAM-store AOT expansion

Date: 2026-10-16. This round extends the restricted instruction-bus model to
WRAM stores and promotes two Demo 1-1 leaves, increasing the compiled frontier
from **50 to 52 eligible variants**. The preceding 50-variant build passed user
testing, including DK coin pickup. demoOnly1 remains isolated.

## Selected functions and scope

| Project label | Native entry | Behavior |
| --- | --- | --- |
| `ClearEightWramBytesUnlessSix` | `$169F2B`, M1/X1 | Reads DB:`$1F11`; unless it equals six, clears `$7F:FFA0–FFA7` with a descending eight-byte loop |
| `CopyLevelBufferPointers` | `$0DA6BA`, M1/X1 | Copies direct-page `$04/$05` to `$6B/$6C` and `$6E/$6F`, then DB:`$1928` to DB:`$1BA1` |

These names describe the observed code; they are not recovered original source
symbols. Both leaves end in RTS, keep fixed M1/X1 widths and make no calls.
Their bytes are verified against the prepared ROM in differential tests.
The preceding route interpreted 129,315 instructions within the first leaf's
address range and 47,538 within the second's.

The timing model now includes `CMP #imm`, `DEX`, `BPL`, `STA long,X`, `LDA dp`
and `STA abs`. It retains live DB addressing, 24-bit long-index calculation,
unaligned direct-page charges and instruction-boundary refresh/deadline handling.
Every newly modeled absolute or long-indexed store checks the destination
before charging or accessing it. Only WRAM and its low mirrors are accepted;
ROM, cartridge RAM and hardware stores yield at the current instruction with
live state. The existing direct-page bounds cover direct-page stores.

The hotter `$169585` and `$13EFB2` loops write PPU palette registers. They are
not promoted in this round: the pinned interpreter bridge accumulates bus time
until opcode completion, while paced AOT writes expose the advanced master
clock to `WriteReg`. Matching total instruction clocks alone does not qualify
the register-write timestamp. A separate event-ordering test is needed before
expanding this WRAM-only store model to those loops. No hardware-write timing
fix or global timing compensation is introduced here.

The subsequent [PPU event qualification](aot-mmio-events.md) reproduces the
barrier with real generated code and the pinned interpreter's write callbacks:
equal final clocks conceal 24/30-master-clock write-event differences. The
production guard preserves interpreter timestamps through fallback. Palette
promotion remains deferred; the accepted frontier stays at 52 variants.

## Differential checks

Real generated C runs against the pinned `interp816`, using the runtime's
actual region-speed and paced-accessor bodies with a controlled bus/scheduler.
Each new leaf passes **9,480 differential cases**: five data patterns, skip/fill
paths, fast/slow ROM, mirrored program banks, four data banks, three direct-page
placements, two initial indices and 1,800 clock cutoffs per pattern. Tests compare
registers, flags, stack, guest/master cycles, full WRAM and yield PCs, including
refresh stalls and interpreter continuation. The clear loop also verifies its
eight-byte result directly; the copy probe verifies every destination.

A separate synthetic variation changes the final absolute store to `$2100`.
It confirms that execution yields before that store, with all preceding copies
and live registers intact and no hardware write. Guard endpoint tests include
ROM rejection, the first unsafe direct-page placement, WRAM-to-hardware
boundaries and the `$7F:FFFF` to `$80:0000`
WRAM-mirror transition. The complete project suite passes **28 tests**.

## Full-route regression

| Full 6,104-call route | Prior 50 variants | New 52 variants | Pure interpreter |
| --- | ---: | ---: | ---: |
| Compiled-body bridge entries | 267,717 | 276,494 | 0 |
| Interpreted opcodes | 75,601,748 | 75,424,920 | 84,175,861 |
| Interpreted opcodes in the clear leaf's address range | 129,315 | 0 | 129,315 |
| Interpreted opcodes in the copy leaf's address range | 47,538 | 25 | 47,538 |

The new leaves remove **176,828 interpreted opcodes** from the route. Their
8,777 added bridge entries equal the observed 3,495 clear calls plus 5,282
copy calls. The remaining 25 interpreted copy opcodes are continuations;
promotion does not guarantee every instruction always executes as compiled
code. Entry and instruction counts have different units and do not define
an AOT percentage or a speed claim.

All eight complete WRAM snapshots and raw framebuffers match the preceding
50-variant capture byte for byte. Mode / `$13` / `$14` match it at every one
of the 6,104 calls. All **85 dense-transition samples** also match full
WRAM and raw framebuffers. No multi-field calls or beam-origin inconsistencies
were added. The first selected reference differences remain mode at 2154, `$13`
at 2155 and `$14` at 2260; broader timing parity remains incomplete.

The pure-interpreter run has zero compiled-body entries and matches the
preceding pure-interpreter run at all eight complete WRAM and image samples.
Its known transient `$14` observation at call 897 remains. The compiled and
pure-interpreter snapshots still differ by 2–9 WRAM bytes at six samples,
with identical images, as in the preceding round. This does not establish
full-state equivalence between the execution modes.

## Audio regression

At the matched 32,000-Hz SDL dummy device rate, all **1,719,253 generated stereo
PCM frames** are byte-identical to the accepted 50-variant audio capture.
The generated WAV remains at the native 32,040-Hz rate. Output diagnostics
also retain the historical **4 underflows / 2,132 missing output frames / 0
priming events**, with no ring overflow drops. These checks qualify generated
PCM and the matched dummy-output regression; physical-device listening is not
newly qualified. The user's deferred subjective star-music concern remains
separate.

## Manual checkpoint

On 2026-10-16, following the requested map movement, Entry loading,
pipe/underground and map-return checks, the user reported no issues with the
52-variant build. Together with the automated checks, this passes the bounded
regression checkpoint. No exact session duration or executable hash was
supplied. DK coin pickup was explicitly confirmed on the preceding
[50-variant build](aot-indexed.md); no new collectible failure was reported.
See [playtesting.md](playtesting.md) for the manual evidence and scope.

## Reproduction

```sh
python3 tools/m1.py generate
python3 tools/m1.py build
python3 -m unittest discover -s tests -v
python3 tools/m1.py native --capture aot-wram-new
python3 tools/m1.py native --interpreter-only --capture aot-wram-floor-new
python3 tools/analyze_aot_coverage.py \
  local/captures/aot-wram-new local/captures/aot-wram-floor-new
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture aot-wram-audio-new
```

The prior configuration, generated tree, executable and receipt are archived
at `local/probes/aot-wram-baseline/`, including the previous target symbols and
timing policy. Generator patch hashes and generated-source identities remain
checked through generation, build and capture receipts. Tracked upstream files
remain unchanged.

Local captures: `aot-wram-full`, `aot-wram-interpreter`, `aot-wram-transitions`
and `aot-wram-audio`. Reports under `local/reports/` include
`aot-wram-differential.log`, `aot-wram-differential-final.log`,
`aot-wram-tests.log`, `aot-wram-coverage.json`,
`aot-wram-scenes.json`, `aot-wram-state.json`, `aot-wram-timing.json`,
`aot-wram-floor-scenes.json`, `aot-wram-floor-regression.json` and
`aot-wram-transition-scenes.json` and `aot-wram-audio-comparison.json`.
