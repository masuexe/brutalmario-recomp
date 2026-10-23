# World 1 next course: room 010 resource candidate

Date 2026-10-22. Isolated candidate descending from the accepted
`world1-room106` base. Restores the graphics and music that room 010 needs so
the first course's normal exit continues into a course Mario can actually walk
in, instead of falling after the opening message.

## Initial identity (before the room106 music attempt below)

- Recipe `config/restorations/world1-next-course.json`.
- Base ROM `faec11a6f1c12b6a1b667b4bdf6bb8b0169027bda7d19ec4445d7084b4e462fc`
  (`world1-room106`, itself from the accepted `star-world-forest`).
- Candidate ROM
  `f772fe6757107a18d0861b6f9c2a52898d33087713d5410f6049111e703e4ce5`.
- Binary `local/build/world1-next-course/BrutalMarioWorld1NextCourseSNESRecomp`,
  SHA-256 `4a707c1a054f7badac68efd035112ea3026c48951e0cc7ddd924d53ce94f4d8c`.
- Entrance map 0, `$018,$1B8`, translevel `0x10`, room `010`. Its intended
  course number was initially unknown; the user later identified it as 1-2 (see acceptance below).
- Launch: `python3 tools/play_demo_only1.py --restoration world1-next-course --show-location`.

## What changed

4,731 differing bytes, all inside reviewed regions:

| Item | Detail |
| --- | --- |
| Graphics `151` -> private `FBC` | donor `demo8` stream at `30E0A3`, relocated to `0x250000` |
| Graphics `102` -> private `FBB` | donor `demo8` stream at `25E32D`, same allocation |
| Selector patch `14AF1A` | `5101` -> `bc0f`, second occurrence of source `151` reuses `FBC` |
| Music `2F` | donor group at `298009`, 2-byte legacy trailer, `destination_base 0x5400`, pointer `0FE08D` |
| Custom sprite `8D` | rooms `0x10` and `0x4A`, destination `33C3F9` |

There were separate missing dependencies. Missing graphics corrupted the
terrain buffers; the absent song `2F` also stalled the SPC acknowledgement at
`0FC347/0FC34A` during Mario Start. Graphics-only diagnostic builds still stall.
The combined graphics, song, and custom-sprite recovery makes this course
playable; graphics alone are not sufficient to fix its entry.

`adapt_music` gained a reviewed `source_trailer_size` option (2 or 4 bytes) because
this donor group ends with a two-byte legacy terminator; unit tests cover both the
accepted and rejected widths.

## Qualification

`python3 tools/qualify_world1_next_course.py` is a read-only assertion runner.
Report: `local/reports/world1-next-course-qualification.json`. It verifies:

- candidate, base and donor identities against their pins;
- the diff footprint is confined to the reviewed regions; both protected graphics
  payloads match their donor streams and both selectors resolve to the private ids;
- **terrain**: at `entry600` and `ability_walk`, both Map16 buffers (`0xC800`,
  `0x1C800`) match the donor byte-for-byte over the active area of nine screens
  (`9 * 0x1B0` cells);
- **entry**: reference, native and donor all sit in room `010` in mode `0x14`;
- **death**: a real pit death sample exists and re-entry returns to room `010` on
  both hosts;
- **progression**: the first course (room `105`) reaches its goal tape, returns to
  the map, and the normal exit then enters room `010` and Mario can walk there;
- **subroom**: the existing subroom `04A` is still reachable on both hosts.

## Initial qualification limits (superseded where noted below)

- A complete World 1 route, collectibles and audible output remain unqualified.
- Course numbering was initially unknown; the user later identified room `010` as 1-2.
- Overworld connectivity beyond the first course is not claimed.
- This is a bounded resource recovery plus playtest candidate, not a new
  manually accepted baseline.

## User acceptance (2026-10-23)

The user playtested this candidate and reports that the 1-2 course has no
problems. That promotes the candidate from a bounded playtest target to a
playtest-accepted checkpoint, and it also settles the earlier open point about
numbering: the user identifies this course (room `010`) as **World 1-2**.

