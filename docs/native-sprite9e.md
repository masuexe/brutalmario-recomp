# Immutable external sprite-code pilot

## Result

`demo11-native-sprite9e` adds cheap_demo custom sprite `9E` through an external
1,291-byte code pack, descending from `demo11-native-pack-pilot`. Room `146`
now has functioning horizontal and vertical lifts. Both carry Mario with the
same positions, speeds and actor state as the verified donor fixture. This
installs code without allocating a window or moving graphics in the ROM.

This is an automatically qualified fixed-code mapping. It is not a completed
course, a complete Boss port, arbitrary dynamic module switching or new manual
acceptance. The full cross-version restoration remains open.

## Content and dependency review

The source is the pinned official cheap_demo ROM, SHA-256
`f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822`.
The source record is at file `0x083B3D`; the RATS block is at file `0x1295CD`,
SNES `$25:95CD`. Initialization is `$25:95DC`; main is `$25:9629`.
The destination record is at file `0x188C52`. The recipient places `9E` in
rooms `097` and `146`; their sprite-list dependency set is checked before
preparation. Placement numbers alone are not used as source identity.

The builder checks the original record, RATS bounds, complete code hash and
shared helper ranges in both recipient and donor. Static decoding of both
entries and their local callees finds 14 local entries and 581 instruction
variants. Local absolute references stay inside the block, no long reference
uses the original code bank, and the reviewed long-call set is:

`01801A`, `018022`, `01802A`, `01A7DC`, `01B7B3`, `03B664`, `03B72B`, `27FAF4`.

Additional matching helper ranges cover the stock movement calls below
`01802A`. The audit is a bounded control-flow/reference check, not a formal
proof of every indexed access or the unexercised UFO branch. The runtime
comparisons qualify the normal lift branches. The supplied source lists and
walkthrough reference were used for orientation; the payload comes from the
verified official ROM, without assembling an unverified source package.

## Mapping contract

Only the one 16-byte sprite record changes in the descendant ROM. The adapted
entry pointers are `$A5:95DC` and `$A5:9629`, retaining their low 16 bits.
The code bytes, including their RATS header, stay in `sprite9e.bin` and are
absent as an installed block in the ROM. The original `$25` bank bytes are
unchanged. In particular, the old space trial's unknown graphics blob is not
moved, cleared or repointed.

The native runtime supplies immutable upper-half views for raw banks `$A5`
and `$B6`, using a contiguous 4 MiB host backing plus a guard byte. `$A5`
contains the external code over a copy of the recipient bank data; `$B6`
continues serving the external ExGFX `FFD` payload from the preceding pilot.
The ordinary `$25` and `$36` views continue using the descendant ROM. Low
addresses retain the system-bus WRAM and hardware mappings, so the main entry's
`PHK/PLB` idiom and low WRAM accesses remain valid.

Mappings are installed once, before execution, and do not change with the room
or current PC. Interrupts and calls use the existing guest stack and bus. The
build rejects generated nodes in banks `$25/$A5/$36/$B6`. Live pointer
identity prevents the existing dispatcher from treating the split banks as
ordinary mirrors. The external body runs through the interpreter fallback;
shared engine routines retain their existing dispatch. No AOT sprite-body
claim is made.

The runtime reuses the pinned cartridge hook patch from the graphics pilot,
with a separate feature implementation and generated header. Its SHA-256 and
pack identities are captured in build/capture receipts. The original graphics
pilot implementation and evidence identities remain intact. Each pack is
required and is checked against its compiled size/hash before use.

## Qualified behavior

Final evidence uses the `native-sprite9e-final` capture prefix:

- Eleven source/native dump pairs match the active actor records, relevant
  state/speed fields and Mario positions. Horizontal platform/Mario movement
  is 126 pixels between `board` and `ride128`; the vertical pair moves upward
  by 62 pixels between `vertical_board` and `vertical64`.
- Room `146` background/HUD VRAM below byte `0xC000` and its palette match the
  unchanged entry control. Sprite graphics changes are confined to the upper
  sprite area in the examined entry samples. Visual inspection also finds the
  expected arrow lift and coherent background in source and native captures.
- Native pipe-action fixtures enter room `097`, return to `146`, and recreate
  the initial platforms. The `097` transition sample has no active `9E` actor
  in either host; it does not qualify that room's platform gameplay.
- A fall-position fixture triggers the game's real death action, loses a life,
  returns to the map and re-enters room `146` with platforms active. No death,
  life, sprite or completion flags are written to prove these results.
- The unchanged Grassland Star and Boss corridor/room `BC` routes retain all
  420 exact comparisons at 42 dump points: WRAM, VRAM, CGRAM, OAM, SRAM,
  framebuffer, APU trace, PPU-write trace, register and DMA snapshots.
