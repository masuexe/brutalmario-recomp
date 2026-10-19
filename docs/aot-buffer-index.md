# Word buffer-index AOT expansion

This checkpoint qualifies `ComputeLevelBufferIndex`, **$15A2FD..$15A33D**,
for the **64-variant Demo 1-1 candidate**, using the accepted 63-variant
build as its bounded gameplay/audio baseline. The user subsequently reported no issues in response to the requested
gameplay/audio check; this bounded manual checkpoint is accepted. The separate demoOnly1 target is unchanged.

## Function and timing model

The descriptive symbol identifies a 34-instruction leaf, independently
checked against the verified local ROM. It enters and returns in M0/X1,
computes a word index in direct-page $04 from words $00/$02, and conditionally
adds $0400 according to the low byte of DB:$1F11,X. It is a dependency of
larger bank-15 callers; this checkpoint does not promote those callers.

The model now admits the leaf's M0/X1 direct-page LDA/STA/ADC, immediate
AND/ADC, accumulator ASL, CLC, BEQ, indexed absolute LDA and RTS. Earlier
mixed-width SEC/SBC/STA/SEP support remains qualified separately. Other
unmodeled width/opcode combinations still fail generation. Word memory
operations count two data transfers, and direct-page bounds include their
high byte: the maximum accessed offset is $05, making D=$1FFA the last
admitted placement. No pinned upstream source or runtime patch is changed.

Carry is preserved through AND and propagated from the fourth ASL into
ADC. In binary arithmetic, bit 12 of the second coordinate therefore adds
one to the resulting index; replacing this sequence with an ordinary
truncated shift would change behavior. Decimal execution, including invalid
BCD inputs, is retained and compared against the interpreter.

The live word-read guard checks both bytes. With a system-bank WRAM mirror,
X=$ED reads $1FFE/$1FFF safely, whereas X=$EE would read $1FFF/$2000 and
must yield at $15A32D before either byte. Full WRAM banks remain admitted.
The existing bank-endpoint guard also retains fallback where the runtime's
word accessor and interpreter would disagree about wrapping the high byte.

## Differential qualification

Two new probes compile the actual generated C with the runtime's paced bus
accessors and compare it with the pinned interpreter. They pass **291,525
cases**:

- 262,144 coordinate cases sweep every 16-bit value in each input word,
  varying the other word, binary/decimal mode, incoming flags and layer value.
- 576 context cases cover slow/fast code, bank mirrors, WRAM data banks,
  hardware-adjacent indices and ordinary/last-safe direct-page placements.
- 28,800 deadline cases sweep clocks 1..1200 across six edge pairs, both
  arithmetic modes and both ROM speeds, checking paused state and subsequent
  interpreter continuation through RTS.
- Four cases check an unmapped data-bank read and rejected direct-page,
  stack and emulation contexts.
- One synthetic operand relocation checks a word read starting at $7EFFFF.
  This relocation affects only the temporary test fixture.

Comparisons include A/X/Y, S/D/DB/PB, status and M/X flags, CPU/master clocks,
all 128 KiB WRAM and the order and value of byte writes. Independent binary
result assertions supplement the interpreter oracle. The controlled bus and
scheduler probes do not establish arbitrary rewritten-return handling or
physical bus timing; route captures check integration separately.

## Route regression

All **77 project tests** pass (101 seconds), including the new differential
probes. `python3 tools/m1.py check` also passes; pinned upstream worktrees
remain clean.

On the fixed 6,104-call route:

| Counter | Accepted 63 variants | Candidate 64 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 305,061 | 315,360 |
| Interpreted instructions | 68,801,087 | 68,492,117 |
| Interpreted instructions in $15A2FD..$15A33D | 308,970 | 0 |

This removes **308,970 interpreted instructions** on this route. Body-entry
and interpreted-instruction counts have different units; they establish
neither an AOT percentage nor a measured host speed improvement.

All eight full-route WRAM/framebuffer samples and all 85 dense-transition
samples match the accepted baseline exactly. Mode, $13/$14, CPU/beam clocks
and beam positions match at every one of 6,104 calls.

The interpreter-only run records zero compiled entries and matches its prior
63-variant floor at all eight samples and 6,104 selected state/clock rows.
Compiled versus interpreter-only sampling retains six WRAM differences
(6, 3, 9, 8, 2 and 2 bytes); all images match. These are existing floor
versus compiled differences, not new regressions. Relative to Snes9x, the
first mode/$13/$14 differences remain at calls 2154/2155/2260, with the
interpreter-only $14 transient still at 897. Neither run adds multi-field
calls or beam-origin mismatches. Full-state and cross-core equivalence are
not claimed.

## Generated audio and build identity

All **1,719,253 stereo PCM frames** match the accepted baseline byte for
byte, with WAV rate 32,040 Hz and SDL dummy device rate 32,000 Hz. The PCM
SHA-256 remains
`1447bfbbc050a936d39233c76942c7e610e2cd1c651b052c1b8e77bd499d6352`.
All 3,225 selected audio-route state/clock rows also match.

The diagnostic reports zero overflow drops, four output underflows, 2,132
missing output frames and no priming, matching the baseline's latter counters.
Such dummy-output counters are host dependent; generated PCM equivalence does
not constitute physical listening. The existing Windows-native audio launcher
is retained for the new executable's manual check.

Verified SHA-256 values:

- Regular executable: `9955ebe282746c00ca41f2b466a706a48bdaec846021d15e7d6edcbd9d669c5d`.
- Audio diagnostic executable: `377496f1c0e3eaed406097bb5de3dc04e825f62209e45b577e3a67a822a4e87a`.

Both binaries match their build receipts and current analysis identity;
capture receipts match the corresponding binary. The previous regular binary,
configuration, generated tree and timing sources are archived with hashes
under `local/probes/aot-buffer-index-baseline/`. Captures and local comparison
reports use the `aot-buffer-index-` prefix.

## Reproduction and manual check

```sh
python3 -m unittest discover -s tests -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py native \
  --script local/captures/aot-helpers-transitions2/input.script \
  --capture NEW_TRANSITIONS_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
python3 tools/play_demo_1_1.py
```

For interactive acceptance, check Entry loading, movement/jumping, tile
collision and object behavior, the pipe/underground route and return, map
return, transitions and ordinary music/effects. Prior 63-variant acceptance
does not automatically accept this candidate. Use the launcher so this WSL
setup selects Windows-native audio. No new demoOnly1 manual check is required
by this change.


## Accepted manual follow-up

The user subsequently reported no issues in response to the requested
64-variant gameplay/audio check. This accepts the bounded manual checkpoint
and makes this build the next regression baseline. The workspace regular
executable still matches its build receipt and the SHA-256 recorded above.
No exact duration, itemized outcomes or independent user hash were supplied.
Continue using `python3 tools/play_demo_1_1.py` for interactive testing.
No new demoOnly1 or whole-port fidelity qualification is inferred.
