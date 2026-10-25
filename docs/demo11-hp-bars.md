# Boss and Mario HP display repair

The user reports missing health-point (HP) bars in rooms `0xBC` and `0xCC`.
The isolated `demo11-hp-bars` descendant repairs their shared HUD upload.
The accepted head and all parent ROMs remain intact.

## Cause

Both rooms already populate `$7F:FFE0..FFEF` with sixteen display characters.
They set `$7F:FFDF` to `1` to identify the custom row.

- Sprite `0x2B` initializes the BOSS label and eight gauge cells in room `0xBC`.
- The existing routine at `$2C:8BA0` initializes Mario's label and HP cells in room `0xCC`.
- That routine also updates Mario's cells after guest damage.

Original cheap_demo uploads the row to VRAM word `$5028` through `$34:9E57..9E7B`.
Demo 1-1's replacement at `$10:8294` omits that sixteen-character path.
Its remaining upload serves another custom row, with its own flags.
Thus valid HP data never reaches the visible tilemap.
The original reference host reproduces this failure on the parent restoration.
It is not an AOT-only or native-renderer failure.

The earlier boss-spawn diagnosis was incorrect.
Its probes treated `$161A,x`, the sprite-list index, as the sprite number.
They excluded zero, the valid list index of the boss in this room.
In the preserved `bossmusic-a9/s42` capture, slot 9 has status `8` and custom ID `0x2B` at `$7F:AB9E,x`.
Its complete HP buffer is also present.
This evidence agrees with the user's report that the boss attacks already work.
No additional working-fight save is necessary to establish this cause.

## Change

The recipe installs an 83-byte routine at `$3E:A108` with an eight-byte RATS header at `$3E:A100`.
It changes the call at `$00:8DE1` from `$3E:A008` to the new routine.
The total allocation is 91 bytes; 84 bytes differ from the parent ROM.

The new routine performs these operations:

1. Call the existing `$3E:A008` routine for the recipient HUD and accepted room009 fuel display.
2. Preserve A and the processor status.
3. Require room `0x00BC` or `0x00CC`, game mode `0x14`, and a nonzero legacy HUD flag.
4. Upload the sixteen existing characters from `$7F:FFE0` to VRAM word `$5028` through DMA channel 1.
5. Restore A and the processor status, then return.

The DMA sequence comes from the pinned official cheap_demo ROM.
The adaptation uses `SEP #$20` instead of `SEP #$30` to retain the caller's index width.
The new routine does not change X, Y, DB or direct page.
The recipient status routine, fuel routine, boss record and Mario HP logic remain byte-identical to the parent.
The patch does not copy donor room layouts, global HUD dispatch or default-row tables.

## Identities

| Item | SHA-256 |
| --- | --- |
| Parent `demo11-boss-room-music-a9` ROM | `1a56f3fc8b7188cb1f91cae0e6e2e7f0a4a60139c32c81bfa6b4ba4e6b8a8bdf` |
| Candidate ROM | `1f505ebc9f3d27b7c3fe995c3b788499c4a61cde74b2b6e451b9d34dfa9607d9` |
| Candidate native binary | `247d628d4b321b0d9e417c8f8ed38e16e70ba7c06df0a077a1787ace798bf85f` |
| Official cheap_demo ROM | `f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822` |
| Donor DMA sequence, 37 bytes at `$34:9E57` | `8ed5ae79fc8b16c862364156d57bbbddc24b07547d86f99d312443e3f1348918` |
| Reference Snes9x core | `39aff6a57c370035486e1b5ca3d33b99ac31ed5e809a883984bce9be51aecf7c` |

The recipe pins the patch bytes and their source.
Each capture receipt pins its ROM, input and host identities.
The qualification report also records the core identity and candidate build identity.

## Verification

`tools/qualify_demo11_hp_bars.py` checks the reproducible recipe and the following captures:

| Capture group under `local/captures/` | Evidence |
| --- | --- |
| `hp-bc-base-{ref,native}-r3` | Active boss and HP data, absent upload before the fix |
| `hp-cc-base-{ref,native}-r3` | Mario HP data, absent upload before the fix |
| `hp-bc-fixed-{ref,native,interpreter,optimized}-r2` | BOSS label and eight cells on the visible tilemap |
| `hp-cc-fixed-{ref,native,interpreter}-r2` | Mario label, real damage, updated cells and return to the ordinary HUD |
| `hp-{bc,cc}-cheap-ref-r2` | Original donor display characters, glyphs and palette |
| `hp-fuel-fixed-{ref,native}-r1` | Accepted fuel gauge and real fuel depletion |
| `hp-fuel-base-ref-r1` | Fresh parent control for the fuel regression |

The BC route uses a map-position and map-node fixture, then ordinary corridor movement and door input.
The CC route uses an explicit room-exit fixture because it is a subroom.
A vanilla Koopa spawn fixture causes actual Mario contact damage.
The guest changes Mario's power state from `2` to `0`, then the HP routine restores it to `2`.
The damage counter increases from `1` to `2`, and the displayed row loses another HP cell.
The script does not write HP, HUD, completion or SRAM values.

All HP characters equal their guest RAM buffer in reference, native and interpreter captures.
Both native renderers pass the BC display check.
The displayed glyphs and their palette equal the original cheap_demo display assets.
Pure interpreter logs report zero AOT bridge entries.
Startup pictures match fresh parent controls on each respective host.
The ordinary corridor HUD matches its parent before and after the CC fixture.
The FUEL label, gauge cells and depletion match fresh parent reference captures.

The whole-line byte audit reports 886,851 changed bytes and zero unexpected bytes.
The integrated suite reports **61/61** checks.
All **122** unit tests pass.
The free-space budget passes with 357,680 bytes, above the reviewed 300,000-byte floor.
These checks qualify HP display and the exercised damage path, not an unassisted boss fight or course clear.
CC's other missing custom sprite records and broader boss restoration remain separate work.

## Commands

```sh
python3 tools/restore_star_world_1.py --target demo11-hp-bars
python3 tools/m1.py scaffold --target demo11-hp-bars
python3 tools/m1.py generate --target demo11-hp-bars
python3 tools/m1.py build --target demo11-hp-bars
python3 tools/qualify_demo11_hp_bars.py
python3 tools/audit_demo11_line.py --head demo11-hp-bars
python3 tools/check_demo11_line.py
python3 tools/play_demo_only1.py --restoration demo11-hp-bars --level-id 0x15F
```

The scaffold command requires a fresh experiment directory.
The qualifier requires the named captures; it refuses mismatched identities.
Use `tools/m1.py reference` or `native` with the tracked `demo11-hp-*` inputs to create fresh captures.
The donor BC input uses a room-exit fixture because donor translevel `0x83` loads a different room.
A numeric translevel match alone does not identify matching content.
