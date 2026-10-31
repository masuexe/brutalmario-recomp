# Room 151 boss extended graphics 0x282

Date: 2026-10-30. Candidate: `demo11-native-mazo-gfx282-v1`. Parent:
`demo11-native-product-r14`. The accepted product stays r14.

## Finding

The room 151 boss sprite 9C code holds this sequence at pack offset `E0A`:

```
C2 30        REP #$30
A9 82 02     LDA #$0282
8F 90 FF 7F  STA $7FFF90
E2 30        SEP #$30
DA           PHX
22 80 F7 0D  JSL $0DF780
```

This is an explicit extended graphics request for id `0282`. The product
pointer at file offset `0A048E` is `FFFFFF`. The mazo pointer is `3F:B5C8`,
and its stream decodes to 4096 bytes.

Id `027E` is also empty. The mazo pointer is `3F:80D5` and decodes to 4096
bytes. No code request for `027E` appears in the supplied packs.

Capture `mazo-9c-gfx282-window-v2` shows the sibling sets in VRAM on every
sampled fight frame: `027F` at `E800`, `0280` at `F800` and `0281` at `D800`.
Id `0282` does not appear. The product already holds `027F` to `0281` byte equal
to mazo, so `0282` is the only empty member of the family. The missing set likely
fills VRAM `C800` or an adjacent slot.

The VRAM check uses bytes `2048..2111` of the decoded stream. The first 64 bytes
can match unrelated sheets. `tools/check_vram_graphics.py` applies this slice.

## Change

The candidate adds one data-only pack and one pointer patch.

| Item | Value |
| --- | --- |
| ROM | `626a5c5c3fee9ae54962c448e04dcb24b4b962ee87d9edfeb2279ef4a324c186` |
| Binary | `0ee9b3ff9458b9da6e610b5ee08b0a00b6c3ee5c505f0831a650fd0e70b34dd2` |
| Pack | `local/native-modules/mazo-gfx282-v1/gfx282.bin`, 3344 bytes |
| Pack address | `D2:8000` |
| Pointer | offset `0A048E`, `FFFFFF` to `0080D2` |

The first candidate used `D1:9000`. The native host rejects two packs in one bank,
so the pack moved to `D2:8000`.

`tools/prepare_mazo_gfx282.py` builds the candidate from the r14 config. It
verifies the parent ROM and the mazo stream before it writes the config.

## Verification

- The ROM delta from r14 is exactly the three pointer bytes.
- The pack equals the mazo compressed stream and decodes to 4096 bytes.
- `tests/test_mazo_gfx282.py` pins both facts.
- No sampled room 151 frame executes the request. The request likely belongs to
  a 9C phase that needs boss damage. Automation cannot damage 9C, so the runtime
  frame stays open. This is the same blocker as the phase music.

## Id 027E

`tools/inspect_extended_graphics.py` reads the pointer and searches every
native pack for an immediate request. Id `027E` has an empty pointer and no
immediate request in the supplied packs. Ids `027F`, `0280` and `0281` decode to 4096 bytes. None has an immediate
request in a 9C pack. The room 190 boss 9B requests `0280`. Sprite 9C requests
`0281`. So `027E` stays unexplained rather than proven unused. Do not install it without a requester.

## Attack probe

An assisted attack probe `mazo-9c-attack-v1` uses the tracked align-fine prefix,
temporary immunity and 240 Up+B/Up+A cycles with 29 samples. The room stays in
live `151`. The boss part `1528` values stay at 0, 4, 6, 7 and 248 and never
drop. Ids `0D85` and `0D8F` stay 0, so the room 190 health table does not apply.
No `0282` data appears in VRAM or WRAM. The request needs a phase that these
inputs do not reach.

## Green orb damage window

The user reports the room 151 damage rule. Touch the green orb above the boss.
A ruby prompt appears, and Mario flashes green. Damage occurs only during the
green flash. The flash expires, and the player must touch the orb again.

A probe teleports the player to `(168,80)`, the orb position in the sampled
frame. A countdown at `1496` reads `43` at room entry and decays to zero. A
contact sample read `40`, but the countdown also runs without contact, so it is
not proven to be the green-window timer. A frame near the contact shows a damage
number. The green-window variable stays unknown.

A frame scan with `tools/find_green_orb.py` shows the orb at
`(170..181, 82..93)` for the whole sample, with a two-frame pulse.
`tools/find_cgram_animation.py` shows entry `100` pulsing the same way while
the player stands away from the orb. That entry is the orb glow, not a player
flash. A frame without the star timer still shows the cross at the same screen
position. The cross is the orb and not a star sparkle.

