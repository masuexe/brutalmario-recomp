# Indexed table-read AOT expansion

Date: 2026-10-16. Demo 1-1 now has **50 eligible compiled variants**, up from
49. The new native M1/X1 leaf at `$04F87C–$04F8A5` is named
`CheckOverworldAccessMask` for this project; this is a descriptive label, not
an original source symbol. It reads indexed tables and status bytes, writes
a direct-page scratch byte, and returns a masked Boolean result. demoOnly1
remains isolated.

## Timing and fallback

The [instruction-bus model](aot-timing.md) now includes the leaf's absolute,
absolute-indexed, direct-page, immediate, shift, transfer and branch operations.
Instruction fetches use live PBR/MEMSEL speed; data accesses use the existing
paced helpers. Index page crossings and unaligned direct-page penalties use
six master clocks per internal cycle. Data addressing uses the live DB register,
which need not equal the program bank.

Every absolute or indexed read checks its live address before charging or
accessing it. Unsupported addresses yield at the current instruction with live
registers for interpreter continuation. Direct-page and return-stack checks
remain in force. This does not qualify MMIO accesses or general bus-event
ordering. The model continues to reject unmodeled instructions.

Differential testing exposed a missing synchronization before the generator's
existing block-entry deadline exit. The opt-in path now synchronizes refresh
and beam time there, as well as at instruction boundaries and returns.
Other compiled variants retain their existing timing model.

## Automated evidence

The new ROM-verified 42-byte fixture runs real generated C against the pinned
`interp816`, sharing controlled bus/scheduler support with the pointer test.
**3,510 cases** cover all conditional paths, zero/nonzero masks, crossing and
noncrossing indices, fast/slow ROM, mirrored program banks, four data banks,
aligned/unaligned direct pages, refresh stalls and every tested clock cutoff.
Guards also cover unsupported data banks and stable-memory endpoints.
The complete project suite passes **25 tests**, including the existing negative
test reproducing the old pointer timing error.

| Full 6,104-call route | Prior 49 variants | New 50 variants | Pure interpreter |
| --- | ---: | ---: | ---: |
| Compiled-body bridge entries | 212,564 | 267,717 | 0 |
| Interpreted opcodes | 76,504,998 | 75,601,748 | 84,175,861 |
| Interpreted opcodes in the new leaf's address range | 954,775 | 51,525 | 954,775 |

This removes **903,250 interpreted opcodes** from the route. Remaining work
includes interpreter continuations; a promoted leaf is not guaranteed to run
entirely as compiled code on every invocation. Entry and instruction counts
have different units and do not define an AOT percentage or a speed benchmark.

All eight full-WRAM snapshots and raw framebuffers match the preceding accepted
49-variant build byte for byte. Mode / `$13` / `$14` also match it at every one
of the 6,104 calls. All **85 dense-transition samples** match full WRAM and raw
framebuffers. No multi-field calls or beam-origin inconsistencies were added.
The first reference differences remain mode at 2154, `$13` at 2155 and `$14`
at 2260; broader timing parity remains incomplete.

The new pure-interpreter capture has zero compiled-body entries and matches
the preceding pure-interpreter capture at all eight full-WRAM/image samples.
Its known transient `$14` observation at call 897 remains. Comparing compiled
and pure-interpreter snapshots still leaves 2–9 differing WRAM bytes at six
samples, with identical images; this round does not claim full-state equivalence
between those execution modes.

## Audio regression

Generated audio remains byte-identical to the accepted 49-variant capture:
all **1,719,253 stereo PCM frames** have the same SHA-256. The first two
new runs used the default 32,040-Hz dummy device, whereas the accepted audio
baseline used 32,000 Hz. Their output counters therefore are not a matched
device regression: they report 218 / 214 underflows and 96,173 / 94,729 missing
frames, with no ring overflow drops. Repeating without concurrent test jobs
did not eliminate this difference. The device-rate distinction and its known
dummy-output limitation are described in [audio.md](audio.md).

The matched **32,000-Hz** repeat restores the historical **4 underflows /
2,132 missing output frames / 0 priming events**, with no overflow drops and
the same generated PCM hash. This supports the existing dummy-device rate
limitation rather than a new AOT audio regression. This is a generated-PCM
and matched dummy-output regression check; the deferred subjective star-music issue is
not reopened, and physical output is not newly qualified.

## Manual checkpoint and reproduction

On 2026-10-16, following the requested map movement, level-entry and
pipe/underground return checks, the user reported no issues with the new build
and explicitly confirmed normal DK coin pickup. Together with the automated
checks, this passes the 50-variant build's bounded regression checkpoint.
The DK coin pickup follow-up is closed. Save/reload persistence and whole-port
fidelity are not established by this report. See [playtesting.md](playtesting.md)
for the manual evidence and its scope.

```sh
python3 tools/m1.py generate
python3 tools/m1.py build
python3 -m unittest discover -s tests -v
python3 tools/m1.py native --capture aot-indexed-new
python3 tools/m1.py native --interpreter-only --capture aot-indexed-floor-new
python3 tools/analyze_aot_coverage.py \
  local/captures/aot-indexed-new local/captures/aot-indexed-floor-new
python3 tools/m1.py build --audio
python3 tools/m1.py native --audio --audio-device-rate 32000 \
  --script recomp/inputs/star-audio.script --capture aot-indexed-audio-new
```

Local evidence: captures `aot-indexed-full`, `aot-indexed-interpreter`, and
`aot-indexed-transitions`, `aot-indexed-audio`, `aot-indexed-audio-solo`, and
`aot-indexed-audio-32000`; reports `local/reports/aot-indexed-coverage.json`,
`aot-indexed-scenes.json`, `aot-indexed-state.json`, `aot-indexed-timing.json`,
`aot-indexed-transition-scenes.json`, `aot-indexed-floor-scenes.json`,
`aot-indexed-floor-regression.json`, `aot-indexed-audio-comparison.json`,
and `aot-indexed-tests-final.log`.
The preceding configuration, generated source, binary and receipt are archived
at `local/probes/aot-indexed-baseline/`. Generator hashes, timing policy and
built analysis identities remain recorded in generation/build/capture receipts.
