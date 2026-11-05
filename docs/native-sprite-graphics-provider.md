# External sprite graphics provider

## Result

Product r21 mounts the external sprite graphics provider. One reviewed pack
writes the donor sprite VRAM into the candidate when the game enters room
`175`. The image bytes do not change.

| Item | Value |
| --- | --- |
| Target | `demo11-native-product-r21` |
| Parent | `demo11-native-product-r20` |
| ROM | `f4185fe22f57c66c338b800bbe423dcd915860c87cc2ec395baa7236cad5e567` |
| Binary | `dd91a960667d7f0b2910b430771e5301a0d08ad7f5c6214606e880319fcc4460` |
| Config | `6e23e1714bd64d32d14b9476ae0165a92fd99d79bd155fcdecd64359f55084e9` |
| Manifest | `f9bfae7b1827803a1dabedf1b0f7f48062e1d12aa8d7d19d426a2e7877f8665b` |
| Pack | 16,392 bytes, `58ee028b92d17b340abf052386de3ea2c3369f17c37d55b0c8580ac737a9dd82` |
| Qualification | `cd858a9c8ba7d1426f2c25c318cb40aef895bad7e35b831272280a31b698df15` |

The ROM SHA-256 equals the r20 ROM SHA-256. The provider is a runtime feature,
not an image change.

## Mechanism

| Part | File | Role |
| --- | --- | --- |
| Pack builder | `tools/prepare_sprite_graphics_pack.py` | Turns a reviewed VRAM capture into a pack |
| Manifest review | `tools/native_sprite_graphics.py` | Validates the manifest, writes the header |
| Runtime | `recomp/native_sprite_graphics.c` | Mounts the packs, writes the ranges |
| Cartridge patch | `tools/patch_sprite_graphics.py` | Adds the mount and the tick call |

The runtime mounts every pack at content load. It reads one byte of room state
per frame. When the game is in gameplay mode and enters a room that the
manifest names, it writes the reviewed VRAM range. A room that the manifest
does not name is never written.

A manifest can set `persist`. The runtime then rewrites the range on every
frame of the named room, because the game can re-upload part of that range
while the room runs. Without `persist` the runtime writes the range once per
room entry.

The pack holds a range count and, for each range, a word address, a word count
and the words. The manifest holds the size, the SHA-256, the slot, the room
list and the persist flag.

## Range selection

The first pilot used the object character range with a single write at room
entry. That write did not survive the room, and the picture did not change.

The donor draws the three yellow platforms with object tiles `168` to `170`,
and the candidate holds identical bytes at those tile addresses. The tile
bytes were therefore not the cause.

The reviewed range is words `0x6000..0x7FFF`, which is the object character
area that the platform sprites read. The provider writes that range on every
frame of room `175`, and the platforms appear.

## Qualification

| Check | Result |
| --- | --- |
| Pack size and SHA-256 | Match the manifest |
| Applied count in room `175` | 514 frames |
| Applied count in room `154` | 0 |
| Candidate VRAM inside the range, against the donor | 16 bytes differ |
| Candidate VRAM inside the range, against the parent | 196 bytes differ |
| Candidate VRAM outside the range, against the parent | 0 bytes differ |
| Parent VRAM inside the range, against the donor | 212 bytes differ |
| Yellow platform pixels, donor | 570 |
| Yellow platform pixels, candidate | 570 |
| Yellow platform pixels, parent | 38 |
| Room `154` VRAM, against the parent | Identical |

The provider delivers the reviewed range with a room scope and no spill. The
platform art appears, and its pixel count matches the donor.

## Frame result

The candidate frame is not identical to the parent frame. The platform
region is the main change, and the platform pixel count now matches the
donor.

The remaining difference is not the platform art. The candidate and the donor
hold the same sprite entries, the same object tiles and the same palette.
The remaining candidates are the object attribute table timing and the object
priority against the background layers.

## Limits

- One pack exists. It covers room `175` only.
- The pack holds 16,392 bytes for one room. A product pack needs a review of
  the bytes it shares with other rooms.
- The provider writes after the room starts. A later game upload can
  overwrite the range; `persist` rewrites it every frame.
- The qualification uses assisted room entry. It is not a route or a clear.
- The frame difference stays open.

## Reproduction

```sh
python3 tools/prepare_sprite_graphics_pack.py --slot 175 --id sprite-graphics-175-obj \
  --donor demo-only-1 --capture donor175-native-oam-v2 --frame f512 \
  --ranges 6000:2000 --rooms 175 \
  --scope 'Object character range for room 175.' \
  --manifest config/native-content/sprite-graphics-175-obj.json \
  --output-directory local/native-modules/sprite-graphics-175-obj
python3 tools/prepare_product_sprite_graphics.py
python3 tools/m1.py build --target demo11-native-product-r21
python3 tools/m1.py native --target demo11-native-product-r21 \
  --script recomp/inputs/native-modern-175.script \
  --capture product-r21-room175-obj-v2
python3 tools/qualify_sprite_graphics_packs.py \
  --output local/reports/product-r21-sprite-graphics.json
python3 -m unittest tests.test_sprite_graphics_packs
```

## Next work

1. Explain the remaining frame difference with the object attribute timing.
2. Review the bytes that the pack shares with other rooms before a product
   promotion.
3. Add a pack per slot that needs graphics.
