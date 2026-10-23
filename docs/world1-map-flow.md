# World 1 map flow after a real clear

Date 2026-10-23. Answers whether the rightward route to Yoshi's House being
closed after a real 1-1 clear is a restoration regression.

## Method

One script (`local/probes/w1-complete-only.script`, a truncation of the tracked
`world1-next-course-progression.script` before its room-010 assertions) plays the
first course to its real goal tape and stops on the map. It was run on the
original demoOnly1 ROM and on the current cumulative candidate.

## Result: the candidate matches the original

Both ROMs produce the identical post-clear map state:

| Field | Original demoOnly1 | Candidate |
| --- | --- | --- |
| mode | `0x0E` | `0x0E` |
| position | `(0x018,0x1B8)` | `(0x018,0x1B8)` |
| `$1ECB` | `0x8A` | `0x8A` |
| `$1F02` clear bits | `0x40` | `0x40` |
| `$13BF` | `0x29` | `0x29` |

Captures: `local/captures/w1-orig-complete2` (original) and
`local/captures/w1-cand-complete2` (candidate).

## Why movement to the House is blocked, and that this is original

With a `$1ECB = 0x8F` fixture and a fresh map transfer to `(0x048,0x198)`,
holding right walks to `(0x068,0x198)` and `(0x088,0x198)`, so the map cells and
movement code are intact. A real clear leaves `$1ECB = 0x8A`, whose direction
bits differ only by bits `0x05` from the fixture value.

Because the original demoOnly1 leaves exactly the same byte and the same
position, the closed right route after a real clear is **original behaviour, not
a regression**. No production change is justified, and none was made. Do not
write `$1ECB` direction bits to make the route acceptance pass.

## Consequence

The natural World 1 flow after clearing 1-1 is: map at the 1-2 node, enter 1-2.
That is now playable. Reaching Yoshi's House is not part of that flow in this
recipient, matching the original ROM.

## 1-2 (room 010) route mechanics, from user guidance plus probes

The user described the course: fly/float to the very end, enter a pipe, the next
scene goes upward, then a second pipe is the exit. It is the fart-propulsion
course, not the chase-Yoshi course.

What the probes establish on the current candidate:

- The course is about nine screens wide; the camera stops at `camX = 0x228`
  around `x = 0x292` while the player is at `y = 0xC0`. There is a ceiling
  obstruction at that point: at `y = 0xC0` the player cannot pass `x = 0x292`
  no matter how the flight is driven (held B, mashed B, or an air-swim fixture).
- Passing it requires being LOW. After dropping to about `y = 0x100` at
  `x = 0x292`, holding right advances to `x = 0x2D4`, then to `x = 0x324`
  (`camX = 0x2B9`) when swimming resumes.
- Walking on the ground alone falls into a pit at `x = 0x17E` (death, map
  return), so the course does require the flight ability.
- Pressing down plus right at `x = 0x283` while high on the screen leads to a
  pit death, not a pipe.

So any traversal script has to fly over the pit at `x = 0x17E`, drop below the
ceiling before `x = 0x292`, then continue. The `air-swim` fixture
(`forcepoke 85 01`), which the 1-1 route already uses for assisted traversal, is
the practical way to script it.

The following qualification supersedes the earlier pipe-location uncertainty.

## Two-pipe route and actual normal exit

The first pipe is downward-facing, at room010 screen08, columns09/0A,
row0E (`137/138`). An assisted placement near `(0898,00F0)`, an upward launch,
and **Up** enter it normally and reach room `04A`. Pressing Down is the wrong
entry direction.

Room04A is a 13-screen vertical course. Its extra-bit custom sprite `8D` near
`Y=09F0` follows the player's X coordinate. Actual contact sets `$14AF=1`,
which removes the controller's `Y>=00C0` clamp and enables automatic propulsion.
This explains why simply moving Mario below the top pipe without collecting
that item fails. Large instantaneous vertical teleports also bypass sprite
loading and can trigger the camera-relative death boundary; incremental
position fixtures keep the actual camera and sprite loading active.

The top pipe, columns07/08, row08, leads to room `161`, a two-screen exit
scene. Walking right touches the real goal. After the clear animation, the
recipient returns to map0 at `(058,1D8)`, sets course10's normal-clear state
`$1EB2: 0C -> 8C`, and entering the selected node reaches room `106`.
The demo8 donor follows the same room/goal/node sequence, with its own original
direction bits (`$1EB2: 00 -> 84`). Do not copy those direction bits into the
recipient to make the bytes identical.

Reproduce with `recomp/inputs/world1-next-course-two-pipes.script` and run
`python3 tools/qualify_world1_two_pipes.py`. This is an **assisted boundary
regression**, using position, upward-launch, water and invulnerability fixtures.
It skips traversal obstacles. The power-up, pipe transitions, goal and clear
are game-generated; no exit tables, ability state, goal timer, event or
completion flags are written. It does not establish unassisted traversal or
collectibles. See the next-course restoration document for pinned identities.
