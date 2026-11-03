# Demo 1-1 level music retarget

Date: 2026-11-03. Status: candidate checkpoint. The user listening check is
open.

## Report

The user played the current build and listed one wrong music entry for each
course. The list is at `local/wrongmusiclist.md`. It gives the level number,
the song the build plays, and the song that the course must play. Some rows
give only the song title because no Demo 1-1 slot holds that song.

The list has two defect classes:

1. The course requests a legacy-family song number. That number selects a
   different song in the Demo 1-1 song table, so the course plays the wrong
   track. Most rows are in this class.
2. The intended song has no Demo 1-1 slot. The course can not play it at all
   until the song data arrives.

## Root cause

The Demo 1-1 level data came from the legacy demo family. Each level holds a
music object with the legacy song number. The music object is three bytes:

| Byte | Meaning |
| --- | --- |
| 0 | `0x40` plus the screen number |
| 1 | `0x60` plus the vertical position |
| 2 | Song number plus one |

The object number is `((b0 >> 5) & 3) * 16 + (b1 >> 4)`, so a music object
has object number `0x26`. The level loader decrements byte 2 and writes the
result to `$0DDA`.

A legacy number selects a different Demo 1-1 slot because the two song tables
are version-local. `docs/music-mapping.md` gives the cross-version map.

## Donor selection

The user asked to port the missing songs from the newest version that holds
them. A scan of every pinned official ROM finds the legacy four-song upload
groups only in `cheap-demo`. The groups sit at these addresses:

| Bank group | Addresses |
| --- | --- |
| `$29`-$`2B` | `298008` to `2BA008` |
| `$3E`-$`3F` | `3EB008` to `3FE008` |
| `$44` | `448008` to `44E008` |

`7hero`, `mazo`, `ow`, `demo7`, `demo8`, `boss`, `demo-only-1` and
`demo-1-1` hold no such group. A content search for the same payload bytes
finds them only in `cheap-demo`. Therefore `cheap-demo` is the donor for
every legacy-exclusive song.

The song number gives the group and the slot:

```
group = (song - 0x20) >> 2
slot  = (song - 0x20) & 3
```

The group address follows this order: `298008`, `29A008`, `29C008`,
`29E008`, `2A8008`, `2AA008`, `2AC008`, `2AE008`, then `3F8008`,
`3FA008`, `3FC008`, `3FE008`, then `448008`, `44A008`, `44C008`,
`44E008`.

## Recipe

The recipe `demo11-music-retarget` descends from `demo11-overworld-music`.

| Item | Value |
| --- | --- |
| Target | `demo11-music-retarget` |
| Base ROM SHA-256 | `4ee6d47e0f3a6bfb5395d7531f683ab8aaedf6b29de15ab877341adbd0b71e8b` |
| ROM SHA-256 | `82741528f9d8c335901157184a6398eb1f05d4ec7395f7ec3c6c72249168e9fa` |
| Native binary SHA-256 | `981b9ab8a081f287d265092845e6984a0026e3b414a12ca7541ee94c72a52da1` |
| Changed bytes | 9,258 |
| Selection bytes | 208 |
| Installed songs | 3 |

The recipe changes one byte per reviewed music object. It also installs four
legacy songs at free Demo 1-1 slots:

| Legacy song | Demo 1-1 slot | Payload | Rooms |
| --- | --- | --- | --- |
| `31` Go Red Team (Treasure Hunter G) | `35` | 3,110 | `013`, `014`, `06D`, `112`, `121` |
| `49` Sky Sands (Kirby Air Ride) | `3A` | 2,806 | `047`, `111`, `13A` |
| `51` Dr. Wily Stage 2 (Mega Man 3) | `3D` | 1,397 | `061`, `115`, `156` |

The user listened to the `0AA` and `0AB` courses and reported that the
legacy song `0x37` is an older arrangement of Demo 1-1 slot `0x30`. Those two
courses now request `0x30`, so no port is needed and the earlier `0x37`
install is gone.

Each song uses the reviewed `adapt_music` walk. The walk relocates every
sequence and pattern pointer to ARAM `$5400`. The tool rejects a song with a
command outside the reviewed subset.

The target inherits the `native_sprite_gap` content of its base, because
the base ROM runs those native modules. The prepare step copies the base
pack files into the target directory and verifies every hash. The play
launcher then mounts them.

