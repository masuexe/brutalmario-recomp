# Demo 1-1 line: playtest checklist

Date 2026-10-23. This is the human acceptance step for the Demo 1-1 rebase. All
automated checks pass (`tools/check_demo11_line.py`); what remains needs eyes and ears.

## What this build is

- Base changed from demoOnly1 to **Demo 1-1**, so World 1-1 and the World 1 castle are
  the newer layouts, with their own custom sprite behaviour.
- Five dependency recoveries were ported onto that base: room 106 graphics `1A2`,
  room 010 graphics `151`/`102`, room 010's missing song `2F`, room 138's private song
  `7E` (plus its sample bank selector) and the shared graphics `12A`.
- Custom sprites `8D` and `0B` are **not** ported: Demo 1-1 supplies working
  equivalents natively.
- Head target: `demo11-room0cb-gfx`; save games are isolated per target, and Demo 1-1
  saves use a different SRAM format from the demoOnly1 line.

## Launching

```
# World 1-1 on the new base (the main objective of this rebase)
python3 tools/play_demo_only1.py --restoration demo11-room0cb-gfx --level demo11-world1-1

# World 1-2 (ported graphics 151/102 and song 2F)
python3 tools/play_demo_only1.py --restoration demo11-room0cb-gfx --level demo11-world1-2

# World 1 room 138 (ported private song 7E and its sample bank)
python3 tools/play_demo_only1.py --restoration demo11-room0cb-gfx --level demo11-world1-138
```

Useful extras: `--show-location` prints map coordinates and room IDs in the terminal;
`--air-swim` enables swimming in air for exploration (a fixture, not normal play);
`--complete-all` marks the practice save's levels and events complete.

## What to check

**World 1-1** (main):

1. The layout should be the *newer* one - four screens longer than the demoOnly1
   course, with its own springs/bouncing objects.
2. Mario should start on the ground, not fall at the start.
3. The bouncing objects should bounce Mario normally.
4. Reaching the tape should complete the course and return to the map.

**World 1-2**:

1. The tileset should look correct rather than like unrelated graphics.
2. The music should be audible and sound like the intended song (this is the `2F`
   transplant; a music-selection byte is not proof of correct sound).
3. The pipes should work when entered in normal play. The scripted assisted route
   cannot enter the first pipe on this base, and that is a known version-level table
   difference, not a port error - a real playthrough is the deciding evidence.

**Room 138**:

1. The custom object placed in the room should appear and behave sensibly.
2. Its private song should be audible.

## How to report

Describe the symptom and where it happened: which course, which screen or room ID
(`--show-location` shows it), and what you expected instead. A screenshot or capture
directory helps. Please do not adjust the ROM or the recipes to work around a symptom;
report it so the cause can be pinned.

## Not defects (known limitations)

- The assisted route scripts for the *old* 1-1 layout cannot be reused: their goal
  positions assume demoOnly1's course.
- Scripted 1-1 goal detection is blocked because this hack remaps sprite identity and
  placement between level data and runtime; a playthrough closes that gap.
- The room 010 scripted pipe route fails on this base for the table reason above.
- Practice entrances are teleport fixtures, so odd spawn spots during exploration are
  fixture artefacts, not course behaviour.

## Reverting

Every migration is an appended descendant target, so reverting means launching an
ancestor (or the demoOnly1 line). The pre-migration snapshot and the two rollback
routes are documented in `docs/rollback.md`.
