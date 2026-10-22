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
