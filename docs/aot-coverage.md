# Static coverage: first measured expansion

Date: 2026-10-16. The first expansion targets Demo 1-1's fixed-size data-copy
leaf. The separate demoOnly1 target has no new analysis inputs in this round.
The user confirmed no issues in the preceding counter-read build and authorized
coverage work. This document records automated evidence for the new build;
that preceding manual report does not qualify this later executable.

Later update: [instruction bus timing](aot-timing.md) corrects the deferred
pointer-read leaf and qualifies its promotion to 49 variants. Measurements
below retain the first 48-variant expansion.

## Selection and implementation

The accepted 6,104-call route executed 81,207,715 interpreted instructions,
with no dropped cost samples. Of those, 44,532,932 were the main wait pair at
`$00806B/$00806D`. Compiling this wait is not the first experiment: its event
and deadline behavior is more consequential than a bounded leaf's behavior.

The two initial candidates came from exclusive PC-cost records and observed
calls in the pinned target ROM, without importing stock SMW function maps:

| Exact entry | Observed behavior | Original interpreted instructions in address span | Decision |
| --- | --- | ---: | --- |
| `$0480B9`, M0/X0 | Copies eight words, then eight zero-extended bytes; RTS at `$0480DF` | 3,657,766 | Promote |
| `$00B983`, M1/X0 | Reads through a long pointer and advances its LoROM position; RTS at `$00B991` | 794,274 | Keep interpreted |

The source of truth is
[the target symbol map](../recomp/targets/demo-1-1/symbols.toml). RESET/NMI
labels retain the existing LLE boundaries. The data-copy entry is named
`CopyEightWordsAndEightBytes`. The analyzer reports a leaf with 21 distinct
instructions, no call demands and no rejection reasons. Generated C stays
under ignored `local/`, regenerated from the user's verified ROM.

`tools/m1.py generate` installs the checked-in symbols, synchronizes bank
configs before generating `funcs.h`, and invokes the pinned analyzer/emitter.
Build and capture receipts now record hashes of local analysis inputs and
the program manifest. A native capture also retains that exact manifest.
Changed symbols require regeneration; analysis changes after a build require
rebuilding before capture. No interpreter-fallback stub is silently promoted.

## Rejected two-function experiment

Promoting both candidates initially produced 49 eligible variants and reduced
interpretation, but introduced a new selected-state mismatch at frame 163:
the reference entered mode `$02` while the candidate remained in `$01`.
Later sampled pictures also differed. That experiment is not accepted.

The pinned emitter charges blocks using CPU cycles multiplied by the code
region's speed. The interpreter prices individual bus transfers and internal
cycles separately. Inspection of the emitted code establishes that the two
models differ; the experiment does not prove every later mismatch is caused
solely by that difference. The pointer-read leaf runs inside long loads, so
it remains explicitly `emit = false`. Correct AOT timing before reconsidering
it; do not tune game counters, input offsets or arbitrary cycle constants to
match the samples.

With only the copy leaf promoted, all three selected values match the
preceding runtime throughout the full route. The same block-timing limitation
still applies to this leaf. Its current qualification is bounded replay
behavior, not cycle-exact translation or equivalence for all possible inputs.

## Accepted replay evidence

The accepted analysis has **48 eligible variants**, up from 47. A separate
all-interpreter run disables every generated manifest PC and its LoROM mirror;
its exit log must report zero compiled-body entries. Frame deadlines can
resume partway through an AOT leaf in the interpreter; this is expected.

The first accepted replay measured:

| Full-route counter | Previous runtime | Copy leaf promoted |
| --- | ---: | ---: |
| Compiled-body bridge entries | 52,684 | 80,186 |
| Interpreted instructions | 81,207,715 | 77,298,999 |
| Interpreted instructions in the copy leaf's address span | 3,657,766 | 97 |
| Eligible static variants | 47 | 48 |

The total interpreted workload falls by **3,908,716 instructions (4.81%)**.
The total reduction also includes changed idle-loop work; it is not an
exclusive function-cost subtraction. Body entries and instructions have
different units, so none of these values is a percentage of executed AOT
instructions. Runs overlapped and used SDL dummy devices; their wall times
are not a controlled performance benchmark.

