# World 1 overworld route repair: handoff

Date 2026-10-24. Status: **planned, not started**. Written for another agent to execute.
The accepted Demo 1-1 line plays all three World 1 courses individually, but the
overworld route onwards from 1-1 is missing in the source build. Repair it as a reviewed
restoration, then re-run acceptance.

## Current accepted state (do not disturb)

| Item | Value |
| --- | --- |
| Head target | `demo11-sprite0b` |
| Head ROM SHA-256 | `584117d2755465d2ad2ac644c0f10a59f3412b25eafd946ffc7178cfb17eabfe` |
| Head native binary | `BrutalMarioDemo11Sprite0BSNESRecomp`, SHA-256 `a8b794e3b0e7baa1384ad0cd9c632074978f1525d32ecb828fa5533f783889e6` |
| Chain | `demo11-base` -> `demo11-room106` -> `demo11-room010-gfx` -> `demo11-room010-music` -> `demo11-room138-audio` -> `demo11-room0cb-gfx` -> `demo11-sprite8d` -> `demo11-sprite0b` |
| Acceptance | `python3 tools/check_demo11_line.py` -> **11/11** |
| User playtest | 1-1, 1-2 (full natural clear) and room 138 all reported fine on 2026-10-24 |
| Rollback | `docs/rollback.md` plus `local/backups/pre-room105-migration-20261023-051544` |

Freeze this head. Any map repair must be a **new descendant target**; never edit the
accepted ones.

## The problem

After clearing 1-1 the overworld does not allow progress:

- the clear itself works (`$1493` runs the tape animation, the game returns to the map,
  `$1ECB = 0x8A`, `$13CE = 0x01` on both hosts);
- back on the map at `$1F17 = 0x0048`, `$1F19 = 0x0198`, pressing Right/Left/Up/Down for
  60 frames changes neither coordinate - the map player does not move at all;
- pressing A re-enters 1-1, so input and state are fine: the **node has no outgoing
  path**.

The user confirmed this also happens in the **original Demo 1-1 ROM**, so it is
unfinished source content rather than a restoration regression.

## Evidence already collected

| Path | What it shows |
| --- | --- |
| `local/captures/d11-mapdiag` | after clear: map position frozen at `(0x48,0x198)` for every direction; A re-enters 1-1 |
| `local/captures/d11-mapmove` | same, with the practical detail that A on the map enters the course |
| `local/captures/d11s0b-11-goal-ref` / `-native` | the clear path: `$1493 = 0xC9`, map mode `0x0E`, `$1ECB = 0x8A`, `$13CE = 0x01`, identical on both hosts |
| `local/captures/only1-11-goal` | demoOnly1 line's post-clear map (has visible dotted paths) for comparison |
| `local/frames/map-demo11-after-clear.png` | demo11 map after 1-1 clear: no dotted path near the node |
| `local/frames/map-only1-after-clear.png` | demoOnly1 map after its 1-1 clear: dotted path present |

Useful WRAM: map position `$1F17`/`$1F19`, submap `$1F11`, map state `$1ECB`, map
events `$13CE`, level room `$10B`.

## Hypotheses to test, in order

