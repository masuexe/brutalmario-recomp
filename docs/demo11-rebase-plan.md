# Rebasing the restoration onto Demo 1-1

Date 2026-10-23. The user decided to change the restoration base to Demo 1-1 instead
of reverse-engineering its custom sprite mechanism. This records the evidence behind
that decision and the plan.

## Why rebasing beats sprite reverse-engineering

Migrating the newer World 1-1 *into* demoOnly1 stalled: the level layout, graphics,
sprite placement and headers can be copied, but the custom sprite behaviour cannot,
and without it the course hard-stalls at `x=0xF92` of 24 screens and cannot be
completed. Demo 1-1's custom sprite storage does not use the 16-byte record table
this project restores from, so it would have to be reverse-engineered with no
guarantee of parity.

Rebasing removes that problem entirely, because Demo 1-1 **natively** has:

| Property | Demo 1-1 |
| --- | --- |
| Newer World 1-1 (`105`) and castle (`10E`) | present |
| Custom sprite behaviour for that layout | present |
| Extended graphics `29E 29F 2A0 2A2` | present |
| Music `69 6A 6B 86 B0` | present |

## What still has to be restored on the new base

Both builds share the same missing dependencies, verified by pointer tables:

| Missing | Affects | Note |
| --- | --- | --- |
| Graphics `1A2` | room106 | absent in both builds |
| Graphics `151`, `102` | room010 (1-2) | absent in both builds |
| Music `2F`, sprite `8D` | room010 | absent in both builds |
| Music `21` (song group) | room138 | slot absent in both builds |
| Graphics `12A` | room0CB | absent in both builds |
| Music `1E` | 100-coin cue | absent in both; engine-special |

So the rebase keeps roughly five recoveries instead of the twelve-target chain, and
none of them needs sprite-mechanism reverse-engineering.

## Plan

1. **Base line.** `demo11-base` roots the new chain and reproduces the pinned Demo 1-1
   input exactly (`314496f6…`). No changes at this target.
2. **Port the recoveries** one at a time as descendants: room106 graphics, room010
   graphics/music/sprite, room138 song/sprite, room0CB graphics.
3. **Re-qualify World 1** on the new line: entry, goal/save, death, the 1-1 -> room106
   -> room120 -> room138 chain, using the existing scripts adapted where the newer
   layout changes the route.
4. **Switch the head** once qualified; archive the demoOnly1 line and its backup.

## Risks and mitigations

- **Saves do not carry over.** The baseline SRAM header exponent differs (5 vs 1), so
  practice sessions and existing saves are not interchangeable. The launcher already
  isolates per-target saves; back up before switching.
- **Every qualification must be re-run.** The existing captures pin demoOnly1-based
  ROMs; none of them transfer.
- **Engine flows need re-verification.** demoOnly1 was chosen originally because
  boss/shop/map flows had been exercised there. Demo 1-1's content is largely
  identical, but those flows must be re-run on the new base before acceptance.
- **A few levels are richer in demoOnly1** (`0C5`, `102`, `025` and small rooms). They
  are outside the World 1 scope; evaluate before any wider switch.
- **Rollback stays available**: `tools/backup_state.py` snapshot
  `local/backups/pre-room105-migration-20261023-051544` plus `docs/rollback.md`.