The frame vertical scroll is `192`, so screen `y 86` maps near world `y 278`.
The player can stand on the crystal at world `(180,247)`, just below the orb. A
position write into that crystal prevents a jump.

A running jump from the floor reaches an apex near `(175,282)`. The frame shows
Mario inside the green ball, but no ruby text appears. The next check is the
orb hitbox, a required button, or a specific orb pulse. The script
`recomp/inputs/mazo-9c-translevel-entry.script` enters the room through
map 6 and translevel `075`, keeps the fight live and touches the orb. The
contact samples still show the boss attack text box, not a ruby prompt. The
next probe must find the green-window state and the prompt condition.

## Next work

Find the orb reappearance condition, then attack only while `1496` is nonzero.
After that, check VRAM for the decoded `0282` data. Decide on `027E` only after a
requester appears. Do not promote this candidate.

## Superseding orb qualification (2026-10-30)

The previous proposed button/pulse investigation is superseded. Official mazo
code at `22:8309` identifies the green orb as custom 9C variant `1504=05`,
initially at world `(168,272)`. It uses sprite clipping index 0, whose rectangle
is `(170,275,12,10)`. The main 9C actor's clipping index 7 is not the orb hitbox.
With `$9D=0`, `JSL $01A7DC` tests ordinary player contact. Carry set increments
`C2` from 0 to 1, clears `1570`, and relocates the orb to `(120,96)`. This branch
has no button or pulse requirement. Existing `mazo-worldorb-v1/w5`,
`mazo-jumporb-v1/j3` and `mazo-orbnoimm-v1/k3` already contain phase 1; the old
short samples ended during the resulting freeze rather than proving no contact.

Phase 1 lasts 160 actor ticks; it calls the message routines at tick 16 and
creates variant 6 at tick 112. Phase 2 lasts 64 ticks and releases `$13FD`.
Phase 3 sets `$7FFE00=1`; `1602` advances every fourth frame until `FF`, at
which point the orb returns to phase 0 at `(168,272)`. `$7FFE01` drives a
separate temporary reaction/freeze. At `22:91A4`, a nonzero `$7FFE00` permits
that reaction and sets the controller timer to `80`. Neither `$1496` nor the
observed `1528` values establish the strengthening window or boss health.
The former is not referenced by the 9C program; `1528` also holds positions and
pattern parameters. Do not infer damage from those values.

Reproduce with the tracked `mazo-9c-orb-sequence.script` on
`demo11-native-mazo-gfx282-v1` and `mazo-9c-orb-sequence-donor.script` on the
official mazo donor, with `snes9x_echo_buffer_hack=enabled`. These declare map
or pipe entry, one player placement at `(180,250)`, and persistent `$1497=FF`
immunity. They never write orb state, strengthening flags, health or completion.
They qualify assisted contact, not unassisted traversal or ordinary combat.

Captures `mazo-orb-sequence-native-v2` and `mazo-orb-sequence-source-v3` each
contain 98 complete WRAM/VRAM samples and terminate at scripted quit. The checker
`tools/qualify_mazo_orb_sequence.py` validates ROM/build/module/runtime/script
identities, dump sizes, live room 151, actual contact, phases 1/2/3, activation,
expiry and respawn. Fifteen contact/cutscene samples match the selected fields
exactly. Both activate at `orb14`; the native four-frame progress clock is one
tick ahead. Native reactions at `orb45..47` and `orb62..64` pause its clock;
source has no sampled reaction. Reset is observed at native `orb83`, source
`orb78`. Later fight timing is not claimed equal.

Report: `local/reports/mazo-orb-sequence-v2.json`. Native ROM remains
`626a5c5c3fee9ae54962c448e04dcb24b4b962ee87d9edfeb2279ef4a324c186`;
**the binary actually used by these captures** is
`656a0be24ab09de7050de16d796dfbb756431d49b2302ebbe19b34cd23ef3902`.
The earlier binary identity above belongs to the earlier checkpoint. Source ROM
is `94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1`.
Receipts retain exact script, pack and build identities.

`0282` still has zero VRAM slice hits in these samples. No damage, later boss
arrival, audible music, earned victory or save is accepted. Next: trace the
controller's vulnerability and actual damage storage from the official code,
then exercise attacks during the now-qualified `$7FFE00` window. A manual
sample is no longer a prerequisite for establishing orb activation. This
candidate descends from r14; any later accepted integration must preserve the
modern-sprites-v2 modules rather than promote this older fork over them.

The [reflection checkpoint](native-mazo-reflection.md) supersedes the next action
above: five real returns plus one scripted marker now introduce the second boss
on both hosts. Later survival and the `0282` request remain open.
