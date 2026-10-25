# Custom sprite graphics gap

Date: 2026-10-26. An experiment ported the remaining five cheap-demo custom
sprite records of level rooms: `0x10`, `0x23`, `0x25`, `0x92` and
`0x93`. The batch passed the static checks and moved the graphics blocks
that blocked the sprite windows. The experiment is dropped.

## Finding

Sprite IDs are version-local. A level can place sprite `0x10` without the
custom flag byte, for example room `0x15B` in level `0x07F`. The record
table is global, so installing the cheap-demo record for `0x10` also changes
the plain placements. The sprite then draws tiles that this line does not hold.
Level `0x07F` showed a grey tile area after the experiment. The
translevels `086` to `08A` also changed outcome.

The code record alone is not sufficient for these IDs. Their sprite tile graphics
are missing too. The boss chain keeps the final state that the user accepted for
room `0x49`.

## Retry conditions

1. Locate the sprite tile graphics table and the tile data for each ID.
2. Port the tile graphics together with the code record.
3. Re-run the full-range survey and compare every framebuffer.

## Evidence

- Captures: `local/captures/d11-survey-s2-*` and
  `local/captures/sub-new-*`.
- The unchanged chain is `demo11-gfx-boss76`.
