# Star World lower-left course restoration

Date: 2026-10-19. This is the first isolated content-restoration candidate,
using demoOnly1 as the recipient. The user has playtested the candidate and
reports behavior broadly matching the original, with minor issues still open.
The original Demo 1-1 and demoOnly1 ROMs, builds and ordinary saves are separate.

```sh
python3 tools/play_demo_only1.py --restoration star-world-1 --show-location
```

This launches a fresh, uncleared practice save at map 6, X=`$0128`,
Y=`$01E8`, the lower-left node in the nine-star hub. Enter normally.
Restarting the command makes the course available again. Do not use
`--complete-all` with this preset: completion changes the node into a portal.
Windows audio uses the existing launcher path.

## Entrance and exit identity

The user selected the star course itself, rather than a course after warping
to World 1. They explained that clearing it turns it into a Warp Star.
The initial investigation used completion practice flags and consequently
tested the portal instead of the playable course. An uncleared fresh session
corrected that scope: its entrance loads room `$005`, translevel `$05`.

Observed branches, following the existing screen exits:

| Route | Observation in the restoration candidate |
| --- | --- |
| `$005`, screen `$09` -> `$054` | Vertical room with Koopas, a key and a keyhole. |
| `$005`, screen `$1C` -> `$048` | Starry final room with the normal goal tape. |
| `$048`, screen `$01` -> `$051` | Side-exit room with two signs; leaving its edge returns to the hub. |
| Normal goal in `$048` | Returns to the hub; slot `$05` changes from `$09` to `$89`. The lower-left course remains enterable. |
| Keyhole in `$054` | Returns to the hub with slot `$05` equal to `$8B`; the lower-left star then warps to World 1, map 0 / `$0068,$01B8`. |

The normal and secret exits have different results. A normal goal alone did
not activate this Warp Star in the probes. Goal/keyhole probes use coordinate
shortcuts and a damage-immunity cheat; they do not edit destinations, the
key's carried state, completion flags, events or DK bits. The game itself
picks up the key, completes the exit and performs the map transfer. These
are transition checks, not an unassisted end-to-end playthrough.

Same map coordinates are not a donor identity. At this location demo7 enters
`$110`, cheap_demo enters `$000`, and demo8 enters `$00D`. Donor exploration
also required clearing the intro-only `$0109` flag before a map transfer;
the baseline startup inputs alone leave those versions in their intro room.
Those diagnostic transfers do not qualify their natural startup routes.

## Cause and bounded repair

The unmodified recipient fails in both the pinned Snes9x reference and the
native build. Its layout is initially built correctly, including ground
tiles `$0600/$0601` at the starting floor. During mode `$12`, graphics
initialization corrupts the low Map16 buffer at `$7E:C800`, while its high
bytes remain in `$7F:C800`. Mario then falls through the visible floor.

The instruction trace follows `$0F:F872` / `$0F:F1F8` into the LZ2 loader
at `$00:B8DE`. Room `$005` selects ExGFX `$101`, `$102` and `$103`, whose
24-bit source pointers in the recipient are all `$FFFFFF`. Decompressing
those invalid streams into `$7E:AD00` overruns the intended graphics buffer
and overwrites level data. Merely changing Mario's entrance or collisions
would leave this resource defect in place.

cheap_demo contains all three valid streams. demo8 has identical compressed
streams for these IDs; demo7 differs for `$102/$103`. The other examined
extended graphics used by this room (`$100`, `$109`, `$881`) decode identically
between the recipient and cheap_demo. The room layouts share substantial
data, but their complete Layer 1 payloads differ; no claim of byte-identical
complete donor layouts is made.

The candidate copies only the three missing graphics streams from cheap_demo:

| Donor ExGFX | New recipient ID | Source | Compressed bytes | Decoded bytes |
| --- | --- | --- | ---: | ---: |
| `$101` | `$FFD` | `$25:D76C` | 3,001 | 4,096 |
| `$102` | `$FFE` | `$25:E32D` | 1,256 | 4,096 |
| `$103` | `$FFF` | `$25:E81D` | 2,945 | 4,096 |

Only room `$005`'s graphics selection words are remapped, at record
`$14:ADA8`. Original IDs `$101–$103` retain their original table bytes.
New streams occupy RATS-protected blocks inside reviewed zero padding at
physical ROM offsets `$1E0000–$1E1C39`; this range has no existing RATS
allocation. The builder checks that no existing room selects the new IDs.
It preserves recipient layout, exits, sprites, Map16 definitions, custom code,
music, palettes, save logic and all other room configuration records.
No engine opcode or resource loader is replaced.

