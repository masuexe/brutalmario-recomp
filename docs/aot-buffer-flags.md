# Buffer-match flag AOT expansion

This checkpoint qualifies `UpdateLevelBufferMatchFlags`, **$15A110..$15A166**,
for the **66-variant Demo 1-1 candidate**, using the accepted 65-variant
build as its bounded gameplay/audio baseline. The user subsequently reported
one test round without issues; this bounded manual checkpoint is accepted.
The separate demoOnly1 target is unchanged.

## Function and model

The descriptive symbol identifies 39 instruction sites (41 decoded M/X
states in the generated manifest). Its 87 instruction bytes are independently
checked against the verified local ROM. It enters
and returns in M1/X1, temporarily switching both widths to read a word from
$7ED000 indexed by direct-page word $08. It masks the value to a byte, stores
that byte in direct-page $08, and scans ten comparison entries in reverse.

Ordinary entries compare against that byte. A $FF entry instead checks the
low byte of DB:$1F11 indexed by the low byte of DB:$0DB3, then compares two
coordinate words against fixed long-address words. Failed special predicates
restore the saved loop X and continue scanning. A match reads a mask from
DB:$A106,X, ORs it into direct-page $07 and returns. No match returns with
that output byte unchanged. The comparison and mask tables are independently
loaded from the verified ROM into temporary test fixtures.

The model adds direct-page CMP/ORA and absolute-long CMP, qualifies the
needed M0 absolute LDA/LDX, TAX and BNE, and admits REP #$30 from M1. Word
reads count both bytes. All absolute/long reads retain live guards, including
word endpoints and hardware crossings. The highest direct-page byte accessed
is $09, making D=$1FF6 the last admitted placement. Existing byte PHX/PLX
support covers the saved loop index, including failure branches while M0 is
still live. No pinned upstream source or runtime patch is changed.

### Index-width correction

A deadline probe caught X=$0101 remaining live after SEP #$30 where the
interpreter had already truncated it to $0001. The upstream flag-mirror
helper updates widths without truncating X/Y. A later LDX normally hides
this difference, but a pause immediately after SEP exposes it.

The project-owned instruction-bus transformation now clears X/Y high bytes
whenever a generated REP/SEP flag synchronization leaves X eight-bit,
matching the interpreter's flag-setting contract. It preserves A's high byte.
The correction applies only inside selected instruction-bus functions.
Existing selected functions remain covered by the complete regression suite.

## Differential qualification

Four new probes compare generated C and actual paced accessors against the
pinned interpreter. They pass **519,998 cases**:

- 65,536 cases sweep every input word index, including the initial word-read
  bank endpoint and safe indexed carry into bank $7F.
- 65,536 cases sweep every buffer word, including high bytes discarded by AND.
- 262,144 cases cover all byte values, all initial output bytes and all four
  special-predicate outcomes, with independent match/mask assertions.
- 768 context cases cover ROM speeds/mirrors, six data banks, direct-page
  placements and safe stack endpoints. Cases that overwrite the guest return
  frame are excluded from this harness.
- 126,000 deadline cases sweep clocks 1..3500 across nine paths, two arithmetic
  modes and both ROM speeds. They compare paused state and interpreter
  continuation through RTS, including the immediate post-SEP truncation.
- Eleven cases check initial and special-path live guards, last-safe mirrored
  word reads, wrapped byte-stack pulls, and rejected direct-page, stack and
  emulation contexts.
- Three synthetic long-CMP relocations check a hardware crossing, a bank
  endpoint and the last safe word before that endpoint. They affect only
  temporary fixtures; guarded cases retain the saved loop index on the stack.

Comparisons include A/X/Y, S/D/DB/PB, flags and M/X widths, CPU/master clocks,
all 128 KiB WRAM and ordered guest byte writes. Independent result assertions
supplement the interpreter oracle for controlled contexts without aliases.
The controlled refresh and scheduler probes are supplemented by route captures.
Arbitrary rewritten return frames and physical bus timing are outside this
qualification.

## Route regression

All **84 project tests** pass (153 seconds), including the new differential
probes and the existing mixed-width, stack, caller, sprite and audio tests.

On the fixed 6,104-call route:

| Counter | Accepted 65 variants | Candidate 66 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 322,226 | 325,659 |
| Interpreted instructions | 68,402,859 | 68,001,198 |
| Interpreted instructions in $15A110..$15A166 | 401,661 | 0 |

This removes **401,661 interpreted instructions** on this route. Body-entry
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
byte for byte. WAV rate is 32,040 Hz and SDL dummy device rate is 32,000 Hz.
PCM SHA-256 remains
`1447bfbbc050a936d39233c76942c7e610e2cd1c651b052c1b8e77bd499d6352`.
All 3,225 selected audio-route state/clock rows match as well.

The dummy output reports zero overflow drops, three underflows, 1,599 missing
frames and no priming. The baseline reported four underflows and 2,132 missing
frames; these host-dependent counters vary between runs. Neither that change
nor exact generated PCM establishes physical listening quality. The new
executable still needs its manual gameplay/audio check.

Verified executable SHA-256 values:

- Regular: `5def7c6769443ca30003500b0a08d5fa29c27a6b67a09256782c8633be794768`.
- Audio diagnostic: `252d1c6540e8b0e234499cf6c6105d7e53f82ac78a58e0c40fd6570c5d5fb0f0`.

Both match build receipts and current analysis identity; capture receipts
match the corresponding binary. `python3 tools/m1.py check` and
`git diff --check` pass, and pinned upstream worktrees remain clean. The
accepted 65-variant binary, generated tree, configuration and timing sources
are archived with hashes under `local/probes/aot-buffer-flags-baseline/`.
Captures and local reports use the `aot-buffer-flags-` prefix.

## Reproduction and manual check

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k buffer_flags -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py native \
  --script local/captures/aot-buffer-read-transitions/input.script \
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

The user reported one test round without issues in response to the requested
66-variant gameplay/audio check, then authorized committing and pushing this
checkpoint before continuing. This supersedes its pending manual status above.
The workspace regular executable still matches its build receipt and the
SHA-256 recorded above. No exact duration, itemized outcomes or independent
user hash were supplied. The accepted 66-variant build becomes the next bounded
regression baseline. Continue using `python3 tools/play_demo_1_1.py` for
interactive checks. No new demoOnly1 or whole-port fidelity claim is inferred.
