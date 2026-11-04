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

### The output is noise, not music

The user listened to the rendered file and reported noise with no musical
content. A spectrum check confirms it: the energy sits at unrelated
frequencies such as 12,766, 2,347, 814 and 9,606 Hz, and the magnitude
saturates. A melody would put its energy on harmonics of one fundamental.

The cause is a missing table. The DSP pitch register is a sample-rate
multiplier, not a note number: `0x1000` reads one BRR sample per
cycle. The song byte is `0x80` plus a semitone count, so it must be
converted through the driver note table. The player wrote the raw byte, so`0x90` became a rate of 144, about three percent of normal. That is a rumble, not
a note.

A second attempt converted the byte with a plain semitone ratio. The output
is still noise, because the conversion needs the driver table, which is
indexed by sample as well as by note. The table is not in the game image as a plain list. It is in the AddmusicK
SPC engine, which reimplements the same driver:
https://github.com/HertzDevil/AddmusicK, `test/asm/main.asm`.

That source gives the two pieces this project was missing:

- `PitchTable`: thirteen words, `085F 08DE 0965 09F4 0A8C 0B2C
  `0BD6 0C8B 0D4A 0E14 0EEA 0FCD 10BE`, one octave.
- `SetPitch`: divide the note by `0x18` to pick the octave, interpolate
  with the remainder, then multiply by the sample base pitch in `$02f0`.

The same repository gives `InstrumentData.asm`: twenty music instruments of
six bytes, sample, ADSR1, ADSR2, GAIN, tuning, subtuning.

Those tables are copied into `tools/spc_reference.py
and into the player. The output is still not a melody: the rendered file
reaches a constant clipped level instead of a note sequence. The conversion
still differs from `SetPitch`, most likely in the `$02f0` base-pitch term,
which the engine derives per sample and this player does not.

The parser and the sequencer are sound: the command stream, the phrase rule
and the subroutine return all match the reference corpus. The audio stage is
not solved.

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
