# Room 190 Mode 7 background recovery

## Result

`demo11-native-product-r3` restores the missing mazo background resource `1E5`.
The vertical stripes disappear. The sky gradient, clouds, boss face and health
bar render together. The accepted product and r2 remain intact. The user reports
that r2 is fully playable apart from the background; this report qualifies the
r3 graphics repair, not a complete earned fight or saved completion.

## Cause and correction to the previous handoff

Mode 7 uses the **low** byte of each VRAM word as its tilemap and the **high**
byte as its character pixels. See `PpuDrawBackground_mode7` in the pinned
runtime source. The previous handoff reversed these roles. Comparing r2 `q1`
with mazo `h24` gives **16,384 equal map bytes**, but only 7,474 equal pixel
bytes. There is no evidence of a different map source.

A dense, explicitly assisted practice-transfer capture (`takeover-r2-load`)
shows sequential CPU writes to the character lane during room load. The
instruction trace at frames 2688–2691 (`takeover-r2-pc2`, local trace
`local/probes/corridor-takeover/load-pc.csv`) identifies code `9E:FC77–FCF4`,
inside the immutable mazo 9B module. Its setup writes `01E5` to `$7F:FF90`
and calls `$0F:F780`. It then converts the decoded graphics at `$7E:AD00`
into Mode 7 pixels through `$2119`. The mazo donor code is at `1E:FCxx`.

The r2 `1E5` pointer is `FFFFFF`. The previous `1E6` repair fixes the boss face
but leaves this separate background request empty. No renderer or gameplay
code change is needed.

## Reviewed resource recipe

- Donor: official mazo ROM SHA-256
  `94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1`.
- Source compressed stream: `$31:EAEC`, 1,545 bytes, SHA-256
  `9beea9998d0fe150fc78018d305433b8a05e32181ad8f80ea1a4cdfb6728f7f3`.
- Decoded: 4,096 bytes, SHA-256
  `82574d4347552ff5e14e907c74b0044fb3e130d98d5509fe830d28ef483902bf`.
- Destination: file `0x108008`, CPU `$21:8008`; the bounded all-zero allocation
  passes the existing RATS overlap guard. The pointer is `08 80 21` at file
  `0x0A02B7`. Bank `21` is read directly; the independent `A1` code pack retains
  its own mapping.
- Recipe: `config/restorations/demo11-native-product-r3.json`, the complete r2
  recipe plus only this stream and pointer. No other bytes change.
- Output ROM SHA-256:
  `3c36c27984e9660b2454c0ddf94a4a9b2881a0c78f5637462ef470cdb3b4f76d`.

## Verification

`tools/qualify_corridor_background.py` checks the pinned donor, decoded stream,
allocation, exact two-window delta from r2, room/mode, both Mode 7 lanes and
native/interpreter framebuffer agreement. Its report retains the complete
capture receipts, their hashes, dump hashes and frame numbers.

- Fresh native: `local/captures/takeover-r3-190/q1`.
- Fresh interpreter: `local/captures/takeover-r3-190-interp/q1`.
- Historical donor, reused with its original identities:
  `local/captures/mhp/h24`, a labelled health-lock fixture.
- Native/interpreter: all 65,536 VRAM bytes and the framebuffer match.
- Native/donor: all 16,384 map bytes and all 16,384 character bytes match.
  Different ROMs and entry fixtures mean this is resource agreement, not
  same-image parity or complete fight timing parity.
- Unchanged room 191 regression: five active-room samples (`w1`–`w5`)
  are byte-identical between fresh r2/r3 captures for WRAM, VRAM, CGRAM, OAM
  and framebuffer (25 file comparisons). Receipts and hashes are retained in
  `local/reports/corridor-background-r3-regression.json`.
- Full unit suite: **313 tests pass** (`local/probes/corridor-takeover/unit-tests.log`).
- Visual inspection: `local/probes/corridor-takeover/r3.png` has a smooth sky
  without the old repeated vertical lines.

The tracked practice script uses an overworld override and forced pipe action;
it does not qualify ordinary traversal. Rooms 191/192 still need the Japanese
message font. No acceptance is claimed for that separate defect.

```sh
python3 -c "import sys; sys.path.insert(0,'tools'); import native_sprite_gap; native_sprite_gap.prepare('demo11-native-product-r3')"
python3 tools/m1.py --target demo11-native-product-r3 scaffold
python3 tools/m1.py --target demo11-native-product-r3 generate
python3 tools/m1.py --target demo11-native-product-r3 build
python3 tools/play_native_cheats.py --target demo11-native-product-r3 --room 0x190
```

Reproduce the graphics and unchanged-room assertions with the retained captures:

```sh
python3 tools/qualify_corridor_background.py \
  --native local/captures/takeover-r3-190/q1 \
  --interpreter local/captures/takeover-r3-190-interp/q1 \
  --donor local/captures/mhp/h24 \
  --regression-base local/captures/takeover-r2-191 \
  --regression-candidate local/captures/takeover-r3-191 \
  --output local/reports/corridor-background-r3.json
```
