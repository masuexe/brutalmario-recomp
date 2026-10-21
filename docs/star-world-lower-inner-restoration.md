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
  `1c35a893ec79fa369a68874b7743943c1e08532426d91bfa4ceca33e143df0e9`.
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

Death/re-entry, all DK coins and an unassisted 100-coin route remain outside
this checkpoint. The separate center-course damage regression and reported
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
