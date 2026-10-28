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

### The Mode 7 tilemap structure explains the stripes

The Mode 7 tilemap for both builds uses tile `0x0FF`. The difference is the
palette field.

| Build | First 32 bytes of VRAM `0x0000` |
| --- | --- |
| mazo | `ff00 ff00 ff00 ff00 ...` |
| product | `ff0a ff09 ff0b ff0b ff09 ...` |

In Mode 7 each tilemap cell is one tile number, not a tile with a palette. Mazo
uses tile `0x00` and tile `0xFF`. The product uses tiles `0x08` to `0x0B` across
the row, so the row shows a repeat of a few tiles. That repeat is the vertical
stripe pattern.

A probe on top of the `1E6` candidate also swapped every differing base GFX
(`00`, `01`, `02`, `10`, `28`, `2A`, `2B`) to the mazo streams. The stripes stayed.

Probe target: `demo11-native-allgfx`.

So the missing item is the Mode 7 tilemap itself, not the base GFX.

### Mode 7 tilemap storage

The whole mazo ROM holds no 12-byte window of the Mode 7 tilemap. So the game
compresses the tilemap, or it builds the tilemap at run time.

A scan of all 1998 RATS blocks in the mazo ROM decoded each block and compared
the result with the 16384 byte tilemap. No block matched.

So the tilemap comes from another path. The next step is to read the level
loader code and find the table it uses.

### Control room: 0x10C uses mode 1

Room `0x10C` is in the same level and renders a clean night sky. Its PPU mode is
`1`, not `7`. So that frame does not prove that Mode 7 rendering works.

Fixture: `local/captures/walk30` (level `0x30` via the map node, then walk).

Room `190` reports mode `7` when entered from level `0x30` and when entered from
the map 6 path. Room `0x10C` in the same level reports mode `1`. So the room
data selects the mode. Room `190` sets Mode 7 on purpose.

## Open item

The Mode 7 tilemap of room `190` differs from mazo, and the source is not a
plain ROM block and not a RATS block. Two candidates remain:

1. The game builds the tilemap at run time from level data that this line has
   not ported.
2. The native PPU writes the Mode 7 tilemap area with wrong data.

No Mode 7 room of this line has a verified correct frame. So case 2 is
still open. The next check is a capture of a second Mode 7 room to compare.

## DMA source tracing

The runner can log every DMA with its source address. The facility is off in a
production build. Set `BM_DIAG_PPU_DMA_HISTORY=1` at the build stage, then set
`SNESRECOMP_DMA_LOG=1` at the native stage.

```
BM_DIAG_PPU_DMA_HISTORY=1 python3 tools/m1.py --target <t> build
SNESRECOMP_DMA_LOG=1 python3 tools/m1.py --target <t> native --script <s> --capture <c>
```

The configure log then reports `SNES PPU/DMA history: enabled`, and `run.log`
holds `[dma] f<frame> ch<n> A->B src=BB:AAAA dst=$21NN size=N` lines.

### First result

A dense capture across the room `190` transition records 33,994 DMA events.
Almost every transfer to VRAM `$2118` reads from work RAM, for example
`src=7E:9000`. The game builds the VRAM image in work RAM first. It then copies that image.
So the DMA source does not name the ROM stream.

The next link is the work RAM write. The runner already has a work RAM write log
hook (`snes_set_wram_write_log_hook`). The next step is to record which ROM
addresses fill the work RAM range that the room load then copies to VRAM
`0x0000`.

## The real entry path (user report)

The user supplied the map facts from Lunar Magic:

- A new save puts Mario on the map node for level `0x10C`. That level is
  translevel `0x30`.
- Room `0x190` sends the player to room `0x191` automatically while the player
  stays alive.

So the correct way into these rooms is level `0x30`, not a map 6 teleport plus a
room poke.

Measured on the product:

| Check | Result |
| --- | --- |
| level `0x30` entry | starts at room `0x10C` |
| room `0x10C` frame | starfield, stone pillars, vine and a block |

Room `0x10C` renders correctly, so the level and the corridor start are sound.
The open question is the room change from `0x10C` to `0x190`.

An idle capture holds room `0x10C` for 2160 frames, so the change needs input.
A right-walk and a vine climb both end in a death mode, so the exit is not found
yet.

Captures: `local/captures/idle30`, `local/captures/vine`, `local/captures/walk30`.

### Room 0x10C holds one object

The room `0x10C` level stream is 11 bytes. After the two header bytes and the
music byte, the stream holds a single object at x `0xC0`, then the terminator.
So the room change is one object, not a walkable path. Wandering right or
climbing the vine does not find it.

## Renderer check

The capture configuration uses `NewRenderer=0`. A capture with
`--renderer optimized` gives a byte-identical frame for room `190`. The fault is
not in the renderer choice.

## VRAM address writes

`$2116` and `$2117` capture the VRAM word address of each write. During the room
`190` transition only word addresses `0x1C00`, `0x6000`, `0x6100` and `0x6700`
appear. A Mode 7 tilemap covers word addresses `0x0000` to `0x1FFF`.

