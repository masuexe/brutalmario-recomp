# World 1 room138 custom sprite recovery

Date 2026-10-23. The user playtested the `world1-room138-audio` candidate and
reported that the course itself works but its custom sprite is not loaded, so a
strange object falls at the start of the level.

## Cause

Room `$138` places one custom sprite, id **`$0B`**. The recipient's 16-byte
sprite record slot for that id is the empty default
`0000ffffffffffff218001218001ffff`, while cheap_demo holds
`013601063b139964a8d310b3d3100000` pointing into its own code block. Without a
record the sprite never initialises: in a settled sample its status byte stays
`00` where the donor has `08`, and the spawned object falls as garbage.

## Change

A new descendant target `world1-room138-sprite` builds on
`world1-room138-audio`:

| Item | Value |
| --- | --- |
| Sprite id | `$0B` |
| Rooms depending on it | `0F`, `82`, `9A`, `138` |
| Donor block | `$10:D377`, 781 bytes, RATS header verified |
| Relocated to | `$3F:D377` (same bank-local offset, bank < `$40`) |
| Donor record | `$10:B20D` |
| Recipient slot | `$10:B13A` |

Only the sprite code block (781 bytes), its 16-byte record and the two record
bank bytes change: 773 differing bytes in total, all inside those regions.

## Identity

- Recipe `config/restorations/world1-room138-sprite.json`.
- Base `world1-room138-audio`
  `9cdd46b38ae238e83e6e3dad9e9440a4f85cc1db2e5b24678caed44fe285a000`.
- Candidate `fe8ff01841960d911dd15415193b3cb7197032504be1855b5741a59dc9fd2890`.
- Binary `local/build/world1-room138-sprite/BrutalMarioWorld1Room138SpriteSNESRecomp`.
- Launch `python3 tools/play_demo_only1.py --restoration world1-room138-sprite --show-location`.

## Verification

`python3 tools/qualify_world1_room138_sprite.py` passes. Report
`local/reports/world1-room138-sprite-qualification.json`. It checks the
identities, the sprite room dependencies, the donor RATS block, the relocated
block, the record with only its bank bytes rewritten, and that every changed
byte is inside the two reviewed regions. Captures
`world1-138-sprite-qualified-{reference,native}` show that in a settled room138
sample the sprite status array (`$14C8..$14D4`) and sprite numbers
(`$161A..$1626`) match the donor, as does the terrain on both hosts.

## Limits

- Entry and movement scope only. The flow, clear, natural-route and death
  captures remain pinned to the `world1-room138-audio` leaf and have not been
  re-run on this candidate.
- The sprite's in-level behaviour beyond initialisation is not individually
  audited; the user's playtest is the deciding check for how it looks.
- Audible output is not claimed, and room106's music stays deferred.
