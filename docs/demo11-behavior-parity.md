# Behavior parity harness for collision and sprite work

Date: 2026-10-26. This note starts the terrain collision and custom sprite
work. The method is a matched-scene comparison between the reference host and
the native host.

## Method

1. Write a practice script. Use the map transfer and level entry pattern from
   `local/probes/parity-baby-yoshi.script`.
2. Capture the same script on both hosts with `tools/m1.py reference` and
   `tools/m1.py native`.
3. Compare the matched scene dumps with `tools/compare_captures.py`. It reports
   the game mode, level, player position, WRAM byte differences and framebuffer
   differences.

The comparison is bounded: matched scene samples only. It is not a full
frame-by-frame or audio qualification.

## Baseline: Baby Yoshi Hill (room 0x126)

Script: map 5 node `0x178,0x128`, enter the level, walk right, then stop.

| Scene | Mode | Level | Player | WRAM different bytes | RGB5 different pixels |
| --- | --- | --- | --- | ---: | ---: |
| title | `07` | `0C7` | `80,320` | 4 | 0 |
| files | `08` | `0C7` | `80,320` | 4 | 0 |
| intro | `14` | `0C5` | `128,352` | 12 | 0 |
| entry240 | `14` | `126` | `80,320` | 43 | 0 |
| play1 | `14` | `126` | `258,320` | 40 | 274 |
| play2 | `14` | `126` | `258,320` | 42 | 0 |

The entry state matches: same mode, level and player position. The small WRAM
differences are consistent with counters and host bookkeeping. The play1
framebuffer difference is one transient animation frame.

Captures: `local/captures/parity-baby-yoshi-reference` and
`local/captures/parity-baby-yoshi-native`.

## Known issue in this room

The user reports that a baby Yoshi does not grow after it eats a flower or a
feather. This is recorded in `docs/demo11-open-issues.md` and deferred. The
likely cause is a Demo 1-1 override of the growth code.

## Next steps

1. Collect specific collision and custom sprite symptoms from the user: level,
   position, sprite and expected behavior.
2. Extend the parity scripts to the reported scenario. Add interaction steps
   (jump, stomp, carry, touch) and compare the WRAM sprite table and the
   collision outcome.
3. Locate the sprite data pointer table for this ROM. Level data tables are at
   `05:E000` (layer 1) and `05:E600` (layer 2). The sprite table is still
   unidentified.
4. For each repaired behavior, add a bounded qualifier script and keep the
   reference and native captures as evidence.

## Limits

- A matching entry state does not prove matching gameplay.
- Collision claims need a scripted interaction with a clear end state.
- The harness does not claim cycle accuracy.