The song numbers and the intended slots are in
`config/music-level-targets.json`. The file records the user report and the
decision for each level.

## Song table pointer banks

The song table entry is a 24-bit LoROM pointer: bank, high byte, low byte. The
cartridge reaches file banks `0x7E` and `0x7F` only through the
`0x80`-`0xFF` mirror. A plain `0x7E` or `0x7F` pointer names
WRAM, so the DMA reads the wrong bytes and the SPC upload never completes.
The game then stays in Mario Start mode `0x12` with no sound and a black
screen.

The first build of this recipe used plain bank bytes for three songs. A
console teleport to room `013` and to room `0AA` showed the stall.
The tool now emits the mirror form for those banks, and the qualifier rejects
a plain `0x7E`/`0x7F` entry. Room `013` then enters
gameplay with `$0DDA` `0x35`.

## Skipped entries

The tool reports every entry that it does not change. Reasons:

| Reason | Rooms |
| --- | --- |
| No music object; the room inherits the parent song | `020`, `02E`, `033`, `034`, `036`, `03C`, `062`, `06C`, `081` |
| Ambiguous music object | `02F`, `032`, `035`, `05D`, `05E`, `0D3`, `102`, `107`, `122`, `173` |
| No Demo 1-1 slot for the intended song | `0A2` |
| Already correct | `018`, `01B`, `066`, `068`, `069`, `070`, `074`, `0A9`, `0BD`, `0F5`, `10B`, `116` |

A room without a music object plays the song of the room that leads to it.
These rooms become correct when the parent room is correct. The room list does
not record the parent, so this claim stays open for the playtest.

Room `0A2` needs legacy song `4F` (X vs. Zero, Mega Man X5). That song uses
a command outside the reviewed subset, so the tool can not install it. The
slot `4F` is null.

Room `107` holds a music object that does not control its entry song.
The console audit reads slot `0x47`. The object move recipe adds an
object with slot `0x6B`, and a new audit reads `0x6B`.

## Console teleport song audit

The first recipe could not identify the music object of some rooms, so those
rooms stayed unchanged. A native audit now enters each of them with the
built-in console teleport and reads `$0DDA` on arrival.

The arrival sample is the reliable one. A short jingle can finish inside a
later wait, and `$0DDA` then reads `FF`.

Result of the first audit:

| Result | Rooms |
| --- | --- |
| The single music object controls the song; retargeted now | `05D`, `05E`, `0D3`, `102` |
| Correct with no patch | `018`, `01B`, `02E`, `062`, `066`, `068`, `069`, `06C`, `070`, `074`, `081`, `0A9`, `0BD`, `0F5`, `10B`, `116`, `122` |
| Inherited song; object added | `02F`, `032`, `033`, `034`, `035`, `03C`, `107` |
| Silent by convention | `020`, `036` |
| Stalls on entry | `0A2` |
| Leaves gameplay | `173` |

Rooms `02F`, `032`, `033`, `034`, `035` and
`107` all played slot `0x47`, and room `03C` played slot `0x1E`.
Those rooms hold no level music object, so they keep the parent song. The
user report marks the same rooms with `*`, which means "play the song of the
previous scene". The section below records the fix.

After the retarget, rooms `05D`, `05E`, `0D3` and `102`
play `0xA4`, `0x83`, `0x89` and `0x6B` on arrival.

The audit tool is `tools/audit_demo11_music_selection.py`. It writes
`local/reports/demo11-music-audit.json`. The teleport is an assisted
fixture: it proves the song selection of a direct room entry, not an ordinary
course route and not an audible match.

## Rooms that inherit their song

The user report marks several courses with `*`, which means "play the song of
the previous scene". Those rooms hold no level music object, so the level
loader keeps the parent song. The user also reported that the correct song for
them is `0x6B` (`02F`, `032`, `033`, `034`, `035`, `107`)
and `0x51` (`03C`).

The tool `tools/prepare_music_objects.py` adds a music object to those
rooms. A level block has no spare byte, so the tool moves the whole block into
a free within-bank range, appends the object before the terminator, and
repoints the level table. The destination must be empty and unprotected, and
the qualifier re-parses the moved stream.

