# Mazo corridor and boss room graphics

## Result

The mazo corridor rooms work as code and as actor data. Their graphics do not
match the recipient. This document records the measured state.

Room `191` renders a normal screen. Room `192` shows a large rectangle of
undefined tiles. Room `190` renders a full corrupted background and tileset.

## Measured data

The checks below use the product ROM and the cheat tool.

| Room | Tileset byte | Extended graphics words | Render |
| --- | --- | --- | --- |
| `190` | `0B` | none | corrupted |
| `191` | `3B` | none | normal |
| `192` | `0B` | none | undefined rectangle |

All three rooms hold the extended graphics record `0100` and then `FFFF`
words. So these rooms request no extended graphics ID.

## Cause

The corridor plan copied the mazo level streams and the mazo sprite lists. It
did not copy the tileset data. It did not copy the Map16 definitions.

A tile object stores a Map16 tile number. Map16 is separate ROM data. The
recipient and mazo hold different Map16 data for the same tileset number. A
copied tile object therefore shows a different tile in the recipient.

The project used the same reasoning for the Forest Star port. That port installs
a room-scoped private Map16 bank. It also installs scoped lookup shims. So one
room can use a different Map16 set without change to other rooms. See
[the restoration record](content-restoration.md).

The corridor plan also states that room `183` and room `184` "do not qualify
graphics". See [the corridor plan](native-mazo-b0.md).

### Header bytes, measured again

| Room | `$05F000` mazo | recipient | `$0EF300` mazo | recipient |
| --- | --- | --- | --- | --- |
| `190` | `0B` | `0B` | `02` | `00` |
| `191` | `3B` | `0B` | `02` | `00` |
| `192` | `0B` | `0B` | `00` | `C2` |

Room `191` renders a normal screen although its tileset byte is the donor `3B`.
Room `192` holds an odd recipient value `C2` in `$0EF300`.

Note: another session rebuilt `local/restoration/demo11-native-sprite9e` during
this check. One read returned a transient wrong byte. Re-read the bytes after
the rebuild before you trust a patch recipe.
## Selector test

The first probe used a minimal pack set. Two different single byte patches
gave the same frame. That made the probe invalid, because the missing packs
rendered the frame blank.

The second probe used the full product pack set. It set `$0EF300 + room` for
room `190` from `00` to `02`, the mazo value.

The frame was byte-identical to the unpatched product frame. So `$0EF300` does
not select the background or the tile graphics of room `190`.

The probe config is `config/restorations/demo11-native-r190fix.json`.

The corridor transition enters room `190` and shows the same corrupted frame.
So the fault is not a raw teleport fixture.

Room `190` is the same room in mazo and in the recipient in header and in level
data. So the difference is the graphics data itself. The recipient holds no
mazo background, tile and palette data for this room.

## Resource identification

Two checks find the graphics files that the three rooms use.

### Decoded content

Decompress all base GFX files `00` to `31` and compare the decoded bytes. Only
seven files differ. Six of them are below.

| GFX | Decoded size | 2bpp or 4bpp |
| --- | ---: | --- |
| `00` | 4096 | 4bpp |
| `01` | 4096 | 4bpp |
| `02` | 4096 | 4bpp |
| `10` | 4096 | 4bpp |
| `28` | 2048 | 2bpp |
| `2A` | 2048 | 2bpp |
| `2B` | 2048 | 2bpp |

The pointer addresses differ for all GFX files. The pointer address alone is
not a difference. Only these seven files hold different decoded bytes.

### VRAM content match

Search the decoded bytes of each GFX file in a room 190, 191 and 192 VRAM
dump. The search shows which files each room uses.

| GFX | VRAM address | Room 190 | Room 191 | Room 192 | Content differs |
| --- | --- | --- | --- | --- | --- |
| `01` | `0xD000` | no | yes | yes | yes |
| `28` | `0x8000` | yes | yes | yes | yes |
| `2A` | `0x9000` | yes | yes | yes | yes |
| `2B` | `0x9800` | yes | yes | yes | yes |
| `00`,`02`,`10` | none | no | no | no | yes |

So rooms `191` and `192` use GFX `01`, `28`, `2A` and `2B`. Room `190` uses
GFX `28`, `2A` and `2B`. GFX `00`, `02` and `10` differ but do not load in
these rooms.

