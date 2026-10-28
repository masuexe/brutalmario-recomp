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

## Combined Map16 and GFX probe

The strongest probe changed two things at once, with the full product pack set.

| Change | Detail |
| --- | --- |
| Map16 bank | replace `$12:8000` (32768 bytes) with the mazo block |
| GFX | redirect `00`, `01`, `02`, `10`, `28`, `2A`, `2B` to the mazo streams |

The probe ROM holds the mazo Map16 block and the mazo GFX. The check compares
the probe ROM bytes to the mazo bytes.

Captures show no change for room `190`. Room `191` frame `w4` is byte-identical
to the unpatched product frame. So the Map16 block and the base GFX files are
not the cause.

Probe target: `demo11-native-m16probe`.

## The room 191 fault is a message box

A walk capture of room `191` shows a black rectangle with a white grid in the
upper left. The rectangle stays at one screen position. The user reported this
as garbage tiles and crystal-ball text.

The rectangle is not terrain. A terrain fault would move with the camera. An overlay at one screen position
uses Layer 3 or a message sprite.

The room `191` sprite list holds custom ids `A9` and `77`. The corridor remapped
the mazo id `B0` to the product slot `A9`. The product record for `A9` points to
code at `A1:8998`, inside the mazo module, so the sprite code is present.

Custom sprite and room ids are version-local. A copied id can name a different
resource in the recipient. The graphics of the message element are the open
item.

### Sprite placement evidence

The room `191` work RAM holds one live custom sprite in slot `7`:

| Field | Value |
| --- | --- |
| status `$14DC` | `08` |
| sprite number | `40` |
| custom id `$1AB9E` | `A9` |

The corridor plan remapped the mazo id `B0` to the product slot `A9`. The
record code is present at `A1:8998`. The project already records the open item:
sprite code alone is not sufficient, because sprite tile graphics are also
missing (see [the sprite graphics gap](demo11-sprite-graphics-gap.md)).

So the black box is a custom sprite that draws tiles this line does not hold.

## Root cause: the GFX selection, not the data

A pinned mazo reference capture gives a real baseline. The fixture is
`recomp/inputs/mazo-190-mode14-fixture.script`. The captures are
`local/captures/mazo-190-mode14` and `local/captures/mazo-191-donor`.

The mazo frame shows the full boss room: castle backdrop, canyon, waterfall,
grass and a Japanese message bubble.

Compare the GFX files that each build loads in room `190`. The method searches
the decoded stream of every GFX id in the room VRAM dump.

| Build | Loaded GFX ids |
| --- | --- |
| mazo | `28` `29` `2A` `2B` `82` `83` `85` `E5` `E7` `E8` |
| product | `28` `29` `2A` `2B` `0D` `22` |

So the product loads a different 4bpp set. The product does not load `82`, `83`,
`85`, `E5`, `E7` and `E8`.

The level `0x30` header tables and the `0x14AD08` graphics record are identical
in both builds. A translevel wait also does not change the result. So the
product reads a different GFX set for the same selector.

An earlier probe installed the mazo data for `82`, `83`, `85`, `E5`, `E7`, `E8`
and pointed those slots at it. The frame did not change. The product never
loads those ids, so the data alone is not sufficient.

### VRAM slot test

Room `190` is stable at translevel `0x30` in the product. A forced translevel
does not change the loaded set: the product still loads `0D` and `22`.

The product writes `0D` at VRAM `0xD000` and `22` at `0xF000`. Mazo writes `E5`
at `0xD000` and `E8` at `0xF000`. A probe pointed the product slots `0D` and `22`
at the mazo streams. The frame changed in a small area only.

The product writes no data at VRAM `0x0000`, `0x1000` or `0x2000`. Mazo writes
`82`, `83` and `85` there. These are background character areas, so the product
background reads empty tile data.

Probe target: `demo11-native-slots`.

### What this establishes

The fault is the GFX set selection for the room, not the GFX bytes. The product
selects a set that omits three background files. A data port has no effect until
the selection changes.
## Next concrete action

1. Find the GFX set table that maps a level selector to a GFX file list. Compare
   the mazo table with the product table for the selector that room `190` uses.
2. Port the table entry and the GFX data together.
3. Check rooms `191` and `192` the same way.
### The GFX selector

Work RAM bytes `$0D9A`, `$0D9B`, `$0D9D`, `$0D9F` and `$0DB1` select the GFX
files to load. A probe pinned them to the mazo values before the load.

The product then loaded `E5`, `E7` and `E8` at the mazo VRAM addresses. So the
selector drives the load, and the product can load the mazo set.

Room metadata `0x14AD08` and the level `0x30` header tables are identical in both
builds. So the run time sets the selector, not a data byte.

## Port direction

Add a room-scoped native adaptation. For rooms `190`, `191` and `192`, set the
GFX selector bytes to the mazo values before the GFX load runs.

| Byte | Product | Mazo |
| --- | ---: | ---: |
| `$0D9A` | `37` | `30` |
| `$0D9B` | `C1` | `02` |
| `$0D9D` | `15` | `15` |
| `$0D9F` | `FA` | `80` |
| `$0DB1` | `01` | `08` |

