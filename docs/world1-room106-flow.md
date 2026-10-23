# World 1 room106: chase clear and death regression

This extends the previously accepted graphics/gameplay recovery on the current
`world1-next-course` cumulative target. No ROM or runtime code changed.
Room106 music is still incorrect and explicitly deferred by the user.

## Identity and replay

- ROM: `3a7fd69f58c541e73ffeffaad91f4ff1bbba48fdbba87d95b37b1d68195eda7c`.
- Native binary: `7efb8fa11c57d83c779fa07889dda0cd5643eead8e4323f55b43383c818a2973`.
- Donor: pinned original `cheap-demo`, ROM
  `f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822`.
- Inputs: `recomp/inputs/world1-room106-clear.script` and
  `recomp/inputs/world1-room106-death.script`.
- Check: `python3 tools/qualify_world1_room106_flow.py`.
- Report: `local/reports/world1-room106-flow-qualification.json`.
- Captures: `local/captures/world1-106-clear-qualified-v3-{reference,native,cheap}`
  and `world1-106-death-qualified-{reference,native,cheap}`.

Fresh captures are made with `tools/m1.py reference` / `native`, target
`world1-next-course`. The donor uses `tools/probe_reference.py` with
`local/content-versions/cheap-demo/input-manifest.json` and `rom.sfc`.
Use new capture names and update the qualifier's explicit names when collecting
a new set; existing evidence directories must remain intact.

## The actual exit mechanism

The shared level-script prefix at physical ROM `171A90` matches cheap_demo.
Its behavior agrees with the supplied `data1/levelasm/yoshi.asm` and the runtime
captures: the initial mount starts the chase and forcibly dismounts Mario;
the late-course camera position changes Yoshi's running behavior; re-mounting
Yoshi sets `$7FFD06=1` and displays message2; after message dismissal the script
sets `$1493` and starts the normal goal sequence. There is no goal tape or pipe
exit to find at the far wall. Running to that wall alone does not complete it.

The clear fixture walks through the course with invulnerability, aligns Mario's
X and horizontal velocity near the final wall, and uses repeated jump edges to
re-mount Yoshi. Those edges also dismiss the real success message. It never
writes riding, level-script state, message, goal, completion, events or SRAM.
The recorded jump sample at which re-mount succeeds can differ between hosts;
the qualifier checks the actual captured outcome rather than one fixed jump.

All three hosts show real re-mount and goal activation, then return to map0
`(088,1F8)`. Course2A's clear byte `$1ECC` changes `04 -> 84`, event bit
`$1F02 & 10` is set, and no life is lost. Both active Map16 buffers match the
donor at the settled sample across all 11 horizontal screens.

## Real death and re-entry

The second fixture uses only the initial map transfer. Ordinary movement and
an enemy encounter trigger `$71=09`; the game returns to the map with exactly
one fewer life and clear byte04. Re-entering reaches room106 in mode14, and the
chase success flag remains zero. This passes on reference, native and donor.

## Collectibles and onward survey

The loaded 11-screen terrain has zero standard DK/dragon-coin tiles (`02D/02E`)
at the settled sample, on all three hosts. This is an inventory result, not a
claim that every custom collectible mechanism was tested. Custom-block audit,
DK persistence and save/reload of this course's clear remain unqualified.

A separate exploratory input, `local/probes/world1-survey/after-room106-entry.script`,
follows the real clear and presses Y at its selected node. Both candidate
reference and cheap_demo enter room120, translevel44, in mode14 at `(0016,0150)`.
Captures: `local/captures/world1-after-106-entry-{reference,cheap}`. This is the
next course to survey; its full traversal, exit and native route are not yet
qualified. Do not infer a full World 1 pass from these samples.

## Later room120 qualification

The [room120 cave regression](world1-room120-regression.md) supersedes the
entry-only limit above for the listed boundaries: natural entry on native,
reference and cheap_demo; five real DK pickups; normal clear; candidate reset
and File A persistence. Its next node enters room138, where the candidate
stalls in Mario Start and cheap_demo does not. Full World 1 remains incomplete.
