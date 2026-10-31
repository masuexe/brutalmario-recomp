# Native product r14 release note

Date: 2026-10-31. Target: `demo11-native-product-r14`. This note records the
current native product build and its default map behaviors.

## Identities

| Item | Value |
| --- | --- |
| ROM SHA-256 | `393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b` |
| Binary SHA-256 | `b854560490132a35343a8150a3e12cb746da50474f29544f70dc582e1ec09eed` |
| Windows package | `local/release/product-r14-2026-10-31.zip` |

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

World 2 room `126` clears with ordinary right and A input from the entry
fixture. The goal byte reaches `9B`, lives rise from four to five, and the SRAM
hash changes after the map return. World 2 rooms `121` and `122` stop on their
simple routes and need specific paths. Castle boss rooms `06E`, `06F`, `070`,
`071` and `072` all have live entry captures. The Phase, exit and save checks
for those rooms stay open.
