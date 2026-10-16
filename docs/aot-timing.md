# Instruction timing for the pointer-read AOT leaf

Date: 2026-10-16. The previously deferred Demo 1-1 pointer-read leaf is now
compiled with an opt-in instruction bus timing model. The static frontier
increases from **48 to 49 eligible variants** without the earlier frame-163
regression. This is a qualified correction for a restricted instruction set,
not a general declaration of cycle-exact AOT execution.

## Minimal reproducer and cause

The pinned ROM leaf at `$00B983–$00B991`, entered in native M1/X0, reads one
byte through a long direct-page pointer, advances that pointer and returns.
A synthetic 15-byte fixture contains the same eight instructions; the test
also checks those bytes against the prepared target ROM when present. It
runs real generated C and the pinned `interp816` core against a controlled
memory bus. It uses the actual `cpu_region_speed` and paced-accessor function
bodies from the pinned runtime, not a replacement timing classifier.

The old generator charges a block's CPU cycles times its code-region speed.
The interpreter charges each actual bus transfer at its address's speed and
remaining internal cycles at six master clocks. The ordinary slow-ROM path
therefore has these costs:

| Instruction | Transfers and internal work | Corrected master clocks |
| --- | --- | ---: |
| `LDA [$8A]` | 2 fetches, 3 pointer reads, 1 data read | 48 |
| `LDX $8A`, X16 | 2 fetches, 2 data reads | 32 |
| `INX` | 1 fetch, 1 internal cycle | 14 |
| `BNE`, taken | 2 fetches, 1 internal cycle | 22 |
| `STX $8A`, X16 | 2 fetches, 2 data writes | 32 |
| `RTS` | 1 fetch, 2 stack reads, 3 internal cycles | 42 |
| **Total** | | **190** |

The unmodified generator produces **200**, reproduced by the negative test.
On pointer wrap, the untaken branch plus `LDX #$8000` / `INC $8C` path costs
**246**, also checked against the interpreter. Fast-ROM code/data and
unaligned direct page are separate test cases; no game-specific compensation,
input shift, forced counter, or hard-coded per-function cycle total is used.

## Implementation and scope

The [generator patch](../patches/generator/0001-add-opt-in-instruction-bus-timing.patch)
uses [project-owned timing emission](../recomp/generator/instruction_bus.py)
only for variants explicitly selected in
[the target policy](../recomp/targets/demo-1-1/timing.json). It charges opcode
and operand fetches by their live PBR/MEMSEL regions, uses the existing paced
accessors for data/stack transfers, and charges internal, direct-page and
taken-branch cycles separately. It checks the deadline at each instruction
boundary and retains live state when handing execution back to the interpreter.
The small [runtime support](../recomp/aot_timing.c) synchronizes beam time and
DRAM refresh at these boundaries, including the final return.

The initial model supports only native M1/X0 leaves containing these opcodes:
`A7 A6 E8 D0 A2 E6 86 60`. A selected leaf containing an unmodeled opcode or
width is rejected during generation. Emulation mode, direct-page/stack areas
outside the supported WRAM range, and MMIO source pointers yield to the
interpreter at entry. Validation reads only stable WRAM and does not charge
extra guest cycles. No HLE replacement is introduced.

These restrictions avoid applying paced accessors indiscriminately: other
IR addressing expressions may evaluate pointers repeatedly, and MMIO ordering
needs its own qualification. The model establishes instruction-boundary
agreement with this interpreter for the tested contexts, not silicon bus-event
ordering, other opcodes, interrupt architectures or cartridge coprocessors.
The previously promoted copy leaf and other AOT variants retain their old
timing model. demoOnly1 has no selected variant in this round.

`tools/generator_patches.py` materializes a verified overlay under
`local/generator/`, preserving tracked upstream files. Source, patch and result
hashes are pinned in `config/generator-patches.json`. The timing helper and
materialized variant policy participate in the generator's content digest;
a repeated emission reuses all eight verified bank outputs.

Generation, build and capture receipts include the policy/helper identities
and generated C/header hashes. A changed timing policy or generated source
requires regeneration before building or capturing. A negative CLI probe
changes only the policy, confirms rejection before compilation, restores it,
and verifies that the binary hash did not change.

