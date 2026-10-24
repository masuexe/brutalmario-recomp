# World 1 castle integration: investigation state

Date 2026-10-24. Status: **surveyed; defects located; repair not started**.
Head under test: `demo11-room106-music` (accepted 13/13 line). The user
asked for a natural castle clear; the survey found the castle needs its own
restoration pass first.

## What the user reported

- The castle course (`10E`) contains a missing custom sprite the user has
  never seen (unknown identity).
- It is uncertain whether the boss door is reachable at all.

## Survey facts (captures `d11-castle-*`, `d11-mask-room*`, `d11-f0-probe`)

- Castle `10E` is a wide horizontal course: the right wall sits beyond
  `X=$10EA` (17+ screens). An aerial sweep (air-swim fixture) traverses it
  without finding a visible boss door at ceiling height.
- The screen-5 exit poke (proven on the demoOnly1 line) still works: it
  leads to the mask room `$08C`, a ~`$6B0`-wide corridor ending in a
  decorative wall - no boss door there either.
- A ground walk with invulnerability dies repeatedly in the opening pits
  at `X=$82` and `X=$9C` (pits are not covered by invulnerability). This
  is consistent with missing platform-type sprites in the opening, though
  the aerial pass shows ordinary sprites (firebar `51` clusters, `9F`,
  `B7/B8`) rendering and acting normally.
- The sprite list for `10E` uses ids `06` and `F0` (20 entries). `06` is a
  stock type. **`F0` is deployed exactly once** (list entry 14:
  `cmd=19 xy=63`) and **never appears in any runtime sprite table** across
  every capture - its initialization fails silently. The slot record at
  `$31:8272 + F0*16` is byte-identical across demo11, cheap_demo and
  7hero, so the record exists but the pointed-to behaviour/graphics may
  still be incomplete on this line.
- The opening pits and the missing `F0` are the two concrete defects so
  far; the boss door has not been located (it may sit behind restored
  content, or the castle may route to Lemmy through an exit not yet
  triggered).

## Next steps

1. Decode the sprite-list screen encoding precisely, pin the `F0` site,
   and observe what cheap_demo/7hero render there (donor comparison) -
   the same slot-record-vs-behaviour gap pattern as the earlier `8D/0B`
   sprite ports on this line.
2. Verify the opening pits against donors: if a platform/bridge sprite is
   missing there, port it the same way.
3. Once the course is traversable, complete the integration: real Lemmy
   defeat, clear event, map state, save/reload persistence.

All probes used labelled fixtures (air-swim, invulnerability, position
pokes); no goal, event or completion values were written. The accepted
head and its 13/13 acceptance are untouched.
