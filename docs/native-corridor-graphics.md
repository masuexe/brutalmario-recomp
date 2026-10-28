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

## Fix plan

1. Choose a free Map16 bank and a free ExGFX slot.
2. Copy the mazo Map16 set for tileset `0B` and tileset `3B` into that bank.
3. Add lookup shims that apply only while a corridor or boss room runs.
4. Copy the mazo background and ExGFX streams that room `190` uses.
5. Capture rooms `183`, `184`, `190`, `191` and `192` and compare each frame
   to the donor frame.

Step 4 is the large part. Map16 is `0x800` entries of eight bytes for each
tileset.

## Tools

`tools/fb_to_png.py` converts a host framebuffer BMP dump to a PNG image.
Use it to look at a capture frame.

```sh
python3 tools/fb_to_png.py local/captures/view-r190/f1.fb.bmp /tmp/r190.png 2
```

Captures for this report: `local/captures/cheat-r191`,
`local/captures/view-r192`, `local/captures/view-r190`.