# Demo 1-1 Star World sprite allocation repair

Date: 2026-10-24. Current automatically qualified target:
`demo11-star-sprites-safe`, ROM SHA-256
`11ad648a7885ea7c4792dd818229debead6adf3d238ffaea03f182d41e565887`.
It descends from the intact `demo11-star-music-2` ROM
(`314839039ab602c612b92fdd252c506f01a22ccdcc415d1e09c177f019fc741d`),
bypassing the superseded `demo11-star-sprites` artifact. No new user playtest
acceptance is implied.

```sh
python3 tools/play_demo_only1.py --restoration demo11-star-sprites-safe --show-location
# Another entrance on the same ROM:
python3 tools/play_demo_only1.py --restoration demo11-star-sprites-safe --level star-world-upper-inner
```

## Defects found during reproduction

The previous **18/18** result checked frozen candidate files and bounded entry
samples. Its whole-line audit stopped at `demo11-star-music`, omitted the two
later targets, and listed the unrelated Yoshi House experiment as an ancestor.
It did not establish reproducibility or safe allocation for the sprite head.

1. The music recipe declared both `music_54` and `music_2E`, but the builder
   executed only its duplicate singular `music` field. Rebuilding failed the
   pinned output identity. The recipe now uses `music_tracks`, and the builder
   executes each track. This reproduces the existing ROM without changing it.
2. The sprite array used an unsupported schema, with adapted records described
   as donor records. Seven destinations were occupied: IDs `7A`, `58`, `28`,
   `15`, `45`, `50`, `30`. Their historical installation replaced recipient data.
3. IDs `24`, `37`, `30` changed their low addresses but changed only the banks
   of their record pointers. Their INIT/MAIN pointers fell outside their blocks.
   The earlier claim that no same-low-address allocation existed was incorrect.

The original unsafe ROM and its captures remain intact at SHA-256
`0deb4cb24ae43600b5737b70a336e67d560bc465cb013c53bf4d859018c559e6`.
Its recipe now expresses the historical writes as explicit before/after patches,
with donor identities and placement dependencies recorded under `sprite_ports`.
This reproduces that artifact for diagnosis; it does **not** endorse those writes.
The frozen entry qualifier is labeled historical, and its receipts are unchanged.

## Safe replacement

The [new recipe](../config/restorations/demo11-star-sprites-safe.json) uses the
normal guarded sprite builder for all eleven cheap_demo blocks. Each allocation
is empty in the intact parent, outside protected RATS data, preserves the source
low address, and stays in a bank with low WRAM mirrors. Both entry pointers are
rebased and checked inside their block. Source blocks, source records, shared
routine ranges, recipient dispatcher bytes and all 512-room placement dependencies
are pinned. Existing recipient geometry, sprite lists and graphics remain intact.

| Sprite | Source block | Safe destination |
| --- | --- | --- |
| `7A` | `248B77` | `348B77` |
| `57` | `1EFC95` | `29FC95` |
| `58` | `20FC89` | `2FFC89` |
| `17` | `10CD68` | `34CD68` |
| `28` | `20A261` | `38A261` |
| `24` | `1E8000` | `388000` |
| `15` | `10FCEC` | `30FCEC` |
| `45` | `198493` | `348493` |
| `50` | `1CB8EF` | `2FB8EF` |
| `37` | `21EC22` | `36EC22` |
| `30` | `1B8000` | `3A8000` |

These are global sprite slots: some placements occur outside Star World.
Their complete room sets are in the recipe; those other rooms have no new
behavioral acceptance. The safe target retains the original donor sprite code,
including music selections. It does not silently port the demoOnly1 line's
later cap-music adjustments onto Demo 1-1.

## Bounded verification

`tools/qualify_demo11_star_sprites_safe.py` checks ROM/build/input identities,
script completion logs, WRAM/framebuffer/SRAM sizes, records, allocations and
recipe reproduction. Captures use fresh isolated directories and saves.

