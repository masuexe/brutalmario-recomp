# Demo 1-1 song 0x57 restoration candidate

Date: 2026-10-26. This is a candidate checkpoint. It is not the current head.

## Problem

Translevel `001` (room `001`, the wiki "Rescue Yoshi" level) stalls at Mario
Start (mode `12`). The reference capture requests song `57`. The recipient song
table entry at `$0F:E105` is `00 00 00`, so the SPC upload waits for a null
pointer. The music mapping names slot `$57` **KingBonbie VS MechaBonbie**
(Super Momotarou Dentetsu DX) for Rescue Yoshi.

## Method

The legacy donor family stores four songs in each upload group. The cheap-demo
group at `$44:A008` has:

| Field | Value |
| --- | --- |
| Count | `0x17F0` |
| Source base | `0x6800` |
| Group SHA-256 | `4873f22ab18e2293b2df8e28708bae3e4ec555b5f20f8024183e195abccfdc99` |
| Sequence slots | 4, at group offsets `4, 12, 20, 28` |

`local/probes/derive-group-song.py` walks the reachable command graph with the
same rules as `adapt_music`.

- Sequence slot 0 reproduces the reviewed Snow Star 0x54 relocation list
  exactly. That validates the method and the group layout.
- The tracked helper `tools/derive_legacy_song.py` reproduces both reviewed
  payloads. See the [legacy layout note](legacy-music-layout.md).
- Slot 3 has the relocation list below. The four sequences are the consecutive
  legacy ids `54`-`57`, so slot 3 is `57`.

| Field | Value |
| --- | --- |
| Required song size | 3926 bytes |
| Adapted payload | 3934 bytes |
| Payload SHA-256 | `1d293f8e6439ee80b2fecbfddf08be7a9d1b75a9db0aaf2e3fff04a59b9bba48` |
| Relocations | `0, 2, 6, 3630, 3654, 3685, 3689, 3693, 3697, 3729, 3733, 3741, 3910, 3912, 3914, 3916` |
| Destination base | `0x5400` |
| Allocation | file offset `0x1A6000`, 4096 bytes |
| Slot | `$0F:E105` |

## Identity

| Item | Value |
| --- | --- |
| Target | `demo11-music-57` |
| Base | `demo11-star-bgm`, ROM `8939c2ac...` |
| ROM SHA-256 | `35ff420f04a1cf05195f697191f6dfffb29fb34c429b1a62feaedcc7c371a4c4` |
| Native binary SHA-256 | `214d6c4fdf1192f5114004283f7d72d6566d92474d062250b94d2f565e24cfa6` |

## Verification

`tools/qualify_demo11_music_57.py` checks these items:

- the base and candidate identities;
- the donor group and the adapted payload hash;
- the empty allocation, the RATS header, the installed payload and the slot
  pointer;
- no changed byte outside the allocation and the slot;
- the head capture stalls (mode `12`) and the candidate capture reaches
  gameplay (mode `14` at room `001`);
- the reference and native captures pin the candidate ROM and match on mode,
  room, lives and translevel at entry 240, and on every sampled field at
  entry 600.

The reference capture reaches gameplay at entry 240, requests `57` at frame
2413 and continues. The capture has no input, so the player falls and the level
reloads. That fall is not a music defect and is not claimed as a course
completion. An audible match is not claimed.

The second level that requests slot `57`, translevel `0A5` (room `181`), also
stalls on the head. On the candidate it stays in gameplay at entry 240 and
entry 600.

## Limits

- The song identity relies on the reviewed group layout and the consecutive
  sequence order. It does not use audio comparison.
- The survey covers translevel `001` and the second slot-`57` level `0A5`.
  Other possible requests of slot `57` are not covered.
- The candidate is not accepted as the head yet.

## Next steps

1. Re-run the survey on this candidate to check the other slot-`57` levels.
2. Restore song `02` next; it blocks 32 levels.
3. Keep the retarget candidate and this candidate separate until both are
   accepted.
