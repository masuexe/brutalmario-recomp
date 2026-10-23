# World 1-1 layout migration: first attempt (blocked)

Date 2026-10-23. Attempted content migration of Demo 1-1's newer World 1-1 into the
demoOnly1 queue, per the user's explicit confirmation. **This attempt failed and is
not accepted.**

## What was migrated

Target `demo11-room105` on `demo11-extra-graphics` (which already carries the four
Demo 1-1 extended graphics):

| Item | Demo 1-1 source | Result |
| --- | --- | --- |
| Room `105` layer1 | pointer `46B5CC`, 7,102 bytes | relocated to `$37:B008` |
| Room `105` sprite list | pointer `46D4D2`, 134 bytes | relocated to `$37:CBCE` |
| Room `105` graphics record | `14AD08 + 105*32` | 32 bytes patched |
| Pointers | layer1 slot, sprite low word, sprite bank byte | patched |

Candidate ROM `a45225b136606ca3a9e33d361d5496490b1fb41c022cadb46e06034887414dd2`, 6,019
changed bytes. Native build produced.

## Failure

Entering the course on the migrated build:

| Host | mode | x | music |
| --- | --- | ---: | ---: |
| Demo 1-1 reference | `0x14` | `0x40` | `0x30` |
| migrated reference | `0x14` then `0x0D`/`0x0E` | `0x10` | `0xFF` |
| migrated native | same as migrated reference | `0x10` | `0xFF` |

The player spawns at a different position and the level immediately leaves gameplay,
so the layout, sprite and graphics data are **not sufficient**. Comparing settled
states shows 6,112 differing Map16 bytes in the low buffer and eleven differing
sprite numbers, consistent with a different spawn point rather than a rendering
slip.

## Diagnosis so far

Level header data for the room was not migrated. Probes locate:

- Demo 1-1 room `105` header at `$46:D183`, bytes `40 60 31 40 80 05` (music byte
  `0x31` -> id `0x30`, matching the runtime cue).
- Current head room `105` header at `$39:C2C4`, bytes `40 60 31` followed by `FF`
  and the neighbouring `STAR` RATS header - i.e. the recipient record is only three
  meaningful bytes where Demo 1-1 has six.

Both records share `40 60 31`, so the header's byte0/byte1 start-position fields look
identical, yet the spawn differs. The remaining candidates are the entrance/map-node
start data and the header's `40 80 05` tail (graphics/tileset and sprite-memory
selection), neither of which this attempt migrated.

## Status

- Not accepted, not the head. The accepted head remains `demo11-extra-graphics`
  (`b8da320e`), and `docs/rollback.md` documents how to restore it.
- The failed candidate stays as reproducible evidence; do not promote it.
- Next: identify how the recipient stores the six-byte header and the entrance start
  position for room `105`, migrate those too, then re-run this comparison.

## Second attempt: header tables found and migrated (2026-10-23)

The first attempt failed because only the level's data streams were migrated. The
real level header lives in the vanilla tables indexed by level number, at
`$05:F000 + level`, `$05:F200 + level`, `$05:F400 + level` and friends. For room
`105` three bytes differ between the builds:

| Table | Current head | Demo 1-1 |
| --- | --- | --- |
| `$05:F000 + 105` | `5B` | `56` |
| `$05:F200 + 105` | `00` | `04` |
| `$05:F400 + 105` | `7A` | `9A` |

Those three one-byte patches were added to `demo11-room105` alongside the layer1,
sprite and graphics-record migration. New candidate
`081489e5cd7f8cd43c78bf15635373ed90e305ab1f4b89cd464f1fc1e5bb7c5c`.

### Result: terrain now matches exactly, spawn still differs

| Check | Reference | Native |
| --- | --- | --- |
| stays in gameplay (mode `0x14`) | yes | yes |
| music cue | `0x30` (same as Demo 1-1) | `0x30` |
| both Map16 buffers vs Demo 1-1 | **0 differing bytes of 8,640 each** | **same** |
| sprite status/number differences | 1 byte each (`$14D0`, `$1622`) | same |
| player spawn | `(0x10, 0x00C0)` | Demo 1-1: `(0x40, 0x0160)` |

So the newer layout, graphics and music are genuinely in place - the level renders
byte-identically to Demo 1-1 - but the player still spawns at a different point and
drops instead of standing on the ground.

### Remaining suspect: the map entrance, not the level

The header byte fields that select the start position (`$F000` low nibble for Y,
`$F200` low bits for X, per the level-loader code) are now identical to Demo 1-1,
yet the spawn differs. That points at the **map-node entrance data**, which this
target does not migrate: the recipient map for World 1 may store a different start
entrance or screen for its 1-1 node than Demo 1-1 does.

Next: compare the entrance data the two builds use for the 1-1 node (and how the
loaded level start screen is chosen) before deciding whether the entrance must be
migrated too. Until then this candidate is **not accepted**: the player does not
start where the course expects.
