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

This gives one target for the next step: find the table that maps Layer 3 index
`0x54` to its data, then compare the data of the two ROMs.

A scan for a pointer table with 256 entries gives 13949 candidates. A plain
valid pointer test does not isolate the table. The next check needs the loader
code, not a data scan.

## Layer 3 is enabled and its characters are absent

Room `191` runs in mode `1` with `tm` `0x15`. That byte enables BG1, BG3 and
objects, and `ts` `0x2` enables BG3 on the sub screen. So the Layer 3 layer is on.

The frame outline of the picture is correct on screen. The inside of the frame is
a grid of small marks. A correct tilemap with absent characters gives exactly
that result.

| Item | State |
| --- | --- |
| Layer 3 enable bit | set |
| Layer 3 tilemap | correct, the frame edges show |
| Layer 3 characters | absent, the inside is a grid |

The VRAM patch confirms that a C write to `ppu->vram` changes the frame for room
`191`. The patch now takes a room number from `BM_VRAM_PATCH_ROOM`.

A pack built from the mazo room `191` frame gives a noisy frame, not the picture.
The mazo capture comes from another scene state, so its register set and its
VRAM do not pair with the product state.

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