# Overworld map music for World 4 and World 6

## Summary

World 4 (Cave) played the Special World map theme. World 6 (Sky) played the
World 4 map theme. The overworld map music table stored the wrong song ids for
two submaps. This change corrects four table bytes. It changes no song
payload, map layout, event, save or engine code.

## Cause

Super Mario World selects the overworld map theme from one byte per submap in
the `OverworldMusic` table at `$04:8D8A`. A duplicate table,
`OverworldMusic2`, sits at `$04:DBC8` and serves the submap-swap path. The
recipient Demo 1-1 line stores these seven bytes:

| Submap | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Demo 1-1 | 1E | 22 | 27 | 25 | 29 | 27 | 26 |

The submap ids are not world numbers:

| Submap | World | Evidence |
| --- | --- | --- |
| 1 | World 6, Sky | Map node loads room `$101`; the user confirmed World 6 |
| 2 | World 4, Cave | Map view shows the cave mine and its Save/Exit signs |
| 3 | later world | map view is a different background |
| 5 | Special World | control sample for the special theme |

Submap 2 therefore requested `0x27`, which is the Special World theme, and
submap 1 requested `0x22`, which belongs to World 4. The newest official demo
(`demoOnly1`) stores `0x22` at submap 2 and `0x23` at submap 1. Those are the
intended tracks for World 4 and World 6.

## Repair

The recipe is
[`demo11-overworld-music`](../config/restorations/demo11-overworld-music.json).
It changes four bytes in the two tables:

| Address | Before | After | Meaning |
| --- | --- | --- | --- |
| `04:8D8B` | `22` | `23` | OverworldMusic submap 1 (World 6) 0x22 -> 0x23 |
| `04:8D8C` | `27` | `22` | OverworldMusic submap 2 (World 4) 0x27 -> 0x22 |
| `04:DBC9` | `22` | `23` | OverworldMusic2 submap 1 (World 6) 0x22 -> 0x23 |
| `04:DBCA` | `27` | `22` | OverworldMusic2 submap 2 (World 4) 0x27 -> 0x22 |

The patched table is `1E 23 22 25 29 27 26` for submaps 0 to 6. Submaps 0, 3,
4, 5 and 6 keep their recipient values.

## Verification

The reference host runs the ROM directly. Each script teleports to one submap
and records the music request byte `$1DFB`; the value appears in the changed
WRAM trace.

| Submap | Base request | Patched request |
| --- | --- | --- |
| 1 (World 6) | `0x22` | `0x23` |
| 2 (World 4) | `0x27` | `0x22` |
| 3 | `0x25` | `0x25` |
| 5 (Special) | `0x27` | `0x27` |

The native runtime shows the same requests. Dense per-frame dumps catch the
one-frame request on submaps 1 and 2:

| Submap | Base native | Patched native |
| --- | --- | --- |
| 1 (World 6) | `0x22` | `0x23` |
| 2 (World 4) | `0x27` | `0x22` |

`tools/qualify_demo11_overworld_music.py` rebuilds the target ROM from the base
product ROM, checks the four reviewed bytes and their untouched neighbours,
replays the reference traces and reads the native dumps. It passes six submap
checks.

## Identities

| Item | Value |
| --- | --- |
| Base target | `demo11-native-product` |
| Base ROM SHA-256 | `a1c9d7c8f09399b60193302e33bb1c8111ac0fe8e5b1cb5684fb6f277fddbf91` |
| Target | `demo11-overworld-music` |
| Target ROM SHA-256 | `4ee6d47e0f3a6bfb5395d7531f683ab8aaedf6b29de15ab877341adbd0b71e8b` |
| Native binary SHA-256 | `0ff3eda011059bc7f11e2a28cf3155869e922f6430f43fde5f95c629a10a0f14` |

The native runner bakes the ROM identity and the mod catalog into the binary.
A player must use the rebuilt binary for the patched ROM. A bare ROM swap is
rejected by the mod catalog.

## Limits

- A music-selection byte is not an audible match. This check proves which
  song slot each submap requests. It does not compare the rendered audio with
  another host.
- The song payloads at slots `0x22` and `0x23` are unchanged. The check does
  not re-render them.
- World numbering comes from the observed map views and the confirmed World 6
  room. It does not audit every other world's map theme.

## Reproduce

```sh
python3 tools/qualify_demo11_overworld_music.py
```

The reference captures are `local/captures/owm-ref-{base,patch}-map{1,2,3,5}`.
The native dense captures are `local/captures/owm-d2-{base,new}-map{1,2}`.