All eight sampled raw pictures match the preceding accepted runtime byte for
byte. Full WRAM differs by 0–23 bytes, confined to stack-page addresses
`$01C2–$01D9`; this is not a full-machine equality claim. Mode / `$13` / `$14`
match the preceding runtime across all 6,104 calls, preserving the first
reference mismatch at mode frame 2154. The data output and all other WRAM
bytes match at those eight samples. A selected-state match does not imply
identical execution position, complete video, or audio.

The final build repeats the same counts and sample results. Its paired pure
interpreter reports zero compiled entries and 84,175,861 interpreted opcodes.
All eight raw sampled pictures match between those tiers. Their selected
values differ only at frame 897 (`$14`: compiled 1, interpreter 3), the
previously documented transient loading-progress observation.

The dense transition route records 85 scenes, including 80 consecutive
transition fields. Replaying it with the archived pre-promotion binary and
the promoted binary produces byte-identical raw pictures at all 85 samples.
The 39 stable MARIO START fields (2155–2193) retain their prior RGB5 match,
with no alternating stale background. A comparison against the older
palette-fix build had one different sample at 2197; the paired replay above
isolates AOT from the intervening counter-read correction. Complete cycle
timing is still unqualified.
All 21 existing project tests pass. This round does not add
manual listening, Windows qualification or content from older versions.

## Reproduction

```sh
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture aot-compiled-new
python3 tools/m1.py native --interpreter-only --capture aot-interpreter-new
python3 tools/analyze_aot_coverage.py \
  local/captures/aot-compiled-new local/captures/aot-interpreter-new
python3 tools/compare_captures.py \
  local/captures/aot-compiled-new local/captures/aot-interpreter-new
python3 -m unittest discover -s tests -v
```

The coverage analyzer checks the retained program digest, complete/no-loss
coverage, and agreement with the exit opcode count. Cross-run comparisons
require the same ROM, route and effective runtime source/result hashes.
Patch-text whitespace hashes can differ while reproducing identical sources;
the complete receipts retain those identities instead of discarding them.
It reports exclusive interpreted work, not inferred function ownership.

Evidence is under `local/captures/`: `loading-counter-full` (prior runtime),
`aot-round1-compiled` / `aot-round1-interpreter` (rejected two-function trial),
`aot-copy-only` (accepted isolated copy trial), `aot-round1-final`,
`aot-round1-final-interpreter`, `aot-round1-transitions`, and
`aot-round1-transitions-baseline`.
The prior binary, configuration and generated tree were archived at
`local/probes/aot-round1-baseline/` before promotion. Reports under
`local/reports/` include `aot-round1-coverage.json`, `aot-copy-coverage.json`,
`aot-copy-scenes.json`, `aot-round1-tests.log`, `aot-round1-final-coverage.json`,
`aot-round1-final-timing.json`, `aot-round1-final-scenes.json`,
`aot-round1-final-floor-scenes.json`, `aot-round1-state-check.json`, and
`aot-round1-transition-scenes.json`, and `aot-round1-transition-regression.json`.

The subsequent [instruction-timing work](aot-timing.md) resolves the pointer
leaf's promotion blocker. Further work should continue to choose bounded,
observed entries and qualify newly modeled addressing modes.
The majority of execution is still interpreted, and the overall recompilation
and fidelity goals remain open.

The next [indexed table-read expansion](aot-indexed.md) promotes `$04F87C`
and reaches 50 eligible variants, with 903,250 fewer interpreted opcodes than
the accepted 49-variant route. Its automated regression evidence and passed manual
checkpoint, including normal Dragon Coin pickup, are recorded separately.

The subsequent [WRAM-store expansion](aot-wram.md) adds two bounded memory
leaves and reaches 52 eligible variants. Its full-route capture removes
176,828 interpreted opcodes relative to the accepted 50-variant build. The
user subsequently reported no issues, passing its bounded manual checkpoint.