Then port the GFX data that the mazo set needs: `82`, `83`, `85`, `E5`, `E7` and
`E8`.

Check the selector at the level load phase, because the values differ by phase.
Read the values at mode `0x14`, not at mode `0x0E`.

## Reliable evidence: the background tilemap

VRAM keeps its contents across a room change. So a VRAM search can find a GFX
file left over from an earlier room. A loaded-set result is therefore weak
evidence. The background tilemap is stronger, because the room writes it.

The captures are `local/captures/mazo-190-mode14/a5` and
`local/captures/view-r190/f1`.

| Region | Mazo distinct words | Product distinct words |
| --- | ---: | ---: |
| BG1 tilemap `0x2000` | 188 | 16 |
| BG2 tilemap `0x3000` | 200 | 23 |
| BG3 tilemap `0x5000` | 40 | 3 |

Mazo holds a real background image. The product holds a two-tile pattern that
repeats: `ff0f ff00 ff0f ff00`. That pattern is the vertical stripes in the
screen capture.

So the product writes a degenerate background tilemap for room `190`. The
background source is absent or wrong, not only the tile graphics.

The level `0x30` header tables are the same in both builds. So the next step is
the background pointer table: find the entry that the level selects and compare
the mazo stream with the product stream.

## First result: extended GFX 1E6

A mazo reference capture at mode `0x14` gives the true gameplay baseline. The
frame shows a sunset sky, clouds, a dark floor and the boss.

Fixture: `recomp/inputs/mazo-190-play-fixture.script`. Capture:
`local/captures/mazo-190-play`.

At the same phase the two builds load the same GFX files except one:

| GFX | Mazo | Product |
| --- | --- | --- |
| `0x1E6` | valid pointer | `FFFFFF` (empty) |

The product requests `0x1E6` and finds no data. The pointer slot is at file
offset `0xA02BA`.

The candidate `demo11-native-gfx1e6` installs the mazo stream (2506 bytes) at a
free run and sets the pointer.

Measured result:

| VRAM region | Diffs before | Diffs after |
| --- | ---: | ---: |
| `0xD000` | not equal | 0 |
| `0xE000` | 3741 | 0 |
| `0xF000` | not equal | 0 |

The frame now shows the sunset backdrop, the clouds and the HP bar. Vertical
stripes remain in the background area, so more work remains.

Room `192` keeps the same frame: its fault is the crystal-ball sprite, not this GFX.

### The translevel mismatch

At the gameplay phase the GFX selector bytes are equal in both builds:
`$0D9A`=`37`, `$0D9B`=`C1`. An earlier reading of `02` came from the preview
phase, not from gameplay.

The real difference is the translevel:

| Build | Room | Translevel `$13BF` |
| --- | --- | --- |
| mazo | `0x190` | `0x30` |
| product | `0x190` | `0x6A` |

Mazo reaches room `190` through its own level `0x30`. The product reaches the
same room through a different level.

The fixture `recomp/inputs/mazo-190-level6a-fixture.script` tried to force the
product translevel on the mazo image. The map node override did not take, so
mazo stayed at `0x30` and the test was inconclusive.

Next: check the product level that owns the corridor rooms. Room `190` must run
under the mazo level, or the level must carry the mazo background data.

### The stripes are a background layer

A diagnostic capture clears every sprite slot (`$14C8`+0 to 11) after the room
loads. The boss sprites leave the frame. The vertical stripes stay.

So the stripes are a background layer, not a sprite. The sprite graphics gap is
a separate item.

Room `190` has no Layer 2 (`$05E600+190*3` = `FFDE54`, the sentinel). So the
background comes from the level background path, and that path writes a blank
tile `0x0FF` across the BG1 tilemap instead of the mazo tiles.

Capture: `local/captures/nosp/s2`.

## Room 190 uses Mode 7

Every product capture of room `190` reports `bgmode` = `7` in the PPU register
dump. Mazo draws the same room with a horizon, clouds and perspective, which is
the Mode 7 look.

So the stripes are not a normal background tilemap. The Mode 7 data is wrong:
the Mode 7 tilemap and character data in VRAM `0x0000` to `0x3FFF`.

The VRAM region diffs support this. The largest differences sit in
`0x0000` to `0x2000`, the Mode 7 tilemap and character area.

The earlier statement that the background writes a blank tile `0x0FF` is
incomplete. The BG1 and BG3 tilemaps both use tile `0x0FF` as a solid band with
different palettes, and that is valid. The stripe pattern comes from the Mode 7
data, not from BG1.

## Mode 7 data source

Room `190` has no Layer 2: `$05E600+190*3` = `FFDE54`, the sentinel. A Mode 7
room takes its Mode 7 data from the level Layer 3 path.

A search of the level pointer tables did not identify the Layer 3 table with
confidence. The next step is to locate the Mode 7 data pointer by its decoded
size, then compare the mazo stream with the product stream.

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