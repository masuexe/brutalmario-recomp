# External content packs: region provider and the music pilot

The native target is the product. A single 4 MB LoROM image is not a product
constraint, so content that does not fit can live in a file and load at run
time. This page records the mechanism and the first pilot.

## Why a region provider

The cartridge image holds 3,379,319 bytes of RATS blocks in 2,724 blocks. Level
data is 1,110,761 bytes and music payloads are 289,486 bytes. The free space is
327,746 bytes, but it is split into 39,943 ranges and the largest range is 4,072
bytes. A LoROM data block must stay inside one 32 KB bank, so a 6,144-byte song
block has no place to go.

The sprite-gap runtime already loads external packs, but it maps one bank per
pack. Music blocks are spread across many banks, so the runtime needs a
provider that replaces a byte range rather than a whole bank.

## The region provider

`recomp/native_content.c` holds two providers:

| Provider | Entry points | Unit |
| --- | --- | --- |
| Sprite gap | `bm_content_load`, `bm_content_resolve` | One bank per pack |
| Region | `bm_region_load`, `bm_region_resolve` | A byte range per region |

The sprite runtime owns the backing map. It builds one copy of the image and
fills the mapped banks from their files. It exports `bm_content_backing` so
the region provider writes into that same copy. A second copy would miss the
sprite packs.

`bm_region_resolve` returns a backing pointer only for an address inside a
region. A byte in the same bank but outside the region stays an image byte. This
matters: a first version returned the backing for a whole active bank, and a
mapped sprite bank then read the wrong bytes and crashed.

## Region recipe

A region pack gives, for each region, the image offset, the byte count and the
block hash. The pack holds the blocks back to back in table order. The image
holds zeros where the blocks were, so the runtime can prove that the image and
the pack agree.

`tools/prepare_music_pack.py` builds one. `tools/patch_region_resolver.py` adds
the include, the resolve call and the mount call to a cartridge that already
carries the sprite resolver. The patch is idempotent, so a rebuild keeps the
same result.

## Music pilot

Target `demo11-music-pack` moves six song slots that no level music object
requests:

| Slot | Image offset | Bytes |
| --- | --- | --- |
| `4F` | `230000` | 6,144 |
| `03` | `25C940` | 6,144 |
| `05` | `260000` | 6,144 |
| `06` | `269E58` | 6,144 |
| `54` | `1A3000` | 716 |
| `60` | `0BD08B` | 1,224 |

| Identity | Value |
| --- | --- |
| Base ROM SHA-256 | `82741528f9d8c335901157184a6398eb1f05d4ec7395f7ec3c6c72249168e9fa` |
| ROM SHA-256 | `f552b384b149a9d2b43c48d596e6a468dbd6182aaaac9ead2698a81dcf8bdf76` |
| Pack | 26,516 bytes, `586036ea0d89e7840a661ac18e6ebbfec8a474e443e8ddf5f8fc285aa7f85cd1` |
| Native binary | `3c9491762fcb9397f156d03f796daaeac2a45857394305f3d7532955f70be9a2` |

A capture mounts both providers:

```
[native-seven] mounted immutable A2/A5/A6/B6 views
[native-region] mounted demo11-music-pack regions=6 bytes=26516
```

## Song 4F for room 0A2

Room `0A2` requests song `0x4F`, and slot `4F` was null, so the room
stalled in mode `0x12` with a black screen. The song needs a 6,144-byte
block, and the image held no such range.

The music pilot freed one. Slot `02` is not requested by any level music
object, so its block moved into the pack and its image range became zero.
Song `4F` now fills that range as a region, and slot `4F` points at it.

A capture enters room `0A2` and reads gameplay mode `0x14` with
`$0DDA` `0x4F`. The black screen is gone.

The song does not play. The upload is correct: the pack holds a 6,132-byte
payload at ARAM `$5400` that matches the pack byte for byte, and its
sequence header reads `ff 00 02 54` like the songs that do play. The APU
trace shows two key-on writes for room `0A2` and six for a room whose
song plays, so the driver does not start the tracks.

Song `4F` uses instrument `154`, which no playing song uses. The
cause is not proven. Room `0A2` keeps song `4F` and stays silent.

## Pilot result

Nine rooms request the moved slots. A console-teleport audit enters each one and
reads the song on arrival:

| Slots | Rooms | Song read |
| --- | --- | --- |
| `54` | `008`, `026` | `0x54` |
| `60` | `01C`, `0B8`, `10A`, `117`, `133`, `176` | `0x60` |

