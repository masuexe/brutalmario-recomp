# World 1 castle integration: investigation state

Date 2026-10-24. Status: **corrected and repaired; the castle's missing custom
sprite is restored. Course completion is out of scope: the user reports the
newer castle is most likely author-unfinished, so restoration - not
clearability - is the goal.**

Head under repair: `demo11-room106-music` (accepted 13/13 line). Head after
the repair: `demo11-castle-sprite06` (**14/14** line, see below).

## What the user reported

- The castle course (`10E`) contains a missing custom sprite the user has
  never seen (unknown identity).
- It is uncertain whether the boss door is reachable at all.
- Later context: the course is likely unfinished in the original; restore as
  much as possible, do not require a natural clear.

## Correction of the first survey (2026-10-24, second pass)

The first survey's central claim - "custom sprite `F0` is deployed once and
never appears in any runtime sprite table; its initialization fails silently"
- was a misreading. The second pass decoded the engine instead of trusting the
`sprite_rooms` helper's flag guess, and found:

- Sprite-list entries are three bytes `[cmd, xy, id]`. Decoded from the loader
  at `$02A82E` (cursor loop) and dispatcher `$3180A9`: `xy` high nibble = X
  bits 4-7, `xy` low nibble = X screen (bit 1 of `cmd` extends the screen
  nibble past `$0F`), `cmd` high nibble and low bits carry Y, and **`cmd` bit
  3 marks the entry custom**. `$7FAB10,X` receives `cmd & $0D`; a custom
  install then reads the 16-byte record at `$31:8272 + id*16`, whose byte 1
  overwrites the slot's sprite number. Searching runtime tables for the raw id
  after install therefore finds nothing - that produced the false "F0 never
  spawns" verdict.
- **`F0` works**: it spawns at level x `$360` (screen 3, column `$60`), the
  record at `$31:8272 + F0*16` is native Demo 1-1 data pointing into a valid
  590-byte `STAR` block at `$1AF045`, the slot's number becomes the record's
  byte 1 (`$2F`), and the sprite renders (a small yellow/orange creature on a
  checkered pillar, visible in `d11-castle-survey7` k09-k11). It lives until
  the camera leaves it behind.
- **The real gap was custom sprite `06`**. Entry 5 (`cmd=$49, xy=$B0`) places
  it at level x `$B0`, y `$140`, right after the opening pits. Demo 1-1's
  record slot for id `06` is the empty default, so the spawn reached the
  record-enable gate (`record byte 0 == 0`) and aborted silently - the exact
  slot-record-vs-behaviour gap pattern of the earlier `8D`/`0B` ports, just on
  a different id.
- Lineage evidence: room `$6E` places the identical custom-06 entry
  (`cmd=$98, xy=$C0`) in **every supplied version** (Demo 1-1, demoOnly1,
  cheap_demo, 7hero, demo6/7/8, mazo), so the id is a long-standing shared
  sprite. Only cheap_demo and demo8 actually implement it: both carry the same
  270-byte `STAR` block at `$10:A92F` and the same record at `$10:B1BD`
  (cheap_demo's table base `$10:B15D`). demoOnly1's slot is also empty - the
  gap predates the rebase.
- The far right end of the course (x `$10EA`) has a blue-framed door floating
  above the floor (`d11-castle-survey7/kend`); the survey never attempted to
  enter it. Given the unfinished-course context this stays an observation.

## Repair: `demo11-castle-sprite06`

New descendant of `demo11-room106-music`, recipe
`config/restorations/demo11-castle-sprite06.json`:

| Item | Value |
| --- | --- |
| Sprite id | `$06` (rooms `6E`, `10E` = 110, 270) |
| Donor block | `$10:A92F`, 270 bytes, RATS verified, sha256 `c100c8b5...` |
| Relocated to | `$34:A92F` (same bank-local offset; region verified free) |
| Donor record | `$10:B1BD` (`01360080360319003ea9104da9100000`) |
| Recipient slot | `$31:82D2` (was the default record) |
| Shared deps | `$27FAE4/256`, `$01801A/32`, `$01B7B3/256` - the same hashes the 8D port pinned |

277 bytes change, all inside the block and record regions (whole-line byte
audit re-run clean as part of the suite).

## Verification

`tools/qualify_demo11_castle_sprite06.py` passes; report
`local/reports/demo11-castle-sprite06.json`. On both hosts
(`d11c06-entry-{ref,native}`, entry into `10E` via the recorded map node,
camera at 0, four checkpoints): exactly one custom-06 slot, status `$08`,
`$7FAB10` bit 3 set, sprite number `$36` (the record's byte 1), at
`x=$00B0 y=$0140` - the decoded entry site. Sampled framebuffers show a new
small creature sprite standing there. `tools/check_demo11_line.py` reports
**14/14** with the new check included.

## Closing the two open observations (2026-10-24, third pass)

**The "end door" does not exist.** A pixel scan for the blue-framed door
across every castle framebuffer found nothing; the blue frames in
`d11-castle-end3` are the map UI after death. What exists:

- the playable course ends around `x=$16C1` (an invisible clamp: flight
  stops there; teleports deeper land Mario in a bottomless fall);
- the tile structure at world `x≈$1B40-$1B60` rows 9-13 (tiles
  `877/878/87C/87D/838/84C`) is beyond that clamp and is **non-solid
  backdrop** - Mario falls through at every height;
- the earlier audit's "blue-framed door at `$10EA`" was a misread of a
  framebuffer (likely the death-map screen).

**The opening gap is original unfinished content, not a defect.** Real
jump attempts die identically in cheap_demo and this line: platform at
`x=$60/$61` -> fall at `x=$C4-$C7` (high route) or fall at `$9B` below the
checker blocks (low route). Donor and recipient behave byte-for-byte the
same, so there is nothing to restore - the author never finished the
crossing, consistent with the "restore as-is, completion not required"
directive.

Both observations are closed; no castle content remains actionable except
the Warp-Star fallback rooms documented elsewhere. All probes used labelled
fixtures; no goal, event or completion values were written. The accepted
head is unchanged.