| Room | Song | Object | Destination |
| --- | --- | --- | --- |
| `02F` | `6B` | `40 60 6C` | `0DBD68` |
| `032` | `6B` | `40 60 6C` | `0DBE45` |
| `033` | `6B` | `40 60 6C` | `0DBEAB` |
| `034` | `6B` | `40 60 6C` | `0DBF2D` |
| `035` | `6B` | `40 60 6C` | `0DBF4D` |
| `03C` | `51` | `40 60 52` | `218008` |
| `107` | `6B` | `40 60 6C` | `0DC990` |

Room `107` first failed the object walk. The cause was the object size
table, not the level data. Object `0x28` is three bytes, and the table
said four, so the walk consumed the terminator. With the corrected table all
403 level blocks of the image terminate exactly at the end of their RATS
payload. Room `107` then takes the same move recipe as the others.

Every music object in the shipped image uses the prefix `40 60`, which is
screen 0 and height 0. An added object uses the same prefix.

A new audit of the seven moved rooms reads the reviewed song on arrival.

## Silence convention

The user reported that slot `0x1E` is the legacy convention for "play no
music". Some versions use `0x00` for the same purpose. Rooms `020` and `036`
play `0x1E` on entry, so their current selection is correct and the
recording marks them as silent instead of wrong.

## Legacy songs that stay on the raw path

Music batch G installed songs `3F`, `43` and `53` as raw group slices.
A raw slice keeps the donor base `$6800`. The Demo 1-1 driver expects a
relocated payload at `$5400`. The audible result of a raw slice is not
qualified. The courses that request `3F`, `43` and `53` keep that path
because the reviewed walk rejects those songs:

| Song | Reviewed walk result |
| --- | --- |
| `3F` | no reviewed song size fits |
| `43` | unsupported command `DC` |
| `53` | unsupported command `E8` |

## Verification

`tools/qualify_demo11_music_retarget.py` checks:

- the base, donor and candidate identities;
- every selection site: the site holds a music object, the byte changes, and
  the result byte is the intended song number plus one;
- every installed song: the slot was null, the RATS block and checksum match,
  and the payload hash matches the reviewed walk;
- every reviewed target slot holds a song in the candidate;
- the ROM delta stays inside the reviewed sites and the installed blocks.

The qualifier passes with 208 selection bytes and 3 installed songs.

`tests/test_prepare_music_retarget.py` adds 16 bounded checks for the
music object pattern, the site choice rule, the first-fit allocator, the
protected RATS ranges, the bank boundary and the graphics record choice.
The suite reports 467 tests with the same 8 stale host-audio failures that
the previous session deferred.

This evidence proves song selection only. It is not an audible match. The user
must listen to the courses before this checkpoint is accepted.

Reference-host captures enter four translevels with the map-node override and read `$0DDA`:

| Translevel | Room | Before | After | Target |
| --- | --- | --- | --- | --- |
| `012` | `012` | `24` | `51` | `51` |
| `013` | `013` | `31` | `35` | `35` |
| `018` | `018` | `53` | `53` | `53` |
| `046` | `122` | `03` | `03` | `03` |
| `013` (teleport) | `013` | stall `12` | `35` | `35` |
| `0AA` (teleport) | `0AA` | `37` | `30` | `30` |
| `0AB` (teleport) | `0AB` | `37` | `30` | `30` |

These samples prove the selection bytes and one installed song. They are not an audible match. The user must listen to the courses before this checkpoint is accepted.

## Reproduce

```sh
python3 tools/prepare_music_retarget.py all
python3 tools/qualify_demo11_music_retarget.py
python3 tools/m1.py scaffold --target demo11-music-retarget
python3 tools/m1.py generate --target demo11-music-retarget
python3 tools/m1.py build --target demo11-music-retarget
```

## Play the courses

```sh
python3 tools/play_native_target.py --target demo11-music-retarget
```

## Next steps

1. Build the native target and play the courses. Listen for each row of the
   user list.
2. Extend the reviewed command subset for songs `3F`, `43`, `49`, `4F`
   and `53`, or capture the donor ARAM image at `$6800` and rebase it to
   `$5400`.
3. Find the parent room of each inherited-music room and confirm the fix.
4. Resolve the two ambiguous rooms.