All nine reach gameplay mode `0x14`. Room `151` reads `FF` because its
song is a short jingle that finishes inside the wait.

The teleport is an assisted fixture. It proves the song selection of a direct
room entry, not an ordinary course route and not an audible match.

## The raw base does not play

A raw slice keeps the donor ARAM base `$6800`. Every room that requests a
raw song stays silent. The APU trace shows two key-on writes for those rooms and
six for a room whose song plays:

| Slots | Rooms sampled | Key-on writes |
| --- | --- | --- |
| `3F`, `43`, `53` | `018`, `0Bd`, `0A9`, `066`, `01B` | 2 |

A control run proves the room is not the cause. Room `0A2` with song `35`
reaches six key-on writes in the same fixture, and the same room with song `4F`
reaches two. The song decides the result, not the room.

Song `4F` relocated to `$5400` still stays silent. Its upload matches the
pack byte for byte and its sequence header matches the songs that play. Its
pattern table sits 5,112 bytes above the base, and every song that plays keeps
that table between 593 and 3,070 bytes. The engine state at ARAM `$14` then
holds `0x0053` instead of a song address.

The cause is not proven. The engine layout assumption is not in the reviewed
material, and a deeper analysis needs a disassembly of the driver.

## A native song parser

A native player can bypass the SPC driver, so the format needs a parser that
does not depend on the engine layout. `tools/parse_song.py` reads the
structure and `tools/decode_song.py` reads the command stream.

The reference material is the 100 extracted payloads under
`local/music/demo-1-1`, each with a rendered WAV from the pinned
Snes9x host. That gives a known-good corpus for the parser.

| Check | Result |
| --- | --- |
| Payloads whose structure parses | 100 of 100 |
| Payloads whose tracks decode | 100 of 100 |
| Song `4F` from the region pack | 12 tracks, 266.5 s of music |

Song `4F` decodes with the same parser that reads all 100 reference songs.
The SPC driver refuses it, but the data is complete and well formed. A native
player can therefore play it.

`tools/render_song.py` writes a square-wave probe of the note timeline. The
probe proves the note order is readable. It is not a sample synthesiser, and
its correlation with the reference render is low, so it does not prove an
audible match.

## A native song player

`tools/native_song_player.c` plays one song without the SPC driver. It
reads the song stream, writes the channel registers, and lets the upstream
DSP produce the samples. The sample set and its directory come from a console
capture of the same ROM, because the song payload carries only the stream.

The channel register map matters. The first attempt wrote the volume and
gain into the wrong offsets and produced silence. The correct map per voice
is pitch at `0x00`, volume at `0x02` and `0x03`, sample number at `0x04`, and
gain at `0x07`. The `FLG` register must clear both reset and mute, because a
set reset forces the channel gain to zero.

Result for a 300-frame run:

| Song | Non-zero samples | Peak |
| --- | --- | --- |
| `07` (reference corpus) | 159,840 of 320,400 | 256 |
| `4F` (region pack) | 159,871 of 320,400 | 256 |

Song `4F` produces the same sample density as a reference song. The SPC
driver refuses that song, but a native player can play it.

The player now runs the whole command stream over time. Each voice keeps its
own cursor, instrument, volume and wait counter, so every note of the song
sounds in order. A subroutine call pushes a return address and runs the
target, so a shared phrase plays from every track that calls it.

A 300-frame run:

| Song | Notes played | Non-zero samples | Peak |
| --- | --- | --- | --- |
| `07` (reference corpus) | 49 | 160,039 | 14,848 |
| `4F` (region pack) | 63 | 159,778 | 15,721 |

Song `4F` plays with more notes and a higher peak than the reference song.

### Song 4F plays in the real engine

Earlier notes in this file record that song 4F stays silent. That claim is
wrong, and this section replaces it.

The reference host renders 4F when the carrier slot points at a valid upload
block. The block has the same layout as the blocks inside the Demo 1-1 image:

    +0  payload length, little-endian word
    +2  ARAM destination, little-endian word
    +4  payload bytes

A first attempt wrote the bare payload, so the engine read the payload bytes
as a header and started no song. A second attempt wrote the block at 0x300000,
which holds game data, so the level failed to load. The block now goes at
0x2057B4, the largest zero run in the image, and the route reaches gameplay
mode 0x14.

Result of that render:

| Item | Value |
| --- | --- |
| Duration | 18.6 s |
| Silent fraction | 0.043 |
| Peak | 11,104 |
| RMS | 799.6 |

