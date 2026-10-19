# Sprite-entry loop preserving the incoming Y

This checkpoint qualifies `AppendIndexedSpriteEntries`, **$13F13D..$13F192**,
M1/X1, for the **58-variant Demo 1-1 candidate**. The accepted 57-variant
sprite-loop build is the regression baseline. The user subsequently reported
no issues in response to the requested manual pass; this checkpoint is
accepted within that scope.
The separate demoOnly1 target has no new analysis inputs.

## Selection and behavior

The baseline coverage records 3,435 calls to this entry and 1,374,000
interpreted instructions in its address span on the fixed route. It is a
sibling of the previously qualified $13F06F loop. It saves the incoming Y
with PHY, calls the qualified $13F1A7 coordinate routine, and restores Y
with PLY. The coordinate routine itself calls the qualified $13F1C2 helper.

The loop scans X=$19 down to zero (26 candidates), adds indexed coordinate
offsets, clips candidates with nonzero high coordinates or X >= $F0, and
writes visible position/tile/attribute bytes at DB:$0300+Y. It temporarily
saves Y around the size-byte write at DB:$0460+(Y/4). Each visible entry
advances Y by four; the incoming offset is preserved across the coordinate
call. Finally X is reloaded from DB:$0DDE. The symbol is descriptive, not an
original source label.

The existing instruction bus model covers all instructions and both direct
callees. This promotion only adds the symbol and timing-policy selection;
no timing implementation or runtime patch is changed. Native-mode,
direct-page, live data-address and stack guards remain active. Word PHY/PLY
remain unqualified, and unsupported contexts retain interpreter fallback.

## Differential qualification

The shared sprite harness now takes its entry, table span, candidate count
and incoming-Y behavior from the fixture header. Both old and new loops are
compiled and tested separately. Each links the real generated caller and
coordinate helper with the pinned interpreter and actual paced accessors.
The new 86-byte instruction sequence is checked against the verified local
ROM; its indexed tables and helper bytes are loaded into temporary fixtures.

The new loop passes **498,557 cases**:

- 4,800 complete executions combine slow/fast mirrored code, eight data-bank
  contexts, index edges, direct-page offsets 0/$0101/$1FF0, binary/decimal
  arithmetic and coordinate values.
- 61,728 cutoff cases sample clocks 1..18000 in steps of seven for six value
  pairs, both ROM speeds and binary/decimal arithmetic.
- 24 complete executions force every candidate visible for starting Y values
  $00/$01/$EF/$F0/$FC/$FF. They assert each output byte, final Y modulo 256
  and 218 ordered writes, including scratch bytes, call frames and saved Y.
- 432,000 further cases sweep every clock 1..18000 in those fully visible
  contexts, checking pauses inside both nested calls and every loop iteration.
- Five guarded contexts check exact fallback after the initial PHY for S=0
  or S=1, at the wrapped child's entry for S=2, at an unsupported child data
  read, or at the outer entry for unsafe direct page.

Y increments wrap at eight bits; an absolute indexed store still adds Y to
the full sixteen-bit operand. Thus starting Y=$FF writes entry bytes at
$03FF..$0402 before subsequent Y increments wrap. The output assertions check
this distinction, as well as unaligned size-byte indices.

Each comparison covers A/X/Y, S/D/DB/PB, flags, M/X, CPU/master clocks, all
128 KiB WRAM, ordered writes, guest frames and host shadow-stack unwinding.
Paused cases also compare interpreter continuation through the outer return.
The bus and scheduler are controlled here; full-route captures separately
check integration. Arbitrary rewritten returns and physical hardware timing
are outside the new harness's claims.

## Regression results

All **64 project tests** pass, including both the existing 138,536-case loop
fixture and the new 498,557-case fixture. On the same 6,104-call route:

| Counter | Accepted 57 variants | Candidate 58 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 290,294 | 290,294 |
| Interpreted instructions | 70,328,905 | 68,954,905 |
| Interpreted instructions in $13F13D..$13F192 | 1,374,000 | 0 |

The selection removes **1,374,000 interpreted instructions**. Bridge entries
and interpreted instructions have different units and imply neither an AOT
percentage nor a measured performance improvement.

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

All **1,719,253 generated stereo PCM frames** match the accepted baseline
byte for byte (32,040-Hz WAV, matched 32,000-Hz SDL dummy device). Both runs
retain 4 output underflows, 2,132 missing output frames, zero priming and no
ring-overflow drops. Shutdown tail consumption varies. No new physical
listening comparison is claimed.

The regular executable SHA-256 is
`8a9f33d3fd6be204f20c1860bc05d77eab0f12b08057f0e5804b20a569c5fce1`;
the audio executable is
`e54abdce0603c31f1873a2a8da0898eefce7c89ed9fa6dea907cef6398fc67fc`.
Both match build receipts, capture receipts and current analysis identity.
`python3 tools/m1.py check` passes and pinned upstream worktrees remain clean.

## Manual checkpoint

The user reported no issues in response to the requested manual regression
pass using `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp`. The requested
checks covered ordinary map movement, Entry loading/play, jumping,
player/enemy/object positions and graphics, pipe/underground return, map
return, transitions and ordinary sound. This accepts the 58-variant build's
bounded manual checkpoint.

The workspace regular executable was rechecked against its build receipt,
full-route capture receipt and checkpoint SHA-256 above. No independent user
hash, exact session duration or individual checklist results were supplied.
The accepted 58-variant build becomes the next regression baseline. No new
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
hashes under `local/probes/aot-sprite-y-baseline/`. Captures and reports use
the `aot-sprite-y-` prefix.


The subsequent [bank-15 coordinate expansion](aot-coordinate15.md) qualifies
$15A023 and $15A032 together. The accepted 58-variant build above remains its
regression baseline; the 60-variant build's silent manual pass and pending
audible verification are recorded in the linked report.