1. **Missing path data.** The map's path tiles/objects around the 1-1 node are absent.
2. **Wrong event gate.** Path tiles exist but are revealed by a different event bit
   than `0x8A` (the map is a different version from demoOnly1's).
3. **Node/entrance mismatch.** The launcher teleports to demoOnly1-derived coordinates;
   if Demo 1-1's own 1-1 node sits elsewhere, the level's exit data and the map's
   connection do not line up.
4. **Unfinished demo.** The map beyond 1-1 was never finished; in that case repair
   means authoring the missing links to match the demo's own node layout.

## Suggested first steps

1. Re-read `AGENTS.md`, `docs/demo11-rebase-plan.md`, `docs/demo11-playtest.md` and
   `docs/content-restoration.md` (the Demo 1-1 rebase section).
2. Reproduce: `python3 tools/m1.py reference --target demo11-sprite0b --script
   recomp/inputs/demo11-world1-1-goal.script --capture <fresh-name>`, then inspect
   `$1F17/$1F19` in the `on_map` sample.
3. **Map connectivity survey.** Write a probe that pokes a map position and loader
   (`poke 1f11/1f17/1f1f/0100 0b`, exactly as the existing fixtures do), then presses
   each direction for 60 frames and dumps `$1F17/$1F19`. Wherever the coordinates
   change, a path exists. This maps the usable overworld graph without decoding data,
   and shows exactly which node links are missing around World 1.
4. **Locate the map data.** The overworld is room `0x0C7`; its L1/L2 streams are
   5,708/… bytes in Demo 1-1 versus 5,687/… in demoOnly1
   (`local/reports/demo11-additions-inventory.json`). Compare those streams and the
   surrounding structures. The hack relocates data, so follow pointers through the
   level tables at `$05E000`/`$05E600` (3-byte entries) rather than assuming vanilla
   addresses.
5. Decode enough of the map format to identify the node objects and path segments
   around `(0x48,0x198)`. Cross-check by writing a tile and seeing it appear in a
   reference capture.
6. **Repair recipe.** Add a descendant target (for example `demo11-world1-route`) with
   a reviewed `config/restorations/<id>.json`. Reuse the existing primitives in
   `tools/restore_star_world_1.py`: `raw_blocks` for pinned blobs with a RATS header,
   `code_patches` for equal-width byte edits, `level_data` for level streams with
   pointer patches. Free space must be zero-filled and inside one bank; pin every
   `before` byte; keep allocations small and record them in the recipe.
7. **Verify.** Walk naturally from the 1-1 node to the next World 1 course node, enter
   it, and confirm the room id in WRAM. Do it on reference and native, with dumps and
   a receipted route (`recomp/inputs/...`). Then re-run
   `tools/check_demo11_line.py` and add a new check for the repaired route.
8. Ask the user for a short playtest at the end. Only their playthrough accepts it.

## Constraints

- Follow `AGENTS.md`: no subagents, commit and push verified checkpoints, never
  overwrite receipts, label fixtures, never write completion flags, neutral docs.
- Do not modify accepted targets or their recipes; append descendants only.
- Preserve user saves and running game processes; use fresh capture directories.
- Numeric ids are version-local. Do not infer a node or level id from the other
  build - entering the course and reading `$10B` is the only reliable check.
- Keep the current 11/11 green. Add checks, do not weaken existing ones.

## Things not to chase

- The scripted room 010 pipe route fails on this base, but a **natural playthrough
  clears 1-2** (user-confirmed 2026-10-24). Treat the scripted failure as a fixture
  limitation, not a defect.
- The gap around `x=0xDE` at the start of 1-1 is the newer design, not a regression.
- Scripted 1-1 goal detection needs the far-right end platform; that route is already
  tracked as `recomp/inputs/demo11-world1-1-goal.script`.

## Key paths

| Purpose | Path |
| --- | --- |
| ROM inputs | `local/content-versions/<id>/rom.sfc`, pins in `config/content-versions.json` |
| Recipe outputs | `local/restoration/<target>/rom.sfc` |
| Recipes | `config/restorations/<id>.json` |
| Targets and binary names | `tools/restoration_targets.py` |
| Build/run stages | `tools/m1.py` (`check`, `scaffold`, `generate`, `build`, `reference`, `native`) |
| Recipe runtime | `tools/restore_star_world_1.py` (`make_candidate`, `prepare`, `verify`, `lorom`) |
| Launcher | `tools/play_demo_only1.py --restoration demo11-sprite0b --level demo11-world1-1` |
| Acceptance | `tools/check_demo11_line.py` with `qualify_demo11_*.py`, `audit_demo11_*.py` |
| Reports | `local/reports/*.json` |
| Captures | `local/captures/<name>/` with `receipt.json`, `run.log`, `*.wram.bin`, `*.fb.bgrp` |

## Definition of done

1. Natural overworld walking from the 1-1 node to the next World 1 course node works and
   the course can be entered, on reference and native, with a receipted route.
2. A reviewed descendant recipe records the change with pinned bytes and small
   allocations; the whole-line byte audit still reports zero unexpected bytes.
3. `tools/check_demo11_line.py` reports 12/12 with the new route check.
4. The user playtests the natural progression and accepts it.
