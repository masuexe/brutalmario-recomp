# Star World upper-left cave restoration

Date: 2026-10-20. This cumulative demoOnly1 candidate retains the previously
restored lower-left course and restores the upper-left vertical cave at
map 6 / X=`$0128`, Y=`$0168`, translevel `$04`, room `$004`.
The user has accepted this restoration milestone after testing: custom
sprites load normally, and the original damaged regions no longer occur.
Automated qualification covers the bounded routes below.

```sh
python3 tools/play_demo_only1.py --restoration star-world-upper-left --show-location
```

The launcher creates a fresh, isolated, uncleared practice save and selects
the cave node. Enter normally. Restart the command for another fresh session.
Completion practice flags can turn star nodes into portals, so this preset
rejects `--complete-all`. The original targets and ordinary player saves
remain separate. The new binary is
`local/build/star-world-upper-left/BrutalMarioStarWorldUpperLeftSNESRecomp`.

## Two missing dependencies

Room `$004` selects missing ExGFX `$144` through a `$FFFFFF` pointer. The
original graphics initialization changes 4,839 low Map16 bytes, damaging the
loaded cave. The candidate imports cheap_demo's 1,825-byte LZ2 stream from
`$2D:F41F`, decoding to 4,096 bytes. demo8 has the same compressed stream;
this does not establish release chronology or whole-course donor parity.
The room's graphics word at `$14:AD92` changes from `$144` to unused `$FFC`.
A RATS block occupies physical `$1E2000..$1E2729` (exclusive end), within
reviewed zero padding. The global `$144` pointer remains untouched.

A graphics-only prototype exposed a second defect: the cave was dry and its
water platforms did not work. Custom sprite `$7A` has an empty record in the
recipient. In cheap_demo it implements the platform interaction and water
controller, including swimming physics and the water display's HDMA tables.
A scan of all 512 recipient sprite lists finds `$7A` only in room `$004`.

The candidate copies its complete 1,320-byte RATS block from `$24:8B77` to
`$3D:8B77`. Keeping the lower address unchanged preserves bank-local calls
and data references; the MAIN entry uses the program bank as its data bank.
The recipient's empty `$7A` record at `$10:B82A` receives the donor record
from `$10:B8FD`, with INIT/MAIN banks changed to `$3D`. The existing calls
into shared routines are retained; reviewed ranges at their destinations
are hash-checked in both versions. The graphics and code allocations do not
overlap either each other or the lower-left repair.

The builder preserves recipient object layout, sprite placements, exits,
Map16 definitions, music and save rules. The donor's pre-graphics low Map16
buffer differs at one ordinary coin (`$7E:E056`); that difference is retained.
Enabling water is guest sprite behavior, not an air-swim cheat. No loader or
shared engine implementation is replaced.

The [recipe](../config/restorations/star-world-upper-left.json) pins the
original inputs, lower-left base, graphics streams, sprite code/record,
shared dependencies, allocations and final output. It rejects unexpected
room dependencies, occupied slots, altered code, bank-local relocation
changes and conflicting output files. Build/generation/native launch also
reject a stale scaffold ROM identity, preventing a build receipt from
masking an outdated embedded ROM/mod target.

Final candidate SHA-256:
`7bffb1c7eb369297cd8dc2f6e84c908e718a5f06a5c445c722512f2e67e7aa37`.
The lower-left-only target remains
`88da794a436f97fe86ff60c48b74a8d7160e1ae39d304c648804d80b6d760bb5`.
ROMs, donor bytes, generated code, saves, captures and reports stay untracked.

## Bounded qualification

The tracked inputs use disposable fresh saves. Position shortcuts and damage
immunity help reach interactions; they do not fabricate DK counters/bits,
water state/target, sprite state, completion, exit destinations or SRAM.
They do not qualify an unassisted ascent through the entire cave.

