# Indexed coordinate arithmetic and mixed accumulator widths

Date: 2026-10-18. This round promotes one small helper to produce a
**55-variant Demo 1-1 candidate**, following the manually accepted 54-variant
palette build. The larger display-data loops remain interpreted. Automated
results and the subsequently passed manual checkpoint are recorded below.

## Selection and behavior

The remaining hot loops around $13F076/$13F14C call helper $13F1A7, which calls
and later falls through into the leaf at **$13F1C2..$13F1D4**. The pinned ROM
leaf has nine instructions:

```text
LDA $0E65,X
XBA
LDA $0E35,X
REP #$20
SEC
SBC $001A,Y
STA $0000,Y
SEP #$20
RTS
```

It assembles a 16-bit coordinate from two indexed bytes, subtracts a reference
word and stores the result in WRAM. It enters/exits in native M1/X1 and uses
M0/X1 for the subtraction/store. The project name `SubtractIndexedCoordinateWord`
describes this observed behavior; it is not a recovered original symbol.

The [target symbols](../recomp/targets/demo-1-1/symbols.toml) and
[instruction policy](../recomp/targets/demo-1-1/timing.json) select only that
entry variant. Promoting this prerequisite is smaller than qualifying the
entire caller, whose nested calls and other arithmetic need additional work.

## Restricted timing-model extension

The [instruction model](../recomp/generator/instruction_bus.py) now supports
`XBA`, `REP #$20`, `SEC`, `SBC abs,Y`, `STA abs,Y` and `SEP #$20` in the
qualified sequence. M0 is permitted only for the explicitly modeled subset;
other status masks and unsupported width/instruction combinations are rejected.
The selected entry retains X1 throughout. This does not qualify arbitrary
index-width changes or general mixed-width functions.

Data-transfer counts and live-address guards now use the accumulator width for
the new subtraction/store. The model charges real code/data bus costs plus
internal cycles, and retains page-cross, refresh and instruction-deadline
handling. The existing generated arithmetic implements the pinned interpreter's
binary and decimal SBC semantics; this round qualifies its restricted use
instead of adding a game-specific arithmetic replacement.

Two-byte stores must fit wholly in WRAM. Reads must fit the existing stable
WRAM/ROM policy. Unsupported accesses yield before either byte is touched,
preserving live registers, flags, stack and M0 status after REP.

There is also an explicit **bank-end word guard**: pinned runtime word accessors
wrap the high-byte address within the bank, while `interp816`'s indexed word
path carries to the next bank. The model therefore yields when a two-byte
access starts at low address $FFFF. This avoids silently qualifying different
address semantics; no shared runtime accessor was changed. The actual leaf's
small indexed operands do not encounter this endpoint in its normal X1 context.

The earlier byte-only palette-port timing contract remains separate. This
round does not enable word MMIO or alter hardware register-write timing.

## Differential checks

[C harness](../tests/aot_coordinate_timing_test.c) and
[Python driver](../tests/test_aot_bus_timing.py) compile real generated C against
the pinned interpreter and actual paced-accessor/region-speed bodies on the
existing controlled bus and scheduler.

| Probe | Cases |
| --- | ---: |
| Actual ROM M1 -> M0 -> M1 leaf | 23,616 |
| Synthetic all-M1 byte-arithmetic variation | 23,616 |
| Word endpoints, last-safe stores and unsafe data-bank fallback | 112 |
| **Total** | **47,344** |

Each arithmetic probe covers edge values, binary/decimal mode, incoming flags,
slow/fast ROM, mirrored code banks, six data banks, indexed page crossings,
three direct-page placements and controlled refresh. Decimal data includes
both valid and invalid digit patterns, compared to this pinned interpreter;
that does not establish independent silicon BCD correctness.

For 20,160 deadline cases per arithmetic probe, tests compare the exact yielded
PC, architectural registers, accumulator/index widths, flags, guest/master
clocks and full WRAM, then continue through the interpreter and compare the
final state/memory as well. Cutoffs cover intermediate XBA flags and both sides
of REP/SEP. Initial accumulator B values include zero and negative cases.