The dominant frequency moves through 47, 78, 156, 579, 782 and 986 Hz over
the render. A melody changes its fundamental. Noise does not.

Song 4F therefore plays through the real driver. The native player in this
project does not reproduce it yet, because its pitch conversion is not the
engine conversion. The engine path is the authority.
### Room 0A2 is not silent in the native runtime

Earlier notes record that room 0A2 enters gameplay but plays no music.
That claim is also wrong, and this section replaces it.

The native runtime can dump its own DSP output through the
`M1_AUDIO_WAV` environment variable. A capture of room 0A2 in the
product r17 target gives the following result. A capture of room 013, whose
song is known to play, is the control.

| Room | Song | Frames | Peak | RMS | Non-zero samples |
| --- | --- | --- | --- | --- | --- |
| 0A2 | 4F | 65,536 | 4,592 | 630.7 | 113,008 of 131,072 |
| 013 | 35 | 65,536 | 3,643 | 646.1 | 120,850 of 131,072 |

The two rooms carry the same audio level. Room 0A2 is therefore not silent.

The dominant frequency moves in both captures: 156, 63, 1,314 and 94 Hz in
room 0A2, and 375, 563, 876 and 782 Hz in room 013. Both carry musical
content.

The earlier silence claim came from a trace sample that read the APU key-on
register before the song started. It did not measure the audio output.

Two conclusions follow. Song 4F is valid, and the region pack delivers it.
The native player in this project still does not reproduce it, because its
pitch conversion is not the engine conversion.
### User acceptance and a correction about the silent rooms

The user listened to product r17 in room 0A2 and reports that the music is
correct. Room 0A2 is accepted.

An earlier table in this file lists rooms 066 and 0A9 as digitally silent. That
result is a measurement artifact, and this section replaces it.

The native runtime dumps its audio through the M1_AUDIO_WAV environment
variable. The dump keeps the last 65,536 samples of the run. The standard room
probe waits 180 frames after the arrival dump and then quits, so the dump
window can land after the quit, where the output is silent. A probe with a
900-frame tail moves the window over the playing music.

Room 0A9 with the longer tail gives peak 4,340 and RMS 1,112.5, so the room
carries audio. Rooms 018, 01B, 013 and 0A2 carry audio in both probes.

A spectral flatness check gives similar values for all measured rooms, between
0.08 and 0.43. A flatness near 1 means noise. No room shows a noise signature,
so the audio of these rooms is tonal.

### The legacy songs added by earlier restorations

Slots 3F, 43 and 53 are NULL in the Demo 1-1 image. The product image holds a
block for each of them:

| Slot | Block offset | Payload size | ARAM destination |
| --- | --- | --- | --- |
| 3F | 0x1EDCF8 | 6,128 | 0x6800 |
| 43 | 0x22CF68 | 6,128 | 0x6800 |
| 53 | 0x213E70 | 6,128 | 0x6800 |

The destination is 0x6800, not the 0x5400 that the Demo 1-1 songs use. These
blocks come from an earlier restoration, and the retarget recipe does not
create them.

Both the native runtime and the reference host play these blocks. A capture of
room 0A9 shows the upload matches the image byte for byte, 6,128 of 6,128
bytes.

The user reports that song 43 sounds wrong, and that other songs also sound
wrong. The measured level and tonality of the room audio do not show a fault,
so the defect is not a silence and not noise. The cause is not known.

### Song 0x41 and room 0x43

The wrong-music list records one line without a table row:

    43关卡的音乐（41）正确但是听感有问题

That line says the music for room 43 is song 0x41, that the choice is correct,
and that the sound quality has a problem.

The room data does not agree with that line. Room 0x43 holds one music object
at offset 17 of its level block:

| Image | Music object | Song |
| --- | --- | --- |
| demo-1-1 | 40 60 45 | 0x44 |
| product r17 | 40 60 45 | 0x44 |

A console capture of room 0x43 in product r17 reads 0DDA as 0x44, so the game
starts song 0x44 and not song 0x41. The object encoding is calibrated on three
rooms whose song is known: room 0AA holds 40 60 31 and plays 0x30, room 018
holds 40 60 54 and plays 0x53, and room 01B holds 40 60 40 and plays 0x3F.

Song 0x41 itself is present and well formed:

