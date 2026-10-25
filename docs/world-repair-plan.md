# World-by-world repair plan

Date: 2026-10-26. The user asked to repair terrain collision and custom sprite
problems world by world so the work stays ordered. This note records the order,
the detection method and the current results.

## World order

The order is the walkthrough order in `docs/walkthrough-reference.md`:
World 1 Grassland, World 2 Forest, World 3 Bay, World 4 Cave, World 5 Plateau,
World 6 Sky, World 7 Snowfield, World 8 Bowser's Valley, then Star World.
`config/world-map.json` holds the room lists.

## Detection methods

| Reported symptom | Detection |
| --- | --- |
| Missing textures or a screen of vertical lines | Reference and native framebuffer comparison on matched scene samples |
| Terrain collision fails at the start | Reference and native player state comparison; both hosts falling means a content or layout gap |
| Custom sprite code missing or a strange object falls | Sprite status and number array comparison; record table audit with donor records |
| Missing music or a load stall | Already covered by the full-range course survey |

Tools:

- `tools/world_audit.py --world world1`: static gaps for a world (empty
  extended graphics slots, default sprite records that a donor defines, level
  entries that the index does not list). The sprite-record part is a heuristic
  and needs calibration before it drives repairs.
- `tools/world_parity.py --world world1`: captures each world room on the
  reference and native hosts, then compares mode, level, player state, sprite
  arrays, WRAM and framebuffer.

## World 1 result (first pass)

| Room | Translevel | Result |
| --- | --- | --- |
| `104` | `028` | parity |
| `105` | `029` | parity |
| `106` | `02A` | parity |
| `010` | `010` | parity |
| `120` | `044` | framebuffer difference (4760 pixels at entry) |
| `138` | `05C` | parity |
| `06E` | - | boss room, no level entry |
| `014` | `014` | framebuffer difference (1240 pixels at entry) |

The two framebuffer differences have equal game state and equal sprite arrays.
The difference pattern follows animated background details, so the first
hypothesis is animation phase, not missing textures. A dense-frame capture will
decide. Report: `local/reports/world-parity-world1.json`.

## Next steps

1. Add a dense-frame phase check to `tools/world_parity.py` and reclassify the
   World 1 differences.
2. Run the parity triage for World 2 to World 8 and Star World.
3. Fix the true divergences in world order. Add a bounded qualifier for each
   repair.
4. Calibrate the sprite-record heuristic against the known 8D and 0B ports.

## Limits

- The triage compares matched scene samples only.
- A parity sample does not prove normal gameplay.
- Content that is equally wrong on both hosts is not detectable this way; those
  cases need a donor comparison or a user report.