- `demo11-star-sprites-entry.script` resets between seven map-coordinate entry
  fixtures. Both hosts enter cave `$004`, snow `$008`, sky `$009`, coaster
  `$007`, caps `$117` and upper-right `$002`, with expected active sprite numbers
  at two samples each. Upper-right reference PCM is non-silent (RMS about 520).
  These are entry observations, not six complete courses or listening acceptance.
- `star-world-upper-inner-goal.script` uses a map shortcut and frame-phase pokes,
  then actual coaster/jump/tape inputs. Both hosts return to map mode `$0E`,
  `$13CE=1`, with translevel `$07=$81`. Both SRAM copies (`$0007/$01B4`) and
  console-reset/File A reload retain `$81`. No completion flags are written.
- `star-world-lower-inner-route.script` uses a map shortcut, then actual movement
  and jumps through the warp-star chain. Both hosts reach X at least `$0D00`.
  Six player-position samples agree within 8 pixels with a fresh reference replay
  on the previously qualified `star-world-forest` demoOnly1 ROM. This covers the
  formerly broken progression, not the 100-coin clear or all cap interactions.

Primary captures are `local/captures/d11-safe-entries-{ref,native}`,
`d11-safe-ui-goal-{ref,native}`, `d11-safe-li-route-{ref,native}` and
`d11-safe-li-only1-ref`. Their immutable receipts identify ROM, host, script and
upstream revisions; reference sample metadata identifies Snes9x `1.63 1bcc369`.
The exact binary hash and per-sprite data are in
`local/reports/demo11-star-sprites-safe.json` and
`local/build/demo11-star-sprites-safe/m1-build.json`.
Reference/native framebuffer equality is not claimed; player-position comparison
is bounded independently of animation/rendering differences.

The whole-line audit now follows actual recipe ancestry to the safe head,
rebuilds all **16** recipes in memory, and compares each with its stored ROM.
It includes music arrays and sprite arrays. Against pinned Demo 1-1 there are
**58,498 changed bytes**, all within **79,947 declared region bytes**, zero
unexpected. The standalone historical sprite artifact also reproduces exactly.
The integrated check reports **19/19**; earlier qualifiers continue to pin their
own frozen targets, so this is not a replay of every old route on the new head.
The 32 restoration tests and three ROM-preparation tests pass.

```sh
python3 tools/restore_star_world_1.py --target demo11-star-sprites-safe
python3 tools/m1.py scaffold --target demo11-star-sprites-safe
python3 tools/m1.py generate --target demo11-star-sprites-safe
python3 tools/m1.py build --target demo11-star-sprites-safe
python3 tools/m1.py reference --target demo11-star-sprites-safe \
  --script recomp/inputs/demo11-star-sprites-entry.script --capture fresh-safe-entries-ref
python3 tools/m1.py native --target demo11-star-sprites-safe \
  --script recomp/inputs/demo11-star-sprites-entry.script --capture fresh-safe-entries-native
python3 tools/check_demo11_line.py
```

## Open center-node mapping and remaining scope

The center map coordinate `(map 6, $0178,$01A8)` selects translevel `$00` and
loads room `$000`, not `$00A/$079`, on both safe hosts. A separate fresh-save
reference replay on the intact `demo11-star-music-2` parent reproduces the same
selection. `demo11-star-center-sprites.script` records this diagnostic, with
post-entry damage immunity explicitly labeled; captures are
`d11-safe-center-base-ref` and `d11-safe-center-v2-ref`. This is an existing
Demo 1-1 map/entry gap, not a successful center Boss load. The central boss's
accepted unfinished ending on the demoOnly1 line remains unchanged.

Next: compare the two versions' center overworld level-selection data and entry
mapping before proposing a bounded repair. Do not transplant donor events or
invent a boss clear. Other Star World full routes, per-sprite interactions,
lower-inner clear/cap music, DK and death/re-entry coverage remain open at this
new head. Earlier World 1 user acceptance remains recorded on its exact targets.
