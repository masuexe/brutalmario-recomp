# Indexed sprite-entry loop

This checkpoint qualifies `BuildIndexedSpriteEntries`, **$13F06F..$13F0C4**,
M1/X1, for the **57-variant Demo 1-1 candidate**. The accepted 56-variant
nested-coordinate-caller build is the regression baseline. The user subsequently reported no issues in response to the requested
manual pass; this checkpoint is accepted within that scope. demoOnly1 analysis inputs are unchanged.

## Selection and behavior

The retained exclusive instruction-cost profile identifies this loop as a
frequently executed remaining region, with 3,435 observed calls to its entry
on the fixed route. The function calls $13F1A7, which in turn calls $13F1C2;
those two functions were already qualified. It then scans X=$1F down to zero,
adds indexed offsets to the coordinate pair, clips candidates with nonzero
high bytes or X >= $F0, and writes visible entries at DB:$0300+Y. It writes
four position/tile/attribute bytes and a size byte at DB:$0460+(Y/4), saving
and restoring Y around the size lookup. Each visible entry advances Y by four;
finally X is reloaded from DB:$0DDE. The name is descriptive, not recovered
original source.

Unlike the main wait pair and SPC upload polling code, this function has a
bounded 32-iteration loop and only qualified direct callees. The earlier
$04F853 candidate reaches an inline dispatch table after a call to $0086DF;
naive fall-through decoding treats its data as instructions. This checkpoint
does not promote that dispatcher or the hardware polling paths.

## Timing and safety

The opt-in model adds byte `ADC abs,X`, immediate ORA, TYA, INY, and X1
PHY/PLY. The existing BPL, indexed loads/stores, direct-page, JSR and mixed
accumulator-width models cover the remaining instructions. Absolute indexed
reads and stores retain live address checks. Direct-page $0F is the highest
byte accessed, making D=$1FF0 the last admitted placement. Native-mode,
return-stack and existing child guards remain active.

PHY writes one byte before decrementing S; PLY increments S before reading.
Their new guards yield before accessing unsupported memory. Only X1 forms
are admitted; word PHY/PLY remain unqualified. Nested calls retain the existing
LLE owner-unwind propagation and live guest frames when an instruction boundary
hits its deadline. No pinned upstream source or runtime patch changed.

## Differential qualification

The new harness links all three generated functions and the pinned interpreter.
It verifies the actual 85-byte function against the user's local ROM, and
loads the indexed tables and intervening caller/helper bytes from that ROM
into temporary fixtures. No ROM is bundled in the project or modified.

It passes **138,536 cases**:

- 4,800 complete executions cover slow/fast mirrored code, eight data-bank
  contexts including the actual table bank, index edges, direct-page offsets
  0/$0101/$1FF0, binary/decimal arithmetic and coordinate values.
- 61,728 deadline cases sample clocks 1..18000 in steps of seven for six value
  pairs, two ROM speeds and binary/decimal arithmetic.
- Four complete executions force all 32 candidates to be visible and assert
  every output byte, final Y=128 and 265 ordered byte writes, including
  coordinate scratch, both JSR frames and temporary PHY writes.
- 72,000 further cases sweep every clock 1..18000 in those fully visible
  contexts, exercising every iteration and the temporary stack frame.
- Four guarded contexts compare exact fallback before the outer JSR, at
  wrapped child entry, at an unsupported child read, or at unsafe direct page.

Each case compares A/X/Y, S/D/DB/PB, status flags, M/X, CPU/master clocks,
all 128 KiB WRAM, ordered byte writes and unwind propagation. Paused cases
also compare interpreter continuation through the outer return. The bus and
scheduler are controlled; separate full-route runs qualify integration.
Arbitrary rewritten return frames and physical bus timing remain outside
this harness's claims.

## Regression results

All **63 project tests** pass. On the same 6,104-call route:

| Counter | Accepted 56 variants | Candidate 57 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 290,294 | 290,294 |
| Interpreted instructions | 71,733,510 | 70,328,905 |
| Interpreted instructions in $13F06F..$13F0C4 | 1,404,605 | 0 |

This removes **1,404,605 interpreted instructions**. Bridge entries and
instruction counts have different units; they do not establish an AOT
percentage or a measured speed improvement.

All eight full-route WRAM/framebuffer samples and all 85 dense-transition
samples match the accepted baseline byte for byte. Mode, $13/$14, CPU/beam
clocks and beam positions match at every call. The pure-interpreter route
has zero compiled-body bridge entries and matches its previous run at all
eight samples and all 6,104 selected state/clock observations.

Compiled versus pure-interpreter samples retain six 2–9-byte WRAM differences
with identical images. Relative to Snes9x, existing first mode/$13/$14
mismatches remain at calls 2154/2155/2260; the pure-interpreter $14 transient
still starts at 897. Neither run introduces multi-field calls or beam-origin
mismatches. Complete cross-core and full-state equivalence are not established.

All **1,719,253 generated stereo PCM frames** match the accepted baseline
byte for byte, at a 32,040-Hz WAV rate and matched 32,000-Hz SDL dummy device
rate. Both runs retain 4 output underflows, 2,132 missing output frames,
zero priming and no ring-overflow drops. Shutdown tail consumption varies.
No new physical listening comparison is claimed.

The regular executable SHA-256 is
`376a1ce9e1919093b7866778cf160d7f91493c5b950d8d6914c473f090094f83`;
the audio executable is
`ea344d234892c0f5ab6d94c17ffd4929c90de5d3c601122ee13b1148584480df`.
Both match build receipts, capture receipts and current analysis identity.
`python3 tools/m1.py check` passes and pinned upstream worktrees remain clean.

## Manual checkpoint

The user reported no issues in response to the requested manual regression
pass using `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp`. The requested
checks covered map movement, Entry loading/play, jumping, player/enemy/object
positions and graphics, pipe/underground return, map return, transitions and
ordinary sound. This accepts the 57-variant build's bounded manual checkpoint.

The workspace regular executable was rechecked against its build receipt,
full-route capture receipt and checkpoint SHA-256 above. No independent user
hash, exact session duration or individual checklist results were supplied.
The accepted 57-variant build becomes the next regression baseline. No new
demoOnly1 or whole-port fidelity claim is made.

## Reproduction

```sh
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k sprite -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
```

The accepted prior binary, generated tree and configuration are archived with
hashes under `local/probes/aot-sprite-baseline/`. Local captures and reports
use the `aot-sprite-` prefix.
