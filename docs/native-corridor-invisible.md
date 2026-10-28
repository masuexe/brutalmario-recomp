# Room 191 invisible graphics adaptation

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
