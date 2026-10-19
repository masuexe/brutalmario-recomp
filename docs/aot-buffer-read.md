# Buffer-value AOT expansion

This checkpoint qualifies `CheckLevelBufferValue`, **$15A0E3..$15A105**,
for the **65-variant Demo 1-1 candidate**, using the accepted 64-variant
build as its bounded gameplay/audio baseline. The user subsequently reported
no issues in response to the requested gameplay/audio check; this bounded
manual checkpoint is accepted. The separate demoOnly1 target is unchanged.

## Function and model

The descriptive symbol identifies a 19-instruction leaf. Its 35 instruction
bytes are independently checked against the verified local ROM. It enters
in M0/X1, reads the direct-page word at $04, and rejects indices at or above
$0800. Otherwise, it switches to M0/X0, saves X, loads the indexed word at
$7EC800, restores X and masks the value to its low byte. Values $01..$86
return carry clear; zero and values $87..$FF return carry set. All paths
restore M1/X1 before RTS. A rejected index remains in the full A register,
including its high byte, after the accumulator becomes eight-bit.

The instruction-bus model adds PHX/PLX and long-indexed LDA, extends the
required M0 instructions to X0, and admits REP/SEP #$30 from M0. It counts
stack and memory transfers at their resolved widths. Existing unsupported
opcode/width combinations and unrelated flag masks remain rejected.
Direct-page accesses end at offset $05; D=$1FFA remains the last admitted
placement. The long read is independent of DB.

A new ordered-write probe exposed the upstream word-push emitter's low-byte
first write sequence. Although that sequence leaves the same stack memory,
architectural PHX writes the high byte at the original S first, then the low
byte at S-1. The project-owned instruction-bus pacing transformation now
expands timed word PHX into those two paced byte writes, with S restored to
its appropriate value for each access. The surrounding emitter's final
stack decrement is retained. This transformation is limited to the timed
word-push statement; pinned upstream files and runtime patches are unchanged.

New guards defer unsafe stack accesses and long reads before their effects.
A word push from S=0 yields before PHX; a subsequent PLX from S=$FFFF after
a safe push at S=1 yields with the saved X still on the guest stack. Long
word reads defer before either byte if they cross into hardware or start at
a bank endpoint where the runtime accessor and interpreter disagree about
high-byte wrapping. The actual bounded $7EC800+$0000..$07FF range stays
entirely in WRAM; synthetic relocations qualify the fallback policy.

## Differential qualification

Three new probes compare generated C and actual paced accessors against the
pinned interpreter. They pass **740,973 cases**:

- 131,072 cases sweep every input index in binary/decimal modes.
- 65,536 cases sweep every table word, including high bytes discarded by AND.
- 524,288 cases test every low-byte value at every admitted index $0000..$07FF.
- 864 context cases cover both ROM speeds and mirrors, independent data banks,
  direct-page placements and stack endpoints, including real RAM aliases.
- 19,200 cutoff cases sweep clocks 1..800 across six index/value combinations,
  arithmetic modes and both ROM speeds, comparing paused state and resumed
  interpreter execution through RTS.
- Five cases check guarded push/pull, unsafe direct page, unsafe entry stack
  and emulation-mode rejection. The unsafe S=0 push is checked only up to
  fallback; the controlled test bus does not implement writes to ROM.
- Eight cases using two synthetic long-operand relocations check the last
  safe words, $001FFF hardware crossing, $7EFFFF high-byte wrapping and safe
  indexed carry into bank $7F. Guarded cases yield with X still saved and
  compare interpreter continuation, without changing the prepared ROM.

Comparisons include A/X/Y, S/D/DB/PB, flags and M/X widths, CPU/master clocks,
all 128 KiB WRAM, and the order and value of guest byte writes. Independent
result/predicate assertions supplement the interpreter oracle for contexts
without input/return-frame aliasing. Controlled refresh and scheduler probes
are supplemented by route captures. Arbitrary rewritten return frames and
physical bus timing are outside this qualification.

## Route regression

All **80 project tests** pass. The strengthened relocated-boundary probes
also pass in a subsequent focused run. On the fixed 6,104-call route:

| Counter | Accepted 64 variants | Candidate 65 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 315,360 | 322,226 |
| Interpreted instructions | 68,492,117 | 68,402,859 |
| Interpreted instructions in $15A0E3..$15A105 | 89,258 | 0 |

This removes **89,258 interpreted instructions** on this route. Body-entry
and instruction counts have different units and imply neither an AOT
percentage nor a measured speed improvement.

All eight full-route WRAM/framebuffer samples and 85 dense-transition samples
match the accepted baseline. Mode, $13/$14, CPU/beam clocks and beam positions
match at every one of 6,104 full-route and 2,319 dense-transition calls.

The interpreter-only run records zero compiled entries and matches the prior
floor at all eight samples and 6,104 selected state/clock rows. Compiled
versus interpreter-only sampling retains the existing six WRAM differences
(6, 3, 9, 8, 2 and 2 bytes), with identical images. Relative to Snes9x, first
mode/$13/$14 differences remain at calls 2154/2155/2260; the interpreter-only
$14 transient remains at 897. Neither run adds multi-field calls or beam-origin
mismatches. Full-state and cross-core equivalence are not established.

## Audio and identity

All **1,719,253 generated stereo PCM frames** match the accepted baseline
byte for byte. The WAV rate is 32,040 Hz and the SDL dummy device rate is
32,000 Hz. PCM SHA-256 remains
`1447bfbbc050a936d39233c76942c7e610e2cd1c651b052c1b8e77bd499d6352`.
All 3,225 selected audio-route state/clock rows match as well.

The dummy output reports zero overflow drops, four underflows, 2,132 missing
frames and no priming, matching the corresponding baseline counters. Those
host-dependent counters and generated PCM are separate from physical
listening; the new executable still needs its manual gameplay/audio check.

Verified executable SHA-256 values:

- Regular: `3f4ef3817b249e595d66de8197e70a45b9e495255e7780e0554f4bb8629b2cb3`.
- Audio diagnostic: `5ca1fee9c39c74554af5d5873cce2d67e1c0831516a7bc74b9a1b347d198159f`.

Both match build receipts and the current analysis identity; capture receipts
match the corresponding binary. `python3 tools/m1.py check` and
`git diff --check` pass, and pinned upstream worktrees remain clean. The
accepted 64-variant binary, generated tree, configuration and timing sources
are archived with hashes under `local/probes/aot-buffer-read-baseline/`.
Captures and local reports use the `aot-buffer-read-` prefix.

## Reproduction and manual check

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k buffer_read -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py native \
  --script local/captures/aot-buffer-index-transitions/input.script \
  --capture NEW_TRANSITIONS_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
python3 tools/play_demo_1_1.py
```

Check Entry loading, movement/jumping, tile collision and object behavior,
pipe/underground travel and return, map return, transitions and ordinary
music/effects. Use the launcher to select Windows-native audio on this WSL
setup. Previous acceptance does not automatically accept this new executable;
no additional demoOnly1 qualification is inferred.


## Accepted manual follow-up

The user subsequently reported no issues in response to the requested
65-variant gameplay/audio check. This accepts the bounded manual checkpoint
and supersedes the pending manual status above. The workspace regular
executable still matches its build receipt and the SHA-256 recorded above.
No exact duration, itemized outcomes or independent user hash were supplied.
The accepted 65-variant build becomes the next regression baseline. Continue
using `python3 tools/play_demo_1_1.py` for interactive checks. No new demoOnly1
or whole-port fidelity qualification is inferred.
