# Room 191 invisible graphics adaptation

> Correction: the user found that r5 also hid the rightmost question orb.
> The SP4 suppression was incorrect. Use the r6 correction below; the r5
> qualification did not test that the orb remained visible.


The user accepted the room 190 r3 background repair, then identified two unwanted
pictures in room 191 (`/tmp/Snipaste_2026-10-29_01-39-47.png`). The user states
that the original has no visible object at either marked location.

Both marked red foreground pictures belong to invisible checkpoints. This is the
same recipient/donor graphics difference previously corrected for the official
T ending room; see `native-seven-ending.md`. The lower rectangle also overlaps the mazo B0 control actor (native custom
A9), which submits tile `18C` with properties `6B`. Its logic must remain
active; its placeholder pattern must also be transparent.

`tools/prepare_corridor_invisible.py` creates two room-private graphics clones:
recipient GFX 17 with absolute character patterns A4–A7/B4–B7 transparent, and
GFX 05 with sprite patterns 18C/18D/19C/19D transparent. This is an explicit
native integration adaptation based on the user's original-appearance report;
it does not claim a new matching donor run. The two programs, sprite list,
foreground objects, Map16 definitions, collision and exits are unchanged.

The clones use literal LZ2 streams in a new immutable data-only D0 pack. Private
IDs FF9/FFA were empty. Room 191 alone enables extended graphics and selects
these streams; other rooms retain their existing graphics. The accepted r3 and
older product builds remain intact. Room 192's message font is separate work.

The recipe is `config/restorations/demo11-native-product-r5.json`. Generate the
pack and recipe using the pinned r3 ROM, then use the ordinary target workflow:

```sh
python3 tools/prepare_corridor_invisible.py
python3 -c "import sys;sys.path.insert(0,'tools');import native_sprite_gap;native_sprite_gap.prepare('demo11-native-product-r5')"
python3 tools/m1.py --target demo11-native-product-r5 scaffold
python3 tools/m1.py --target demo11-native-product-r5 generate
python3 tools/m1.py --target demo11-native-product-r5 build
```

The old 191 header word `0100` did not enable the extended graphics list;
`0180` does. An initial diagnostic with the disabled list is retained under
`local/probes/room191/first-*` and capture `invisible-r4-191`. It is not evidence
for the final recipe. Reference entry attempts `takeover-191-mazo*` did not reach
normal room 191 gameplay and are not donor appearance evidence.

## Qualified candidate

Target `demo11-native-product-r5`, ROM SHA-256
`7fc6e9f5177ef2f339721d3099d35f60e5176e5028ab0d365a486e4c3aa22c76`.
The 8,210-byte D0 pack SHA-256 is
`15300375ac2a620a04ef93f85e4336585d8640cac66bce59b418f279b94dfdbe`.
Room 191's record selects `15,19,FF9,14,FFA,13,01,00`. In this engine record
order, the two variable sprite slots select SP4 then SP3. The earlier r4
extended-selection diagnostic swapped those slots; it is not the deliverable.
The final r5 preserves SP3 and blanks only the intended SP4 patterns.

`python3 tools/qualify_corridor_invisible.py` passes. It checks five active-room
samples, all expected transparent patterns in VRAM, exact sky pixels in both
marked foreground rectangles at `w1`, retained control-actor OAM, palette and
sprite states, and native/interpreter framebuffer, VRAM, OAM and palette
agreement. Contact sparkle effects remain visible; the control actor is not
removed. Mario Y agrees; X differs by up to two pixels on the later assisted
samples. Pickup animation/OAM phases also differ from r3, so full same-frame
playback equivalence is not claimed. Actor programs and collision data are
unchanged. The resource-load path now explicitly decompresses the private
streams instead of using the default graphics list.

All five room 190 dump files (WRAM, VRAM, framebuffer, OAM and CGRAM) match r3
exactly. The 313-test unit suite passes. Evidence: captures `invisible-r5-191`,
`invisible-r5-191-interp`, `invisible-r5-190`; comparison controls
`takeover-r3-191` and `takeover-r3-190`. Full capture receipts and hashes are
retained in `local/reports/corridor-invisible-r5.json`. Unit log:
`local/probes/room191/unit-tests.log`. These are assisted pipe/movement fixtures,
not a real exit or a full level clear.

```sh
python3 tools/play_native_cheats.py --target demo11-native-product-r5 --room 0x191
```


## r6 correction: retain the question orb

The user verified that the unwanted foreground pictures were gone, but reported
that the rightmost question orb had also disappeared. The prior description of
its tile 18C as a disposable control-marker pattern was wrong. The actor has
visible graphics as well as room-transition logic.

