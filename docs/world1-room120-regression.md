# World 1 room120 cave regression

The cave at map0 `(088,1F8)`, translevel44, is reached naturally after the
room106 chase clear. It already runs on the cumulative `world1-next-course`
target. This checkpoint adds reproducible checks without changing ROM,
graphics, terrain, sprites, runtime, music, events or save behavior.

## Identity and reproduction

- ROM: `3a7fd69f58c541e73ffeffaad91f4ff1bbba48fdbba87d95b37b1d68195eda7c`.
- Native binary: `7efb8fa11c57d83c779fa07889dda0cd5643eead8e4323f55b43383c818a2973`.
- Donor: pinned cheap_demo ROM
  `f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822`.
- Input: `recomp/inputs/world1-room120-coins-save.script`.
- Check: `python3 tools/qualify_world1_room120.py`.
- Report: `local/reports/world1-room120-qualification.json`.
- Captures: `local/captures/world1-120-qualified-{reference,native,cheap-clear}`.

Candidate captures use `tools/m1.py reference` / `native` with target
`world1-next-course` and the tracked input. Use fresh capture names for reruns.
The original donor comparison stops before console reset. Reproduce its exact
prefix with:

```sh
python3 tools/qualify_world1_room120.py --prepare-donor-script
python3 tools/probe_reference.py \
  --manifest local/content-versions/cheap-demo/input-manifest.json \
  --rom local/content-versions/cheap-demo/rom.sfc \
  --script local/probes/world1-survey/room120-donor-clear.script \
  --capture NEW-UNUSED-NAME
```

The qualifier computes that donor script hash from the tracked route. It checks
receipt identities, completed logs, complete WRAM/SRAM, and the actual states.

## Verified boundaries

All three hosts reach room120 in mode14 after the real room106 normal clear,
with Yoshi and water flags `$85/$75=1`. Both loaded Map16 buffers match cheap_demo
across all 14 horizontal screens (6,048 cells per buffer).

The assisted route positions Mario at five actual DK/dragon-coin objects:

| Coin | Upper tile X | Upper tile Y |
| --- | --- | --- |
| 1 | `0250` | `0150` |
| 2 | `0510` | `0090` |
| 3 | `0630` | `0130` |
| 4 | `09B0` | `0090` |
| 5 | `0B20` | `0150` |

Each collision increments both `$1420/$1422` to 1 through 5. The fifth sets
saved bit `$1F37=08` and grants one life. From the fifth coin, real swimming
loads the goal tape at `0CA0` and reaches it. `$1493` becomes nonzero, then the
normal clear returns to map0 `(0A8,1D8)` with `$1EE6: 0B -> 8B`, retaining the
Dragon Coin bit and the extra life. All three hosts pass these checks.

On the candidate reference and native hosts, console reset, actual File A load
and map re-entry preserve the clear/Dragon Coin state; room120 contains no remaining
standard coin tiles. The donor's attempted full route did not restore the same
state after reset (capture `world1-120-qualified-cheap`); no donor persistence
claim is made. That failed extended donor attempt is not accepted evidence for
reload. Its separate `cheap-clear` capture qualifies only through normal clear.

Position and invulnerability fixtures skip course obstacles. They do not write
coin counters, riding, goal timers, message state, completion, events or SRAM.
Direct jumps near the goal can bypass sprite loading; the final route swims
from the last coin so the actual tape spawns. The script qualifies pickups,
normal clear and recipient persistence, not an unassisted full-course run.
Secret exits, room120 death/re-entry and audible music remain unqualified.

## Next actual failure: room138

The real normal clear selects map0 `(0A8,1D8)`, translevel5C. A separate
exploratory input, `local/probes/world1-survey/after-room120-entry-late.script`,
then enters room138. In the candidate reference, both the 600-frame and later
1,500-frame samples remain in mode12 (Mario Start). Original cheap_demo reaches
mode14 at both samples. Captures:
`local/captures/world1-after-120-late-{reference,cheap}`.

The room's graphics record is identical and selects only IDs below100, with no
missing extended graphics pointer found by the existing survey. The raw Layer1
pointer/header also match (`5CEBE5`, `1240249918`). These facts do not establish
all dependencies. Diagnose the actual stall and version-local audio/code/data
before selecting a repair. Do not copy cheap_demo music IDs into the recipient
as an assumed song match. Room106's incorrect music remains deferred.

## Later room138 recovery

The [room138 music recovery](world1-room138-restoration.md) diagnoses the stall
above and introduces the isolated `world1-room138-audio` candidate. Direct and
natural entry now pass on native/reference, with donor terrain, an exact
relocated source sequence and the original sample-bank dependency. Its whole
course remains unqualified; this does not promote an entry check to a full pass.
