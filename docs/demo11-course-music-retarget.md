# Demo 1-1 course music retarget candidate

Date: 2026-10-26. This is a candidate checkpoint. It is not the current head.

## What the candidate does

The course loading survey found 78 Mario Start stalls in translevels
`001`-`0C0`. Every sampled stall requests a music slot that the Demo 1-1 line
leaves null, so the SPC upload waits forever. The recipient stores the requested
song in the level data as a `40 60 <song+1>` record.

`demo11-course-music-retarget` descends from `demo11-star-bgm` and changes the
course music byte of 17 stalled levels from the legacy-family id to the
verified new-family equivalent from `config/music-mapping.json`:

| Legacy | New | Rooms |
| --- | --- | --- |
| `36` | `61` | `01A`, `118`, `13E` |
| `3B` | `9C` | `00D` |
| `3E` | `8D` | `108` |
| `42` | `71` | `124`, `12A` |
| `43` | `59` | `110`, `131`, `132`, `14B`, `14C` |
| `47` | `6B` | `015`, `021`, `129`, `12E`, `130` |

No song data is installed. The candidate only retargets the requests to slots
that the head already has.

## Identity

| Item | Value |
| --- | --- |
| Target | `demo11-course-music-retarget` |
| Base | `demo11-star-bgm` |
| ROM SHA-256 | `f2b4d3ad640680897e609a172123bad665b8c4a2e951f78b469db67fe0c8b464` |
| Changed bytes | 17 |

## Verification

`tools/qualify_demo11_course_music_retarget.py` checks the candidate and base
identities, the 17 patch sites, and the survey captures. Seven retargeted
translevels reach gameplay on the candidate while the head captures stall:

| Translevel | Head | Candidate |
| --- | --- | --- |
| `015` | stall `12` | gameplay `14` |
| `021` | stall `12` | gameplay `14` |
| `03C` | stall `12` | gameplay `14` |
| `048` | stall `12` | gameplay `14` |
| `04E` | stall `12` | gameplay `14` |
| `054` | stall `12` | gameplay `14` |
| `056` | stall `12` | gameplay `14` |

The other ten retargeted translevels still return to the map or die after the
music fix (`0E`, `0D`, `0C` or `17`). They need separate follow-up work and
are not claimed here.

## Full-range candidate survey

The candidate reran all 192 probes with the same method:

| Result | Head | Candidate |
| --- | ---: | ---: |
| Playable `14` | 70 | 77 |
| Mario Start stall `12` | 78 | 61 |
| Return or death | 44 | 54 |

Seven translevels move from stall to gameplay. The other retargeted levels now
return to the map or die, so they need separate work. The 61 remaining stalls
request 20 unique songs. Song `02` blocks 32 of them, and song `05` blocks 3.

## Native build

| Item | Value |
| --- | --- |
| Binary | `local/build/demo11-course-music-retarget/BrutalMarioDemo11CourseMusicRetargetSNESRecomp` |
| Binary SHA-256 | `fd302e1c570edcb4d0f9ae73046c69a76572f5f07d63ce2468c3120e98cbbf3e` |

Seven native captures ran on the candidate. For each fixed translevel the
native and reference samples match exactly on mode, room, X, Y, lives and
translevel, and both captures pin the candidate ROM identity. The qualifier
checks these native captures, the native build identity and the reference
samples.

## State

- The candidate is built at `local/restoration/demo11-course-music-retarget`
  and registered in `tools/restoration_targets.py`.
- The suite now runs the new qualifier: **33/33**.
- The current head stays `demo11-star-bgm`; the candidate is built and has a
  native build, but it is not accepted yet.
- The whole-line byte audit for the head is unchanged.

## Next steps

1. Build the native target and re-run the reference survey on it.
2. Restore the remaining stalled songs (legacy-exclusive `53` and `57`, and
   the unmapped slots `02`, `03`, `05`, `06`, `21`, `2C`, `3C`,
   `3F`, `44`, `45`, `46`, `55`, `56`, `5B`) from the donor versions.
3. Investigate the post-music `0E`/`0D` results on the other retargeted
   levels.