The new recipe `demo11-native-product-r6` keeps only the private FG2 clone FF9.
It selects original GFX 05 for SP4, with its entire 4,096 decoded bytes unchanged.
There is no sprite-graphics clone, no FFA pointer patch, and no change to actor
logic, collision, object placement or input fixtures. The D0 pack contains only
the 4,105-byte FG2 stream. Previous product/r3/r5 builds and captures remain intact.

- ROM SHA-256: `5ff22880ebd044930867b4e5eb2b637cf74c2cd57abb7c4ba348eb56c56926b7`.
- Pack SHA-256: `6dcddb8214d00d859142e5d81b0a8ad37b9e581be0a498ff39be427318435644`.
- Room 191 graphics selection: `15,19,FF9,14,05,13,01,00`.

The preparation and qualification tools retain their original r5 behavior by
default for historical reproduction. Use `--restore-orb` for r6:

```sh
python3 tools/prepare_corridor_invisible.py --restore-orb
python3 -c "import sys;sys.path.insert(0,'tools');import native_sprite_gap;native_sprite_gap.prepare('demo11-native-product-r6')"
python3 tools/m1.py --target demo11-native-product-r6 scaffold
python3 tools/m1.py --target demo11-native-product-r6 generate
python3 tools/m1.py --target demo11-native-product-r6 build
python3 tools/qualify_corridor_invisible.py --restore-orb
python3 tools/play_native_cheats.py --target demo11-native-product-r6 --room 0x191
```

The corrected qualification requires the complete restored SP4 page to equal
the original decoded GFX 05 at all five samples. It also requires visible
non-sky pixels at the orb's OAM position, while retaining the exact sky-pixel
assertions for both unwanted foreground rectangles. The actor's OAM descriptor
and sprite states must still match the r3 control. This explicitly covers the
regression that the r5 checks missed.

Fresh r6 qualification passes at five samples: full SP4 agreement, active orb
actor, both garbage rectangles transparent, and native/interpreter VRAM,
framebuffer, OAM and palette agreement. The first orb rectangle contains 186
non-sky pixels. The before/after image
`local/probes/room191-orb/before-after.png` shows the r5 missing orb above the
restored r6 green question orb. The foreground marker pictures do not return.
Room 190 retains five byte-identical full dump files versus r3.

Captures: `invisible-r6-191`, `invisible-r6-191-interp`, `invisible-r6-190`.
Receipts are retained in `local/reports/corridor-invisible-r6.json`. As in r5,
this is an assisted entry/movement fixture, not a complete course pass. The
Japanese message font remains unresolved.

The same visibility assertion rejects the preserved r5 negative control:
only 14 non-sky pixels (contact sparkle) versus r6's 186. The r5 SP4 page also
fails the original-data assertion. This checks that the added regression gate
actually detects the user's reported failure, rather than merely agreeing
between two render paths that both hide the orb.

The fresh full unit suite passes **313 tests**; log:
`local/probes/room191-orb/unit-tests.log`. Default r5 preparation was also
reproduced with no change to its tracked recipe, preserving historical inputs.

## Room 192 extension (r7)

The user accepted r6 and requested the same foreground repair in room 192.
`tools/prepare_corridor_192.py` creates `demo11-native-product-r7` from pinned
r6. The only ROM delta is room 192's 32-byte graphics record; it reuses the
accepted FF9 foreground clone and original GFX05 sprites. No new pack, code,
Map16, collision or sprite data changes. ROM SHA-256:
`e18964c5b90e53eba2836f293dbb209ee4118af7649b1e7ecc6882a5892fe8b1`.

`tools/qualify_corridor_192.py` passes five assisted room192 samples: mode/room,
transparent checkpoint patterns, complete original SP4 page, unchanged actor
states versus fresh r6, and native/interpreter framebuffer, VRAM, OAM and
palette agreement. Room191 and room190 retain 30 byte-identical dump files
versus their accepted r6 captures. Six existing product identity tests also
pass; the prior 313-test suite was not rerun for this one-record extension.
Receipts: `local/reports/corridor-192-r7.json`. Fresh captures:
`corridor-r7-192`, `corridor-r7-192-interp`, `corridor-r6-192`,
`corridor-r7-191`, `corridor-r7-190`. Input:
`recomp/inputs/mazo-192-product-practice.script` (assisted pipe/movement).
Japanese text and full course completion remain separate unresolved work.

```sh
python3 tools/prepare_corridor_192.py
python3 -c "import sys;sys.path.insert(0,'tools');import native_sprite_gap;native_sprite_gap.prepare('demo11-native-product-r7')"
python3 tools/m1.py --target demo11-native-product-r7 scaffold
python3 tools/m1.py --target demo11-native-product-r7 generate
python3 tools/m1.py --target demo11-native-product-r7 build
python3 tools/play_native_cheats.py --target demo11-native-product-r7 --room 0x192
```