## Validation

All **24 project tests pass**, including three new tests:

- Generated code versus `interp816`: 96 full executions cover normal/wrapped
  pointers, bank `$FF` wrap, RAM/ROM data, code mirrors, MEMSEL, unaligned
  direct page and preserved flags. Registers, full test WRAM and both CPU/master
  cycle counts agree. Another 620 deadline placements cover ordinary/wrapped
  paths with a controlled refresh stall: yield PC/state/cycles agree, and
  interpreter continuation gives the same completed result. Four unsupported
  entry contexts fall back.
- The original generator reproduces the `200 versus 190` clock error.
- An unmodeled opcode is rejected by the new timing path.

These controls test execution, not just the presence of a desired constant
in emitted text.

| Full 6,104-call route | Prior accepted build | Corrected pointer leaf |
| --- | ---: | ---: |
| Eligible variants | 48 | 49 |
| Compiled-body bridge entries | 80,186 | 212,564 |
| Interpreted instructions | 77,298,999 | 76,504,998 |
| Interpreted instructions in pointer-leaf span | 794,274 | 273 |

Interpretation decreases by **794,001 instructions**, approximately **1.03%**
of the preceding total. The residual 273 instructions are compatible with
mid-function deadline continuations; they are not evidence of a missing AOT
entry. Entry counts and instruction counts have different units and are not
an AOT percentage. Concurrent dummy-device runs are not speed benchmarks.

Across the full route, mode / `$13` / `$14` agree with the preceding native
build at every call. The eight full-WRAM snapshots and raw pictures match it
byte for byte, including stack memory. All 85 dense-transition samples likewise
match full WRAM and raw pixels. The first selected-state difference from Snes9x
remains mode at 2154, with `$13` at 2155 and `$14` at 2260; no new startup
shift, multi-field calls or native beam-origin inconsistencies are introduced.

The paired pure-interpreter run reports zero compiled-body entries and
84,175,861 interpreted opcodes. Its known transient `$14` observation at 897
remains a separate limitation; the main reference timing is not declared fixed.

The existing star-audio diagnostic is used only as an automated audio
regression: all **1,719,253 generated stereo PCM frames are byte-identical**
to the preceding accepted native audio capture. There are no ring overflow
drops. Dummy-output underflow/missing counters are the same historical
4 / 2,132; this is not a clean-device or new manual-listening claim.
The user's subjective star-music concern remains deferred at their request.

## Manual checkpoint

On 2026-10-16, the user confirmed normal play in Demo 1-1's Entry course and
normal Baby Yoshi behavior in the underground Entry area reached through its
pipe. Together with the automated checks, the current instruction-timing
regression checkpoint passes for those covered flows. DK coin collection was
not tested and remains a follow-up item rather than a blocker for this bounded
checkpoint. See [playtesting.md](playtesting.md) for the report's scope.

## Reproduction and evidence

```sh
python3 tools/m1.py generate
python3 tools/m1.py build
python3 -m unittest discover -s tests -v
python3 tools/m1.py native --capture aot-bus-new
python3 tools/m1.py native --interpreter-only --capture aot-bus-floor-new
python3 tools/analyze_aot_coverage.py \
  local/captures/aot-bus-new local/captures/aot-bus-floor-new
```

Local captures: `aot-bus-boot`, `aot-bus-loading`, `aot-bus-full`,
`aot-bus-full-interpreter`, `aot-bus-final`, `aot-bus-transitions`, and
`aot-bus-audio`. The prior configuration, generated tree and binary are at
`local/probes/aot-timing-baseline/`. Final binary/analysis identities are retained
in the capture and build receipts.
Reports under `local/reports/`: `aot-bus-final-scenes.json`,
`aot-bus-final-timing.json`, `aot-bus-final-coverage.json`,
`aot-bus-transition-scenes.json`, `aot-bus-audio-comparison.json`,
`aot-bus-generation-guard.json`, and `aot-bus-tests-final.log`.

Future promotions can extend this restricted timing model with differential
cases for each new addressing mode. Wider timing/fidelity, a recorded ZSNES
comparison and historical content integration retain their separate status.