So the room transition does not write the Mode 7 tilemap. The visible pattern
comes from data another scene left in that area.

## Room-copy experiment

A candidate copies the whole of mazo room `190` into a free room number `0x1A0`:

- the Layer 1 stream (`00100040001f000100040000ff`),
- the Layer 2 pointer `FFDE54`,
- the sprite list `0008009BFF`,
- the `0x14AD08` room record `0100FFFF...`,
- the `0x0EF300` byte `02`.

The candidate builds and enters room `0x1A0` at mode `0x14` with `bgmode` `7`.
The frame is byte-identical to the room `190` frame.

Table of the result:

| Item | Value |
| --- | --- |
| target | `demo11-native-roomcopy` |
| room reached | `0x1A0` |
| frame hash | same as room `190` |

So the room number, the room streams, the sprite list and the room record do
not change the frame. The missing data is not room-scoped.

## When the Mode 7 data loads

Fixture `recomp/inputs/mazo-190-loadtiming-fixture.script` dumps the mazo VRAM
just before and just after a room `190` entry.

Result: the mazo build already sits in room `190` at mode `0x0E` before the
entry poke, and the Mode 7 area does not change across the entry:

| VRAM region | Bytes changed |
| --- | ---: |
| `0x0000` | 0 |
| `0x1000` | 0 |
| `0x2000` | 0 |
| `0x3000` | 53 |
| `0x4000` | 0 |

So the scripted button sequence reaches room `190` on its own, and the Mode 7
data is present before the room change finishes.

Conclusion: the game loads the Mode 7 data at level load, not at room entry.
That is why a room copy changes no pixel and a level port is the operation that
matters.

## Mode and DMA results

A probe sets `$0100` to `0x0E` after the room `190` entry, matching the mode that
mazo holds. The frame changes to a different pattern of lines, so the mode alone
does not supply the background.

The DMA log gives no direct ROM source for the VRAM image. Every large transfer
reads from work RAM (`7E:` and the `7F:` mirror). The only ROM sources are small
blocks in bank `00`, payloads in bank `04`, and one 1792 byte block at `10:E20B`.

So the game decodes the graphics into work RAM first. To reach the ROM stream the
next step needs a work RAM write log, or a read of the level loader code.

## Trace tooling survey

These facilities exist but are not active in the current builds.

| Facility | Gate | Note |
| --- | --- | --- |
| `SNESRECOMP_DBTRACE`, ring probes | `SNESRECOMP_ENABLE_TRACE` | off in the production build |
| `SNESRECOMP_WRITE_WATCH` (WRAM write, logs PC) | `SNES_COSIM` | the exact tool for this task |
| `debug_server` `get_vram_trace` | TCP client | needs a client |
| snes9x boot trace (`BM_BOOT_TRACE`) | core patch | patch exists, core not built with it |

`tools/m1.py` now accepts two opt-in build switches, both off by default:

```
BM_DIAG_PPU_DMA_HISTORY=1   -> -DSNESRECOMP_ENABLE_PPU_DMA_HISTORY=ON
BM_DIAG_CPU_TRACE=1         -> -DSNESRECOMP_ENABLE_TRACE=ON
```

`local/upstream/snesrecomp` is a pinned checkout. `m1.py` rejects a build when a
tracked file in it changes, so a runtime change must go through the per-target
runtime patch, which today covers `snes/cart.c` only.

The snes9x reference core does not include
`patches/diagnostics/snes9x-boot-trace.patch`, so `BM_BOOT_TRACE` writes no file.

### Next actions

1. Extend the per-target runtime patch to log ROM reads in `cart_getRomPtr` for a
   frame window, then read the address range that feeds the Mode 7 image.
2. Or rebuild `snesref` with the boot trace patch and trace the mazo image.

## ROM read trace (working)

`tools/m1.py` can inject a read trace into the per-target `cart.c` copy. It is
off by default and needs no change to the pinned upstream tree.

```
BM_DIAG_ROM_TRACE=1 python3 tools/m1.py --target <t> build
BM_ROM_TRACE_LOG=/tmp/rom.log python3 tools/m1.py --target <t> native ...
```

Each line is `frame offset`, written once per distinct ROM address.

A differential run compares two captures: one that enters room `190`, and one
that stops at the map. Addresses that only the room `190` run reads are the
room load set. The largest runs on the product:

| ROM range | Size |
| --- | ---: |
| `0x230008`-`0x2317FF` | 6136 |
| `0x35A157`-`0x35AF74` | 3614 |
| `0x3D0F8B`-`0x3D1C9A` | 3344 |
| `0x05CF33`-`0x05DAC0` | 2958 |
| `0x14DF58`-`0x14E678` | 1825 |

A probe copied the mazo bytes into the three largest ranges. The game then
shows a black frame, because those ranges hold code as well as data. A range
copy is not usable without separating code reads from data reads.

Probe target: `demo11-native-rtprobe`.

Next: restrict the trace to the level load frame window. The level load burst
was around frame 2210, so a window there separates the load from the steady
state.

### Trace check

