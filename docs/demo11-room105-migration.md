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
