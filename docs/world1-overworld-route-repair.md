# World 1 overworld route repair

Date 2026-10-24. Status: **implemented and qualified (12/12)**; user playtest
pending. The accepted Demo 1-1 line plays all three World 1 courses individually,
but the overworld route onwards from 1-1 was missing in the source build. This
checkpoint repairs it as a three-byte reviewed restoration on a descendant target.

## Result

Target `demo11-world1-route` (descendant of the accepted `demo11-sprite0b`):

- ROM SHA-256: `5265a7bd3f1ee818683287c5429c67d903c4d90a41d8c09cefc53a965d2f1057`
- Recipe: `config/restorations/demo11-world1-route.json`
- Launch: `python3 tools/play_demo_only1.py --restoration demo11-world1-route --show-location`
- Qualifier: `python3 tools/qualify_demo11_world1_route.py`; report
  `local/reports/demo11-world1-route-qualification.json`
- Route script: `recomp/inputs/demo11-world1-route-walk.script`
- Captures: `local/captures/d11-route-walk-{ref,native}`

Exactly three bytes differ from the accepted base. The overworld route-enable
table is mirrored into WRAM at `$CA00` from ROM physical `0x679DF` (verified by
matching the loaded map WRAM byte-for-byte in both builds). Original Demo 1-1
zeroes three cells around the 1-1 node that demoOnly1 sets to `20/04/04`:

| ROM offset | SNES | before | after | meaning |
| --- | --- | --- | --- | --- |
| `0x67A63` | `$0CFA63` | `00` | `20` | right/up-path enable at the node |
| `0x67A72` | `$0CFA72` | `00` | `04` | up-path enable |
| `0x67A74` | `$0CFA74` | `00` | `04` | left-path enable (towards 1-2) |

Diagnosis chain: after a real 1-1 clear the map froze at `(0x48,0x198)` with
`$CA84/$CA93/$CA95 = 00/00/00`; writing the three cells back in WRAM restored
movement (left reaches `(0x18,0x1B8)`, up reaches `(0x18,0x178)`), matching the
demoOnly1 behavior recorded in the earlier route audit. The original Demo 1-1
ROM contains the same zeros, so this is unfinished upstream content, not a
restoration regression.

## Qualification

On both reference and native builds, with the accepted assisted 1-1 goal
flight and **no map fixtures after the goal**:

1. the real clear event itself walks the player along the enabled path to the
   1-2 node `(0x18,0x1B8)` (`$1ECB=8A`, `$13CE=01` intact);
2. the repaired cells load from ROM as `20/04/04`;
3. the normal level-entry button opens **room `$010`** (1-2), mode `$14`.

`tools/check_demo11_line.py` now reports **12/12** with the new
`qualify_demo11_world1_route` check; the earlier 11 checks are unchanged and
still pass against their pinned identities. The qualifier pins the ROM, base,
binary, script and both capture receipts, audits every fixture write in the
script, and asserts the candidate differs from the base at exactly the three
reviewed offsets.

## Acceptance

On 2026-10-24 the user playtested the repaired build and confirmed the map
route is fixed: the natural 1-1 clear walks to the next node and progression
works. The repair is accepted; `demo11-world1-route` is the accepted head of
the Demo 1-1 line.

## Post-acceptance World 1 connectivity census

After the user's acceptance, a bounded census (`local/captures/d11-w1-census`,
`d11-n106-survey`, `d11-node12-survey`; map-transfer fixtures only, natural
direction presses) mapped the usable World 1 graph on the accepted head:

| Node | Reachable neighbours |
| --- | --- |
| 1-1 `(0x48,0x198)` | left -> 1-2, up -> `(0x18,0x178)` |
| 1-2 `(0x18,0x1B8)` | up -> 1-1, down -> room120 node |
| room120 `(0x58,0x1D8)` | left -> 1-2, down -> room106 node |
| room106 `(0x88,0x1F8)` | right -> room138 node, up -> `(0x68,0x1B8)` |
| room138 `(0xA8,0x1D8)` | up -> castle, down -> room106 node |
| castle `(0xA8,0x1A8)` | down -> room138, right -> `(0xE8,0x1A8)`, up -> `(0xA8,0x158)` |

The main chain 1-1 -> 1-2 -> 120 -> 106/138 -> castle is fully connected with
no further zeroed route cells. Unexplored side nodes (`(0x18,0x178)`,
`(0x68,0x1B8)`, `(0xE8,0x1A8)`, `(0xA8,0x158)`) were not entered in this
census; entering a node and reading `$10B` remains the only reliable course
identification.

## Remaining scope

- The right-path enable byte (`0x67A63 -> 20`) restores demoOnly1 parity but
  the Yoshi's House node to the right was not separately entered in this run.

## Accepted base at repair time (preserved)

Head target `demo11-sprite0b`, ROM SHA-256
`584117d2755465d2ad2ac644c0f10a59f3412b25eafd946ffc7178cfb17eabfe`, binary
`BrutalMarioDemo11Sprite0BSNESRecomp`, acceptance 11/11 before this repair,
user-playtested on 1-1, 1-2 (full natural clear) and room 138. Chain:
`demo11-base` -> `demo11-room106` -> `demo11-room010-gfx` ->
`demo11-room010-music` -> `demo11-room138-audio` -> `demo11-room0cb-gfx` ->
`demo11-sprite8d` -> `demo11-sprite0b` -> **`demo11-world1-route`**.
Rollback documentation and backups are unchanged; see `docs/rollback.md`.

## Problem statement and prior evidence (historical)

After clearing 1-1 the overworld did not allow progress: the clear itself worked
(`$1493` tape, map return, `$1ECB = 0x8A`, `$13CE = 0x01` on both hosts), but at
`(0x48,0x198)` no direction input moved the map player, and pressing A re-entered
1-1 - the node had no outgoing path. The user confirmed the original Demo 1-1 ROM
behaves the same way, so this was unfinished source content, not a restoration
regression. Hypothesis 1 (missing path data) was confirmed as the route-enable
cells described above; the map visuals differ between builds but were not the
blocker.

Pre-repair evidence captures: `local/captures/d11-mapdiag`, `d11-mapmove`,
`d11s0b-11-goal-{ref,native}`, `only1-11-goal`, plus
`local/frames/map-{demo11,only1}-after-clear.png`. Post-repair evidence:
`d11-route-repro1`, `d11-route-threecell{,2,3}` (WRAM diagnostics, fixture
labelled), `d11-route-walk-{ref,native}` (qualification).
