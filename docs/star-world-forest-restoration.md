# Independent Forest Star restoration

Date: 2026-10-21. The independent forest course is automatically qualified as
the separate `star-world-forest` candidate. It replaces the middle-left
water duplicate in this candidate only. The accepted `star-world-center`
and `star-world-middle-left` targets remain available with their previous
identities and content.

The subsequent user playtest reported normal gameplay but exposed a retained
water flag. That flag is corrected in the current identity below; the original
automated checkpoint did not compare the donor's water state.
The user subsequently retested the correction and reported no remaining issue,
accepting the scoped fix. This does not expand the automated route coverage
or establish a new donor-audio listening comparison.

```sh
python3 tools/play_demo_only1.py --restoration star-world-forest --show-location
```

This starts a fresh uncleared practice session at map 6, `$0158,$01A8`,
translevel `$03`, room `$003`. Enter the star normally. B controls the
parrot's upward movement; R fires its projectile. Clearing the secret exit
changes the node into the existing World 1 portal. Restart the launcher to
play the course again; do not use `--complete-all` for this entrance.

## Donor and scope

The [identity investigation](star-world-middle-left-identity.md) established
that cheap_demo's room `$003` repeats water room `$120`. demo6/demo7 retain
the distinct vine/forest course. demo8 retains that course too, including
the same 14 sprite records, and supplies updated music objects and valid
sprite-code protections. The pinned demo8 image is the donor here; this is
a content choice, not a claim that demo8 is the latest complete game.

The [recipe](../config/restorations/star-world-forest.json) uses the accepted
center ROM as its base and installs:

- Room `$003` Layer 1, its 143-byte Layer 2 stream, sprite placements,
  secondary headers, background-format flags, graphics selection and palette.
- Missing ExGFX `$15D`, relocated to unused `$FC0`. Existing graphics
  `$B0,$99,$B9,$9A` decode identically between the donor and recipient.
- The parrot, its projectile and the vine enemies. Donor slots `$0D,$0E,$47`
  become previously unreferenced ordinary-sprite slots `$B0,$B1,$B2`.
  The consecutive parrot/projectile ids preserve the donor's `id + 1` spawn.
- The normal-goal room `$04E`, including its complete 34-byte object stream,
  two missing graphics streams `$14D/$14E` (now `$FBF/$FBE`), graphics
  selection and palette. Its background stream and secondary headers already
  match the donor; standard GFX `$1F` also decodes identically.

The missing final music object in the recipient goal-room stream was material:
without donor `40 60 5E`, entry attempts stock song `$02` and waits for SPC
acknowledgement at `$0F:C347`. Copying the complete donor stream selects the
existing recipient song `$5D` and the room loads normally.

The room-settings byte at `$05:DE03` also needs to change from `$40` to `$00`.
Both original demo7 and demo8 use `$00`. During level initialization,
`$05:DD12` sets the global water flag `$85` when bit `$40` is present; Mario's
in-water state `$75` then becomes active throughout the course. The water
duplicate left that bit enabled despite the replaced terrain and graphics.
The follow-up repair changes exactly this one ROM byte. Fresh reference and
native checks require `$85=$75=0` during entry, shooting and B/right movement,
matching a fresh unmodified-demo7 room diagnostic. Parrot flight is retained.

Room `$003` has ten screens. Its usable screen-`$07` exit leads to `$04E`;
the end-area key/keyhole supplies the secret exit. The old screen-`$0F`
record pointing to `$04B` is beyond this room's screen count and is retained
as donor data. Room `$04B` is not overwritten.

## Room-scoped Map16 definitions

Copying graphics alone leaves cloud fragments in place of vines because the
recipient changed their Map16 definitions. The original recipient bank
`$12:8000–FFFF` stays byte-identical to the accepted base. A private complete
donor copy occupies `$44:8000–FFFF`, protected by a RATS header at `$43:FFF8`.

Two small ROM shims select that copy only while room `$003` is loading or
active, in modes `$11–14`. The graphics entry at `$06:F540` replays the
overwritten `TAY/CMP`, continues the original routine and redirects only its
bank-`$12` result. The ActsLike read at `$06:F623` selects the matching private
collision definitions. Other calls retain the original lookup results.
The mode check masks the unrelated high byte at `$0101`.

Sprite programs retain their original bank-local addresses in banks `$3C`
and `$35`, where their data-bank accesses still reach low WRAM mirrors.
The old `$0D/$0E/$47` recipient slots remain untouched, so enabling this
course does not enable their dangling placements in unrelated rooms.
The builder validates vacant sprite slots, shared helper identities, source
payloads, byte edits, empty allocations, RATS geometry and output identity.
Raw streams are length-pinned: embedded `FF` in a Layer 2 stream is not a
terminator for the copy operation.

## Automated qualification

