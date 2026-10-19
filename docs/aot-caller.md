# Nested coordinate caller

This checkpoint qualifies `BuildCoordinatePair` at **$13F1A7..$13F1D4**,
M1/X1, for the **56-variant Demo 1-1 candidate**. The accepted 55-variant
coordinate-helper build is the regression baseline. The user subsequently reported no issues in response to the requested
manual regression pass; this checkpoint is accepted within that scope.

## Function and timing model

The caller adds $10 to the incoming eight-bit X index through A, sets Y=2,
and invokes the previously qualified $13F1C2 coordinate helper with `JSR`.
It then reloads X from DB:$0DDE, subtracts DB:$0E55,X from direct-page $02,
and decrements direct-page $03 on borrow. With Y=0 it executes the coordinate
helper's instruction sequence inline, returning through the outer stack frame.
The helper enters sixteen-bit accumulator mode temporarily and restores M1
before returning. The symbol is descriptive; no original source label is known.

The opt-in instruction bus model now handles this function's byte arithmetic,
transfers, branch, direct-page decrement and native `JSR`. Fetches and internal
cycles are charged separately from the existing paced data/stack accessors.
`JSR` pushes the high byte then low byte of $F1B0 before entering the child.
Only direct calls to an already selected instruction-timed callee with the
same static M/X mode are admitted. This is a bounded extension, not general
call-graph qualification.

The normal entry guards still restrict native mode, direct-page accesses and
stack-return reads to supported WRAM contexts. The added call guard yields
before a stack push could reach unsupported memory. With S=1 both pushes
are valid, but the child's wrapped S=$FFFF is rejected on entry; the already
pushed frame remains available to the interpreter. Unsupported data addresses
also yield at the guarded instruction, preserving any live child frame.
No pinned upstream source was edited.

## Differential qualification

The generated caller and generated child are linked together and compared
with the pinned interpreter using the verified 46 ROM bytes. The new harness
passes **27,604 cases**:

- 3,600 complete executions cover slow/fast ROM mirrors, six WRAM data-bank
  mappings, direct-page offsets 0/$0101/$1FFC, index edges including ADC
  wraparound, binary/decimal arithmetic and coordinate values.
- 24,000 cutoff cases sweep master-clock deadlines 1..1000 across two ROM
  speeds, binary/decimal arithmetic and six value pairs. Each paused state
  and its interpreter continuation are compared with the reference.
- Four guarded cases stop before an unsafe JSR stack write, at child entry
  after stack wrap, at the child's unsupported data read, or before the
  caller executes with an unsafe direct page.

Comparisons include A/X/Y, stack/direct-page/data/program banks, status flags,
M/X widths, CPU/master clocks, all 128 KiB WRAM and ordered byte writes.
Deadline checks exercise both child and parent suspension. The controlled
owner-unwind stub returns the runtime's LLE sentinel, and the test checks
parent propagation, guest stack preservation and empty host shadow stack.
The scheduler is controlled for these tests; full-route captures provide the
separate integration check. Arbitrary rewritten return frames and physical
hardware bus timing are outside this new harness's claims.

A separate negative test rejects a caller redirected to an unqualified callee.
All **62 project tests** pass. A final nested-only rerun also passes after
strengthening continuation write-order checks.

## Regression evidence

| Same 6,104-call route | Accepted 55 variants | Candidate 56 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 290,294 | 290,294 |
| Interpreted instructions | 71,888,085 | 71,733,510 |
| Interpreted instructions in $13F1A7..$13F1D4 | 154,575 | 0 |
| Interpreted instructions in $13F1C2..$13F1D4 | 61,830 | 0 |

The two address spans overlap and must not be added. The new selection removes
**154,575 interpreted instructions** on this route, including the previous
helper fall-through work. Bridge-entry and instruction counts have different
units and do not imply an AOT percentage or measured performance gain.

All eight full-route WRAM/framebuffer samples and all 85 dense-transition
samples match the accepted baseline byte for byte. Selected state, CPU/beam
clocks and beam positions match at all 6,104 calls.

The pure-interpreter route has zero compiled-body bridge entries and matches
its prior run at all eight scene samples and all 6,104 selected state/clock
observations. Compiled versus pure-interpreter samples retain the existing six
2–9-byte WRAM differences with identical images. Relative to the Snes9x
reference, the existing first mode/$13/$14 differences remain at calls
2154/2155/2260; the pure-interpreter $14 transient still starts at 897.
Neither native run introduces multi-field calls or beam-origin mismatches.
These checks do not establish full-state or cross-core equivalence.

All **1,719,253 generated stereo PCM frames** match the accepted baseline
byte for byte (32,040-Hz WAV, matched 32,000-Hz SDL dummy device). Both runs
retain 4 output underflows, 2,132 missing output frames, zero priming and no
ring-overflow drops. Shutdown tail consumption varies. This is automated
PCM/output regression evidence; no new physical listening test is claimed.

## Reproduction and acceptance

```sh
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k nested -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
```

The prior binary, generated source and configuration are archived with hashes
under `local/probes/aot-caller-baseline/`. Candidate captures and local reports
use the `aot-caller-` prefix.

The requested manual check used
`local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` and covered ordinary map
movement, Entry loading/play, jumping, character/enemy/object positions,
pipe/underground return, map return, transitions and ordinary music/effects.
No new demoOnly1 or whole-port fidelity claim is made.

The verified regular executable SHA-256 is
`a6a578adf8c17521da45f68ad5b4312cb029ce3d606a9efe5fbba5fd5132a21f`;
the audio executable is
`39fedd1a5dc1c9f8ee4c79642910beb31d5a7bc3c241b24705ceb63870fe8a07`.
Both match their build receipts, capture receipts and current analysis identity.
`python3 tools/m1.py check` also passes. The user reported no issues in
response to the requested manual pass, accepting this bounded checkpoint.
The workspace regular executable was rechecked against the build receipt;
the user did not supply an independent hash, exact session duration or
individual checklist results. The accepted 56-variant build becomes the next
regression baseline.


The subsequent [indexed sprite-loop expansion](aot-sprite.md) qualifies the
$13F06F caller and its 32-iteration output loop. The accepted 56-variant build
above remains its regression baseline; manual acceptance of the 57-variant
build is recorded in the linked report.
