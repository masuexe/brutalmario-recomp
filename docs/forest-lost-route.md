# Lost Forest color maze and saved normal exit

Date: 2026-10-29. Target: `demo11-native-product-r13`.
ROM SHA-256:
`c02dc11e0c79c804740b38797463a1fc9645a8a05cdb4e18c7c09fff45760681`.
Native binary SHA-256:
`131b9522f4edfa4eba5793780f228a9f3ed1c7a7e040e46e00bd6f032e493be0`.

## Result

Eight actual color-matched maze choices advance the counter from zero to eight,
load goal room `050` and reach a real tape clear. The saved normal-exit byte
survives console reset/File A reload, and ordinary onward entry opens room
`11F`. A separate negative control chooses one correct exit followed by a
wrong-colored exit: progress returns to zero without clearing or losing a life.
Native and the limited same-image reference route agree at 21 paired samples.

These are assisted maze/goal/map/save boundaries. Map/player coordinates, the
initial pipe action and damage immunity bypass the first log/P-switch/spring
puzzle. No puzzle count, color data, actor, exit destination, event, completion
flag or SRAM byte is written by either tracked script. No game code, ROM,
resource pack, level data or intended mechanics changed.

## Intended route and code identity

The [Lost Forest guide](https://brutalmario.fandom.com/wiki/Lost_Forest),
consulted on 2026-10-29, describes movable logs followed by a maze whose
butterfly exits must match the background flowers for eight rounds. It has no
secret exit listed. This checkpoint exercises the maze, not the complete first
puzzle traversal or five Dragon Coin pickups. The earlier user acceptance of
the wood sprite remains recorded in [the sprite report](demo11-custom-sprites-w234.md).
It is not relabelled as acceptance of this later target or a full clear.

Custom sprite `08` handles both log and butterfly behavior. Its existing
restoration recipe is in `config/restorations/demo11-sprites-cheap-demo.json`:

- Original protected block: `14:ED08`, 1,364 bytes, SHA-256
  `10e273a46d2e4ac6b6895bcca968c79cd056afecd464a44e415f2ef01e1bc6b1`.
- Installed block: `34:ED08`, byte-identical to that official cheap_demo block.
- Installed record:
  `01360000e2a6a94517ed348fed340000`.

The checker verifies the installed record and complete block. All inspected
newer official sources (`mazo`, `7hero`, `boss`, demoOnly1 and Demo 1-1) hold a
placeholder in slot `08`, supporting the existing cheap_demo source selection.
Every source ROM is checked against its tracked official pin, including the
separate Boss manifest. Both complete bounded layer streams and sprite lists
for rooms `123`, `042` and `050` match all six official images. This establishes
component identity, not whole-engine donor parity.

The Layer 2 background stream is not an ordinary object list. The local
exploratory object parser can walk past a terminator into adjacent RATS blocks
when its object lengths or stream kind are wrong. Use the bounded RATS payload
and live exit table for evidence; do not interpret that parser's unbounded tail
as extra level geometry or exits.

## Actual color choices

The room `042` controller exposes the left/right/up/down butterfly palette
attributes at `$7F:FCCC..FCCF`, the flower pattern at `$7F:FDDD`, its matching
palette at `$7F:FDDE`, and the rendered pattern selector at `$7F:C004`.
These are version-local values, validated against the pinned program. Scripts
only read the progress byte with assertions; they never set any of these values.

| Round | Left / right / up / down | Flower palette | Chosen boundary | Result |
| --- | --- | --- | --- | --- |
| 1 | `03 / 0D / 0F / 07` | `0F` | Up | Progress `01` |
| 2 | `03 / 07 / 0D / 0F` | `0F` | Down | Progress `02` |
| 3 | `0F / 03 / 0D / 07` | `0F` | Left | Progress `03` |
| 4 | `0D / 0F / 03 / 07` | `07` | Down | Progress `04` |
| 5 | `07 / 03 / 0F / 0D` | `07` | Left | Progress `05` |
| 6 | `07 / 0F / 0D / 03` | `07` | Left | Progress `06` |
| 7 | `0F / 0D / 07 / 03` | `0D` | Right | Progress `07` |
| 8 | `07 / 0D / 03 / 0F` | `0F` | Down | Progress `08`, room `050` |

The script positions Mario at the selected boundary. The original controller
then compares colors, updates `$14AF`, selects its original primary/secondary
exit and executes the room transition. Those destination writes are guest code,
not input-fixture edits. The checker verifies a live custom `08` controller,
a unique matching palette and the next progress value for every round.

The negative control repeats the first correct up choice. On the next layout,
it takes left (`03`) instead of the matching down (`0F`). The game reloads room
`042`, resets `$14AF` to zero, retains the uncleared `08` flag and four lives,
and never starts the goal timer. This distinguishes correct selection from
unconditionally advancing on any room transition.

## Normal clear and persistence

| Boundary | Native and reference result |
| --- | --- |
| Existing node and entry | Main map `0188/0178`, translevel `47`, room `123` |
| Initial existing screen exit | Room `123`, screen `04`, `42/04` -> room `042` |
| Eight correct choices | Real controller advances `0..8`; final room `050` |
| Real tape | Vanilla `7B/08` -> `7B/06`, nonzero goal timer |
| Normal map return | Four lives; next hollow-course node `01B8/0158` |
| Guest completion/save | WRAM `$1EE9`, SRAM `0047` and `01F4` change `08 -> 88` |
| Console reset/File A reload | All three bytes retain `88`; next node remains selected |
| Ordinary onward entry | Room `11F`, mode `14`, four lives |

No map fixture is used after the goal. The final ordinary entry therefore
checks real onward selection, not another replacement of a practice node.

## Evidence and comparison scope

Tracked inputs:

- `recomp/inputs/forest-lost-normal-save.script`
- `recomp/inputs/forest-lost-wrong-color.script`

Native captures are `forest-r13-lost-{normal,wrong}-v1`; final reference replays
are `forest-r13-lost-{normal,wrong}-ref-v2`. Earlier probes and reference v1
receipts remain unchanged. Reference v2 uses the course-specific local manifest
at `local/probes/forest-lost/reference-manifest.json` with the same r13 ROM pin.

The product is native-only in general. As in [the shack check](forest-shack-route.md),
`probe_reference.py` can exercise this measured subset because every external
mount logs zero resolutions and zero executed page instructions. The checker
rejects future captures that use a pack and requires an explicit dependency
review. Reference options are `snes9x_echo_buffer_hack=enabled`.

At all 21 paired samples, asserted semantic fields, player positions, actor
identities/statuses/positions, palette attributes, flower selectors and four
Map16 buffer regions match exactly. The buffer regions total 27,648 bytes per
sample. Full WRAM, framebuffer equality, all visible color details and audible
music are not qualified by those state comparisons.

Checker: `tools/qualify_forest_lost.py`.
Report: `local/reports/forest-lost-acceptance-v1.json`, SHA-256
`5444e0dc5bfd350e1b3189423274d23615786153161767ed18f4bc65929ceb15`.
All **344 existing unit tests** pass; log:
`local/reports/unit-tests-forest-lost-v1.log`.

Use fresh captures and output paths. The checker expects native `PREFIX-ROUTE-v1`
and reference `PREFIX-ROUTE-ref-v2`, where ROUTE is `normal` or `wrong`:

```sh
python3 tools/m1.py native --target demo11-native-product-r13 \
  --script recomp/inputs/forest-lost-normal-save.script --capture FRESH-normal-v1
python3 tools/m1.py native --target demo11-native-product-r13 \
  --script recomp/inputs/forest-lost-wrong-color.script --capture FRESH-wrong-v1
# Run probe_reference.py with the same scripts and the pinned r13 manifest.
python3 tools/qualify_forest_lost.py \
  --prefix FRESH --output local/reports/FRESH.json
```

## Next work

Continue the hollow course at room `11F`, then the remaining Forest courses,
secret exits and map/save acceptance. Full first-puzzle traversal, collectibles,
Lost Forest death/re-entry and visible/audio acceptance remain separate gaps.
The broader restoration, C2, endgame and other-world catalog review stay open.
