# World 1 castle entrance room 10E audit

Date 2026-10-23. Checks whether the castle room entered after room138's clear has
a missing-dependency defect like the earlier courses, and whether its loaded Map16
terrain differing from cheap_demo indicates a restoration gap.

## Entry and behaviour

Entering map 0 `(0A8,1A8)` on `world1-room138-sprite` reaches room `0x10E` in
mode `0x14`; the player moves normally (`x` advanced from `0x70` to `0x99`) and the
level requests music `0x83`.

## Dependencies are all present

| Check | Result |
| --- | --- |
| Extended graphics selected by the room | none |
| Sprites in the room | 9, **none** carrying the custom-sprite flag |
| Music slot `0x83` | pointer `18BC86`, installed |

## Why the terrain differs from cheap_demo

At the same position the loaded Map16 buffers differ by 64 cells (rows 4 onward).
That is not a missing resource: the level content itself differs between the two
builds.

| Stream | Candidate vs cheap_demo |
| --- | --- |
| Layer 2 | identical |
| Layer 1 | 767 differing bytes, differences start around offset 1090 |
| Sprite list | 10 vs 12 bytes, 9 of the first 10 differ |

The recipient is demoOnly1 and the donor is a separate build, so level content
differences are expected; donor content is only imported where a dependency is
missing. No recipe restores castle level data, and none should be invented to make
the two builds match.

## Conclusion

No missing-dependency defect was found in the castle entrance room. The Map16
difference from the donor is explained by version content differences, not by a
broken resource. This closes the castle thread for now; unassisted full traversal,
the castle interior beyond this room, and audible output remain open but are not
implicated by any observed failure.
