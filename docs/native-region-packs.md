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
| `02` | `230000` | 6,144 |
| `03` | `25C940` | 6,144 |
| `05` | `260000` | 6,144 |
| `06` | `269E58` | 6,144 |
| `54` | `1A3000` | 716 |
| `60` | `0BD08B` | 1,224 |

| Identity | Value |
| --- | --- |
| Base ROM SHA-256 | `82741528f9d8c335901157184a6398eb1f05d4ec7395f7ec3c6c72249168e9fa` |
| ROM SHA-256 | `6f9fa7434dbf1029b32061e8f0509e92dd00d99e306625c7da1191f193de9b2e` |
| Pack | 26,516 bytes, `5c1894140b0249dd3c9d2e2484a6f654b310679275fcad96b4cbbe4e540d8a03` |
| Native binary | `3c9491762fcb9397f156d03f796daaeac2a45857394305f3d7532955f70be9a2` |

A capture mounts both providers:

```
[native-seven] mounted immutable A2/A5/A6/B6 views
[native-region] mounted demo11-music-pack regions=6 bytes=26516
```

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

## What this opens

The pilot shows that music no longer needs a free 6,144-byte range inside one
bank. A later recipe can move every song block, which frees 289,486 bytes and
removes the bank-contiguity limit for the legacy raw songs.

Level data is the next candidate. It is the largest block class, and every
block has exactly one reference, so a move recipe has a clean input. The pilot
does not prove the level read path yet: that path needs its own capture.
