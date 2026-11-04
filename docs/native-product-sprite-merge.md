# Product sprite merge, seven reviewed records

## Result

Product r20 adds seven reviewed custom sprite records to product r19. The
placement census on r20 lists seven placeholder slots. The parent lists
fourteen.

| Item | Value |
| --- | --- |
| Target | `demo11-native-product-r20` |
| Parent | `demo11-native-product-r19` |
| ROM | `f4185fe22f57c66c338b800bbe423dcd915860c87cc2ec395baa7236cad5e567` |
| Binary | `786e7058c8a03a0da6a28e6f2ade4d4b2f6f75146e37c26b3bcc04f6f3d40f47` |
| Config | `bb68843201bad0e7ec716ebb567ae5a18868ca0618a4dc654e68a4aa943ea4e1` |
| Census report | `d75c6b48161cfdba94c46c4dc31e48373f536564e5507cbc00db9bcb7369d700` |
| Qualification report | `6bd160596efaf1df34e39092e9f389ce90cc77fe34269ba2f96b46e057038617` |

The merge does not port new code. Each record has a reviewed recipe on an
isolated sprite line. The merge moves those recipes onto the product image.

## Selected records

| Slot | Rooms | Recipe | Code view | Source line |
| --- | --- | --- | --- | --- |
| `25` | `154` | `sprite25-boss-product-module` | `8F:AB9D` | Boss |
| `33` | `0FE` | `sprite33-boss-product-module` | `8E:ADFE` | Boss |
| `94` | `0EF` | `sprite94-boss-product-module` | `8D:B34D` | Boss |
| `97` | `1EF` | `sprite97-modern-module` | `8C:A52A` | ow |
| `99` | `174`, `175`, `176` | `sprite99-modern-module` | `8B:A6FC` | demoOnly1 |
| `A1` | `175`, `176`, `178` | raw pack `BM_NATIVE_SPRITE_A1_PACK` | `8A:88EB` | demoOnly1 |
| `C2` | `170` | `type3-c2-boss-lowmirror` | `91:DD21` | Boss |

The C2 record also mounts the reviewed adapter at `92:8000`. The adapter
changes two C2 limits to C3 and the exclusive shooter limit to 33. C0 and C1
keep B0 and B1.

Slot `A1` uses a raw protected block. Its record patch is one of the two
extra patches. Slot `97` also uses an extra patch for its record.

## Construction

`tools/prepare_product_sprite_merge.py` builds the image. The tool:

1. copies the r19 pack list and marks the inherited recipes as frozen;
2. appends the seven new recipes;
3. applies the two record patches;
4. verifies every patch against the expected bytes;
5. copies the inherited music region pack.

The frozen recipes still mount their packs. The shared preparer skips their
record patches, because the parent image already holds the records.

The r20 target mounts 56 packs. The music layer, the room layouts, the hooks
and the 61 inherited patches do not change.

## Runtime evidence

Each capture uses one room-entry fixture. The parent capture uses the same
fixture and script.

| Room/slot | Parent | r20 |
| --- | --- | --- |
| `154`/`25` | no actor | actor rises from Y 232 to 182 at X 208 |
| `0EF`/`94` | no actor | two actors; the second moves from Y 224 to 320 |
| `0FE`/`33` | no actor | actor moves from X 208 to 133 at Y 368 |
| `174`/`99` | no actor | static actor at X 130, Y 320 |
| `175`/`99` | no actor | three actors at X 290/207/143, Y 287/306/338 |
| `175`/`A1` | no actor | actor at X 64, Y 256 |
| `176`/`A1` | no actor | actor moves from X 64 to 369; absent at frame 512 |
| `178`/`A1` | no actor | Y 271 to 146 at frame 128, then 271 at frame 256 |
| `1EF`/`97` | no actor | static actor at X 192, Y 368 |
| `170`/`C2` | no generated actor | two generated actors with state 15 at X 353/373 |

The room 174 fixture needs `BM_SEVEN_RETURN=0`. The Seven return hook moves
room 174 to the overworld. Without the setting, the fixture never reaches
gameplay.

## Rendering check

The checker compares the framebuffer and the VRAM of each candidate sample
with the same sample of the parent.

| Room/slot | Framebuffer pixels | VRAM bytes |
| --- | ---: | ---: |
| `154`/`25` | 116,267 | 20,222 |
| `0EF`/`94` | 7,893 | 186 |
| `0FE`/`33` | 81,859 | 1,079 |
| `174`/`99` | 0 | 4 |
| `175`/`99` | 149 | 3,609 |
| `176`/`A1` | 99,662 | 2,415 |
| `178`/`A1` | 60,650 | 4,632 |
| `1EF`/`97` | 1,643 | 197 |

Slots `25`, `33`, `94`, `97` and `A1` change the frame. Slot `99` runs in
WRAM but its drawing stays wrong. Room `174` keeps an identical frame.
Room `175` changes 149 pixels only. The sprite tiles of slot `99` do not
change in VRAM, so the graphics for this slot stay open.

This check is a frame delta, not a visual match. The donor frame is not
compared pixel by pixel.

## Remaining placeholders

Seven slots stay placeholders: `96`, `A5`, `A6`, `E8`, `E9`, `EA`
and `F5`. Every supplied official image holds the default record in these
slots. Their rooms match the Demo 1-1 layout. Do not install a program.

## Limits

- The captures use assisted room entry and immunity fixtures. They do not
  prove a normal route, a boss fight or a course clear.
- The merge checks frame deltas only. Slot `99` does not change the frame in
  room `174`, so its graphics stay open.
- The `99` position offsets and the missing `99` actor in room 176 remain
  open from the modern sprite line.
- The C2 check reads generated actors in room 170 only. The `16B` shooter
  phases remain open.
- Product r20 is not a release. The accepted product line stays at r19 until
  a user check.

## Reproduction

```sh
python3 tools/prepare_product_sprite_merge.py
python3 tools/audit_native_sprite_placements.py \
  --target demo11-native-product-r20 \
  --output local/reports/product-r20-sprite-census.json
python3 tools/m1.py scaffold --target demo11-native-product-r20
python3 tools/m1.py generate --target demo11-native-product-r20
python3 tools/m1.py build --target demo11-native-product-r20
BM_SEVEN_RETURN=0 python3 tools/m1.py native --target demo11-native-product-r20 \
  --script local/probes/modern-sprites-pilot-v1/native-174.script \
  --capture product-r20-room174-native-v2
python3 tools/qualify_product_sprite_merge.py \
  --output local/reports/product-r20-sprite-merge.json
python3 -m unittest tests.test_product_sprite_merge
```

The qualification tool reads these captures:

- `product-r20-room154-native-v1`, `product-r19-room154-control-v1`
- `product-r20-room0EF-native-v1`, `product-r19-room0EF-control-v1`
- `product-r20-room0FE-native-v1`, `product-r19-room0FE-control-v1`
- `product-r20-room174-native-v2`, `product-r19-room174-control-v2`
- `product-r20-room175-native-v1`, `product-r19-room175-control-v1`
- `product-r20-room176-native-v1`, `product-r19-room176-control-v1`
- `product-r20-room178-native-v1`, `product-r19-room178-control-v1`
- `product-r20-route1EF-native-v1`, `product-r19-route1EF-control-v1`
- `product-r20-room170-native-v1`, `product-r19-room170-control-v2`

## Room recheck list

`local/r19-sprite-recheck.md` joins the user room notes from
`local/wrongmusiclist.md` with the r19 census. It classifies each note. The
user notes confirm the `99` and `A1` defects in rooms 174 and 178.
