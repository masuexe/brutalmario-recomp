# WRAM record-writer AOT expansion

This checkpoint qualifies `AppendSelectedBufferRecords` ($15A19F..$15A25A)
and its callee `AppendAlternateBufferRecords` ($15A25B..$15A2FC) together for
the **68-variant Demo 1-1 candidate**. The accepted 66-variant build is the
bounded gameplay/audio baseline; there is no separate 67-variant manual
checkpoint. The user subsequently reported another test round without issues;
this bounded manual checkpoint is accepted. The separate demoOnly1 target is
unchanged.

## Functions and model

These are descriptive labels. The 188-byte caller and 162-byte callee are
independently checked against the verified local ROM; their manifests decode
68 and 55 instructions, respectively. The caller selects one bit from
$7F1820 using DB:$06B7 and a DB-relative mask table. A set bit calls $A25B.
Otherwise, status $7FFFDD=$22 returns immediately; a changed status is set
to $22 before appending four records. The callee uses status $33 and a second
set of record payloads. Both enter and return M1/X1, switching to M0/X0 while
writing their records.

Each record reads the live word pointer at $7F837B, adds six with CLC/ADC,
stores the updated pointer and writes three words using the previous pointer
as X. Decimal mode is preserved, including invalid BCD arithmetic. After four
records, SEP #$30 truncates X to eight bits before the final byte store.
The final $FF therefore uses the truncated X; it cannot generally be replaced
by a store at the full pointer plus a constant. Buffer writes can also alias
the status byte or low WRAM mirrors, and admitted cases retain those effects.

The timing model adds absolute-long LDA/STA and indexed-Y absolute AND,
qualifies the required M0/X0 immediate loads, TAX, CLC/ADC and long stores,
and resolves long write transfers at the accumulator width. Both bytes of
word stores must be WRAM, and bank endpoints defer before either write when
the runtime word accessor and interpreter disagree about high-byte wrapping.
Existing read, stack and native-mode guards remain active. There are no
direct-page operands, so D=$1FFF remains admitted. The caller requires the
qualified callee; this does not relax the existing direct-call policy.
No runtime patch or pinned upstream file is modified.

## Differential qualification

A shared probe compiles both real generated functions, their actual nested
call and the runtime's paced accessors against the pinned interpreter. It
passes **424,913 state/write-order/clock/continuation cases**:

- Both roots attempt all 65,536 pointer values in binary and decimal modes:
  262,144 combinations. Seventy-two cases that rewrite an active guest return
  frame are excluded from this harness, leaving 262,072 qualified executions
  or guarded prefixes.
- 65,536 caller cases sweep every selector and bit-field byte, varying the
  initial status gate and arithmetic mode.
- 1,296 context cases cover both roots, ROM speeds/mirrors, six data banks,
  direct-page placements, stack endpoints and all three status classes.
- 96,000 deadline cases sweep clocks 1..4000 across six root/path/pointer
  combinations, both arithmetic modes and ROM speeds. They include nested
  no-op returns, record writes and boundary hand-backs.
- Nine cases check unsafe JSR, wrapped child entry, unsupported DB reads and
  rejected direct-page, entry-stack and emulation contexts for both roots.

Comparisons include A/X/Y, S/D/DB/PB, status and M/X flags, CPU/master clocks,
all 128 KiB WRAM, ordered byte writes, balanced host shadow stacks and parent
unwind propagation. Paused executions are continued through the interpreter
to RTS or to the next unsupported write boundary. The controlled bus does
not implement MMIO/cartridge writes; such prefixes are compared up to the
handoff, without claiming those writes were performed. The S=0 JSR guard is
likewise checked only before its unsafe second stack write.

Independent binary assertions check the four record headers/payloads, pointer
advance, status and truncated-X terminator for bounded, non-aliasing inputs.
The bus, refresh and scheduler are controlled here; route captures qualify
integration separately. Arbitrary rewritten return frames and physical bus
timing remain outside these probes' claims.

## Route regression

All **85 project tests** pass (150 seconds), including the new paired probe
and the existing caller, mixed-width, sprite, guard and audio tests.

On the fixed 6,104-call route:

| Counter | Accepted 66 variants | Candidate 68 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 325,659 | 329,092 |
| Interpreted instructions | 68,001,198 | 67,949,603 |
| Interpreted instructions in $15A19F..$15A25A | 51,595 | 0 |
| Interpreted instructions in $15A25B..$15A2FC | 0 | 0 |

The fixed route removes **51,595 interpreted instructions**. It does not
exercise the alternate callee; qualification of that branch comes from the
shared differential probe, not a newly reached gameplay scene. Promoting the
two dependencies also prepares the larger bank-15 caller for a later round.
Body-entry and interpreted-instruction counts have different units and imply
neither an AOT percentage nor a measured speed improvement.

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

The dummy output reports zero overflow drops, four underflows, 2,132 missing
frames and no priming. The baseline reported three underflows and 1,599
missing frames. These host-dependent counters vary between runs; generated
PCM equality and counter observations are separate from physical listening.
The new executable still needs its manual gameplay/audio check.

Verified executable SHA-256 values:

- Regular: `3a9c1f5dc3d821d2fc02086785e36628349a96d340e02e5cf4b3c69c05866677`.
- Audio diagnostic: `94a63ab6397f047bf84570ac1b6c99fca36feaccc842df3b50b72e36010be444`.

Both match build receipts and current analysis identity; capture receipts
match the corresponding binary. `python3 tools/m1.py check` and
`git diff --check` pass, and pinned upstream worktrees remain clean. The
accepted 66-variant binary, generated tree, configuration and timing sources
are archived with hashes under `local/probes/aot-records-baseline/`. Captures
and local reports use the `aot-records-` prefix.

## Reproduction and manual check

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k records_word -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py native \
  --script local/captures/aot-buffer-flags-transitions/input.script \
  --capture NEW_TRANSITIONS_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
python3 tools/play_demo_1_1.py
```

Check Entry loading, movement/jumping, tile/object appearance and interaction,
pipe/underground travel and return, map return, transitions and ordinary
music/effects. Use the launcher to select Windows-native audio on this WSL
setup. Previous acceptance does not automatically accept this executable;
no additional demoOnly1 or alternate-branch gameplay qualification is inferred.


## Accepted manual follow-up

The user reported another test round without issues, accepting this bounded
68-variant gameplay/audio checkpoint. This supersedes its pending manual
status above. The regular executable still matches its build receipt and the
SHA-256 recorded above. No exact duration, itemized outcomes or independent
user hash were supplied. The user also requested fewer routine manual gates
and prioritized restoring cross-version content; see
[content restoration](content-restoration.md). Alternate-callee gameplay and
whole-port fidelity remain separate from this acceptance.