The room `190` capture reads 211,549 distinct ROM addresses. The load burst is
frame `2750` with 2006 first reads. Its largest run is one contiguous block:

| ROM range | Size | Bank |
| --- | ---: | --- |
| `0x1B0008`-`0x1B09D1` | 2506 | `0x36` |
| `0x0F74BD`-`0x0F7882` | 966 | `0x1E` |
| `0x0F7B0D`-`0x0F7C1D` | 273 | `0x1E` |

The `0x1B0008` block is the `1E6` graphics stream, which the `1E6` candidate
placed at that address. It decodes with LZ2 to 4096 bytes.

So the trace identifies a graphics stream and its reader. That is the check the
tool needed.

The bank `0x1E` runs do not decode from their first byte, so the run start is
inside a stream that an earlier frame already started. The next step is to read
the stream start, then decode each stream in the window and compare its size with
the Mode 7 area.

## Read holes

The read trace gives a stronger check. A read hole is a ROM range that the game
reads, holds zeros in the product, and holds data in mazo. The `1E6` stream is one
such hole, so the method has a known positive case.

The room `190` run gives 29 holes of 64 bytes or more:

| ROM range | Size | mazo bytes |
| --- | ---: | ---: |
| `0x1B0008` | 2506 | 2344 |
| `0x23174E` | 178 | 148 |
| `0x1BCD9B` | 149 | 122 |
| `0x1BC5A4` | 136 | 122 |
| `0x078089` | 131 | 99 |

The first row is the `1E6` stream. So the largest read hole is the one that is
already known.

### Bulk fill does not work

Candidate `demo11-native-holes` copies mazo data into 26 of these holes. The game
then shows a black frame. Some zero ranges are deliberate, and the loader uses
them.

The corridor entry gives the same hole set, so the room change adds no graphics
read. A Mode 7 background needs 16384 bytes of tilemap and 32768 bytes of
character data. No read of that size occurs.

Conclusion: the game never starts a Mode 7 graphics load for room `190`. The
missing content is not a hole that the loader reaches.

## Room-scoped VRAM patch

`tools/m1.py` can inject a VRAM loader into the per-target `cart.c` copy. The
switch is `BM_DIAG_VRAM_PATCH=1`, and the loader reads the file named by
`BM_VRAM_PATCH` when the game enters room `0x0190`.

```
BM_DIAG_VRAM_PATCH=1 python3 tools/m1.py --target <t> build
BM_VRAM_PATCH=<pack> python3 tools/m1.py --target <t> native ...
```

The pack holds a run-length form of a VRAM word image. The loader reads the room
number from work RAM `$10B` and `$10C` and writes `g_snes->ppu->vram`.

### Result

A pack built from the mazo room `190` VRAM changes the frame. The clouds of the
sunset appear, and the boss faces render.

So the patch works, and part of the missing image was VRAM content.

### The remaining fault is not in VRAM

A second pack covers all 65536 bytes of the mazo VRAM image. The frame does not
change from the partial pack. The vertical lines stay.

With the whole VRAM equal to mazo, the product still draws lines where mazo draws
a sunset. The Mode 7 matrix is valid (`A` `42`, `D` `256`, `m7sel` `0x80`).

Conclusion: the remaining fault is in the native Mode 7 background path, not in
the content. Content porting cannot correct it.

Next: compare the native Mode 7 line renderer with the hardware rule. The file is
`runner/src/snes/ppu.c`, function `PpuDrawMode7HdLine` and the default path.

### The matrix changes every frame

The product holds `A` `42` and `D` `256` in room `190`. `A` `42` is a six times
zoom on the horizontal axis.

The loader now also sets `A` and `D` to `256` when it loads the pack. The frame
does not change. The game writes the matrix again on the next frame, usually
through HDMA.

So an outside write cannot hold the matrix. A correction needs a change in the
PPU register path, not a one-time write.

A second point weakens the comparison with mazo. The mazo capture of room `190`
sits in mode `0x0E`, a scene mode. The product sits in mode `0x14`, normal play.
Two different scenes can show two different backgrounds.

## Correction: the gameplay frame of room 190

Fixture `recomp/inputs/mazo-190-steady-fixture.script` waits past the load phase
and samples eight later frames.

| Tag | Mode | Room | Translevel |
| --- | --- | --- | --- |
| `e0` | `0x14` | `0x190` | `0x30` |
| `e1` | `0x0C` | `0x190` | `0x30` |
| `e2`..`e7` | `0x0E` | `0x190` | `0x30` |

Frame `e0` is normal play. It shows a dark blue textured field and the player.
It has no boss, no sunset, and no ground.

All earlier comparisons used a mode `0x0E` frame. That frame is a scene, and it
holds the sunset and the boss.

So the target for normal play is the plain dark field, not the sunset. The
earlier target was wrong.

The product frame holds the sunset colours, the boss and the line pattern in mode
`0x14`. It should hold the plain field.

## Room 191 is an illustration

Room `191` in mode `0x14` shows a still picture in mazo. The picture holds a
landscape with cliffs, two waterfalls, green fields and a black machine. A text
line sits above it.

