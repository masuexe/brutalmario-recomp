# Content closure update, 2026-10-30

This note records the progress and the open blockers since the
[content closure audit](content-closure-audit.md). The accepted product stays
`demo11-native-product-r14`. The candidates below stay experimental.

## Closed or narrowed since the audit

| Area | Result |
| --- | --- |
| Type-3 sprites | C0, C1 and C2 run in the candidate line. C0 matches the source after a one-frame shift (63/63 samples). C1 moving children match (64/64). C2 left/right generation and normal 094 entry pass. |
| Modern sprite slots | The project restored programs for 25, 33, 94, 99, A1 and 97, with fresh behavior checks. Slot 97 has a route from room 108 to room 1EF. The other seven slots are default records in every supplied image, so their review closes with no install. |
| Forest exits | 11B screen 11 to 053, 11C screen 9 to 041 and 11E screen 19 to 037 pass live probes. The bounded exit table covers all ten Forest rooms. |
| Ghost Forest and Pyromaniac | Room 114 holds tape `(5232,384)` and keys at `(4176..4208,320)`. Room 11E holds tape `(2656,480)`, which sits below the kill boundary near Y 454. |
| Extended graphics | Sprite 9C requests `0282` and the product pointer is empty. Candidate `demo11-native-mazo-gfx282-v1` mounts the official mazo stream at `D2:8000` and patches three bytes. Id `027E` has no immediate requester in any pack. |
| Seven ending | Entry, child, font, music, ending, hidden 1-up, pit death and map return hold bounded evidence. |

## Open blockers

| Item | Blocker |
| --- | --- |
| Earned Seven victory and saved clear | The tier 6 base part sits about 14 tiles below the arena floor. Forced points, a natural-floor control and a 36-sample attack sweep do not damage it. A short manual fight sample is the next input. |
| Mazo 9C attack and phase music | Assisted real attacks now reach the scripted ending, room192, ordinary sphere goal and map return on both hosts. Native guest flag persists on reset, but practice exit count differs from source; correct world/save identity and later audible music remain open. See [ending boundary](native-mazo-ending.md). |
| Mazo 9B room 190 | The user states that room 190 is a level before the boss fight, not a boss fight. Assisted entries die at `(32,-64)`. The `D85`/`D8F` bytes are not boss health. A real traversal, clear and save check stay open. |
| `0282` cumulative integration | Closed on experimental mazo-cumulative-v1: complete upload matches official mazo, all 45 recipes and 57 inherited packs retained, eleven fresh native regressions pass (1,156 file comparisons). See [cumulative integration](native-mazo-cumulative.md). |
| Room 129 exits | The first screen gives `045`. Screens 2 and 3 need an entry from their left neighbor. |
| Room 11C screen 10 | The first screen gives `041`. Screen 10 needs a neighbor entry. |
| Rooms 114 and 11E lower bands | The project knows the tape positions. It did not find the vertical descent or pipe. |
| Japanese message rendering 191/192 | Actual ending captures locate source GFX2A at VRAM9000 and text at tilemapA000. Native has no sentence, uses blank12F instead of11F and has a different message selector/data path at03BB90. A font-only replacement is insufficient; recover local message identity/encoding/font while preserving recipient course/save identity. |
| Audible music acceptance | Needs listening. |
| World routes 2 to 8 | No route, exit or save acceptance outside Forest. |

## Mazo 9B room 190 is a level

The user states that room `190` is the level before the boss fight, not a boss
fight. Captures `mazo-9b-entry-v1/v2-{donor,native}` agree on the initial state:
mode `14`, room `190`, player `32/-64`. The `D85` and `D8F` bytes are not boss
health. Both hosts then return to map mode. A real traversal, clear and save
check for this level stay open.

## Next steps

1. Restore the room191/192 message selection, encoding and font locally. Reconcile Mazo's actual world/save assignment beyond practice entry. Seven final-part damage remains open.
2. Build neighbor-entry fixtures for 11C screen 10 and 129 screens 2 and 3.
3. Find the lower-band entry in rooms 114 and 11E.
4. Re-run a world parity triage on the current product before more visual work.

No whole-game acceptance or product promotion follows from this note.
