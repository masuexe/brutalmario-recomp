# Bank-15 coordinate pair and word subtraction

This checkpoint qualifies two M1/X1 entries for the **60-variant Demo 1-1
candidate**, following the accepted 58-variant build. The user subsequently
reported no issues in a silent test environment: the bounded non-audio manual
checkpoint passes, while audible music/effects verification remains pending. Two entries are promoted together in this round; there is no separate
59-variant manual checkpoint. The separate demoOnly1 target is unchanged.

## Functions and differences

`SubtractIndexedCoordinateWordBank15` at **$15A032..$15A044** has the same
19 instruction bytes as the previously qualified $13F1C2 helper. It assembles
a coordinate word from DB:$0E65,X and DB:$0E35,X, switches to M0/X1, subtracts
DB:$001A,Y, stores the word to DB:$0000,Y and restores M1 before RTS.
The bytes are independently checked against the verified local ROM.

`BuildCoordinatePairBank15` at **$15A023..$15A044** adds $10 to the incoming
X through eight-bit A, sets Y=2 and calls $15A032. It then reloads X from
DB:$0DDE and executes the helper inline with Y=0. Unlike $13F1A7, it has
no direct-page borrow adjustment between the two coordinate calculations.
Its 34 bytes, including the $A032 call target, are separately verified.
The labels are descriptive, not recovered original source names.

The existing instruction bus model covers both functions. Only symbols and
the target timing-policy selection change production behavior; no timing
implementation, runtime patch or pinned upstream file is modified. The
qualified callee is selected alongside its caller. The existing stack,
mode and live address checks retain interpreter fallback when needed.
Since neither function accesses direct-page operands, D=$1FFF remains an
admitted context, unlike the $13F1A7 caller with direct-page scratch accesses.

## Differential qualification

The existing word-arithmetic and nested-caller probes now also compile the
bank-15 entries with the actual call target and stack return address. Both
bank-13 probes remain in the complete suite to verify the shared harness.

The new entries pass **51,332 differential cases**:

- 23,616 word-helper cases compare binary/decimal arithmetic, flags, widths,
  live B-register effects, indices, data banks, slow/fast code mirrors,
  direct-page contexts and cutoff/interpreter continuation behavior.
- 112 guarded endpoint cases use synthetic operand relocations to test word
  bank endpoints, hardware boundaries, last-safe destinations and unsupported
  data banks at the bank-15 PCs. M0 state remains live when the fallback occurs
  after REP. These relocations affect only temporary test fixtures.
- 27,604 nested-caller cases compare both the explicit call and inline path,
  ordered writes, complete executions, clocks 1..1000, guest stack frames,
  host unwind propagation and interpreter continuation. Guard cases cover an
  unsafe stack push, wrapped child stack, unsupported child read and unsafe
  direct page, including the new last-safe D=$1FFF placement.

The comparisons cover A/X/Y, S/D/DB/PB, status and M/X flags, CPU/master clocks
and all 128 KiB WRAM. Caller cases also check ordered byte writes. The bus,
refresh and scheduler are controlled in these probes; full-route runs qualify
integration separately. Arbitrary rewritten return frames and physical bus
timing are outside these new probes' claims.

## Regression results

All **67 project tests** pass. On the same 6,104-call route:

| Counter | Accepted 58 variants | Candidate 60 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 290,294 | 293,727 |
| Interpreted instructions | 68,954,905 | 68,865,647 |
| Interpreted instructions in $15A023..$15A044 | 89,258 | 0 |
| Interpreted instructions in $15A032..$15A044 | 61,794 | 0 |

The address spans overlap; their instruction counts must not be added.
Promoting both entries removes **89,258 interpreted instructions** and adds
3,433 compiled-body bridge entries on this route. The counts have different
units and imply neither an AOT percentage nor a measured speed improvement.

All eight full-route WRAM/framebuffer samples and all 85 dense-transition
samples match the accepted baseline byte for byte. Mode, $13/$14, CPU/beam
clocks and beam positions match at every one of 6,104 calls.

The pure-interpreter route has zero compiled-body bridge entries and matches
its previous run at all eight scene samples and all 6,104 selected state/clock
observations. Compiled versus pure-interpreter samples retain six 2–9-byte
WRAM differences with identical images. Relative to Snes9x, the existing first
mode/$13/$14 differences remain at calls 2154/2155/2260; the pure-interpreter
$14 transient still starts at 897. Neither run introduces multi-field calls
or beam-origin mismatches. Full-state and cross-core equivalence are not
established by these checks.

### Audio and output-counter variability

All **1,719,253 generated stereo PCM frames** match the accepted baseline
byte for byte, at a 32,040-Hz WAV rate and matched 32,000-Hz SDL dummy device
rate. This holds for the initial candidate run, a standalone candidate rerun
and a selective interpreter control. Their 3,225-call selected state/clock
observations also match the historical audio baseline exactly.

The dummy output counters do not reproduce the historical baseline exactly:

| Run | Underflows | Missing frames | Priming |
| --- | ---: | ---: | ---: |
| Accepted historical baseline | 4 | 2,132 | 0 |
| Candidate during parallel checks | 9 | 4,381 | 0 |
| Candidate after other checks completed | 16 | 7,563 | 1 |
| Same binary, new entries forced to interpreter | 12 | 6,324 | 0 |

All runs have zero ring-overflow drops. The selective control disables only
$15A023/$15A032 and their LoROM mirrors via the retained `disabled-targets.txt`.
Its 154,854 compiled-body entries and 42,007,342 interpreted instructions
match the historical baseline audio route's counts. Both new functions'
address spans execute interpreted in that control. The capture receipt records
the diagnostic target-file hash and entries explicitly.

The extra output underflows therefore also occur without executing the new
compiled entries. The evidence does not isolate their cause or establish
performance parity: scheduling/load or another host factor remains possible.
Generated PCM/state regression passes; exact historical output-counter parity
is not established. No runtime audio adjustment or physical listening claim
is made. All runs are retained under `aot-coordinate15-audio`,
`aot-coordinate15-audio-idle` and `aot-coordinate15-audio-control`.

The regular executable SHA-256 is
`e3e62825d7615aaa589080bf0f715fcfcaf8f39230991f82d4150c4ed648ac63`;
the audio executable is
`1275796bd20c69512deb44e6317d6fd25acc951a74f3aef4611bc58b3513bc62`.
Both match build receipts, capture receipts and current analysis identity.
`python3 tools/m1.py check` passes and pinned upstream worktrees remain clean.

## Manual checkpoint

The user reported no issues while testing in a silent environment in response
to the requested regression pass. This accepts the 60-variant build's bounded
non-audio manual checkpoint. The requested checks covered ordinary map movement,
Entry loading/play, jumping, player/enemy/object positions and graphics,
pipe/underground return, map return and transitions. Individual checklist
results and exact session duration were not separately supplied.

**Audible music/effects verification remains pending.** A silent environment
does not establish whether audio was disabled or simply could not be heard.
The automated PCM evidence and output-counter variability above are retained;
this user report does not resolve the audible-output checkpoint.

The workspace regular executable was rechecked against its build receipt,
full-route capture receipt and checkpoint SHA-256 above. No independent user
hash was supplied. The 60-variant build can serve as the bounded non-audio
regression baseline, with the pending audible check carried forward. No new
demoOnly1 or whole-port fidelity claim is made.

## Reproduction

```sh
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k bank15 -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
```

The prior accepted binary, generated tree and configuration are archived with
hashes under `local/probes/aot-coordinate15-baseline/`. Local captures and
reports use the `aot-coordinate15-` prefix.
