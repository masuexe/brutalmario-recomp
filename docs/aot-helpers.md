# Pointer and indexed-phase helper batch

This checkpoint promotes three M1/X1 leaves for the **63-variant Demo 1-1
build**. The 60-variant build was its bounded non-audio regression baseline.
The user subsequently reported no issues after the demo-1-1 native-audio
launcher follow-up; the 63-variant build is accepted within that reported scope. There are no separate 61- or 62-variant manual checkpoints.
The separate demoOnly1 target is unchanged.

## Selection and behavior

The bank-15 coordinate callers still contain unqualified callees and wider
mode transitions. This round instead qualifies three independently testable
leaves, including an indexed helper used by that bank's caller:

| Descriptive symbol | Entry/span | Behavior |
| --- | --- | --- |
| `RestoreLevelBufferPointer` | $0DA6B1..$0DA6B9 | Copies direct-page $6B/$6C into $04/$05; RTS. |
| `AdvanceLevelBufferRow` | $0DA97D..$0DA991 | Adds $10 to direct-page $57, copies the low result into Y and, on carry, increments $6C and copies it into $6C/$6F/$05; RTS. |
| `ComputeIndexedFramePhase` | $15A055..$15A05B | Adds DB:$A045,X to direct-page $13 with carry cleared; RTS. |

These names are descriptive, not recovered original source labels. All
instruction bytes are independently checked against the verified local ROM.
The phase test's 256-byte table span is loaded from that ROM into temporary
fixtures; only the instruction fixtures are retained in the project.

The only timing-model extension is admitting native M1 `BCC` ($90) with zero
data transfers. The existing branch emitter supplies taken-branch charges;
all other instructions reuse existing qualified timing. Maximum direct-page
operand offsets are $6C, $6F and $13, respectively, so the last admitted D
values are $1F93, $1F90 and $1FEC. Existing native/stack/live-address guards
remain active. No runtime patch or pinned upstream source was changed.

For the indexed phase leaf, X is eight-bit and $A045+X always stays in upper
ROM or WRAM. A bank without a low WRAM mirror, such as $40, is therefore
not itself a reason to reject this particular read. Its allowed full-call
behavior is checked explicitly. This does not expand the runtime's existing
address policy.

## Differential qualification

The new shared helper harness compares actual generated C and paced bus
helpers against the pinned interpreter, including A/X/Y, S/D/DB/PB, flags,
M/X, CPU/master clocks, all 128 KiB WRAM and ordered byte writes. Deadline
cases compare both the paused state and interpreter continuation through RTS.
The controlled refresh/scheduler probes supplement separate route captures.

The three leaves pass **311,172 cases**:

| Leaf | Cases | Coverage |
| --- | ---: | --- |
| Pointer restore | 19,073 | 4,096 byte/flag combinations, 576 context combinations, 14,400 cutoff cases, unsafe-D entry guard. |
| Row advance | 146,049 | All 65,536 low/high byte pairs in binary and decimal modes, 576 context combinations, 14,400 cutoff cases, unsafe-D entry guard. |
| Indexed phase | 146,050 | All 65,536 addend pairs in binary and decimal modes, 576 context combinations, 14,400 cutoff cases, unsafe-D guard and upper-ROM $40 data-bank admission. |

The arithmetic sweeps include invalid BCD inputs. Independent binary result
assertions supplement the interpreter oracle. Context cases include both ROM
speeds/mirrors, ROM and WRAM data banks, indices around the $A0FF/$A100 page
crossing and the last-safe direct-page placement. Cutoffs sweep clocks 1..600
across six edge values, binary/decimal modes and both ROM speeds.

The probes do not claim arbitrary rewritten-return handling or physical bus
timing. No audible manual qualification is inferred from automated audio.

## Verification results

The 63-variant candidate was regenerated, rebuilt and re-captured from the
checked-in sources before this record was written:

| Check | Result |
| --- | --- |
| Project tests | 70 pass (165 s), including the 311,172 new differential cases |
| Full route | 8 memory-image samples, 0 differing WRAM bytes, 0 differing RGB pixels |
| Dense transitions | 85 samples, 0 differing bytes/pixels |
| Pure-interpreter floor | 0 compiled body entries; 8 samples identical to the candidate |
| State/clock samples | 6,104 full-route and 3,225 audio calls, 0 differences in mode, counters, CPU/beam clocks, V/H position |
| Generated PCM | 1,719,253 frames, SHA-256 `1447bfbbc050a936d39233c76942c7e610e2cd1c651b052c1b8e77bd499d6352`, identical to the 60-variant baseline |
| Interpreted instructions removed | 64,560 on the fixed route (68,865,647 -> 68,801,087) |

Remaining interpreted opcodes inside the three spans are bounded hand-backs at
the deadline: 3 for pointer restore, 27 for row advance and 0 for indexed
phase. They are reported, not hidden.

The dummy audio device's underflow counters still vary between runs; that
variability is inherited from the baseline and is not attributed to this
batch. Generated PCM and every selected state/clock sample match exactly.

### Build identity note

Regenerating from the current sources is deterministic: two consecutive
`generate` runs produce identical output, and `build` reproduces the same
executable hash. The binary recorded here is
`334bcdd755914f66b92efc4579979c1d4a19b81c9f7aec7a894f9e1956a633d0`
(regular) and
`28d086d745f9526d18b554262294b2b0e6a69e3bfc6f4620f9fce47f5f344a35`
(audio). Captures `aot-helpers-*2` and `aot-helpers-audio` record that hash
in their receipts.

## Reproduction

```sh
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k restore_pointer -v
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k advance_row -v
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k frame_phase -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
```

The prior binary, generated tree and configuration are archived with hashes
under `local/probes/aot-helpers-baseline/`. Captures and local reports use
the `aot-helpers-` prefix. The user's subsequent gameplay/audio acceptance is recorded below.


## Accepted manual follow-up and launcher

The user reports that this batch and the demo-1-1 audio stutter follow-up were
completed and tested without issues. This accepts the 63-variant build's
bounded gameplay/audio checkpoint and closes the carried audible check for
this current build. Exact session duration, individual checklist results and
an independent executable hash were not supplied. The workspace regular
binary still matches its recorded build receipt.

Use the launcher for subsequent interactive testing:

```sh
python3 tools/play_demo_1_1.py
```

Direct executable launch bypasses Windows-native audio selection on this WSL
setup. See [audio synchronization](audio-sync.md) for the RDP-versus-native
measurements. The historical dummy-output counter variability remains in the
automated evidence and is not reclassified as physical listening evidence.
The accepted 63-variant build becomes the next bounded regression baseline;
no whole-port fidelity or new demoOnly1 coverage is claimed.
