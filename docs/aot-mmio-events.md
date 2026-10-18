# PPU write-event qualification before AOT promotion

Date: 2026-10-18. The next palette-loop expansion is **blocked by a reproduced
event-timestamp mismatch**, not by a total-clock mismatch. The accepted
frontier remains 52 eligible variants. No game runtime, generator policy,
prepared ROM or executable was changed by this investigation.

## Minimal counterexample

The synthetic M1/X1 leaf writes a CGRAM index through $2121, then the low and
high color bytes through $2122, and returns. Its instruction bytes are:

```text
A9 23 8D 21 21 A9 34 8D 22 21 A9 12 8D 22 21 60
```

This is a controlled fixture emitted at an already-selected test entry, not
the actual game function at that address. The real deferred loops $169585
and $13EFB2 contain the same M1 `STA $2121` / `STA $2122` operations among
table reads and loop control. Their complete bodies have not been promoted
or qualified by this fixture.

With slow-ROM fetches, no refresh, and a zero starting clock:

| Event | Interpreter master clock | Test-only unguarded AOT clock |
| --- | ---: | ---: |
| $002121 = $23 | 16 | 46 |
| $002122 = $34 | 62 | 92 |
| $002122 = $12 | 108 | 138 |
| Final clock after RTS | 180 | 180 |

Addresses, values, order, final CPU state and full WRAM agree. Each hardware
write is nevertheless **30 master clocks later** in the candidate AOT path.
With fast-ROM fetches in the mirrored program bank and MEMSEL enabled, the
offset is **24**. Matching final time cannot qualify PPU event timing.

## Why it happens

The pinned interpreter bridge's memory callbacks accumulate transfer time
in `s_interp_bus_master`. While `bridge_bus_write` calls `cpu_write8`, the
CPU's published master clock still holds the instruction-start value. The
bridge advances that clock after `interp816_runOpcode` returns.

Instruction-paced AOT charges the opcode/operand fetches before the effect;
`cpu_write8_paced` then charges the destination transfer before calling
`cpu_write8`. At that moment the exposed clock is the store's completion
value. For this `STA abs`, three slow-ROM fetches plus the six-clock register
transfer give the observed 30-clock difference; fast fetches give 24.

The real `WriteReg` path synchronizes the PPU/beam to the published CPU master
clock before dispatching the register write, so this is a meaningful event
timestamp, not merely a different diagnostic counter. A counterexample near
a scanline boundary can therefore select a different raster line.

This comparison establishes a difference between the existing execution tiers.
It does not establish that the interpreter's instruction-start timestamp is
the silicon bus-write time, or that the candidate end timestamp is a complete
hardware-correct timing model.

## Reproducible test and limits

[Python driver](../tests/test_aot_bus_timing.py),
[C probe](../tests/aot_mmio_event_test.c), and the existing
[controlled bus support](../tests/aot_bus_test_support.h).

```sh
python3 -m unittest discover -s tests -p test_aot_bus_timing.py -k palette -v
```

The probe compiles actual generated C and the pinned interpreter. It extracts
the actual `cpu_region_speed`, paced accessors, bridge write callback, bridge
bus-time accounting and post-op clock-accounting bodies. PPU writes terminate
at an event recorder observing the clock that would be passed to `WriteReg`.
APU callbacks assert if reached; this fixture cannot qualify APU behavior.

There are **412 cases**: 192 whole-leaf contexts across slow/fast fetches,
mirrored code banks, four system data banks, six starting clocks and optional
controlled refresh, followed by 220 deadline cutoffs. Every candidate run
checks registers, flags, stack, clocks, full WRAM, event addresses/values/order,
and expected event-time differences. Deadline cases additionally compare yield
PCs. Across the whole-leaf contexts, **72 write events** fall in different
1364-clock scanline buckets. These are modeled boundary examples, not a full
beam-driver or actual raster/IRQ co-simulation.

The production WRAM-only guard is compiled unchanged under a second name.
With that guard active, generated code yields at the first MMIO store before
any hardware effect; continuing in the interpreter preserves all three exact
event timestamps and the final state. A disposable test-only wrapper bypasses
the guard solely for the two palette ports to expose the counterexample.
Neither the bypass nor a new policy entry reaches a game build.

## Decision and next implementation boundary

Keep the palette loops interpreted. Their eventual AOT path needs an explicit
hardware-event timing contract, rather than a fixed per-loop time adjustment
or indiscriminately enabling hardware destinations in the WRAM write guard.

The smallest next investigation is a restricted byte-write event model for
$2121/$2122 that preserves interpreter-visible event timing while maintaining
instruction totals, refresh/deadline behavior and continuation. Validate it
with these event tests before enabling actual palette loops, then perform the
full-route, dense-transition and generated-audio regressions. Any decision to
change interpreter-wide event timing instead requires separate beam/IRQ/HDMA
qualification; it is broader than this restricted AOT expansion.

The previously accepted 52-variant executable remains the gameplay baseline;
no new manual playtest is needed for this test-only qualification checkpoint.
All **56 project tests pass**. The full-suite log is
`local/reports/aot-mmio-tests.log`; `local/reports/aot-mmio-events.json` records
the checkpoint totals and tested source hashes.