## Room 151 tidal-wave background (r8)

The user reported that room 151 is covered by garbage vertical stripes after the
crystal-ball teleport from room 191. The defect is a missing extended graphics
stream, not a terrain, Map16 or collision fault.

### Cause

The room 151 boss is custom sprite 9C. When its attack starts, the game loads
extended graphics 0x27D for the Tidal Wave background. The recipient pointer for
0x27D is empty (FFFFFF). The loader then decompresses unrelated bytes into the
buffer $7E:AD00 and copies them to VRAM $8000. Those bytes draw the vertical
stripes.

The defect is present in the accepted product r7 and in the separate
demo11-native-mazo-9c target. The official mazo donor loads 0x27D and draws the
correct background. Measurement:

| Buffer | mazo donor, fight120 | product r7 |
| --- | --- | --- |
| $7E:AD00, 4,096 bytes | equals decoded mazo gfx 0x27D | unrelated bytes |
| VRAM $8000, 4,096 bytes | equals decoded mazo gfx 0x27D | stripe pattern |

The room 151 graphics record, the level header tables, and the initial room load
(base GFX 0x28 and 0x29) are equal and correct. Only the dynamic 0x27D request
fails. A scan of every donor room 151 capture finds 0x27D as the only requested
extended graphics id that the recipient leaves empty. The ids 0x27E and 0x282 are
also empty in the recipient, but no sampled frame requests them.

### Fix

tools/prepare_corridor_wave.py creates demo11-native-product-r8 from r7. The
target changes two items only:

- One 3-byte extended-graphics pointer at file 0x0A047F (decimal 656511). The
  value is 00 A0 D0, which is CPU address $D1:8000.
- One data-only pack corridor-wave.bin, 1,553 bytes, mounted at CPU $D1:8000.
  The pack holds the exact mazo LZ2 stream for gfx 0x27D. The decoded content
  is 4,096 bytes.

The target adds no code, collision, Map16, sprite, level or input change.

| Item | Value |
| --- | --- |
| ROM SHA-256 | 4a45955c65c30495940b69fbd4675ed41574e3ae37c4471ecc80c32adf2bd55f |
| Pack SHA-256 | d70774e7549b1af3e368b976782b04b09aa7df84c83fd844bb39c22e5f7fa3e5 |
| Pack size | 1,553 bytes |
| Pointer file offset | 0x0A047F |

### Verification

tools/qualify_corridor_wave.py passes these checks:

- The r8 ROM equals r7 plus the single 3-byte pointer. The pack equals the
  decoded mazo 0x27D compressed stream.
- In room 151 every sampled wave frame (fight100 to fight600) holds the mazo
  0x27D data in both $7E:AD00 and VRAM $8000. The early fight090 sample still
  holds the original room background (0x28), so the initial load is unchanged.
- Native and interpreter captures agree on VRAM, OAM and CGRAM for every room
  151 wave sample. Framebuffer output agrees at all samples except the two
  transient frames fight145 and fight270, where only a sprite position differs.
- Rooms 190, 191 and 192 keep 55 byte-identical dump files versus the accepted
  r7 captures. This includes WRAM, VRAM, framebuffer, OAM and CGRAM.
- The historical donor capture mazo-9c-align-fine-v2-donor holds the same 0x27D
  data in $7E:AD00 and VRAM $8000 at fight120.

Fresh captures: corridor-wave-r8-151, corridor-wave-r8-151-interp,
corridor-wave-r8-190, corridor-wave-r8-191, corridor-wave-r8-192. The report is
local/reports/corridor-wave-r8.json. The full unit suite passes 317 tests. The
input is the represented mazo-9c-align-fine-native.script assisted pipe fixture
with a stationary Mario. It does not prove a full fight clear. The Japanese
message font in rooms 191 and 192 remains open.

Use the fight entry to observe the background. A direct room write does not
reload graphics.

```sh
python3 tools/prepare_corridor_wave.py
python3 -c "import sys;sys.path.insert(0,'tools');import native_sprite_gap;native_sprite_gap.prepare('demo11-native-product-r8')"
python3 tools/m1.py --target demo11-native-product-r8 scaffold
python3 tools/m1.py --target demo11-native-product-r8 generate
python3 tools/m1.py --target demo11-native-product-r8 build
python3 tools/qualify_corridor_wave.py
```

## Room 151 music retarget (r9)

After the r8 graphics repair the user asked to set the room 151 music to slot
`A4`. Slot `A4` is The Decisive Battle (Final Fantasy VI) on this line.

### Cause

