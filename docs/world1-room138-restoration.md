# World 1 room138 entry and music recovery

The room120 normal exit selects map0 `(0A8,1D8)`, translevel5C, room138.
The previous cumulative candidate stays in Mario Start (mode12) after both
600 and 1,500 frames, while original cheap_demo reaches mode14. This checkpoint
repairs the missing music dependency in an isolated descendant target.

## Current candidate

Use `world1-room138-audio`, descending from the sequence intermediate
`world1-room138`, then the accepted `world1-next-course` cumulative ROM.

- ROM: `9cdd46b38ae238e83e6e3dad9e9440a4f85cc1db2e5b24678caed44fe285a000`.
- Binary: `local/build/world1-room138-audio/BrutalMarioWorld1Room138AudioSNESRecomp`.
- Binary SHA-256: `1f52ebf72fc5c293cc58aba6e5cf43502f8a873947cfd5a8fd24f9436972c85f`.
- Recipes: `config/restorations/world1-room138.json` and
  `config/restorations/world1-room138-audio.json`.
- Check: `python3 tools/qualify_world1_room138.py`.
- Report: `local/reports/world1-room138-qualification.json`.
- Launch: `python3 tools/play_demo_only1.py --restoration world1-room138-audio --show-location`.

The earlier sequence intermediate is retained by identity
`f2f0913606c7661d43c0eaad9effae891333ee3fcc83a7abedfa715ded1c075d`.
It establishes the song dependency but lacks the private sample-bank selection.
Use the audio leaf for further qualification. Accepted baselines, existing
builds and captures were preserved.

## Actual failure

Diagnostic instruction sampling at guest frames 3000–3001 records only
`0FC347/0FC34A`, the audio upload acknowledgement loop, in mode12.
The selected global song 21 pointer at `0FE063` is zero. This is the cause of
this Mario Start stall, rather than a map direction or missing extended GFX.

A write watch identifies `0DF13D` selecting music from room138's object 26.
That object's parameter is at `5CFBE5`, following bytes `40 60`; its original
value 22 selects recipient song 21 because this handler subtracts one.
This is an object parameter, not the third byte of the ordinary level header.
The Layer1 stream pointer `5CEBE5` is unique to room138 in the 512-entry table.

## Exact source sequence and dependencies

cheap_demo uploads a four-song bank from `298008` (physical148008), 6,136 bytes,
SHA-256 `c35603b850733bae9b5a6e4bd2fc304ee629356433a44cd8e363f658faeb5207`.
At frame3000 the actual ARAM image matches that upload and its sequence cursor
is 680A, confirming the second sequence at 6808. The source's numeric cue22 is
bank-local; a recipient global 22 would select different content.

The reachable intro/loop graphs for all eight channels were compared against
53 supported existing recipient songs. None matches exactly. The selected
sequence was therefore extracted and its track/call pointers relocated to 5400.
The adapted upload is 1,147 bytes, with the same note, gate, duration,
instrument, command and repeat graphs in all 16 part/channel comparisons.
Its graph SHA-256 is
`7b5f36ef4e2c6977cbc1c9dc4f5d954eb1ca93713b81decd464cf2942c6933d1`.

| Change | Scope |
| --- | --- |
| Protected song payload | Physical280000 RATS header; song at508008 |
| Private global 7E | Pointer `0FE17A`, originally zero |
| Music object parameter | `5CFBE5: 22 -> 7F`, selects private 7E |
| Sample-bank selector | `0FCF7E: 00 -> 02`, inherits the original request21's bank 2 |

There are 1,068 changed bytes from the accepted cumulative base, confined to
these reviewed regions. Original global 21 remains absent, other song and
sample selectors remain unchanged, and no geometry, sprite placement,
collision, map-event or save data was changed. No audio driver was transplanted.

## Verification

- Direct entry and ordinary movement pass on final native/reference builds
  and cheap_demo. Both active Map16 buffers match the donor across 19 horizontal
  screens at entry and after the movement sample.
- Final native/reference states select song 7E and sample bank 2. The actual
  uploaded song image at 5400 matches the adapted payload byte-for-byte in the
  diagnostic reference and native ARAM dumps.
- A route starting at room106, reaching its real chase goal, collecting the
  five actual room120 coins, touching its real tape, and entering the naturally
  selected room138 node passes on final native/reference builds. It retains
  the earlier position/invulnerability fixtures; no exit, goal, event or
  completion values are injected.
- The room120 five-coin/normal-clear/File A reset regression passes on the new
  native build, retaining clear 8B and DK bit 08 and re-entering room120.
- Existing restorer and practice-launcher suites pass: 32 and 18 tests.

Inputs are `recomp/inputs/world1-room138-entry.script` and
`world1-room138-natural-entry.script`. Final captures under `local/captures/`:
`world1-138-audio-qualified-{reference,native}`,
`world1-138-audio-natural-qualified-{reference,native}`, and
`world1-138-audio-regression-room120-native`. Direct donor capture:
`world1-138-qualified-cheap`. Diagnostic source/target ARAM images and the
negative-baseline PC trace remain in ignored `local/probes/world1-survey/`.
The qualifier pins identities and checks complete dumps and terminal logs.

## Assisted flow, clear persistence and real death

`python3 tools/qualify_world1_room138_flow.py` passes for the pinned candidate
and donor identities. Inputs are `recomp/inputs/world1-room138-clear-save.script`
and `world1-room138-death.script`; captures are
`world1-138-flow-qualified-{reference,native,cheap}` and
`world1-138-death-qualified-{reference,native,cheap}`. Report:
`local/reports/world1-room138-flow-qualification.json`.

The flow route is explicitly assisted: air swimming, invulnerability and one
final landing alignment bypass obstacles and combat. Under those fixtures the
guest still reaches and triggers the REAL goal tape (`$1493` set by the game),
returns to the map normally clear at map0 `(0A8,1A8)` with `$1EFE=8F` and no
life lost, naturally enters the onward castle room `$10E` node, and keeps the
clear across console reset and File A reload, including saved-course re-entry.
The death route uses only the initial map transfer: a real enemy hazard kills
Mario (`$71=09`), costs exactly one life, returns to the map with the course
still uncleared, and allows re-entry. All three hosts (final reference, final
native, original cheap_demo) pass every check, and the loaded Map16 terrain
still matches the donor at the settled and two in-flight samples.

No standard `$02D/$02E` DK tiles exist in the main room, so a standard DK
pickup route is not applicable to this course.

## Remaining scope

Room138 is enterable with the recovered sequence and sample selection, an
assisted whole-course progression, real normal clear, onward castle entry,
File A persistence, and real death/re-entry qualified. Still open: a secret
exit (room `$0CB` exit record exists but its actual entry is unproven in both
candidate and donor), any custom-block/collectible behavior beyond the main
path, donor-side castle entry and save persistence, and audible output.
Do not call the whole stage restored until those are resolved or explicitly
bounded. Room106's incorrect music remains explicitly deferred.
