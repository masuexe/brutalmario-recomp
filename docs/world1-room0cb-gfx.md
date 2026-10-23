# World 1 room 0CB extended graphics recovery

Date 2026-10-23. Room `$0CB` is a two-screen room with only four placed sprites
(`$35` roto_disc, `$19` bonus, `$45` number, `$CF`), which looks like a bonus or
minigame room. Its actual entry is still unknown; the earlier note that an exit
record points at it could not be reproduced, so this target only installs the
missing resource.

## Cause

Rooms `000`, `0CB`, `100` and `116` select extended graphics **`$12A`**. The
recipient's pointer slot for that id is `FFFFFF` (empty) while cheap_demo points
at `$28DAEF`, a 661-byte stream that decompresses to 4096 bytes. Any of those
rooms would render with missing graphics.

## Change

A descendant target `world1-room0cb-gfx` builds on `world1-room138-sprite`:

| Item | Value |
| --- | --- |
| Graphics id | `$12A` (shared: same id and same room set) |
| Donor pointer | `$28DAEF` |
| Compressed / decoded | 661 / 4096 bytes |
| Relocated to | file `0x188000` (bank `$31`), protected RATS block |
| Rooms inheriting it | `000`, `0CB`, `100`, `116` |

No selector is patched because the id already matches; only the pointer slot is
written. 503 differing bytes, all inside the allocation and the three pointer
bytes.

## Identity

- Recipe `config/restorations/world1-room0cb-gfx.json`.
- Base `world1-room138-sprite`
  `fe8ff01841960d911dd15415193b3cb7197032504be1855b5741a59dc9fd2890`.
- Candidate `e66b05983af43412b87eb248b675645cf3baeb42e12875255d5ac1353dc0bb84`.
- Binary `local/build/world1-room0cb-gfx/BrutalMarioWorld1Room0CbGraphicsSNESRecomp`.
- No entrance is known for room `$0CB`, so the practice launch uses the room138
  node of the same build:
  `python3 tools/play_demo_only1.py --restoration world1-room0cb-gfx --level world1-room138-sprite --show-location`.

## Verification

`python3 tools/qualify_world1_room0cb_gfx.py` passes. Report
`local/reports/world1-room0cb-gfx-qualification.json`. It checks the identities,
that the recipient slot was empty, the shared room dependency set, the donor
stream and its decompression, the installed pointer and protected payload, that
only the allocation and pointer changed, and that a room138 entry capture on both
hosts still matches the donor terrain.

## Limits

- Room `$0CB` cannot be entered yet, so its **appearance is not verified**; only
  the resource install is.
- Rooms `000`, `100` and `116` inherit the same graphics without separate entry
  checks.
- The hidden room's purpose, and whether any exit really targets it, remain open.
- Audible output is not claimed; room106 music stays deferred.

## Visual check via a diagnostic pipe (2026-10-23)

Room `$0CB` has no known entrance, so it was reached with a **diagnostic fixture**,
not a gameplay route and not part of any recipe: on a throwaway copy of the
candidate, the first room010 pipe destination byte (room 010 layer1, file
`0x3246C4`) was changed `$4A -> $CB`, and the tracked two-pipe route then lands in
room `$0CB` in mode `$14`.

What the room is: an outdoor sky area with a flat gold-coin ground, a green pipe
on the left, and a **message box that reads a debug greeting (`hi cSUB EIP`)**.
Together with its two screens and four sprites this looks like a leftover
**developer test room**, not a normal bonus room and not obviously a secret-exit
destination. No exit from it was observed.

The graphics recovery is visible in an A/B render of the same fixture:

| Build | Framebuffer | Visible difference |
| --- | --- | --- |
| with `$12A` restored | 8,681 bytes differ from the negative | red `20` counter drawn above Mario |
| without `$12A` (base) | reference | the counter area is blank |

So `$12A` carries the drawn-number tiles used by the room's `$45` number sprite;
without it that element disappears. Screenshots and dumps stay local under
`local/captures/w1-cb-view` and `local/captures/w1-cb-nofix`.

### Consequence for the secret-exit question

A debug/test room is unlikely to be the target of a real secret exit. The earlier
note that an exit record points at `$0CB` remains unreproduced, and this visual
check does not support treating `$0CB` as a missing secret area. Do not invest in
reaching it through gameplay until an exit is actually identified.
