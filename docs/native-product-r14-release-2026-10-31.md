# Native product r14 release note

Date: 2026-10-31. Target: `demo11-native-product-r14`. This note records the
current native product build and its default map behaviors.

## Identities

| Item | Value |
| --- | --- |
| ROM SHA-256 | `393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b` |
| Binary SHA-256 | `e75b707217cccc6e3ab575ef3ec1b8612c931639a615522cb67db844622aefc3` |
| Windows package | `local/release/product-r14-event30-v2.zip` |
| Package SHA-256 | `057c2b433a0c6da735868f39a284cf14f2d22e9d62cc3d952653349d288af010` |

## Default behaviors

- A new save starts at Yoshi's House: pixel `(104,408)`, tile `(6,25)`.
- The main-map 10C node keeps course `30` and enters room `10C` by default. The B4 shortcut to room `190` needs `BM_MAZO_190_NODE=1`.
- The room `174` post-Seven transition returns to the main map 10C node.
- The map hook does not change the Seven boss code.
- The Mazo event switch selects event30 by default. `BM_MAZO_EVENT30=0` disables it.

## Verification

- Capture `product-r14-yoshi-v1`: Yoshi start.
- Capture `product-r14-node-v1`: 10C node to room `190`.
- Capture `mazo-174-return-hook-v2`: room `174` to main map.
- The full unit suite passes 425 tests (`local/unit-tests-round186.log`).
- `tests/test_product_r14.py` guards the event30 default, the opt-in B4 map
  shortcut, the Yoshi start and the 9C phase music recipe.

The earned Seven defeat, full 9C saved clear and later audible music stay open.

## Recent route checks

Room `126` clears with ordinary right and A input from the entry
fixture. The goal byte reaches `9B`, lives rise from four to five, and the SRAM
hash changes after the map return. Rooms `121` and `122` stop on their
simple routes and need specific paths. Rooms provisionally listed as castle
boss rooms (`06E`, `06F`, `070`, `071` and `072`) all have live entry captures.
Their identities, phase, exit and save checks stay open.

The room126 probe is outside the corrected Forest World2 list. Its historical
node override saves node05 rather than translevel04A. A changed SRAM hash is
not sufficient evidence of correct course-save ownership. See
[the room126 ownership check](world2-course126-route.md).

The replacement room126 route uses its existing `D727=4A` node without a
node-table edit. Real clear, `$1EEC: 0F -> 8F`, both SRAM copies and reset/File A
reload pass. This remains a map-coordinate fixture, outside World2 acceptance.


The default Mazo node override also changes the save index toB4. A real
assisted sphere clear on r14 leaves original course30 completion unset.
An isolated [primary-entry candidate](native-mazo-primary-entry.md) retains
node30 and saves its completion after reset. It is not promoted into this
package. Recipient eventFF/exit count0 and the B0 legacy flag remain open.


The [playable Mazo progress milestone](native-mazo-progress.md) has a separate
native command and profile. It carries the cumulative restored content
and protects recipient00D while saving the actual Mazo30 goal. The r14 package
and its recorded checksum remain unchanged.
