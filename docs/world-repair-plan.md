# World-by-world repair plan

Date: 2026-10-26. The user asked to repair terrain collision and custom sprite
problems world by world so the work stays ordered.

## World order

World 1 Grassland, World 2 Forest, World 3 Bay, World 4 Cave, World 5 Plateau,
World 6 Sky, World 7 Snowfield, World 8 Bowser's Valley, then Star World.
`config/world-map.json` holds the room lists, from the walkthrough reference.

## Detection methods

| Reported symptom | Detection |
| --- | --- |
| Missing textures, vertical lines or a blank screen | Reference and native framebuffer comparison on matched scene samples |
| Terrain collision fails at the start | Reference and native player state comparison |
| Custom sprite code missing or a strange object falls | Sprite status and number array comparison; record table audit with donor records |
| Missing music or a load stall | Covered by the full-range course survey |

Tools:

- `tools/world_audit.py --world worldN`: static gaps for a world. The sprite
  record part is a heuristic and needs calibration.
- `tools/world_parity.py --world worldN`: reference and native captures per
  room, then a comparison of mode, level, player state, sprite arrays, WRAM,
  framebuffer and the color delta histogram.
- `tools/frame_phase.py --translevel TAG`: dense-frame check for phase or
  rendering differences.

## Triage result

62 rooms with a level entry were triaged. 19 rooms diverge in at least one
sampled scene. Reports: `local/reports/world-parity-*.json`.

## Refined classification

A second dense-frame pass shows that many sampled divergences are timing or
periodic-effect phase differences, not wrong content.

| Room | Translevel | Verdict |
| --- | --- | --- |
| World 2 `125` | `049` | phase: dense frames match the reference at an offset; the entry-600 scene is identical (0 different pixels) |
| World 1 `014` | `014` | intermittent; differences stay in the top scanlines and the HUD rows |
| World 5 `10D` | `031` | intermittent; 13 of 16 frames match at the same index |
| World 2 `123` | `047` | intermittent; 10 of 16 frames match |
| Star `001` | `001` | intermittent; player state only |
| World 5 `10E` | `032` | intermittent; 8 of 16 frames match |
| World 4 `015` | `015` | intermittent; 8 of 16 frames match |
| World 4 `127` | `04B` | 3 of 16 frames match; needs more work |
| World 5 `016` | `016` | 3 of 16 frames match; needs more work |
| Star `004` | `004` | persistent difference; best residual 768 pixels |
| Star `009` | `009` | persistent difference; best residual 201 pixels |
| Star `007` | `007` | persistent difference; best residual 3195 pixels |
| World 5 `10F` | `033` | persistent difference; best residual 16312 pixels |
| World 1 `120` | `044` | persistent difference; best residual 1842 pixels, best at offset -3 |

## Room 125 deep look

The first sample showed a dramatic difference: the native host drew a dark field
with a lit circle around Mario, and the reference host drew the full scene. A
dense capture shows both hosts render the same dark-circle effect. At the
sampled entry-600 frame the framebuffers are identical (zero different pixels).

Register traces explain the effect: the level enables HDMA channels 3, 4 and 5
with window registers `$2126`, `$2127` and `$2123` as destinations. The native
host applies the per-scanline window mask; the reference sample was taken a few
frames before the effect's first activation. This is a timing-phase difference,
not a missing-content defect.

## Next steps

1. Investigate the persistent candidates in world order: World 1 room `120`,
   then World 5 room `10F`, then Star rooms `004`, `007` and `009`.
2. For each candidate, compare CGRAM and the PPU write journal with the
   diagnostic snes9x core (`local/diagnostics/snes9x-debug`).
3. Fix the true divergences and add a bounded qualifier each.
4. Calibrate the sprite-record heuristic against the known 8D and 0B ports.

## Limits

- The triage compares matched scene samples only.
- A parity sample does not prove normal gameplay.
- Content that is equally wrong on both hosts is not detectable this way.