Room 151 level data holds the music object `40 60 61` at file `0x2DC0F1`. The
loader subtracts one from the parameter, so the room requested slot `0x60`
(Iceberg Ocean). The `$0DDA` record showed `0x60` in gameplay.

### Fix

`tools/prepare_corridor_music.py` creates `demo11-native-product-r9` from r8. The
target changes one byte: the music-object parameter at file `0x2DC0F3` moves from
`0x61` to `0xA5`, so the room requests slot `0xA4`. No other byte changes.

- ROM SHA-256: `d29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552`
- Music object: `40 60 A5` at file `0x2DC0F1`.
- Slot `A4` block: pointer and 17,534-byte payload equal the official demo 1-1 ROM.

### Verification

`tools/qualify_corridor_music.py` passes these checks:

- The r9 ROM equals r8 plus the single byte at `0x2DC0F3`.
- The `A4` upload block equals the official demo 1-1 song block byte for byte. The
  song is therefore present, not a null slot.
- Every room 151 sample holds `$0DDA = A4`. Gameplay reaches mode `0x14` and stays
  there, so the room does not stall in Mario Start.
- An isolated audio capture is non-silent in room 151: overall RMS 1,540 and
  loudest one-second RMS 4,207. The capture is
  `local/captures/corridor-music-r9-151-audio`.
- Rooms 190, 191 and 192 keep 55 byte-identical dump files versus the accepted r8
  captures.

Captures: `corridor-music-r9-151`, `corridor-music-r9-151-audio`,
`corridor-music-r9-190`, `corridor-music-r9-191`, `corridor-music-r9-192`. Report:
`local/reports/corridor-music-r9.json`. The input is the represented
`mazo-9c-align-fine-native.script` assisted fixture; it is not a full course clear.

```sh
python3 tools/prepare_corridor_music.py
python3 -c "import sys;sys.path.insert(0,'tools');import native_sprite_gap;native_sprite_gap.prepare('demo11-native-product-r9')"
python3 tools/m1.py --target demo11-native-product-r9 scaffold
python3 tools/m1.py --target demo11-native-product-r9 generate
python3 tools/m1.py --target demo11-native-product-r9 build
python3 tools/qualify_corridor_music.py
```

## Room 190 music override (r10)

After r9 the user asked to set the room 190 music to slot `A4`'s relative `9E`.

### Cause

Room 190 has no music object in its level data. Its song comes from the engine
music remap table at RAM/ROM `$05:84DB`, index `0`, which holds `0x02`. That
default is shared by about 128 levels, and rooms 191 and 192 use the same index.
A ROM data edit therefore cannot change room 190 alone. Changing the table entry
made rooms 190, 191 and 192 all play `9E` in a probe, so that approach is rejected.

### Fix

`demo11-native-product-r10` keeps the r9 ROM byte for byte and adds a rooms-scoped
native adaptation in `recomp/native_seven.c`. `bm_room_music_override()` runs from
`bm_content_resolve()`. When work RAM room `$10B/$10C` is `0x190`, it sets
`$0DDA = $9E` and `$1DFB = $9E` once on entry. No other room is touched.

- ROM SHA-256: `d29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552`
  (identical to r9; the change is native code, not ROM data).
- `g_ram` uses a weak binding so the isolated boundary-test links still build;
  the full runner provides the strong array.

### Verification

`tools/qualify_corridor_music2.py` passes:

- The r10 ROM equals the r9 ROM, and the config declares the `room-music-override`
  adaptation for room `0x190`, slot `0x9E`.
- Room 190 samples hold `$0DDA = 9E` and reach gameplay mode `0x14`. The boss scene
  still renders (Mode 7 sky, clouds, boss face, health bar).
- Room 191 and room 192 keep `$0DDA = 02`. Room 151 keeps `$0DDA = A4`.
- Rooms 151, 191 and 192 keep 270 byte-identical dump files versus the accepted
  r9 captures.
- The isolated audio capture `r10-190-audio` is non-silent (overall RMS 1,293;
  loudest one-second RMS 4,201).
- The full unit suite passes 325 tests.

Captures: `r10-190`, `r10-190-audio`, `r10-191`, `r10-192`, `r10-151`. Report:
`local/reports/corridor-music-r10.json`. Input is the represented
`cheat-r184`/`corridor-*` assisted fixtures; these are not full course clears.

```sh
python3 tools/prepare_corridor_music2.py
python3 -c "import sys;sys.path.insert(0,'tools');import native_sprite_gap;native_sprite_gap.prepare('demo11-native-product-r10')"
python3 tools/m1.py --target demo11-native-product-r10 scaffold
python3 tools/m1.py --target demo11-native-product-r10 generate
python3 tools/m1.py --target demo11-native-product-r10 build
python3 tools/qualify_corridor_music2.py
```
