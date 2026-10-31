# World 2 room 126 course clear

Date: 2026-10-31. Entry is a labeled map override fixture, not ordinary map
travel. After entry, the route uses only ordinary right and A inputs.

Room `126` (translevel `04A`) starts at player `(80,320)` with four lives.
Twenty cycles of right and A move the player to `(588,320)`. At sample `j10`
the goal byte `$1493` is `9B` and lives rise from four to five. At sample
`j15` `$1493` is `03`. Sample `j20` returns to the overworld (mode `0E`,
room `126`) with five lives.

Capture: `w2-126-run-v1`. Script: `recomp/inputs/world2-room126-run.script`.
The run does not write completion flags, events or saves. It qualifies the
course traversal from the entry fixture, not the full map route.