- Five real-executable startup probes reject missing, corrupt, short and long
  code packs, and missing cumulative graphics. Unit tests also cover graphics
  corruption and ROM mismatch.
- Interpreter coverage observes both adapted entry PCs with `missing_entry`
  fallback. The native flow records 501,188 executed instructions in the code
  pages, distinct from 3,045,973 code-pointer resolutions.

The full project unit suite passes 148/148 tests; the unchanged historical
whole-line suite passes 78/78. A synthetic execution test uses the actual
cartridge resolver and 65816 core to execute an external long call, access low
WRAM through the new DB, take NMI/RTI, and return with JSL/RTL while restoring
the caller's stack and bank. Other tests reject AOT nodes in either split bank
or alias and reject stale launcher feature receipts.

All routes are explicitly labeled map/node, pipe-action, player-position or
fall-position fixtures. They qualify the exercised boundaries, not ordinary
unassisted traversal, a real course exit or persistence after a full clear.
APU trace equality on unchanged routes is not a separate audible-output claim.

## Reference limitation

The donor's same numeric map entrance initially reaches room `14B`, whereas
the recipient reaches `146`. The shared fixture explicitly loads `146` through
the game pipe action before comparing the platforms. The donor and native
scripts have an identical prefix through the return-to-146 sample.

A separate exploratory donor death probe,
`local/captures/native-sprite9e-donor-flow-v2`, reaches real death but times out
waiting for the map, with game mode decimal 12 (`0x0C`) in this reference host.
It is retained as failed evidence. The qualified donor comparison ends before
that boundary; death and re-entry are qualified in the native recipient only.
This is not a verdict that the donor content is absent or universally broken.

## Identities and reproduction

| Artifact | SHA-256 |
| --- | --- |
| Base ROM | `3da980ccd8ad57b9c2bd4628a63e5dd7a0fbe6e7a72b49bee691cb013f1a9865` |
| Candidate ROM | `3077bb3df00a1f26c0728deea091048be792ac1e09af9886cfdb5e36f8d05bb1` |
| Native executable | `dbdc17d913039f76cc8eb7cc2384de096569b7997ce6519bef12f597915e236a` |
| External sprite code | `a6654d22c2dd9f146fc117ba7dca01f9389995fcb8b75f52ba6f2c4a6b1a717d` |
| Native flow script | `b79c832be4ff36cb95522d78a31c26bee5c83b489acc93133d772cac735b9185` |
| Donor behavior script | `3d16ea8c649b31010a6b6c19355bb175555f78ec6b1fd0d360ed2c58b2fbfaa7` |
| Reviewed report | `68bff8a6602b9ee40e6052acfde6547f214a16fa5c46d0f4ecf3b9347fba2fed` |

```sh
python3 tools/native_sprite.py
python3 tools/m1.py scaffold --target demo11-native-sprite9e
python3 tools/m1.py generate --target demo11-native-sprite9e
python3 tools/m1.py build --target demo11-native-sprite9e
python3 tools/qualify_native_sprite.py --capture-prefix YOUR_FRESH_PREFIX --run
```

Skip scaffolding when the isolated experiment already exists. Preparation
requires the pinned official donor and preceding graphics-pilot artifacts.
`tools/restore_star_world_1.py --target demo11-native-sprite9e` also delegates
to this builder. For existing captures, recheck using a fresh report name:

```sh
python3 tools/qualify_native_sprite.py --capture-prefix native-sprite9e-final --report-name YOUR_FRESH_REPORT
```

The final reviewed report is `local/reports/native-sprite9e-final-reviewed.json`.
It pins all twelve capture receipts. Earlier trial captures and reports remain
unchanged and must not be presented as final evidence. Unit and legacy-suite
logs are `local/reports/native-sprite9e-unit-tests.log` and
`local/reports/native-sprite9e-line-check.log`.

Optional fresh practice launch at the reviewed map entrance:

```sh
python3 tools/play_demo_only1.py --restoration demo11-native-sprite9e --translevel 0x6A --show-room
```

The launcher supplies both packs automatically. No new manual playtest is
required for this bounded automatic checkpoint; original ROMs, user saves,
accepted baselines and old captures remain preserved.

## Next action

Inventory the requested 7hero and mazo Boss dependencies, consulting newer
official implementations where present, then choose one complete bounded
fight. Fixed-bank module admission still requires an address/dependency review;
adding another file does not automatically establish its mapping or version
compatibility. The UFO branch, room `097` gameplay, full course completion,
broader save-state compatibility and complete cross-version integration stay
unqualified by this pilot.
