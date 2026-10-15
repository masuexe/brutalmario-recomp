# demoOnly1 death black-screen fix

Date: 2026-10-15. The user reports normal boss behavior but frequent black
screens after death. The failure is reproduced and a target-specific legacy
audio compatibility mode is implemented and enabled in the rebuilt demoOnly1
executable, including direct executable launches.

## Confirmed failure

The existing natural-death smoke route reaches overworld-loading mode `$0c`
and then stalls. At call 2689 the CPU is polling around `$00:8082–8085`,
waiting for the SPC IPL ready pair `$aa/$bb`. NMI is disabled during this
upload. The `FF` reload request has reached the SPC's input port, but the
SPC never replies. An interpreter-only run has the same failure, excluding
compiled guest execution as a necessary cause.

Per-frame APU RAM observations locate corruption before the final black
screen: at call **2498**, during the death-music transition, native echo
writes overwrite SPC engine code. The reference engine's corresponding
code remains intact. The native DSP write log records an ESA change to
`$ef00` while the old echo index is **1778**:

```text
$ef00 + 1778 * 4 = $10ac8 -> 16-bit wrap to $0ac8
```

The wrapped writes enter executable SPC RAM. Later SPC PCs around `$0c3c`
are executing overwritten data, explaining why the next music upload can
wait forever. The frozen picture is a consequence of this handshake stall.

This is a compatibility requirement of this legacy music driver. Snes9x's
pinned libretro options explicitly provide `snes9x_echo_buffer_hack` for old
Addmusic hacks. The user-confirmed historical environment remains ZSNES
1.51; its implementation has not been inspected or run locally.

## Implementation and scope

[0003-add-separate-echo-compatibility.patch](../patches/runtime/0003-add-separate-echo-compatibility.patch)
adds opt-in, per-DSP echo storage. Both echo reads and writes use this
independent 64-KiB memory, while SPC execution and sample decoding continue
to use the real APU RAM. There is no forced IPL acknowledgement, timeout
bypass, or repair of live SPC instructions.

- The generic runtime still defaults to shared RAM.
- demoOnly1 enables `SNESRECOMP_SEPARATE_ECHO=1` by default. The default is
  built into its startup, so the executable also works when launched directly.
  The launcher and capture runner select the same mode explicitly.
- Demo 1-1 keeps shared-RAM behavior and its original compatibility policy.
- An explicit `SNESRECOMP_SEPARATE_ECHO=0` remains available in the capture
  runner for hardware-model diagnostics.
- New demoOnly1 reference captures select
  `snes9x_echo_buffer_hack=enabled`, unless explicitly overridden in
  `SNESREF_CORE_OPTIONS`. Receipts record both native policy and reference
  core options. Earlier captures retain their earlier policies.

Each DSP owns and frees its own storage. Compatibility snapshots append an
`ECHO` chunk containing the feedback history; loading it restores that
history. Older snapshots without the chunk start with a silent separate
buffer and leave the following APU bytes untouched. A loader with the mode
disabled consumes and discards an existing chunk. New compatibility states
require a runtime that understands the chunk; old executables should not
be used to read them. Full game savestate qualification remains separate
from the synthetic storage round-trip test.

The derived ROMs and original IPS inputs are unchanged. Upstream checkouts
remain clean. Both native targets have been rebuilt with matching receipts.

## Validation

- A ROM-free regression reproduces the measured wrapped echo write. Shared
  mode changes the target APU bytes; compatibility mode preserves every APU
  byte and reads feedback from separate storage. It also tests current and
  legacy snapshot handling. The test fails against the pinned original DSP.
- All **17 project tests pass**, including existing PPU and frame-driver tests.
- The short natural-death reproducer now reaches overworld mode `$0e`.
  Its engine bytes `$0c20–0c5f` remain identical to the independent reference.
- Three consecutive natural gameplay deaths return to the overworld, with
  lives decreasing **5 -> 4 -> 3 -> 2**. No state pokes are used by this route.
- A controlled death in boss room `$178` returns to the overworld with one
  life deducted. The script initializes the WRAM effects of the unchanged
  ROM's `$00:f606` death routine, then lets the real animation, music driver,
  and reload run. This is separate from a natural boss-collision test.
  At the final sample, both cores are in mode `$0e`, at X=270/Y=134, with
  four lives, and their pictures match on the RGB5 grid. Full WRAM differs
  by 43 bytes and is not claimed identical.
- The primary Demo 1-1 6,104-call regression has identical full WRAM and raw
  framebuffer bytes at all eight samples compared with `timing-candidate`.
- A direct executable run with no echo environment override and no timing
  observer also completes the natural-death reproducer and returns to the
  overworld with one life deducted. The built-in target default is effective.

After the fix, the user manually tested several deaths and confirmed that
all returned to the overworld without a black-screen hang. This completes
the manual death-return checkpoint. The exact count and cheat setting were
not supplied.

The fix addresses this reproduced audio-memory failure. It does not assert
that every possible black screen has the same cause or qualify all boss
defeat/exit behavior.

## Reproduction

```sh
python3 tools/m1.py build --target demo-only-1
python3 -m unittest discover -s tests -v
python3 tools/m1.py native --target demo-only-1 --renderer optimized \
  --script recomp/inputs/demo-only-1-repeat-death.script --capture repeat-death-new
python3 tools/m1.py reference --target demo-only-1 \
  --script recomp/inputs/demo-only-1-boss-death.script --capture boss-death-ref-new
python3 tools/m1.py native --target demo-only-1 --renderer optimized \
  --script recomp/inputs/demo-only-1-boss-death.script --capture boss-death-new

# Manual retest: close an old process, then launch the rebuilt target.
python3 tools/play_demo_only1.py --boss-door
```

`M1_TIMING_TRACE` now also observes the resume PC, stack, interrupt state,
SPC PC, ports and clock under the existing APU lock. Automated native captures
save a final `apu-ram.bin` before the audio mutex is destroyed. These optional
observations are inactive for normal interactive play. Their wall-clock
overhead means instrumented capture speed is not an interactive performance
benchmark.

Ignored local evidence: `death-floor-baseline`, `death-apu-ram`,
`death-native-apuram`, `death-reference-apuram-ready`, `death-echo-log`,
`death-echo-fixed`, `death-repeat-fixed`, `death-boss-fixed`,
`death-boss-reference-fixed`, and `death-primary-regression` under
`local/captures/`. Reports include `death-boss-comparison.json` and
`death-primary-comparison.json` under `local/reports/`.

The diagnostic reference core under `local/diagnostics/snes9x-apu/` is a
copy of the pinned sources exposing APU RAM through memory ID `$100` for
observation. It is explicitly recorded as a core override and is not the
stock reference binary. Final controlled-death comparisons use the stock
reference binary and its documented echo compatibility option.