| Input under `recomp/inputs/` | Checked behavior |
| --- | --- |
| `star-world-upper-left-entry.script` | Coherent cave, no low Map16 corruption during graphics initialization, ordinary controls and active level. |
| `star-world-upper-left-water.script` | Actual B presses swim; contact with a real platform changes the water target from `$0CB0` to `$0C90`, and the controller reaches that target. Native, restored reference and same-number donor probe agree on these sampled states. |
| `star-world-upper-left-coins-save.script` | Five real DK/dragon-coin collisions increment counters from 1 to 5; the fifth sets saved bit `$1F2F=$08` and grants one life. Screen `$08`'s actual pipe enters `$048`; its real goal returns to the map and saves slot `$04=$85`. Console reset, File A load and re-entry preserve the clear/DK bit, with no remaining coin tiles. |
| `star-world-upper-left-side-exit.script` | Screen `$06`'s alternate pipe enters `$048`; the existing side-pipe transition reaches `$051`, whose edge returns to the hub without a life lost. |
| `star-world-upper-left-death.script` | A fall loses one life, returns to map mode `$0E` and permits fresh entry into `$004`. |

The saved coin bit is also present in actual SRAM at `$07D0`; the adjacent
checksum changes from `$5A5A` to `$5A52`. File loading restores the initial
life count in both hosts; life persistence is not claimed. The donor probe
agrees on coin pickups, water interactions and the pipe/goal route, but has
different initial/completion flags. Recipient save rules are intentionally
retained; complete donor/recipient state equality is not claimed.

Vertical position shortcuts need a finite hold while the camera catches up;
the hold is released before real left input enters a cave pipe. Earlier
one-shot/clamped probes, the dry graphics-only prototype and a Boss script
that handed control to a player instead of quitting are diagnostic attempts,
not acceptance evidence.

Local capture names, identity receipts and assertions are recorded in
`local/reports/upper-left-checkpoint.json`. Existing lower-left opening,
shop and Athletic Special top-door routes are compared against the previous
candidate: all 28 full-WRAM/raw-framebuffer samples match exactly. All 99
project tests pass in 124.284 seconds, and the local checkpoint's 155 selected
assertions pass. Repeated preparation retains both candidate hashes, input
and upstream identities verify, and `git diff --check` passes.
This checks shared route samples, not a new full Boss fight.
No new AOT variants are required; the accepted Demo 1-1 count remains 68.

## Reproduction and manual acceptance

```sh
python3 tools/restore_star_world_1.py --target star-world-upper-left
# Scaffold once in a fresh workspace; do not reuse a different ROM identity.
python3 tools/m1.py scaffold --target star-world-upper-left
python3 tools/m1.py generate --target star-world-upper-left
python3 tools/m1.py build --target star-world-upper-left
python3 tools/m1.py reference --target star-world-upper-left \
  --script recomp/inputs/star-world-upper-left-water.script --capture upper-left-repeat-reference
python3 tools/m1.py native --target star-world-upper-left \
  --script recomp/inputs/star-world-upper-left-water.script --capture upper-left-repeat-native
```

The user subsequently reported that custom sprites load normally, the
original damaged regions no longer occur, and this stage can pass. This
accepts the upper-left cave restoration milestone and supersedes its pending
manual status. The verified workspace ROM is the SHA-256 above; its executable
matches the build receipt with SHA-256
`eea9c5bd64e90689b4f047defb8bfc393781fb3d1c2144326dc75bec13eb66b1`.
The report does not separately itemize full ascent, every branch, sound or
completion, so no additional coverage is inferred from the acceptance.
No further manual gate is needed to close this stage.

Use this cumulative target as the accepted restoration baseline for subsequent
work. The next investigation is the lower-right star, room `$008`, map 6 /
`$01C8,$01E8`: the recipient stalls at MARIO START, whereas the same-number
cheap_demo probe reaches an active room. Missing ExGFX `$1B3` is a verified
resource dependency; it is not yet established as the complete stall cause.