The product shows a black frame with a grid of small marks in place of the
picture. The frame edges are correct, so the tilemap loads and the character data
does not.

The entrance view of room `191` is correct in the product: sky, brick ground,
blocks, pipes and enemies all render. The fault starts where the picture frame
appears.

| View | Product | Mazo |
| --- | --- | --- |
| Entrance | correct | correct |
| Picture area | black frame and grid | full illustration |

A read trace of the room gives 33 holes, and the set matches the room `190` set.
The illustration data is not in a read hole, so the loader does not reach it.

Captures: `local/captures/w191` (product), `local/captures/mazo-191-donor`
(reference).

## All three rooms share one Layer 3 index

The Layer 2 pointers of rooms `190`, `191` and `192` are the sentinel `FFDE54` in
both ROMs. The low byte of the sentinel names the Layer 3 index, `0x54`.

| Room | L2 pointer | Layer 3 index |
| --- | --- | --- |
| `0x190` | `FFDE54` | `0x54` |
| `0x191` | `FFDE54` | `0x54` |
| `0x192` | `FFDE54` | `0x54` |

The room graphics records are also equal, and every slot is the default `FFFF`.

So one Layer 3 image serves all three rooms. It is the Mode 7 background of room
`190` and the illustration of room `191`.

This gives one target for the next step. Find the table that maps Layer 3
index `0x54` to its data. Then compare the data of the two ROMs.

A scan for a pointer table with 256 entries gives 13949 candidates. A plain
valid pointer test does not isolate the table. The next check needs the loader
code, not a data scan.

## Layer 3 draws and its characters are absent

Room `191` runs in mode `1` with `tm` `0x15`. That byte turns on BG1, BG3 and
objects. `ts` `0x2` turns on BG3 for the sub screen, so layer 3 draws.

The frame outline of the picture is correct on screen. The inside of the frame is
a grid of small marks. A correct tilemap with absent characters gives exactly
that result.

| Item | State |
| --- | --- |
| Layer 3 enable bit | set |
| Layer 3 tilemap | correct, the frame edges show |
| Layer 3 characters | absent, the inside is a grid |

A C write to `ppu->vram` changes the frame for room `191`, so the patch writes
the array that the renderer reads. The patch now takes a room number from `BM_VRAM_PATCH_ROOM`.

A pack built from the mazo room `191` frame gives a noisy frame, not the picture.
The mazo capture comes from another scene state, so its register set and its
VRAM do not pair with the product state.

### Capture labels to check first

The capture directory `local/captures/mazo-191-donor` does not hold room `191`.
Every frame in it reports mode `0x0E` and room `0x190`.

So the illustration in those frames is the room `190` scene, and not a room `191`
reference. A reader who trusts the directory name will compare two scenes.

The same check applies to any older capture. Read the mode and room from the work
RAM dump before a comparison.

### Room 192 repeats the room 191 frame

Room `192` renders the same black frame with a grid of small marks. Its registers
match room `191`: mode `1`, `tm` `0x15`, `ts` `0x2`.

| Room | Mode | `tm` | `ts` | Frame |
| --- | --- | --- | --- | --- |
| `0x191` | `1` | `0x15` | `0x2` | black frame, grid inside |
| `0x192` | `1` | `0x15` | `0x2` | black frame, grid inside |

So one Layer 3 image fails for rooms `190`, `191` and `192`. One change
serves all three rooms.

Capture: `local/captures/r192`.

### Layer 3 address estimate

Room `192` reports `BG3SC` `0x53` and a tile address of `1024` words. The usual
rule gives these VRAM positions:

| Item | Value |
| --- | --- |
| Layer 3 tilemap base | VRAM byte `0xA000` |
| Layer 3 character base | VRAM byte `0x0800` |

Content check on the room `192` frame:

| Region | Unique bytes | Zero bytes |
| --- | ---: | ---: |
| characters `0x0800` | 187 | 1871 of 4096 |
| tilemap `0xA000` | 31 | 2 of 8192 |

The tilemap holds data, and the character area is 46 percent zero. That ratio
agrees with a correct map over absent characters.

A patch that writes only the character range `0x0800`-`0x1800` leaves the frame
unchanged. So the visible box does not read its characters from that range, and
the estimate is wrong for this room.

## The product does not carry the 1E6 stream

The product ROM holds 2506 zero bytes at `0x1B0008`. The `1E6` candidate holds
data there. The two configs differ by exactly two patches:

- `mazo extended gfx 1E6 stream`
- `extended gfx 1E6 pointer`

Both configs share the base `demo11-native-sprite9e`. So the two patches move the
product to the `1E6` image without other change.

### Promotion needs a new target

`write_verified` refuses to replace the product ROM, because that ROM is an
accepted baseline. A promotion must use a new target, not an edit of the product.

The verified gain is the cloud layer and the boss faces in room `190`. The line
pattern stays.

The descendant target `demo11-native-product-r2` carries the two patches. Its ROM
digest is `d7a36d90`. A capture of room `190` on that target shows the boss face,
the cloud layer and the health bar. The same capture on the product shows a
garbled boss.

