# World 2 route inventory

Date: 2026-10-29. Baseline: `demo11-native-product-r13` (r12 without `C2`).
ROM SHA-256 `c02dc11e0c79c804740b38797463a1fc9645a8a05cdb4e18c7c09fff45760681`.

## Result

**Superseded course catalog:** [The Forest identity checkpoint](forest-course-identity.md)
now establishes the actual ten Forest nodes and corrects `config/world-map.json`.
The earlier table below remains a historical list of parsed rooms. Its course
labels must not be used for route design. Its seven checked room transitions
remain valid.

This note records parsed exits for rooms assigned to World 2 by the local
catalog. Course names and world assignments are provisional until matched to
the recipient content. This note does not qualify a complete route.

`config/world-map.json` lists nine World 2 rooms: `00F`, `124`, `121`,
`122`, `123`, `125`, `126`, `06F` and `00D`.

| Room | Translevel | Course | Length, screens | Goal tape `7B` | Key `15` | Screen exits (screen to level) |
| --- | --- | --- | ---: | --- | --- | --- |
| `00F` | `00F` | Fishing Spree, secret exit | 20 | `4576,240` | none | none |
| `124` | `048` | World of Water, hidden map | 15 | none | none | `11` to `29`, `13` to `30`, `3` to `27`, `2` to `27` |
| `121` | `045` | Thou Shalt Not Cross This Bridge | 5 | none | none | `4` to `D7` |
| `122` | `046` | A Remote Shack | 16 | `3808,144` | `400,272` | none |
| `123` | `047` | It's Moldy Within The Hollow | 5 | none | none | `4` to `42`, `0` to `23` |
| `125` | `049` | Ghost Forest, secret exit | 20 | `4768,144` | `880,176` | none |
| `126` | `04A` | Mario the Pyromaniac, secret exit | 3 | `544,176` | none | none |
| `06F` | `06F` | Morton boss | 1 | none | none | `0` to `87` |
| `00D` | `00D` | Aneha Estate, scrapped map | 2 | none | none | `3` to `66`, `1` to `62`, `2` to `64` |

The goal entry is the sprite X and Y in level pixels. The exit entry is the
screen number and the destination level byte.

## Method

`local/probes/level-parse4.py` and `local/probes/sprite-parse.py` give the
format. The pointers are the Layer 1 table at `$05E000` and the sprite table
at `$05EC00` with the bank byte at `$0EF100`. The parse reads the test ROM
at `local/restoration/demo11-native-product-r13/rom.sfc`.

The screen exit uses extended object `00` and four bytes. The fourth byte is
the destination low byte. The flag byte carries the destination high bit. The parse checks one known case: room `48` exits to level
`51` at screen `1`, which matches the accepted Star World side-exit check.

## Historical probe blockers (superseded where noted below)

1. A position poke does not start the goal tape in room `126`. The tape is at
   `544,176`. Pokes at `512..576` in X and `128..320` in Y never set
   `$1493`. The player lands on a ledge near `149` at that X, and on the
   floor near `320` below it. The Star World goal route instead follows a
   screen exit into the goal room `48` and touches the tape there. Room `126`
   has no screen exit. A real traversal is the next test.
2. The exit flag bits in byte 1 are not decoded. The destination byte is
   reliable for room `48`. Secondary exits and water flags need a check
   against a known case before a route uses a destination.

## First fixture probe

The Star World side-exit fixture sets the player action byte `$71=6` and a
position. I ran it on translevels `045` (room `121`) and `048` (room `124`).

| Level entry | Result |
| --- | --- |
| Translevel `045`, room `121` | Mode `14`, room `100` |
| Translevel `048`, room `124` | Mode `14`, room `100` |

Both runs reached room `100`. The historical record calls room `100` a boss room, and
neither destination matches the parsed exit. The fixture therefore is not a
valid World 2 exit test in this form.

The corrected checks below supersede this failed fixture. Screen 07 was wrong.

## Checked exit boundaries (2026-10-29)

Seven fresh native captures on r13 qualify these **assisted screen-exit
boundaries**, with four lives retained and no `BRK`:

| Entry room | Screen | Live low byte / flags | Destination |
| --- | --- | --- | --- |
| `121` | `04` | `D7 / 05` | `1D7` |
| `124` | `02` | `27 / 04` | `027` |
| `124` | `03` | `27 / 04` | `027` |
| `124` | `0B` | `29 / 04` | `029` |
| `124` | `0D` | `30 / 04` | `030` |
| `123` | `00` | `23 / 05` | `123` (reload) |
| `123` | `04` | `42 / 04` | `042` |

