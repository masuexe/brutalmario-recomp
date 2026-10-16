# Demo 1-1 timing investigation

Date: 2026-10-15. A frame-driver bug is fixed and the native executable has
been rebuilt. Cross-core timing acceptance remains open.

Later update: the [boot APU-clock investigation](boot-timing.md) fixes the
first 225–226 divergence by making the sound-processor clock consistent with
NTSC beam timing. A further [counter-read fix](loading-timing.md) removes the
frame-838 divergence; the compiled route first differs at frame 2154.
Measurements below retain the earlier interrupt-fix checkpoint.

## Confirmed cause and fix

The beam driver sets a master-clock deadline, but invokes interrupts through
`interp_bridge_run_interrupt`. That entry runs through RTI without scheduler
deadline checks. A long handler can therefore consume several hardware fields
inside one host frame call. This also happens with all compiled entries denied.

The first large jump in the instrumented route is host frame **227**: its CPU
half consumes **7,867,776 master clocks**, about **22.016 field periods**.
Further multi-field calls occur at frames 838, 1990, 2196, 2432 and 2689.
After 6,104 calls, the old driver has advanced approximately 6,158 fields.
Its beam clock and position also lose their common origin starting at frame 899.

The project-owned [runtime patch](../patches/runtime/0002-bound-interrupt-execution.patch)
enters the same resumable scheduler path used for ordinary guest execution
after pushing the architectural interrupt frame. The handler can yield at a
deadline and resume in the next host call, retaining the guest stack. Its real
RTI restores the interrupted PC. Interrupt trace accounting and WAI handling
are retained. The old run-through-RTI API and upstream checkout are unchanged.
No guest logic, ROM, input timing, generated C, or historical content is changed.

## Measurements

All runs use the existing 6,104-call route, fresh capture directories, and the
same source and ROM pins. The before run already includes both PPU fixes.

| Observation | Before timing fix | After timing fix |
| --- | ---: | ---: |
| Calls consuming at least two complete field periods | 6 | 0 |
| Clock-derived field index at call 6,104 | 6,158 | 6,104 |
| Maximum beam overshoot from expected host-frame edge | 19,442,946 clocks | 136 clocks |
| Frames with inconsistent beam clock/position origin | 5,206 | 0 |
| Title WRAM `$13/$14` at call 600 | `37/d5` | `22/c0` |
| Reference title WRAM `$13/$14` | `23/c1` | `23/c1` |

The interpreter-only run also reaches field 6,104 without multi-field calls
or beam-origin inconsistencies; its largest boundary overshoot is 326 clocks.
Its bridge counters confirm **zero compiled entries**. The compiled run records
52,645 bridge entries and 81,247,420 interpreted opcodes; these are different
units and do not define an AOT percentage.

Matched scene pictures improve substantially on the common RGB5 grid:

| Scene | Before: differing pixels | After: differing pixels |
| --- | ---: | ---: |
| Title | 0 | 0 |
| File menu | 38,283 | 38,283 |
| Opening message | 321 | 321 |
| Overworld | 5,556 | 0 |
| Level entry | 774 | 122 |
| Walking | 837 | 480 |
| Pit/death segment | 16,214 | 246 |
| Endurance end | 5,725 | 11 |

Both renderer choices produce the same eight corrected scene pictures. The
compiled and interpreter-only runs have byte-identical framebuffers at all
eight samples. Full sampled WRAM differs by 0–22 bytes, all on the stack page;
these differences are retained, not masked. Per-frame `$13/$14/mode` observations
match between those two runs at 6,103 of 6,104 calls: `$14` differs at **898**
(`c0` compiled, `00` interpreter-only), then matches again. This is a remaining
execution-phase discrepancy, not complete translation equivalence.

## Validation and remaining work

- The ROM-free scheduler test models an interrupt lasting more than three
  fields. It checks one field per host call, the suspended stack frame, a single
  interrupt delivery while the guest has NMI disabled, and the final RTI return.
  It fails against the pinned original driver and passes against the patch.
- All **12 project tests pass**, including both PPU regression tests.
- Compiled execution with both renderer choices and interpreter-only execution
  each complete the full route normally.
- The optimized-renderer transition route preserves the previous fix: all 42
  consecutive MARIO START samples at frames 2155–2196 match the independent
  reference picture on the RGB5 grid.

The first mismatch in the selected game-state observations is now precisely
located: **mode at host frame 225** is `04` in Snes9x and `03` natively; native
reaches `04` at frame 226. This predates the old multi-field jump. The first
`$13` mismatch is at 248 and the first `$14` mismatch is at 308. These are the
first mismatches for those selected bytes, not the first differing instruction
or full WRAM state. Later observations still differ by roughly one or two game
ticks; a constant input-frame shift has not been justified.

Next investigate the boot transition at 225–226 and the compiled/interpreted
boundary at 898. Inspect the reference's frame-end phase and instruction/interrupt
timing before changing inputs or game code. Snes9x 1.63 remains a comparator;
the user-confirmed historical compatibility baseline is **ZSNES 1.51**, which
has not been run locally.

At this timing checkpoint, the file-menu background was missing with both
renderers. This was subsequently traced to render-only HDMA state being
discarded by complete-register restoration, and is now fixed; see
[menu-background.md](menu-background.md). Both the file-menu and opening-message
samples now match the reference picture. The timing differences above remain.
For later audio and boss checkpoints, see [playtesting.md](playtesting.md).
Windows-native execution remains unqualified.

## Reproduction and local evidence

```sh
python3 tools/m1.py build
python3 -m unittest discover -s tests -v
python3 tools/m1.py native --renderer optimized --capture timing-new
python3 tools/m1.py native --renderer legacy --capture timing-legacy-new
python3 tools/m1.py native --renderer legacy --interpreter-only --capture timing-floor-new
python3 tools/analyze_timing.py local/captures/reference-verified \
  local/captures/timing-new local/captures/timing-floor-new
python3 tools/compare_captures.py \
  local/captures/reference-verified local/captures/timing-new
```

`tools/m1.py` now records `timing.csv` for native captures. The project-owned
host glue samples clocks and selected WRAM bytes before CPU execution, after
CPU execution, and after rendering. The optional `M1_TIMING_TRACE` environment
variable enables this observation; it is inactive for normal interactive play.
It writes no guest state. The analyzer reconstructs reference WRAM from its
per-frame delta trace, carrying state across frames without changed bytes.

Ignored local evidence:

- `local/captures/timing-baseline`: PPU fixes, original frame driver.
- `local/captures/timing-candidate`: both runtime patches, optimized renderer.
- `local/captures/timing-fixed-legacy` and `timing-fixed-floor`: paired AOT check.
- `local/captures/timing-fixed-transitions`: dense start-screen regression capture.
- `local/reports/timing-analysis.json`, `timing-baseline-scenes.json`,
  `timing-fixed-legacy-scenes.json`, and `timing-fixed-aot-comparison.json`.

All captures retain binary, ROM, route and source receipts. The current
interactive executable stays at `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp`;
the existing interactive settings and save data are preserved.
