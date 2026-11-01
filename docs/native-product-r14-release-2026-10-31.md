# Native product r14 release note

Date: 2026-10-31. Target: `demo11-native-product-r14`. This note records the
current native product build and its default map behaviors.

## Identities

| Item | Value |
| --- | --- |
| ROM SHA-256 | `393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b` |
| Linux binary SHA-256 | `7683d891d3900c545f3a009be64aa259a309093543a5299cc89527f11d87b808` |
| Playable Windows package | `local/release/product-r14-event30-v2.zip` (base target bundle) |
| Playable package SHA-256 | `057c2b433a0c6da735868f39a284cf14f2d22e9d62cc3d952653349d288af010` |
| Playable Windows binary SHA-256 | `d43be6fac1255c131ccf8028e710c5bc8fd460e9d9d1912a42c49a1265efef20` |
| Experimental console package | `local/release/product-r14-cheat-console-experimental-win.zip` |
| Experimental package SHA-256 | `2c028dc1495cc3b695352d9590a92c0c35fb9c28e4374d831939658da57f6bca` |
| Experimental Windows binary SHA-256 | `10772a6e2297d68871a932a81723d7e0cd215bf0d5ac3a591098df3d05af67ff` |

## Default behaviors

- A new save starts at Yoshi's House: pixel `(104,408)`, tile `(6,25)`.
- The main-map 10C node keeps course `30` and enters room `10C` by default. The B4 shortcut to room `190` needs `BM_MAZO_190_NODE=1`.
- The room `174` post-Seven transition returns to the main map 10C node.
- The map hook does not change the Seven boss code.
- The Mazo event switch selects event30 by default. `BM_MAZO_EVENT30=0` disables it.
- The built-in practice console opens with the backquote key. It carries the
  old Python console commands without external files. The runtime patch is
  `0010-builtin-cheat-console.patch`.
- The console is an experimental Windows build. The normal Windows package
  does not contain it. The experimental build runs the guest at about 3 FPS,
  as recorded in [the performance report](windows-console-performance.md).
- The package checker rejects an experimental binary without the
  `PRACTICE CHEAT CONSOLE` marker.

## Verification

- Capture `product-r14-yoshi-v1`: Yoshi start.
- Capture `product-r14-node-v1`: 10C node to room `190`.
- Capture `mazo-174-return-hook-v2`: room `174` to main map.
- The full unit suite passes 429 tests (`local/unit-tests-win-console.log`).
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
## Windows package identity

Measurements on the shipped Windows bundles give these identities.

- `product-r14-event30-v2.zip` carries the base target binary and the base
  target ROM. The binary title is `Brutal Mario Demo11 Native Product`. The
  bundle has 45 packs. The packaged executable has no `BM_YOSHI_START` and no
  `BM_MAZO_EVENT30` text. Its ROM SHA-256 is
  `a1c9d7c8f09399b60193302e33bb1c8111ac0fe8e5b1cb5684fb6f277fddbf91`.
- The r14 Windows binary in
  `local/build-windows/demo11-native-product-r14/` carries the r14 title and
  both hook names. It runs the guest at about 3 FPS on Windows.
- The r14 Linux binary carries both hook names and the r14 ROM.

The fast Windows bundle is therefore the base target bundle. It runs at
normal speed. It does not contain the r14 default map behaviors above. Use it
for play. Treat the r14 map defaults as Linux-only until the Windows r14
guest speed returns to normal.