Synthetic endpoint fixtures check indexed WRAM-to-I/O crossings, word reads and
stores at a bank end, the last safe two-byte WRAM destination and unsupported
data banks. Guards preserve M0 at the relevant fallback instructions. These
fixtures alter only disposable test code, not the prepared game ROM.

All **60 project tests pass**. The final arithmetic-only run also passes after
strengthening the initial-B/XBA cases. This is controlled CPU/bus qualification,
not general interrupt or full hardware co-simulation.

## Full-route regression and coverage

| Same 6,104-call route | Accepted 54 variants | Candidate 55 variants |
| --- | ---: | ---: |
| Compiled-body bridge entries | 283,424 | 290,294 |
| Interpreted instructions | 71,949,915 | 71,888,085 |
| Interpreted instructions in $13F1C2..$13F1D4 | 123,660 | 61,830 |

The new compiled call path removes **61,830 interpreted instructions** and
adds 6,870 body entries. The caller's fall-through path still executes these
same bytes interpreted: promoting a function entry does not compile every
execution of its address span. The larger caller loops remain future work.
Entry/instruction counts have different units and do not establish an AOT
percentage or measured speed gain.

All eight full-WRAM/raw-framebuffer samples and all 85 dense-transition samples
match the 54-variant build byte for byte. Mode, $13/$14, CPU/beam clocks and
beam position match at every one of 6,104 calls. No multi-field calls or
beam-origin mismatches are introduced. Existing selected reference differences
remain mode at 2154, $13 at 2155 and $14 at 2260; cross-core parity is incomplete.

The pure-interpreter route has zero compiled-body entries and matches the
previous pure-interpreter run at all eight WRAM/image samples and all 6,104
selected clock/state observations. Compiled versus pure-interpreter samples
retain the previous six 2–9-byte WRAM differences with identical images;
full-state equivalence between execution modes is not claimed.

## Audio regression

At the matched 32,000-Hz SDL dummy device rate, all **1,719,253 generated stereo
PCM frames** are byte-identical to the 54-variant capture, at the native
32,040-Hz WAV rate. Both retain 4 output underflows, 2,132 missing output frames,
no priming and no ring-overflow drops. Device-consumed tail counts vary with
shutdown scheduling. This qualifies generated PCM and the matched dummy-output
regression, not a new physical listening or ZSNES audio comparison.

## Manual checkpoint and reproduction

Following the requested direct launch of
`local/build/demo-1-1/BrutalMarioDemo11SNESRecomp`, the user reported no issues
in response to the requested movement/jumping, character/enemy/object position
and display, pipe/underground return and transition checks. Together with the
automated evidence above, this passes the 55-variant build's bounded manual
regression checkpoint.

The workspace executable's SHA-256 is
`2811b0080b0606058f333a9b83a06677a0176230dcb41de46e44aefa7db10423`, matching its
build receipt. This is workspace verification; the user did not supply an
independent executable hash or separately enumerate subtest outcomes and
session duration. Whole-port fidelity and new demoOnly1 coverage are not
established by this report. The accepted 55-variant build is the next baseline.

Reproduction:

```sh
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k coordinate -v
python3 tools/m1.py generate
python3 tools/m1.py build
python3 tools/m1.py native --capture NEW_FULL_CAPTURE
python3 tools/m1.py native --interpreter-only --capture NEW_FLOOR_CAPTURE
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture NEW_AUDIO_CAPTURE
```

The accepted prior regular binary, generated tree, configuration and policy
are archived with hashes under `local/probes/aot-arithmetic-baseline/`.
Local captures use `aot-arithmetic-full`, `aot-arithmetic-transitions`,
`aot-arithmetic-interpreter` and `aot-arithmetic-audio`. Reports under
`local/reports/` use the same `aot-arithmetic-` prefix, including the complete
test log and final arithmetic differential log. Tracked upstream files remain
unchanged.