| Item | Value |
| --- | --- |
| Payload size | 854 bytes |
| ARAM destination | 0x5400 |
| Pattern table | 0x5746 |
| Tracks | 10, five per pattern |
| Notes | 226, 177, 135, 110, 92 |
| SHA-256 prefix, demo-only-1 and demo-1-1 | e4a3969593484db4, identical |

The reference host renders slot 0x41 with RMS 830.6 and a silent fraction of
0.032, so the payload plays.

The retarget tool cannot change this room. prepare_music_objects.apply appends
a music object to a room that has none, and it rejects a room that already
holds one. Room 0x43 already holds one, so a change to song 0x41 needs a
different patch.

Open questions: the room should play 0x41 per the list and plays 0x44 today,
and the list also reports a sound problem in 0x41. The cause of that sound
problem is not known.

### Room 0x43 now plays song 0x41 (product r18)

Room 0x43 held the music object 40 60 45, which selects song 0x44. That song
came from the legacy donor through adapt_music. The port is faithful: of the
825 payload bytes, the only differences from the donor are the relocated
pointer high bytes and the zeroed headers of the other songs in the group. The
score is therefore the donor score, and it is not the score the level wants.

Product r18 changes the music object to 40 60 42, which selects song 0x41.
Song 0x41 is a Demo 1-1 song, 854 bytes, with the same payload in demo-only-1
and demo-1-1.

The change is one byte in place. The level block keeps its size, so the level
table keeps its pointer and no free range is needed.

| Item | Before | After |
| --- | --- | --- |
| Room 0x43 music object | 40 60 45 | 40 60 42 |
| Song requested | 0x44 | 0x41 |
| 0DDA in a console capture | 0x44 | 0x41 |
| Room audio, RMS | not measured | 761.7 |

`tools/prepare_music_override.py` performs the change. It walks the level
block, finds the one music object, and rewrites the song byte. It refuses a
room with no pointer, no bounded block, or a number of music objects that is
not one.

The override list is `music_overrides` in the product recipe. `build_layer` in
`tools/prepare_product_music.py` applies it to the image that it returns.

### Song 0x44 is retired (product r19)

Room 0x43 no longer selects song 0x44, but two other rooms did: 0x114 and
0x11F. Both held the music object 40 60 45. Product r19 points all three rooms
at song 0x41 and then retires slot 0x44.

| Room | Object before | Object after | Song after |
| --- | --- | --- | --- |
| 0x043 | 40 60 45 | 40 60 42 | 0x41 |
| 0x114 | 40 60 45 | 40 60 42 | 0x41 |
| 0x11F | 40 60 45 | 40 60 42 | 0x41 |

A console capture of each room in r19 reads mode 0x14, the expected room, song
0x41, and carries audio:

| Room | Peak | RMS |
| --- | --- | --- |
| 0x043 | 3,635 | 761.7 |
| 0x114 | 3,555 | 825.9 |
| 0x11F | 3,441 | 765.0 |

`prepare_music_override.retire` clears the three-byte song-table entry, so the
game cannot start the song. It refuses when any room still selects that song.
That guard is the reason the two extra rooms are changed first.

The block that slot 0x44 held stays in the image as dead data. It came from an
earlier restoration, so reclaiming the space needs a change to that recipe and
not to this one.

## Level data read path

Level data is the largest block class: 1,110,761 bytes in 744 blocks. Each
block has exactly one reference in the level tables, so a move recipe has a
clean input. Before any move, the read path needs proof.

A diagnostic ROM trace logs the first read of every cartridge byte through
cart_getRomPtr. Two rooms were sampled:

| Room | Block | Payload bytes | Read through the hook |
| --- | --- | --- | --- |
| `0AA` | `29C701` | 35 | 35 |
| `008` | `36A841` | 6,071 | 6,071 |

Both payloads are read in full through the cartridge hook. The sprite-gap
runtime already serves that hook, so the region provider can replace a level
block without a code change.

A second check moves the `0AA` block into the pack and compares the
course entry against the parent image. Both runs reach gameplay mode `0x14`,
and the WRAM images differ by zero bytes.

These checks prove the read path and one small room. They do not prove every
course, and they do not prove an audible or complete course pass.

## What this opens

The pilot shows that music no longer needs a free 6,144-byte range inside one
bank. A later recipe can move every song block, which frees 289,486 bytes and
removes the bank-contiguity limit for the legacy raw songs.

Level data is the next candidate. It is the largest block class, and every
block has exactly one reference, so a move recipe has a clean input. The pilot
does not prove the level read path yet: that path needs its own capture.
