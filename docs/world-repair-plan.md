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
- `tools/world_parity.py --world worldN`: reference and native captures for
  every room in the world, then a comparison of mode, level, player state,
  sprite arrays, WRAM, framebuffer and the color delta histogram.
- `tools/frame_phase.py --translevel TAG`: dense-frame check for phase or
  leftover rendering differences.

## Full triage result (first pass)

62 rooms with a level entry were triaged. 19 rooms diverge.

| World | Room | Translevel | Result | Large-delta pixels |
| --- | --- | --- | --- | ---: |
| World 1 | `120` | `044` | framebuffer | 3697 |
| World 1 | `014` | `014` | framebuffer, top 5 scanlines only | 1240 |
| World 2 | `123` | `047` | player state only | 0 |
| World 2 | `125` | `049` | framebuffer, native shows a dark spotlight and the reference a full scene | 28684 |
| World 4 | `127` | `04B` | framebuffer | 19323 |
| World 4 | `015` | `015` | framebuffer | 540 |
| World 5 | `016` | `016` | framebuffer | 905 |
| World 5 | `10D` | `031` | player and framebuffer | 19028 |
| World 5 | `10E` | `032` | player and framebuffer | 1110 |
| World 5 | `10F` | `033` | framebuffer | 2644 |
| World 6 | `006` | `006` | framebuffer | 574 |
| World 7 | `01C` | `01C` | framebuffer, mostly mid deltas | 4418 |
| World 7 | `12F` | `053` | framebuffer | 23183 |
| World 8 | `018` | `018` | framebuffer | 2851 |
| Star | `001` | `001` | player state only | 0 |
| Star | `004` | `004` | framebuffer | 2374 |
| Star | `006` | `006` | framebuffer | 574 |
| Star | `007` | `007` | framebuffer, mostly mid deltas | 2368 |
| Star | `009` | `009` | framebuffer, large deltas | 4494 |

Reports: `local/reports/world-parity-*.json`. Captures:
`local/captures/world-<world>-<translevel>-{reference,native}`.

## First interpretations

- World 2 room `125` is the clearest case. The native host draws a dark field
  with a lit circle around Mario. The reference host draws the full scene. The
  tile data is nearly identical (470 VRAM bytes differ), so the difference is a
  screen effect, not missing tiles. The intended look needs a user decision.
- World 1 room `014` differs only in the top five scanlines. That is an
  overscan rendering detail, not gameplay.
- World 5 rooms `10D` and `10E` also differ in the player position. A frame
  phase check must separate a timing offset from a collision difference.
- Star room `001` and World 2 room `123` differ only in the player state.
  These are likely timing offsets and need the same phase check.
- Rooms with mostly mid-range color deltas (`01C`, `007`) are probably a
  color-math or palette rounding difference, not a geometry error.

## Next steps

1. Decide the intended look of World 2 room `125` with the user.
2. Run `tools/frame_phase.py` for the player-state rooms and classify them.
3. Fix the true divergences in world order and add a bounded qualifier each.
4. Calibrate the sprite-record heuristic against the known 8D and 0B ports.

## Limits

- The triage compares matched scene samples only.
- A parity sample does not prove normal gameplay.
- Content that is equally wrong on both hosts is not detectable this way.