Accepted scope is exactly what was playtested: the course loads with correct
terrain and graphics, Mario can move through it, and its music plays. Still NOT
qualified: a complete World 1 route beyond 1-2, collectibles, death/re-entry in
1-2 itself, and itemised audible checks of every effect.

## Room 106 course accepted except music (2026-10-23)

The user playtested the room 106 course on the `world1-next-course` build and
reports no problems apart from wrong level music. They explicitly deferred the
music fix, calling it a minor issue that does not affect play.

Recorded acceptance therefore covers: terrain and graphics recovered, normal
movement, and no crashes. Open for this course, besides music: its complete exit
route, DK coins and collectibles, death/re-entry, and itemised audible checks.

## Room 106 numeric music selection attempt (2026-10-23)

The user reported the room 106 course's level music as wrong and deferred the
fix, then authorised using cheap_demo's music for the same level as the
reference.

`cheap_demo` plays music `0x22` in room `0x106` (read from the donor capture
`world1-106-qualified-entry-cheap`, where `$0DDA = 0x22` for the whole course).
The recipient played `0x25`. Room 106's level header sits at `$10:CD61`, so the
music byte at `10CD63` is patched `0x26 -> 0x23` (id + 1).

Verified: a fresh reference capture now reports `room=0x106 music=0x22`.

Candidate identities after the patch: ROM
`3a7fd69f58c541e73ffeffaad91f4ff1bbba48fdbba87d95b37b1d68195eda7c`, binary
`7efb8fa11c57d83c779fa07889dda0cd5643eead8e4323f55b43383c818a2973`. All eight
candidate-side qualifying captures were re-run
against the new ROM and `tools/qualify_world1_next_course.py` passes again.

The intermediate `world1-room106` target retains its previous music selection.
Do not propagate this numeric-ID patch as a proven music correction.

### Latest listening result: incorrect; deferred

The user listened after this patch and reported that the music is still wrong.
Matching `$0DDA = 0x22` across versions establishes only a numeric selection,
not the identity of the uploaded song. The attempt above is **not an accepted
music fix**. The current cumulative ROM retains the attempted selection, but
room 106 music remains an explicit, deferred exception to gameplay acceptance.
Further music investigation was deferred by the user; do not restart it or
copy the patch into other targets without new direction.

## Assisted two-pipe and onward-route regression

The user-provided two-pipe route is now a reproducible regression on the current
cumulative ROM `3a7fd69f58c541e73ffeffaad91f4ff1bbba48fdbba87d95b37b1d68195eda7c`
and native binary
`7efb8fa11c57d83c779fa07889dda0cd5643eead8e4323f55b43383c818a2973`.
No ROM or runtime behavior was changed for this qualification.

- Script: `recomp/inputs/world1-next-course-two-pipes.script`.
- Runner: `python3 tools/qualify_world1_two_pipes.py`.
- Report: `local/reports/world1-two-pipes-qualification.json`.
- Fresh captures: `local/captures/world1-two-pipes-qualified-v2-reference`,
  `world1-two-pipes-qualified-v2-native`, and
  `world1-two-pipes-qualified-v2-donor` (original demo8).

All three hosts enter the screen08 pipe with Up, reach room04A, collect the
extra-bit sprite8D that changes `$14AF` from zero to one, enter the top pipe
into room161, contact the real goal, return to the map at `(058,1D8)`, and
enter room106. Both active Map16 buffers match demo8 for the 13-screen vertical
room04A and two-screen room161 at the recorded entry samples. The recipient's
course10 clear byte changes `0C -> 8C`; the donor retains its different original
direction bits and changes `00 -> 84`.

Position, launch, water and invulnerability fixtures bypass traversal obstacles.
The script does not write the ability flag, exit destinations, goal timer,
events, or completion flags. This qualifies the transitions, power-up, actual
normal clear and onward entry, **not an unassisted full-course run**.
Collectibles remain unqualified. Room106 music remains incorrect and deferred.

See `world1-map-flow.md` for pipe locations and the camera/sprite-loading limits
that made large vertical teleports unsuitable for the route probe.
