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
accepted r14 build is unchanged.
