# Lower-inner star course restoration

The map-6 entrance at `$0178,$01C8` selects translevel `$3B`, room `$117`.
The cumulative candidate restores its missing warp-star actors and 100-coin
controller on the accepted middle-left ROM. This checkpoint qualifies the
actual 100-coin exit and save, using explicit player/camera shortcuts for
the pickups. It does not claim an unassisted complete route or DK coverage.

## Data and identity

- Recipe: `config/restorations/star-world-lower-inner.json`.
- Base ROM SHA-256:
  `394c59841ce22184b4f804f4ad518f83c26190178127a471364ab615069e0388`.
- Candidate ROM SHA-256:
  `cb3e60179cf83af322ce8d0316e1f2248ef4c02b7bc2b8084cfb99a86f3a30f3`.
  The previous candidate was
  `1c35a893ec79fa369a68874b7743943c1e08532426d91bfa4ceca33e143df0e9`; the
  only difference is the interim song-slot alias described under the cap defect.
- No runtime changes, new graphics, geometry replacement or global entrance
  branch edits are included.

The donor layer-1 pointer `$F0:AA50` maps to physical offset `$382A50`,
within the 4 MiB LoROM. Its 9,333-byte terminated stream is byte-identical
to the recipient stream at `$3A:90B4`, SHA-256
`8e52976f05cfeeb1b3f538c527764c52f0b1fe729bd488ad0c5e56fb87377129`.
The 53-byte sprite lists also match, SHA-256
`28b431f0dd8724f6969495d8b069cb0d286584b8b76bfc09035234de676eb7b5`.
An earlier local handoff incorrectly classified the donor pointer as outside
the ROM; it is a valid high-bank mirror. That missing-geometry diagnosis
has been withdrawn.

| Custom slot | Role | Donor RATS block | Destination | Bytes |
| --- | --- | --- | --- | --- |
| `$30` | `hat.asm`: caps and 100-coin controller | `$1B:8000` | `$34:8000` | 1,680 |
| `$37` | `meta.asm`: warp-star movement | `$21:EC22` | `$36:EC22` | 3,428 |

The complete blocks retain their bank-local addresses. The recipe pins
the source records, empty destinations, room dependency sets and shared
helpers. The recipient constructor remains in use with separately pinned
version-specific constructor bytes. Slot `$30` is also selected by room
`$03C`; slot `$37` by `$016,$0F0,$0F1,$0F2,$0F4`. Those other rooms are
not accepted as playable by this checkpoint.

The exploratory `$00:A6AF` global entrance edit from the preceding session
is preserved locally and excluded from both the accepted middle-left
recipe and this candidate. Restoring the missing actors already lets Mario
pass the former `$0522` stop.

## Qualification

`star-world-lower-inner-route.script` uses real controls after the initial
map shortcut. Both hosts cross `$0522`, ride the warp stars and reach about
`$0D20,$0100`, retaining four lives-minus-one. It is a traversal segment.

`star-world-lower-inner-goal.script` is a separate collision fixture. Real
Start pauses permit player/camera placement at the existing coins; finite
position holds keep Mario there while the guest performs pickups. It never
writes coin totals, actor state, life totals, exit flags, the goal timer or
SRAM. The controller observes 99 coins, then the real rollover to zero,
awards the ordinary extra life and triggers its existing ending. Its code
sets `$141C=1`; this report calls it the **100-coin exit** rather than
claiming a separate normal-exit route.

| Sample, both hosts | Result |
| --- | --- |
| Before pickups | Coins 0, lives-minus-one 4 |
| Late pickup sample | Coins 99 |
| Hundred coins | Coins 0, lives-minus-one 5 |
| Ending | Guest `$1493` timer becomes nonzero |
| Overworld return | Mode `$0E`, `$13CE=1`, translevel flag `$1EDD=$8F` |
| Saved result | Both SRAM copies, `$003B` and `$01E8`, contain `$8F` |
| Reset and File A reload | Mode `$0E`, both copies and WRAM retain `$8F`; lives-minus-one 4 |

The goal captures are `lower-inner-goal-reference` and
`lower-inner-goal-native`. The bounded traversal captures are
`lower-inner-qualified-route-reference` and
`lower-inner-qualified-route-native`. Local receipts pin each ROM, input
script and executable/core identity. The generated local report is
`local/reports/lower-inner-qualification.json`.

Nine previous native routes were rerun on this candidate. All **239**
sampled full-WRAM images and raw framebuffers match their prior baselines:
lower-left, shop, bounded Athletic Special boss entry, upper-left, Snow
Star, upper-right, Sky Star, Cave Star and the middle-left water clear.
The boss-entry regression is not a complete boss-fight acceptance claim.

Death/re-entry was outside the original checkpoint above. A subsequent
fresh-session check on cumulative center ROM `e0fb3837…` confirms a real pit
death loses one life, returns to the map and permits re-entry into `$117`
with that life total retained in both hosts. See
`star-world-lower-inner-death.script` and captures
`center-cumulative-lower-inner-death-{reference,native}`. All DK coins and
an unassisted 100-coin route remain unqualified. The center damage regression and reported
cannon-distance issue are tracked in
[the center damage report](center-damage-regression.md).

## Launch

