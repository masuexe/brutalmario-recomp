# Demo 1-1 Star World course BGM

Date: 2026-10-25. The user asked to correct the Star World course music with
the Brutal Mario wiki. The wiki Star Road table, the individual star pages and
`config/music-mapping.json` give the intended songs and the new-family slot
IDs.

Current cumulative target: `demo11-star-bgm`.
ROM SHA-256:
`8939c2ace216af9f6b8c9de365ea8b2614cc8a686b0692e86fec98608afc36c0`.
Native binary SHA-256:
`36ab26fd6d4969490249000963f216228846b96a01d66bad7d662cce0673e57d`.
Parent: `demo11-node-music` (`77a4b7a9…`).

```sh
# Starts at the lower-left Grassland Star entrance:
python3 tools/play_demo_only1.py --restoration demo11-star-bgm --show-location
```

The launcher starts a fresh uncleared practice save. Use `--level` with the
existing `star-world-*` presets for the other courses. The star hub path
unlocks the remaining courses in normal play.

## Finding

The Star World course data on the recipient came from the legacy demo family.
Its music objects still store legacy-family BGM numbers. Demo 1-1 uses the
new-family song table, so those numbers selected the wrong slots. The wiki
Star Road table and the star pages give both numbers:

| Node | Wiki star | Wiki song | Legacy BGM | New-family slot | Result |
| --- | --- | --- | --- | --- | --- |
| lower-left | Grassland Star | Town Where the West Wind Blows (Wild ARMs 2) | 4A | 38 | changed |
| middle-left | Forest Star | vanilla BGM 02 "Here We Go!" (Super Mario World) | 02 | none | kept substitute |
| upper-left | Bay Star | Podol / Boundaries (Romancing SaGa 3) | 28 | 49 | changed |
| upper-inner | Cave Star | Fear Factory (Donkey Kong Country) | 24 | 51 | changed |
| upper-right | Plains Star | Freiluftmusik (SaGa Frontier 2) | 5D | 32 | changed |
| middle-right | Sky Star | Grape Garden (Kirby's Adventure) | 2E | 58 | changed |
| lower-right | Snow Star | Jingle Bells | 54 | 54 | already correct |
| lower-inner | Valley Star | Iceberg Ocean (Kirby's Dream Course) | 40 | 60 | already correct |
| center | Special Warp Star | Slide (Super Mario 64) | 30 | 7A | changed |

The node order follows the Star World page: Grassland, Forest, Bay, Cave,
Plains, Sky, Snow, Valley, Special Warp Star. The lower-left evidence includes
the "Love Animal" title-screen scene; the lower-inner music checkpoint already
matched Valley Star. The Snow slot 54 is a legacy-family exclusive that the
line already restored. The Valley cap cue 79 and the Star-9 boss cue 98 stay as
they are.

Forest Star needs a bounded exception. The wiki lists vanilla song 02. Demo 1-1
has no custom upload for slot 02, and a request of 02 stalls the level load; the
reference host shows the same wait. The line keeps the accepted demoOnly1-line
substitute track at slot 5D. The user shelved the true forest track because the
course came from a demo with no custom music.

## Repair

The recipe is
[`demo11-star-bgm`](../config/restorations/demo11-star-bgm.json). It changes
six one-byte level-data music parameters:

| Address | Before | After | Course |
| --- | --- | --- | --- |
| `3DA32B` | `4B` | `39` | Grassland Star requests 38 |
| `58FBF1` | `29` | `4A` | Bay Star requests 49 |
| `198491` | `25` | `52` | Cave Star requests 51 |
| `1EEC26` | `5E` | `33` | Plains Star requests 32 |
| `5D9FBC` | `2F` | `59` | Sky Star requests 58 |
| `6D8EA6` | `31` | `7B` | Special Warp Star requests 7A |

The music parameter is the song ID plus one; the level loader decrements it
before it writes `$0DDA`. No song asset, level layout, exit or engine code
changes.

## Evidence

Both hosts pass the nine existing node scripts. The reference host requests the
intended slot on every course and no longer requests the legacy numbers. The
native build shows the intended `$0DDA` in the loaded course, and its APU RAM
holds the matching upload body:

| Course | Slot | Upload bytes |
| --- | --- | ---: |
| Grassland | `38` | 1237 |
| Forest | `5D` | 940 |
| Bay | `49` | 609 |
| Cave | `51` | 2656 |
| Plains | `32` | 942 |
| Sky | `58` | 1010 |
| Snow | `54` | 700 |
| Valley | `60` | 1196 |
| Special Warp | `7A` | 2370 |

The Cave course entry script moves into a later event before it quits. A small
extra fixture `demo11-star-bgm-upper-inner.script` stops while the course track
plays, so the Cave upload is checked directly.

Captures are `d11-bgm-<node>-{ref,native}` plus
`d11-bgm-upper-inner-{ref2,native2}`. The report is
`local/reports/demo11-star-bgm.json`, and the suite log is
`local/reports/demo11-star-bgm-line.log`.

`tools/qualify_demo11_star_bgm.py` checks the parent and candidate identities,
the recipe replay, the six reviewed bytes, the Forest exception, all nine
reference requests, all nine native course states and upload bodies, and the
native build identity. The Demo 1-1 line suite passes **26/26**. The whole-line
audit rebuilds 23 recipes: 105,090 changed bytes against Demo 1-1, all inside
139,297 declared region bytes, zero unexpected. The 33 restoration tests, three
preparation tests and 18 launcher tests pass.

## Limits

- The node fixtures use explicit map teleports. This checks course music
  selection, not route completion or ordinary overworld entry.
- The wiki numbers are legacy-family BGM numbers. This change applies the
  new-family IDs from the mapping table. The mapping table is the authority for
  the recipient numbering.
- Upload bodies are version-local. The check confirms that the native ARAM holds
  the body this ROM installs for the selected slot. It does not compare
  arrangements between versions.
- Forest Star keeps the accepted substitute. A custom arrangement of vanilla
  "Here We Go!" would need a separate port.
- The hub map BGM, the Star-9 boss cue 98, other worlds and shop/boss cues stay
  outside this check. The mapping tool can support a wider audit.

## Reproduce

```sh
python3 tools/restore_star_world_1.py --target demo11-star-bgm
python3 tools/m1.py scaffold --target demo11-star-bgm
python3 tools/m1.py generate --target demo11-star-bgm
python3 tools/m1.py build --target demo11-star-bgm
python3 tools/m1.py reference --target demo11-star-bgm \
  --script recomp/inputs/star-world-upper-right-entry.script --capture fresh-bgm-plains-ref
python3 tools/m1.py native --target demo11-star-bgm \
  --script recomp/inputs/star-world-upper-right-entry.script --capture fresh-bgm-plains-native
python3 tools/qualify_demo11_star_bgm.py
python3 tools/check_demo11_line.py
```

## Sources

- https://brutalmario.fandom.com/wiki/Music
- https://brutalmario.fandom.com/wiki/Star_World
- https://brutalmario.fandom.com/wiki/Grassland_Star
- https://brutalmario.fandom.com/wiki/Forest_Star
- https://brutalmario.fandom.com/wiki/Bay_Star
- https://brutalmario.fandom.com/wiki/Cave_Star
- https://brutalmario.fandom.com/wiki/Plains_Star
- https://brutalmario.fandom.com/wiki/Sky_Star
- https://brutalmario.fandom.com/wiki/Snow_Star
- https://brutalmario.fandom.com/wiki/Valley_Star
- https://brutalmario.fandom.com/wiki/Special_Warp_Star