GFX `01` sits at VRAM `0xD000`. GFX `28`, `2A` and `2B` sit at the background
tile addresses `0x8000`, `0x9000` and `0x9800`. This agrees with the black
rectangle and the striped background in the captures.

### Stream identities

| GFX | Recipient stream | Recipient length | Baked length |
| --- | ---: | ---: | ---: |
| `01` | `0x0BE43E` | 3114 | 4096 |
| `28` | `0x098B22` | 1360 | 2048 |
| `2A` | `0x0981DF` | 1162 | 2048 |
| `2B` | `0x08FE2B` | 948 | 2048 |

## Implementation design

The runtime gives the native layer what the override needs.

- The CPU reads a ROM byte through `cart_getRomPtr`. That function calls
  `bm_content_resolve` at `cart.c` line 153 for every read.
- The runtime global `g_snes` points to the console. `g_snes->ram` is the
  0x20000 byte work RAM.
- The room number is at work RAM `$10B` and `$10C`, low byte first.

So a native override can return a pack byte for a ROM read while the room is
`190`, `191` or `192`.

Target streams, by recipient file offset:

| GFX | Recipient offset | Rooms |
| --- | ---: | --- |
| `01` | `0x0BE43E` | `191`, `192` |
| `28` | `0x098B22` | `190`, `191`, `192` |
| `2A` | `0x0981DF` | `190`, `191`, `192` |
| `2B` | `0x08FE2B` | `190`, `191`, `192` |

The pack holds the mazo compressed stream for each target. For a read at a
file offset inside a target window, the override returns the pack byte at the
same window offset. The in-game decompressor stops at the mazo terminator, so
a longer mazo stream is safe.

The design does not change the base GFX pointer table and does not change the
level data. Other rooms read the recipient streams.

## Open check

The override needs the room number in work RAM before the loader decompresses
the stream. Capture one load frame at mode `0F` or `13` and read `$10B`. If the
room number is not set yet, latch the last seen room at the level header read.

## Runtime pack overlay

The corridor data is not in the product ROM image. It is a native pack at
`CA8000`, mounted at runtime by `bm_content_load`. The loader copies the ROM and
then writes each pack at its file offset. Every ROM read then goes through
`bm_content_resolve`, which returns the pack byte for the mapped bank.

So a static read of the product ROM at a corridor room gives the empty hole, not
the level data. A static compare of room `191` and `192` level data is invalid.
At runtime the room level pointers resolve through the pack, and the pack holds
the mazo terrain at offset `55` (room `191`) and `176` (room `192`).

Room `190` is not a corridor slot, so its level data is in the ROM image and
equals the mazo level data.

Result: all three rooms have the correct terrain at runtime. Only the graphics
differ.

## GFX swap probes

Each probe used the full product pack set and a real capture.

| Probe | Change | Room `190` frame |
| --- | --- | --- |
| Background set | swap GFX `28`, `2A`, `2B` to mazo | byte-identical |
| Sprite set | swap GFX `00`, `01`, `02`, `10` to mazo | changed in one BG corner, FG still garbage |

The background set swap changed no pixel. The sprite set swap changed only a
corner. So a GFX swap alone is not sufficient for room `190`.

The remaining cause is the Map16 tile set. The level tilemap gives Map16 tile
numbers. Map16 gives the tiles and the palette for each number. The recipient
and mazo hold different Map16 data for the same numbers. So the floor and the
terrain show wrong tiles even when the GFX bytes match.

Probe targets: `demo11-native-gfx28mazo`, `demo11-native-gfx4bpp`.

## Port plan

1. Build one native content pack that holds the mazo compressed streams for
   GFX `01`, `28`, `2A` and `2B`.
2. Add a room-scoped override in the cart read path. The runtime calls
   `bm_content_resolve` while the CPU reads a ROM byte, at
   `cart.c` line 153. The override returns a pack byte only while the current
   room is `190`, `191` or `192` and the read address is one of the four
   streams.
3. Keep the level data and the base GFX table unchanged. Other rooms keep the
   recipient streams.
4. Mount the pack in the product target and rebuild.
5. Capture rooms `190`, `191` and `192` with the full product pack. Compare
   each frame to the official mazo frame.
6. Run the unchanged-route regression and the full suite.

A global change to GFX `01`, `28`, `2A` and `2B` is not allowed. The
unchanged-route regression covers rooms that use these files, and a global
change breaks those rooms.