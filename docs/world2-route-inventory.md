# World 2 route inventory

Date: 2026-10-29. Baseline: `demo11-native-product-r13` (r12 without `C2`).
ROM SHA-256 `c02dc11e0c79c804740b38797463a1fc9645a8a05cdb4e18c7c09fff45760681`.

## Result

This note records the parsed exit data for the World 2 rooms. It does not
qualify a route. The parsed destinations are the first step of route work.

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

The screen exit uses extended object `00` and four bytes. The third byte is
the destination level. The parse checks one known case: room `48` exits to level
`51` at screen `1`, which matches the accepted Star World side-exit check.

## Known blockers

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

Both runs reached room `100`. The record calls room `100` a boss room, and
neither destination matches the parsed exit. The fixture therefore is not a
valid World 2 exit test in this form.

The next test needs a known exit and a checked destination. The accepted Star
World side-exit check is the control.

## Next actions

1. Enter each World 2 room and dump the first gameplay frame to check the
   room and the mode. The product survey already covers this.
2. For rooms with screen exits, follow the exit with the accepted Star World
   fixture and check that the destination room loads.
3. For rooms with a goal tape, build a tracked route script that climbs to the
   tape. Do not replace the touch with a flag write.
4. Record each route on the native host first. Use the reference host only for
   a course whose data does not need an external pack.
5. Compare the saved flag and the File A reload after a normal clear.
