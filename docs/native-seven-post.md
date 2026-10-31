# Seven post-room route candidate

Date: 2026-10-31. Room `0FF` screen 0 has a screen exit to room `174`. The
room is the candidate for the next path after the Seven fight. The earned
defeat is not proven. This note records only a direct entry check.

Room `174` has translevel `098`. Capture `mazo-174-entry-v1` enters the room
directly. It holds mode `14`, four lives, course `98`, and player spawn
`(32,304)`. The frame shows a playable icy sky area with a pipe, a star item
and foreground terrain. The room has 31 screens and four exits: three screen 0,
19 and 23 exits to room `323`, and one screen 30 exit to room `373`.

A right walk from the spawn leaves the ledge. The player falls from Y `304`
to Y `455`, then Y `858`, loses one life and returns at `(270,302)`. The
route needs a jump or a different path.

The entry is a practice fixture. It does not show the fight-to-room transfer,
a saved clear or a complete route.

The product now intercepts room `174` entry. The default hook `BM_SEVEN_RETURN`
waits until mode `14`, then sets mode `0B` and the map position to the main-map
10C node. Capture `mazo-174-return-hook-v2` returns to the map at pixel
`(256,240)`, tile `(16,15)`, map `0`. The flag `BM_SEVEN_RETURN=0` disables the
hook. The Seven boss code is unchanged.
