# Cumulative center candidate and remaining completion boundary

The current center candidate includes all eight qualified surrounding hub
courses, the center graphics/sprite/music dependencies, the powered-Mario
damage rollback and the controlled cannon-flight qualification. The center
boss ending remains unqualified; this is not a claim that all nine courses
have completed-clear acceptance.

Current candidate SHA-256:
`e0fb3837d227ca2fcacb389572fb6ac519b37a03d57b385e1dcb83aedf7f2e31`.
Its base is the accepted lower-inner ROM
`1c35a893ec79fa369a68874b7743943c1e08532426d91bfa4ceca33e143df0e9`.
The earlier center-only baseline `6db0bb2e…` is retained in the damage and
cannon reports as the identity originally tested there.

## Current checks

Fresh native and reference runs on this exact candidate verify:

- Powered Mario takes a real Koopa hit, shrinks and continues with the same
  life total. See [the damage regression](center-damage-regression.md).
- Actual cannon contact, followed by B without directional input, crosses
  the second-DK pit and collects the DK coin. The relevant native/reference
  samples match. See [the legacy comparison](center-cannon-flight.md).
- Five real DK collisions raise the count to 5, award the ordinary extra
  life and set `$1F30=$20`. This uses paused position/camera fixtures and
  does not qualify saving the center DK result.
- The actual end-star transfer and existing doors reach room `$079`.
  Real blue-block pickup/drop contacts raise the boss hit count to 4 and
  enter phase 2. The attack fixture holds Mario's position and grants
  damage immunity; it is not an unassisted fight or victory acceptance.

The input scripts describe their shortcuts explicitly. They do not write
coin totals, boss hit counts, completion results or SRAM. Their limited
scopes are recorded in each script.

Capture prefixes on this ROM are `center-cumulative-hurt`,
`center-cumulative-cannon`, `center-cumulative-coins` and
`center-cumulative-boss`, each with `-reference` and `-native` suffixes.

All 239 previous native WRAM/framebuffer samples across nine routes remain
exact on the cumulative candidate. The new lower-inner 100-coin exit and
center death/re-entry also pass fresh runs on this identity: both SRAM
copies retain the lower-inner `$8F` result after File A reload; a center pit
death loses one life, returns to the hub and permits re-entry with that life
total retained. Subsequent lower-inner and upper-inner pit checks also lose
exactly one life, return to the hub and re-enter their respective courses
with that life total retained. The scripts are
`star-world-lower-inner-death.script` and
`star-world-upper-inner-death.script`; capture prefixes are
`center-cumulative-{lower-inner,upper-inner}-death`, with both host suffixes.
These make 16 additional bounded host checks. Local reports
retain receipts and assertions in
`local/reports/center-cumulative-qualification.json`; neither ROMs nor
captured states are distributed. The native executable SHA-256 is
`590b76b55eaa8c35268ac0f9cbdb5f1e9bb68f0ae449363c07bf497bf7591ebe`.

## Boss ending

The installed custom `$24` RATS block is 3,603 bytes, SHA-256
`d9ac74c7c0f05ba26dcfff5c2a09da94dff42d57cafe25361c4343fdcd1f448f`.
cheap_demo and demo8 contain exactly this block. Room `$079` selects its
boss class; the source's `$71=6` transfer belongs to the separate room
`$078` item class. The room `$079` level-ASM stub is `RTL`.

The matching source dispatches boss states 0, 1 and 2. Four real hits enter
state 2. That state stops the blue-block spawner, creates its orbiters,
then repeats its movement/attack cycle. There is no implemented terminal
victory state or level-end store in this program. Additional hits would
fall back to the state-0 handler rather than select a completed ending.
The restored block has not been truncated, and the recipe has not invented
a goal, boss-state write or save result.

The bounded phase captures remain in room `$079`, mode `$14`, with goal
timer zero and the center's completion byte unchanged. `$13CE` can already
be set by the preceding room transfer, so it is not used alone as evidence
of boss victory. A completed clear would require the real ending, correct
overworld return and a retained SRAM completion result.

A survey of the nine prepared versions found the matching star program in
cheap_demo and demo8, with identical code. Demo6 and demo7's same-number
room `$00A` has a different 2,756-byte object stream and no custom sprites;
it is not a drop-in completed version of this star course. No completed
corresponding boss donor has been identified. The local survey is
`local/reports/center-donor-program-survey.json`; signature absence is not
treated as proof that another version cannot contain a differently
identified program.

The subsequent `tools/audit_star_boss_donors.py` search derives each version's
SpriteTool table from its installed constructor, examines every type-1 slot,
and scans every valid RATS block rather than relying on sprite `$24` or room
`$079`. A candidate requires the known code hash or at least three reviewed
markers: the hit-counter load/store, graphics slot `$1D4`, and the paired
item/boss room initialization. Marker hits outside protected blocks are also
reported; none were found in the nine inputs.

| Prepared version | Installed type-1 records | Valid RATS blocks | Related programs found |
| --- | --- | --- | --- |
| demo-1-1 | 12 | 2,199 | 0 |
| 7hero | 12 | 2,366 | 0 |
| cheap-demo | 148 | 2,301 | 1: the unchanged `$24` program |
| mazo | 3 | 2,305 | 0 |
| ow | 1 | 2,229 | 0 |
| demo6 | 141 | 1,833 | 0 |
| demo7 | 137 | 1,884 | 0 |
| demo8 | 148 | 2,268 | 1: the unchanged `$24` program |
| demo-only-1 | 12 | 2,147 | 0 |

Both newer supplied `star.asm` copies are 39,310 bytes and have SHA-256
`ee1eb8ee79618c50c6866cbb32f78e33956b010135775b48575a1c9c813988d4`.
They contain the same phase-2 cycle and no subsequent mode-3 handler. The
19,321-byte data1 source is a different star program without this boss
dispatcher. All three extracted sources match the corresponding entries in
the original source ZIPs. This adds no completed matching donor. The
fingerprint remains a heuristic: differently implemented code can evade it,
and the inventory does not establish room correspondence or playability.

Reproduce the read-only search after preparing the pinned version images:

```sh
python3 tools/audit_star_boss_donors.py
```

The report is `local/reports/center-alternate-program-audit.json` and records
each input hash, derived table, candidate and archived source match. This
research does not change the cumulative ROM or its accepted checks.

Finishing this last acceptance item therefore needs either an explicit
exception preserving the donor's unfinished ending, or a completed matching
donor. Designing a new ending would be new content, beyond copying a
verified playable donor. The overall restoration goal remains open while
that boundary is unresolved.

## Launch

```sh
python3 tools/play_demo_only1.py --restoration star-world-center --show-location
```

Restart the command after rebuilding to replace an already-running older
process. The practice launcher still creates a disposable uncleared save.
