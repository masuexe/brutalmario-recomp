# Mazo main-map node redirect to room 190

Date: 2026-10-31. The user supplied the main overworld coordinates for the
`10C` node. The node tile is at X `16`, Y `15` on the main map (map id
`0`). Its translevel table entry is index `1F0`, and the stored value is
`30`.

A direct fixture proves the redirect. Script `map-main-node.script` sets the
player position to that tile, writes `B4` to `7ED1F0`, and presses A. Capture
`map-main-node-v1` then shows:

| Dump | Mode | Room | `13BF` |
| --- | --- | --- | --- |
| `m0` | `0D` | `0C5` | `00` |
| `m2` | `14` | `190` | `B4` |

Thus the entry table byte controls the node. A native runtime adaptation in
`recomp/native_seven.c` now holds this redirect behind the environment flag
`BM_MAZO_190_NODE`. It writes `g_ram[0xD1F0]=0xB4` when game mode is
`0x0E` and the map id is `0`. The accepted product stays r14.

The hook is now built into the `demo11-native-product-r15` candidate. Capture
`map-main-node-r15-hook-v1` runs the same map position without a WRAM write.
The map dump shows `D1F0` change from `30` to `B4`, and the A press loads room
`190` with `13BF=B4`. The flag `BM_MAZO_190_NODE=1` enables the hook. The
hook does not change the accepted r14 build.

The mazo original starts a new save at this tile. The product start differs, so
the fixture uses a teleport to the tile. A normal route to the tile is not
established.

## New save start at Yoshi's House

The user asked to move the product new save start to Yoshi's House. The default
save template holds pixel `(72,408)` and tile `(4,25)`. The Yoshi's House value
is pixel `(104,408)` and tile `(6,25)`. A reference patch of the four template
words moves the start to that value. Capture `new-save-yoshi-hook-v1` uses the
runtime flag `BM_YOSHI_START=1` on the r15 candidate and starts at pixel
`(104,408)`, tile `(6,25)`, map `0`. The flag guards the change. The accepted
r14 build stays unchanged.

The hook is now active by default. The flag `BM_YOSHI_START=0` disables it for a
diagnostic run. Capture `new-save-yoshi-default-v2` starts a new save without an
environment variable and reports pixel `(104,408)`, tile `(6,25)`, map `0`.

A map route probe starts at tile `(6,25)`. Holding right reaches tile `(8,25)`
and stops. Up and down do not move the player. Left returns to `(6,25)`. The
main-map path in this fixture does not connect the Yoshi's House start to the
10C node, so the node proof uses the teleport fixture. An A press at tile
`(8,25)` moves the player to map tile `(23,10)` and stays on the map. That
tile is a map warp, not a course entry.

The map node hook is also active by default. The flag `BM_MAZO_190_NODE=0`
disables it. Capture `map-node-default-v1` enters the node without a WRAM write
and loads room `190` with `13BF=B4`.

Candidate identities: `demo11-native-product-r15` ROM
`9f6d845b19ad24160668633e2f30d0e846662c67b135c6cbc1bca680db20716e` and
binary `a06c50765ce8cf853d6a097e880f800645f1550559497783d5ee1c77e68cf866`.
The accepted r14 binary stays published, and a rebuild of any target includes
the default hooks.