| Target | Boss face | Cloud layer |
| --- | --- | --- |
| `demo11-native-product` | garbled | absent |
| `demo11-native-product-r2` | correct | present |

Run the descendant with `python3 tools/play_native_target.py --target
demo11-native-product-r2`.

## Correction: the VRAM patch does not persist

Earlier this document said that a VRAM pack made the cloud layer appear. That
claim is wrong.

A pack that writes `0xFFFF` to all 32768 VRAM words leaves the frame unchanged in
room `190` and room `192`. The captured VRAM also keeps the game data, and holds
254 distinct byte values after that run.

Two facts explain the result:

1. The write point is inside `cart_getRomPtr`, so it runs at an arbitrary point
   in the frame. The game copies its own graphics to VRAM later in the same
   frame and overwrites the pack.
2. Every pack gave the same frame. The frame changed once when the patch first
   ran, so a timing change, not the content, caused that change.

So the room-scoped VRAM pack needs a hook after the game finishes its VRAM
uploads, near the end of the frame. The current hook cannot do the task.

`g_ppu` is the same object as `g_snes->ppu` (`common_cpu_infra.c` line 1087), so
the write target was correct. The frame position was not.

## The Layer 3 map holds one tile

The estimated map region `0xA000`-`0xC000` holds 4096 words with 31 distinct
values. One word, `0x38FC`, fills 3911 of them. The next value fills 144.

`0x38FC` gives priority `0`, palette `7` and tile `0xFC`. So the visible grid is a
single repeated tile, and the map holds no picture.

A picture map holds many tile indices across its area. This map does not, so the
Layer 3 map is as absent as the characters.

The strip of equal bytes does not match any RATS block in mazo after LZ2 decode
(2305 blocks scanned).

So the whole Layer 3 image is missing, not only the character data. The loader
for index `0x54` does not run in this build.

## Layer 2 table comparison

The Layer 2 pointer can hold a sentinel. The test looks at the middle byte: a
value of `0xC0` or more marks the sentinel. A test on the whole 24 bit value is
wrong and it over-counts.

| ROM | Sentinel rooms of 512 |
| --- | ---: |
| product | 354 |
| mazo | 364 |

413 entries are equal. Rooms `190`, `191` and `192` hold `FFDE54` in both.

So the tables are close, and the three rooms do not differ. The missing Layer 3
image is not a difference in the Layer 2 pointer.

## The black frame is a message box

The user reports the visual: the red block in room `191` is a green question ball.
When the player touches it, the game prints a message, and the dragon fight starts.

So the black frame with the grid is the message window, and the grid is its text.
The report of garbled crystal ball text matches this object.

### The text data is present

A read trace covers the frames where the box appears. In the last 200 frames the
game reads 811 new addresses, and none of them points at a zero range in the
product ROM. The mazo image holds data at all of those addresses.

So the message text source is not a read hole, and a ROM fill cannot correct it.

The fault is in how the message draws, or in the tiles that the message routine
selects.

Fixtures: `recomp/inputs/mazo-191-msg-fixture.script` (room poke, labelled).
A room poke does not reload the graphics, so a capture after a poke keeps the
previous room image and cannot serve as a reference.

## Why only one read hole responded

The product build loads 45 content packs. Each pack replaces a ROM range at run
time. A check of the read holes against the pack ranges explains the mixed result:

| Address | Inside a pack | Result of a ROM fill |
| --- | --- | --- |
| `0x1B0008` | `BM_NATIVE_GRAPHICS_PACK` | works |
| `0x0F74BD` | `BM_SEVEN_CODE_PACK_32` | not tried |
| `0x23174E` | no | breaks the game |
| `0x1BCD9B` | no | breaks the game |
| `0x078089` | no | breaks the game |

So a hole inside a pack is a pack slot that needs data. A hole outside a pack is
a zero range that the game needs as zero, and a fill breaks execution.

This is the rule to follow: fill a hole only when a pack covers it.

## The natural path gives the same frame

Capture `local/captures/cheat-r184` enters room `0x190` through room `0x184`, so
the room change is the game one and not a poke. Both frames report mode `0x14`,
room `0x190`.

The frame holds the same line pattern and the same garbled boss as the poke
entry. So the entry method does not explain the frame.

Compare that with mazo in the same mode: mazo shows a plain dark field and no
boss.

| Build | Mode | Room | Frame |
| --- | --- | --- | --- |
| product, poke | `0x14` | `0x190` | line pattern, garbled boss |
| product, room `0x184` | `0x14` | `0x190` | line pattern, garbled boss |
| mazo, room poke | `0x14` | `0x190` | plain dark field |

So the fault is real and the entry path is not the cause. The target for this
mode is the plain field.

## The level context differs

A work RAM comparison at mode `0x14`, room `0x190`, room state settled:

