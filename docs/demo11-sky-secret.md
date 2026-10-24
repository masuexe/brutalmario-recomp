# Demo 1-1 Sky Star secret exit: investigation

Date: 2026-10-25. Status: investigation only. No ROM change. The user accepted
the Star World BGM checkpoint and supplied the secret-route hint: exhaust the
rocket fuel on purpose, fall, then fly to the right and climb.

## Rocket code facts

The rocket is custom sprite `28`. Its restored block is at `$38:A261` on the
current head. The code gives these mechanics:

- Init at `$38A2CA` sets fuel `$1594` to `0x0B`. It sets fuel to zero when
  `$1EA2` has bit 6 set (a midway-style retry flag).
- Flight runs at `$38B3A9`. The finish check at `$38B53C` runs every frame.
- Normal finish: sprite Y high byte `2` and Y low byte below `0x91`.
- Secret finish: sprite Y high byte `4`, X high byte `1` and Y low byte below
  `0x50`. That is rocket Y in `0x400..0x44F`.
- Either branch sets `$C2=1` (rocket finish state). The rocket stops. Fuel goes
  to zero.
- The rocket Y follows Mario Y minus `0x20`. The check uses the previous
  frame value.
- Climb is one pixel per frame. Fuel drops one unit per 256 frames (first unit
  255 frames, wrap frame does not count). Empty fuel starts the fall.
- Refill sprite `17` sets fuel back to `0x0B`.

## Measured route data (current head, reference host)

- Enter at Mario `$0070/$0CBF` with fuel `0x0B`. A straight climb stalls at
  Y about `$0BB0`.
- Stall to empty fuel there. Keep right pressed during the fall. The rocket
  drifts into the right page and reaches a refill. Observed contact reads
  Mario Y about `$0F1B` at X `$0102`; later dumps read about `$0ECB`.
- After that refill, the right page becomes the climb. Holding right reaches
  X `$01D2` and stalls at Y about `$0DA0`. Moving left from there passes the
  bar and keeps climbing (X `$012D`, Y `$0C71`) in one test.
- The ignored captures under `local/captures/middle-right-*` record earlier
  attempts. The best right-page sample is Mario Y `$0527` at X `$0185` with
  fuel `1`. A left-page climb reaches Y `$03CF` with fuel `2`, but a wall at
  X `$00E2` blocks the crossing into the right page.

## Budget

The secret band needs Mario Y below about `$0470` (rocket Y below `$0450`).
From the refill contact at Y `$0F1B` the climb needs `2,725` pixels. One full
fuel load gives `2,814` pixels. The slack is `89` pixels.

Every ceiling bounce that burns frames without climbing spends that slack. One
test reached Y `$0C71` with fuel `5`; that line wasted about `850` pixels.
A clean line must pass each bar without a stall.

## User verification and status

On 2026-10-25 the user verified this route in play. The user reports that the
course can be completed, and gives these facts:

- The right page has no fuel blocks.
- A right-page ascent line with almost no bar hits is necessary to clear.
- After the ascent there is a key and a keyhole.
- Inserting the key into the keyhole unlocks the Warp Star.

The user asked to stop the automated route search. This document changes no
ROM. Automated route qualification and the secret-clear capture stay deferred.
The route is user-verified; it is not machine-qualified yet.

## Forced-fire diagnostic result

A diagnostic patch relaxed the secret X check. The run set `$C2=1` on the
left-page crossing but did not return to the map. The secret finish needs the
right-page key area, not only the Y band.

## Diagnostic notes kept for later

- An infinite-fuel patch (NOP on the fuel decrement at `$38B3E5`) lets a probe
  climb without a time limit. An alternating left-page line reaches the normal
  finish. A direct position poke to the bottom did not settle in the level.
- One full fuel load gives 89 pixels of slack above the required climb. A
  machine route needs near-zero ceiling bounces.

## Reproduction

```sh
python3 tools/m1.py reference --target demo11-star-bgm \
  --script local/probes/sky-secret-attempt6.script --capture fresh-sky-secret-ref
```

Probe scripts `sky-secret-*` under ignored `local/probes/` hold the tested
lines. They use the usual boss-practice map shortcut and no progress, fuel,
coin, life or SRAM writes.