The earlier probes placed Mario at X `0700` in rooms `121` and `124`.
Neither room has an exit on screen `07`. Their room `100` result does not
establish an exit defect. Selecting the actual exit screen settles the probe.
Each corrected case increments `$141A` once, including the room `123` reload.
The first destination sample for `124 -> 027` is mode `13`. The later sample
reaches mode `14`. Every other destination sample is already mode `14`.

The recipient routine at `$05:DC50..DC6E` checks flag bit 2 for an explicit
exit. It stores bit 1 in `$1B93` (secondary selection) and stores bit 3 shifted
left three in `$192A`. It returns bit 0 as the destination high bit. Thus `D7/05`
names primary room `1D7`, not `0D7`. The qualifier pins those instruction bytes.
All seven cases are primary exits. Secondary and water behavior remain open.

The fresh Star control follows `005 -> 048 -> 051` and reaches the overworld
with four lives. Scripts label map-node, position and pipe-action fixtures.
They never write exit destinations, completion, events or saves. The checks do
not qualify walking to a pipe, real pipe activation, a course clear or saves.

Evidence:

- Scripts: `recomp/inputs/world2-room{121,123,124}-screen*.script` and
  `recomp/inputs/world2-star-exit-control.script`.
- Captures: `local/captures/w2-r13-*-v1` and `w2-star-control-v1`.
- Checker: `python3 tools/qualify_world2_exit_boundaries.py`.
- Report: `local/reports/world2-exit-boundaries-final-v1.json`. This pins ROM,
  binary, build receipt, source and executed scripts, full WRAM sizes, hashes
  and sample frames. Re-runs require a fresh `--output` path.

### Course identity limitation

The community [map directory](https://wikiwiki.jp/kitikumario/マップ攻略),
consulted on 2026-10-29, uses different IDs for the named Forest courses.
Fresh native screenshot `w2-126-walk/cross.fb.bgrx` shows baby Yoshis, and
`w2-r13-121-04-v1/active.fb.bgrx` shows switch-palace graphics. These contradict
the fire and bridge labels directly, independently of historical wiki IDs.
Its base listing calls `126` the baby-Yoshi course, `122` Storm Lake and `00D`
Thunder Valley. Its Cheap Demo section records more changes. Fandom's directory
and the attempted course pages were inaccessible. The earlier table's course
names are local catalog labels, not verified recipient identities. Before
writing a gimmick-specific route, match actual room chains, sprites and visual
content to an official donor and the appropriate walkthrough. A failed tape
probe in `126` cannot yet establish a defect in the named fire course.

A room `122` route entry starts at `(16,336)` with four lives. Simple right
and A cycles reach room `005` with three lives at sample `q15`. The route needs
a different jump path. Room `121` starts at `(272,352)`. Simple right and A
cycles stop at `(338,352)` and do not reach the screen 4 exit. Room `123`
starts at `(112,352)`. Simple right and A cycles stop at `(226,352)`.

The qualifier passes all seven boundaries plus the Star control. A later rerun
on the current tree also passes (`local/reports/world2-exit-regress-v1.json`).
The existing unit suite passes **344/344**. The log:
`local/reports/unit-tests-exit-boundaries-v1.log`. No game code, ROM or resource
pack changed in this checkpoint. Final report SHA-256:
`e7c5884805dd5f5978b2da2199feb88d150d87ebfd8ff666946f13e3b1830a52`.
The reused room126 screenshot receipt pins the same r13 ROM and native binary
as the new boundary captures. Its source script SHA-256 is
`3371dc0a56b317763b5c825339d1240777afa60f8d2ee1708015b10e69416bc6`.
Its framebuffer SHA-256 is
`82adf6fc34f7eec6e8213f1467e07b60e3a43f6344479fa67b49965f76344322`.

## Next actions

1. Resolve version-specific course identities in `config/world-map.json` and
   the walkthrough cross-reference before calling this a World 2 route suite.
2. Follow verified destination rooms and locate their actual clear mechanics.
3. For rooms with a goal tape, build a tracked route script that climbs to the
   tape. Do not replace the touch with a flag write.
4. Record each route on the native host first. Use the reference host only for
   a course whose data does not need an external pack.
5. Compare the saved flag and the File A reload after a normal clear.
