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