| Variable | mazo | product |
| --- | --- | --- |
| `$0100` game mode | `14` | `14` |
| `$10B` room | `190` | `190` |
| **`$13BF` translevel** | **`30`** | **`6A`** |
| `$94` player x | `0020` | `0020` |
| `$96` player y | `FFC0` | `FFC0` |
| `$1A` layer 1 x | `00` | `00` |
| `$0D9A` `$0D9B` `$0D9D` | `37` `C1` `15` | `37` `C1` `15` |

Every value matches except the translevel. The translevel selects the level
header: tileset, background mode, palette and the Layer 3 settings.

So the product draws room `190` with the header of translevel `0x6A`, and mazo
draws it with the header of translevel `0x30`. Content porting cannot correct a
header selection.

### A room swap test

A candidate copied the mazo room `0x10C` data into the product room `0x10C` and
read it back at translevel `0x30`. The room does change, and the frame becomes a
field of blue and yellow tiles. The graphics do not match, because the level
header and the graphics context for that entry still differ.

The test is not kept as a target. It shows that the room data swap applies, and
that the header is the open item.

### Forced reload does not settle

A probe enters translevel `0x30`, writes room `0x190` to `$10B` and `$10C`, then
sets `$0100` to `0x0E` to force a level load.

The state then reports mode `0x0E`, room `0x190`, translevel `0x30`, which is the
wanted combination. The frame stays black with only the status bar, and the mode
never reaches `0x14`.

So a write to the room register is not a room change. The game needs its own
transition to load the room data and the graphics.

To test the header theory, the corridor rooms must live in the level that maps to
translevel `0x30`, and the player must walk the real transition.

## The corridor graphics are present

The room `0x10C` record in mazo starts `0100 C400 AF00`. Those two words are
extended graphics IDs `0xC4` and `0xAF`.

Both IDs exist in the product, and their data equals the mazo data byte for byte:

| ID | mazo pointer | product pointer | Data |
| --- | --- | --- | --- |
| `0xC4` | `488B2C` | `2AC686` | equal |
| `0xAF` | `46AB7C` | `28890F` | equal |

So the corridor graphics are not missing. A room swap gave a field of blue and
yellow tiles for a different reason. The entry still uses a different level
header. The room record is one input to the load, not the only one.

## A corrected room swap

The earlier room swap copied the mazo Layer 2 pointer into the product without
copying the data that the pointer names. The product then read unrelated bytes.
A second candidate copies the data as well: Layer 1, Layer 2, the sprite list and
the room record.

Level headers for index `0x30` are equal in both ROMs:

| Table | `0x05F000` | `0x05F100` | `0x05F200` | `0x05F300` | `0x05F400` | `0x05F500` | `0x05F600` | `0x05F700` | `0x05F800` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| both | `55` | `0F` | `02` | `01` | `0A` | `85` | `00` | `00` | `6A` |

The room records differ:

| Record | Bytes |
| --- | --- |
| product room `0x10C` | `0180 1600 AF00 AE00 1400 0500` |
| mazo room `0x10C` | `0100 C400 AF00 AE00 1400 6102` |

With the data copied, the entry at translevel `0x30` shows a uniform blue tile
field in room `0x10C`. A walk to the right reaches mode `0x0E` and not room
`190`.

So the room content changes, and the room change to `190` is not in the Layer 1
stream of room `0x10C`. That stream holds one object at x `0xC0`.

Capture: `local/captures/rc10b`, `local/captures/rc10w`.

### Room 0x10C holds two sprites

The sprite list of mazo room `0x10C` decodes to two entries:

| Index | y | x | Sprite id |
| --- | --- | --- | --- |
| 0 | `0x80` | `0x48` | `0x20` |
| 1 | `0xB0` | `0x38` | `0x11` |

The list then ends with x `0xFF`.

One of these sprites can start the change to room `0x190`. The layer 1 stream
holds one object at x `0xC0`, so a walk to the right does not reach it.

## Every content table matches

The level header tables of rooms `0x190`, `0x191` and `0x192` are equal in both
ROMs on all nine tables:

| Index | `0x5F000` | `0x5F100` | `0x5F200` | `0x5F300` | `0x5F400` | `0x5F500` | `0x5F600` | `0x5F700` | `0x5F800` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `0x190` | `0B` | `1A` | `00` | `0A` | `0A` | `00` | `00` | `00` | `00` |
| `0x191` | `3B` | `02` | `00` | `0A` | `0A` | `00` | `00` | `00` | `00` |
| `0x192` | `0B` | `03` | `00` | `0A` | `0A` | `00` | `00` | `00` | `00` |

With the room data of `0x190` equal, the header tables equal and the graphics
data equal, no content difference remains for room `0x190`.

### The mazo reference may be the weak side

The mazo capture used as a target came from a set of menu presses. That entry may
also keep stale graphics, in the same way a room poke does.

On that frame the player stands on nothing and the field is flat, which looks
like an incomplete draw. The product frame holds a full scene: sky band, clouds,
boss and health bar.

So the product frame is more likely the complete one, and this document cannot
treat the mazo frame as a correct target.

## A dense reference for room 190

Fixture `recomp/inputs/mazo-190-dense-fixture.script` samples room `190` every 30
frames after the entry. Tags `t0` to `t6` report mode `0x14`, room `0x190`,
translevel `0x30`. Tags `t7` to `t11` report the death modes `0x0B` and `0x0C`.

