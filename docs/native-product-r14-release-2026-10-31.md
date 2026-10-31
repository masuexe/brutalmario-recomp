# Native product r14 release note

Date: 2026-10-31. Target: `demo11-native-product-r14`. This note records the
current native product build and its default map behaviors.

## Identities

| Item | Value |
| --- | --- |
| ROM SHA-256 | `393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b` |
| Binary SHA-256 | `b854560490132a35343a8150a3e12cb746da50474f29544f70dc582e1ec09eed` |
| Windows package | `local/release/product-r14-2026-10-31.zip` |
| Package SHA-256 | `6234e7485cbeba2f01a25a9216fdeba3b1618fd426ca3cb08be098a5f2d1f445` |

## Default behaviors

- A new save starts at Yoshi's House: pixel `(104,408)`, tile `(6,25)`.
- The main-map 10C node at tile `(16,15)` enters room `190`.
- The room `174` post-Seven transition returns to the main map 10C node.
- The map hook does not change the Seven boss code.

## Verification

- Capture `product-r14-yoshi-v1`: Yoshi start.
- Capture `product-r14-node-v1`: 10C node to room `190`.
- Capture `mazo-174-return-hook-v2`: room `174` to main map.
- The full unit suite passes 414 tests (`local/unit-tests-round94.log`).

The earned Seven defeat, full 9C saved clear and later audible music stay open.

## Recent route checks

Room `126` clears with ordinary right and A input from the entry
fixture. The goal byte reaches `9B`, lives rise from four to five, and the SRAM
hash changes after the map return. Rooms `121` and `122` stop on their
simple routes and need specific paths. Rooms provisionally listed as castle
boss rooms (`06E`, `06F`, `070`, `071` and `072`) all have live entry captures.
Their identities, phase, exit and save checks stay open.

The room126 probe is outside the corrected Forest World2 list. Its historical
node override saves node05 rather than translevel04A; a changed SRAM hash is
not sufficient evidence of correct course-save ownership. See
[the room126 ownership check](world2-course126-route.md).

The replacement room126 route uses its existing `D727=4A` node without a
node-table edit. Real clear, `$1EEC: 0F -> 8F`, both SRAM copies and reset/File A
reload pass. This remains a map-coordinate fixture, outside World2 acceptance.