```sh
python3 tools/restore_star_world_1.py --target star-world-lower-inner
python3 tools/m1.py scaffold --target star-world-lower-inner
python3 tools/m1.py generate --target star-world-lower-inner
python3 tools/m1.py build --target star-world-lower-inner
python3 tools/play_demo_only1.py --restoration star-world-lower-inner --show-location
```

Scaffold only when the target directory does not already exist. Practice
launches use disposable uncleared saves so completion does not replace the
course entrance with a Warp Star.
## Known defect: cap pickup freezes the game

Reported 2026-10-21: in this course, eating a cap (hat) changes the music and
the game freezes some time later.

**Root cause.** The recipe restores custom slot `$30` (`hat.asm`: caps and
100-coin controller), which requests music through `$1DFB`:

| Trigger | Song id | Donor table entry | Recipient table entry |
| --- | --- | --- | --- |
| Cap picked up (sets `$7FFFD0/$7FFFD1/$7FFFD2 = $FF`) | `$22` | `30FEEC` | `13CCE2` - a *different* song |
| Cap effects expire (flag drops below `$11`) | `$21` | `13A412` | **`000000` (no song installed)** |
| 100-coin controller award | `$1E` | `0F6CE1` | **`000000` (no song installed)** |

The **recipient's** song pointer table is three bytes per id, big-endian, at
`$0F:E000` (confirmed against the four recipes that restore music). This recipe
restores no music at all, so both ids it requests are empty in the recipient.

The donor does not use the same layout. Reading donor ids through that table
returns payloads with a different destination base (`0x0410` for `$54`, against
`0x5400` in the adapted recipient payload) and some entries are not valid LoROM
addresses at all. Donor music is reached through the per-recipe `music` groups,
not by id-to-id table comparison, so a cheap_demo-to-demoOnly1 id map cannot be
built from the two tables as they stand.

The `[count][base][body][0000]` wrapper is also specific to songs the recipes
install. Only three recipient ids and one donor id pass that structural check,
while the recipient actually has 98 installed ids, so the original songs in both
ROMs use the hack's own layout. Matching a candidate song against the donor
therefore needs that original format decoded, or a runtime SPC capture of the
uploaded song, before any automatic map can be attempted.

Requesting an empty id does not fail gracefully: the guest hangs waiting for
the music engine. Minimal reproduction on `star-world-lower-inner`:

```
enter the course, then   poke 1dfb 21
```

`$1DFB` stays `$21` and is never consumed, and full WRAM is byte-identical from
30 frames after the poke through 600 frames, while the emulator keeps
advancing. Control runs: the same poke on `cheap_demo`, where `$21` is
installed, keeps running normally (5,141 bytes changed over the same window),
and poking `$22` or `$1E` on the candidate does not hang.

This matches the report exactly: the music changes on pickup (`$22`), then the
game freezes when the caps expire and `$21` is requested.

**Interim mitigation (applied).** The recipe now aliases both empty slots to the
course's own level theme: `0FE063` (`$21`) and `0FE05A` (`$1E`) are set to the
three-byte entry of `$40`, currently `15EFEE`, through equal-width
`code_patches`. Re-running the reproduction keeps the game alive (`$1DFB`
returns to zero, full WRAM keeps changing) instead of hanging, and the
100-coin exit still qualifies. This removes the crash; it does **not** play the
donor tracks, so it stays documented as an interim measure.

**Proper fix direction.** Restore the songs `hat.asm` depends on - `$21`, `$1E`
and, for fidelity, `$22` - the same way the lower-right, middle-right,
upper-right and center recipes restore their tracks: one `music` block per song
with its own allocation, `pointer_address` (`0FE063` for `$21`, `0FE05A` for
`$1E`, `0FE066` for `$22`) and reviewed relocations. Do not leave the empty
slots permanently aliased to
an existing track: that plays the wrong music and is not a faithful
restoration. Do not patch the sprite to skip its music request either.

**Until then.** Grabbing a cap in this course freezes the game. The 100-coin
exit fixture does not grab caps, which is why the qualification passed.

**User acceptance (2026-10-21).** The user re-tested in game and reports: eating
a cap switches the music, and when the cap expires the music returns to the
course theme with no freeze. The interim alias is therefore confirmed to remove
the crash while leaving the proper track restoration open.

### Runtime SPC capture makes a faithful fix feasible

The diagnostic core can now dump the full 64 KiB SPC/APU RAM at a chosen host
frame (`BM_APURAM_FRAME`, `BM_APURAM_FILE`). A dump taken while this course's
level theme is playing shows a complete, already-relocated song sequence at
ARAM `0x5400`:

```
@0x5400: 67 54 77 54 FF 00 02 54 00 ...
```

That is the two pattern pointers, the `FF 00` marker and the `$5402` sequence
pointer, i.e. the same base the music recipes write. Because the image in ARAM
is fully relocated, songs can be compared across ROMs byte-for-byte without
decoding either static format, and a donor song can be lifted as a payload with
`destination_base` `0x5400` and installed through the existing `music` block
with no relocation review.

Concrete plan for the proper restoration: force the intended donor id to play,
dump ARAM, take the sequence image at `0x5400`, and install it at `0FE063`
(`$21`) and `0FE05A` (`$1E`). The same technique gives the cheap_demo-to-
demoOnly1 id map for the wider wrong-music question: fingerprint the `0x5400`
image per id in both lineages and match identical images, falling back to
similarity for arrangements that changed between demos.