Both the pinned Snes9x reference and native executable pass these checked-in
routes on the candidate below. Position/camera shortcuts and damage immunity
are diagnostic fixtures; no completion flag, key-carried state, goal timer,
exit destination or SRAM value is written by the exit tests.

| Route | Observed result on both hosts |
| --- | --- |
| `star-world-forest-entry.script` | Active forest, live parrot, R creates the projectile, projectile moves, B/right changes Mario's position without losing a life. |
| `star-world-forest-attack.script` | A real projectile collision changes two live vine enemies from sprite status `$08` to defeated status `$02`. |
| `star-world-forest-normal.script` | Existing pipe exit reaches `$04E`; real tape collision starts `$1493`; hub return and File A reload retain flag `$8C` in WRAM and both SRAM copies. |
| `star-world-forest-secret.script` | Real key pickup/keyhole ending saves `$8E`; reload retains it; the completed node warps to map 0, `$01B8,$01E8`. |
| `star-world-forest-death.script` | Falling below the camera causes death, returns to the hub with one life lost, and permits a fresh forest entry. |

The copied Layer 1 payload is byte-identical to the pinned donor. Initialized
low/high Map16 buffers match the donor diagnostic apart from its single
overworld forcepoke byte `$7E:D7A5`: that fixture overlaps the level buffer
and keeps `$03` there; the recipient correctly has air `$25`. The donor's
same-number-room fixture is not a natural donor-map route qualification.

The preceding `94c48ebe…` checkpoint's fresh baseline/candidate reference checks cover all eight other hub entrances
with 77 semantic scene samples. Native checks additionally cover the
lower-left, upper-left and center routes. Modes, rooms, lives and interactive
positions agree within the probe bounds. The lookup shims add guest instruction cycles, so these are
not byte-identical frame/animation comparisons. A few existing entry probes
end in death on both versions; their noninteractive death animation can be
up to two frames apart. A fresh native/reference check on the unchanged
center baseline also has a one-frame loading difference.

The 48 restorer/launcher tests pass, including embedded-`FF` copies, protected
bank clones, conflicting allocations, unsafe sprite data banks and unreviewed
graphics-record rejection. Local evidence is recorded in
`local/reports/forest-star-qualification.json`; capture prefixes are
`forest-star-accepted-*` and `forest-qualified-regress-*`.
The first four route captures predate comment cleanup only; captured receipt
hashes and identical normalized commands are recorded separately.

After the one-byte water correction, all five forest routes were rerun on
reference and native hosts. Ordinary/secret saved flags remain `$8C/$8E`, the
portal still transfers to World 1, two vine enemies are defeated by real shots,
and death/reentry still succeeds. The new evidence is
`local/reports/forest-water-flag-qualification.json`, with captures
`forest-water-fix-{attack,normal,secret,death}-{reference,native}`,
`forest-water-check-entry-{reference,native}` and
`forest-water-fix-demo7-baseline`. The earlier eight-entrance comparisons are
retained as preceding-checkpoint evidence; the exact one-byte diff is separately
verified, and no other room setting or engine instruction changes.
The checked-in entry route now fails immediately if either water flag is set.

## Music and remaining limits

The forest and goal room use existing recipient song `$5D`, already restored
by the earlier upper-right recipe. A diagnostic dump confirms demo8's forest
selects sequence `$6008`; 10 of its 16 intro/loop channel graphs match this
recipient arrangement exactly. This is a related revised arrangement, not
an exact donor-audio transplant or a new manual listening acceptance. Local
evidence: `local/probes/forest-star/music-identity.json` and
`forest-star-donor-audio-identity`.

This checkpoint qualifies assisted mechanics, exits, saves, portal behavior
and death/reentry. It does not claim an unassisted complete playthrough,
all collectibles, exact original entrance presentation, or whole-game fidelity.
The existing center Boss-ending exception remains unchanged.

## Identity and reproduction

Candidate ROM SHA-256:
`a246c9370f71e2ee1db990724222d877c96476ba3e3dd4ff98b2db160b0d4872`.

Native executable: `local/build/star-world-forest/BrutalMarioForestStarSNESRecomp`,
SHA-256 `8d9f00be7f7f8f52ec5524e8d39a01ac284f648ee67b4c8b8badf45caa89de65`.

```sh
python3 tools/restore_star_world_1.py --target star-world-forest
# Scaffold once into an absent experiment directory:
python3 tools/m1.py scaffold --target star-world-forest
python3 tools/m1.py generate --target star-world-forest
python3 tools/m1.py build --target star-world-forest
python3 tools/m1.py reference --target star-world-forest --script recomp/inputs/star-world-forest-normal.script --capture forest-normal-reference-new
python3 tools/m1.py native --target star-world-forest --script recomp/inputs/star-world-forest-normal.script --capture forest-normal-native-new
```