The [migration config](../config/restorations/star-world-1.json) pins recipient,
donor, per-stream compressed/decoded hashes, original configuration bytes,
allocation and output identity. The builder rejects malformed or oversized
streams, conflicting allocations, occupied/referenced IDs and conflicting
existing output files. ROM bytes and donor assets remain untracked.

Candidate SHA-256:
`88da794a436f97fe86ff60c48b74a8d7160e1ae39d304c648804d80b6d760bb5`.

## Reproduction

```sh
python3 tools/audit_content_versions.py --prepare-local-roms
python3 tools/restore_star_world_1.py
# Scaffold once in a fresh workspace:
python3 tools/m1.py scaffold --target star-world-1
python3 tools/m1.py generate --target star-world-1
python3 tools/m1.py build --target star-world-1
python3 tools/m1.py reference --target star-world-1 --script recomp/inputs/star-world-1-entry.script --capture star1-entry-reference
python3 tools/m1.py native --target star-world-1 --script recomp/inputs/star-world-1-entry.script --capture star1-entry-native
```

The isolated native target is `local/build/star-world-1/BrutalMarioStarWorld1SNESRecomp`.
Generation and build receipts include its ROM identity. The target uses the
existing demoOnly1 runtime/echo behavior and its own generated code and saves.
`star-world-1-goal.script`, `star-world-1-secret.script` and
`star-world-1-side-exit.script` reproduce the shortcut transition checks
separately.

## Automated evidence and remaining acceptance

Local evidence includes:

- `restoration-star1-phases-reference`: original floor tiles are correct
  after layout load and corrupted after graphics initialization.
- `restoration-star1-smoke-{reference,native,interpreter}`: restored floor
  survives initialization, ordinary movement/jump works, a fall removes one
  life, death returns to the hub, and fresh entry reaches room `$005` again.
  Native compiled/floor scene pictures match at all nine checkpoints; WRAM
  samples differ by 3–24 bytes, and the final re-entry checkpoint differs by
  one host frame. This is bounded functional evidence, not complete state or
  timing equivalence. Reference initialization also differs by one host frame.
- `restoration-star1-goal-{warp-reference,native}`: coordinate shortcut to
  `$048`, real goal interaction, normal-clear flag `$89`, map return and
  ordinary re-entry. The historical `world1_warp` dump label in these captures
  was a hypothesis; it actually records re-entry into `$005`. The tracked
  reproduction script now calls that checkpoint `normal_reentry`.
- `restoration-star1-secret-final-{reference,native}`: `$054` loads, the key
  is carried (`$1470=1`), the keyhole completes without losing a life, and
  the resulting Warp Star reaches World 1. Both hosts show clear flag `$8B`.
- `restoration-star1-side-exit-{reference,native}`: `$048 -> $051` loads and
  leaving the side of `$051` returns to overworld mode `$0E`.
- `restoration-star1-{original-shop,regression-shop}` and
  `restoration-star1-boss-{demo-only-1,star-world-1}`: all 18 shop-route samples
  and the Athletic Special top-door sample have identical full WRAM and raw
  framebuffers before/after this ROM change. This is the exercised regression
  boundary, not a new whole-Boss or whole-game acceptance.

Reports live under `local/reports/restoration-star1-*.json`. Original and
restored receipts retain their actual ROM/core/binary identities. Early
wrong-state, wrong-donor-coordinate and unsuccessful key-pickup probes are
exploration only and are not acceptance evidence.

All 92 tests pass, including the five new decoder/output safeguards and two
new launcher isolation/cleared-node checks. Repeated ROM preparation yields
the same candidate hash; pinned upstream worktrees and both original ROM
identities still verify. `git diff --check` passes.

The user subsequently reported that testing broadly matches the original,
but revealed minor issues. They requested committing and pushing this
checkpoint and deferring repairs until daytime. The first specific report is
the [LOVE ANIMAL corpse / respawn concern](star-world-1-animal.md); bounded
comparison finds the expected fixed artwork and a persistent stomp kill
in the native candidate, while default Snes9x rejects the artwork upload.
The user clarified that living Koopas reappear after fireball / other kills.
Leaving a fireball-created coin uncollected reproduces that respawn in both
cheap_demo and the native candidate; this is shared existing gameplay logic.
The user confirmed the explanation in testing and closed this report without
requesting a gameplay change. Other unspecified issues remain unclassified;
this is not a defect-free acceptance. The report does not separately qualify
both pipe branches, screen `$0E`, normal/secret goals, sound, DK persistence
or an unassisted complete traversal. No complete-game restoration is claimed.