Frame `t6` is the settled normal-play frame:

- a dark blue diagonal pattern over the whole screen,
- the player at the bottom centre,
- no boss and no orange sky.

The product frame for the same mode and room holds a warm sky, vertical lines and
a boss. So the two frames differ, and the product frame is not correct.

The pattern in `t6` is a Mode 7 surface at a scale. The two builds render the
same layer with a different matrix or a different palette.

The native dump writes CGRAM (`*.cgram.bin`). The reference dump does not. So a
palette comparison across the two hosts needs a new reference dump.

## Root cause: the wrong level header index

The header tables must be read at the translevel index that each build uses, not
at the room index. The product uses `0x6A` and mazo uses `0x30`, so the comparison
is product `[0x6A]` against mazo `[0x30]`:

| Table | product `[0x6A]` | mazo `[0x30]` | Equal |
| --- | --- | --- | --- |
| `0x05F000` | `02` | `55` | no |
| `0x05F100` | `48` | `0F` | no |
| `0x05F200` | `1C` | `02` | no |
| `0x05F300` | `01` | `01` | yes |
| `0x05F400` | `0A` | `0A` | yes |
| `0x05F500` | `0A` | `85` | no |
| `0x05F600` | `00` | `00` | yes |
| `0x05F700` | `66` | `00` | no |
| `0x05F800` | `0B` | `6A` | no |

`0x05F000` carries the tileset and the palette for foreground and background. A
different value there gives a different palette for the same graphics.

### The palette agrees

Colour counts from the two frames:

| Frame | Distinct colours | Main colours |
| --- | ---: | --- |
| mazo `t6` | 9 | `(41,40,90)`, `(41,40,107)`, `(41,24,90)` |
| product room `190` | 85 | `(66,0,132)`, `(255,222,115)`, `(206,214,239)` |
| Shared | 2 | black and the player green |

mazo draws a dark blue night field. The product draws a warm sky with purple and
orange. The two frames share no background colour.

So the graphics are equal, the room data is equal, and the level header index is
the only difference. The product is not missing content. It selects another
level.

### The change to make

The corridor rooms must run under the level whose translevel is `0x30`. The
correct change is a map node or an entry that sets translevel `0x30`, then a walk
through the real room change.

## Correction: the reference frame is a death effect

The user reports that frame `t6` is the death effect that plays when the health
runs out. The dark blue swirl and the lone player are the drop-out animation.

So that frame is not a normal play frame, and this document must not use it as a
target.

The fixture leaves the player standing still. The health then drops to zero, and
the after-death frames follow. Every mazo capture of room `190` in mode `0x14`
reaches that state within a few hundred frames.

| Frame | State |
| --- | --- |
| `t0` to `t6` | mode `0x14`, already the death sequence |
| `t7` to `t11` | modes `0x0B` and `0x0C` |

### What follows

The product frame of room `190` holds a warm sky, a cloud layer, the boss and the
health bar. A boss battle level with a given background can look like that.

So this document cannot state that room `190` renders wrong. It has no valid mazo
frame of normal play in that room.

The colour difference between the two frames is also explained: one frame is a
death effect and the other is the level.

## The background is correct apart from thin lines

The user supplied a reference frame of room 190. It shows a smooth sky that runs
from purple to red to orange, with orange clouds, the boss heads and a textured
floor.

The product frame holds the same sky, the same clouds, the same boss and the same
floor. The only extra element is a set of thin vertical lines over the sky.

| Element | Reference | Product |
| --- | --- | --- |
| Sky gradient | present | present |
| Clouds | present | present |
| Boss and health bar | present | present |
| Thin vertical lines | absent | present |

So the tile graphics, the palette and the tile map agree. A thin line over a
smooth field is a sampling fault, not absent content.

The Mode 7 path in runner/src/snes/ppu.c draws one sample per screen column. A
wrong scale step, or a wrap at a column edge, gives one line per step.

### Extended graphics slots

Three extended graphics slots hold a null pointer in the product and a valid
pointer in mazo: 0x0BE, 0x0D9 and 0x0DA. A candidate that fills all three changes
no pixel of room 190 and no pixel of room 191.

## The message is Japanese and the font is absent

The user supplied a frame of the working message window. It shows two lines of
Japanese text on black:

   ゴールした そのなかに
   モンスターが ？

So the window must draw a Japanese font. The product draws a repeat of two or
three small shapes instead, and those shapes are level artwork.

### What the font is not

- The base graphics set 0x00 to 0x31 decodes to the same data in both ROMs.
- Extended graphics 0x0BE, 0x0D9 and 0x0DA hold a null pointer in the product. A
  candidate that fills all three changes no pixel of room 190 and no pixel of
  room 191.
- No font block loads when the window opens. The largest new read in that window
  is 73 bytes in bank 00.

So the font must be in VRAM before the window opens, and this build does not put
it there.

### What follows

The next check is the graphics set that the message routine expects, and the
level load that should place it in VRAM. A comparison needs a mazo capture of the
window with fresh graphics, and this document does not have one.

### The reference frame is from mazo

The user confirms the correct message window frame comes from mazo. So mazo holds
a Japanese font for the window, and this build does not.

### Searches that found nothing

| Search | Result |
| --- | --- |
| Base graphics 0x00 to 0x31, decoded | equal in both ROMs |
| Extended graphics 0x0BE, 0x0D9, 0x0DA | a fill changes no pixel |
| Glyph tile bytes taken from the reference frame | no match in either ROM |
| The same bytes in 2305 decoded RATS blocks of mazo | no match |

The glyph bytes come from a screen capture, so the alignment of the grid and the
colour to bit mapping are estimates. A miss does not prove that the font is
absent from a RATS block.

### The reliable next step

A mazo capture of the message window with fresh graphics gives the correct VRAM
image. The product frame and that image then show the font tiles directly. The
open question is the route that reaches the window in mazo.

### Room 190 needs real play

A fixture holds star invincibility through room 190. The star timer reads 0x40,
and the player still leaves normal play: the mode goes 0x14, then 0x0B, then 0x0D,
then 0x0E.

So the death is a fall, not damage, and star power does not stop it. A script that
sends no input cannot stay alive in that room.

The route to room 191 is therefore a real play route, and no fixture in this
document reaches it.

Fixture: recomp/inputs/mazo-190-invincible-fixture.script (labelled, star hold).

### Live room 190 frames in mazo

A fixture holds star power and forced water physics from the first frame of room
190. The mode then stays at 0x14 from t1 to t13, which is about 390 frames, and
the room is 0x190 throughout.

Frame t10, still mode 0x14, shows the same dark blue diagonal field as the earlier
frame. The player is at the bottom centre.

So that field is what mazo draws in room 190 while the player is alive, and not
only in the death sequence.

This does not agree with the reference frame of the boss battle, which shows a
warm sky. Either the two frames come from different rooms, or the entry in this
fixture is not the same scene.

Fixture: recomp/inputs/mazo-190-hold-fixture.script (labelled, star and water hold).

## A live mazo reference for room 190

The boss health bar sits at work RAM 0x1FFE0 to 0x1FFF0 in the product build, and
the mazo build keeps its own copy elsewhere. A search over the frames of a fight
finds the bytes that fall as the bar empties:

| Address | Value at entry | Value before death |
| --- | --- | --- |
| 0x0D85 | 64 | 0 |
| 0x0D8F | 64 | 0 |
| 0x0381 | 72 | 10 |
| 0x01DF | 72 | 10 |

A fixture writes those bytes back every 30 frames. The player then stays in mode
0x14, room 0x190, for more than 720 frames.

Frame h24 shows the room in normal play:

- a clean sky that runs from purple to red to orange,
- orange clouds,
- the black boss,
- a blue textured floor.

It holds no vertical lines. The product frame for the same room holds the same
elements and the same colours, with a set of thin vertical lines over the sky.

So both frames come from the same scene, and the product adds the lines.

Fixture: recomp/inputs/mazo-190-hplock-fixture.script (labelled, health lock).
Capture: local/captures/mhp. Image: local/reports/screenshots/room190-mazo-live.png.

### The room scoped VRAM pack now applies

The pack writes inside cart_getRomPtr while the room number holds. A pack of the
whole mazo VRAM now changes the frame for room 190, so the write does reach the
renderer.

| Pack | Content | Frame |
| --- | --- | --- |
| whole mazo image | 15900 runs | changed, mixed |
| Mode 7 range only, bytes 0x0000 to 0x3FFF | 3483 runs | the sky changes, the lines stay |

So the sky area of this room reads VRAM bytes 0x0000 to 0x3FFF. In Mode 7 that
range holds the map and the character data in the same words, so one pack cannot
replace the map alone.

| Region | Product | Mazo |
| --- | --- | --- |
| distinct bytes, 0x0000 to 0x3FFF | 105 | 105 |
| row 0 leading values | 10, 11 | 0, 3 |

The two maps hold different tile numbers, and the frames agree on every element
except the lines. The next check compares one region at a time, starting with the
lowest quarter.

### The Mode 7 map differs

Both frames hold a simple map, so the count of distinct tiles per row is close:
3.1 for the product and 3.3 for mazo. The values differ.

| Build | Most used tiles |
| --- | --- |
| product | 16, 0, 15, 31, 26 |
| mazo | 16, 0, 9, 7, 5 |

Rows 3 and 4 of the product map repeat 0 and 15 in a short cycle:

    product row 3: 0 0 15 0 0 15 0 15 0 0 15 0 0 15 0 15

The mazo rows carry a long run of different values:

    mazo row 3: 0 3 9 5 7 12 12 12 0 4 9 7 12 11 11 11

A short cycle of two tile numbers over a sky gives one line per cycle. A long run
of decreasing numbers gives a smooth field.

So the product map holds a stepped pattern where mazo holds a gradient. The next
step is the source of that map in the level data, and why the two builds build a
different map from equal level data.
