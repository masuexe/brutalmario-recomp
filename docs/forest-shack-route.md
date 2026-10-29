# Forest shack switch, Big Boo defeat and persistence

Date: 2026-10-29. Target: `demo11-native-product-r13`.
ROM SHA-256:
`c02dc11e0c79c804740b38797463a1fc9645a8a05cdb4e18c7c09fff45760681`.
Native binary SHA-256:
`131b9522f4edfa4eba5793780f228a9f3ed1c7a7e040e46e00bd6f032e493be0`.

## Result

The shack's existing `015 -> 044 -> 046` room chain, a real On/Off switch
activation, three original-block impacts on Big Boo, actual victory, normal
map return, both saved completion copies, File A reload and onward entry into
Lost Forest `123` pass on native and a same-image reference host. A separate
position-assisted pit-death route loses a life and re-enters the uncleared shack.

This is an assisted mechanic/combat/exit/save checkpoint. Position shortcuts,
pipe-action fixtures and damage immunity bypass the complete On/Off/P-switch/
shell puzzle traversal. No On/Off value, collision flag, boss state, actor,
completion flag, event, destination or SRAM byte is written by the clear script.
No game code, ROM, pack, level layout, combat timing or save behavior changed.

## Intended mechanics and investigation

The community [shack guide](https://brutalmario.fandom.com/wiki/A_Remote_Shack)
describes an On/Off ghost-house puzzle ending at Big Boo. Its P-switch and shell
route explains why a direct visit to the first door does not exercise the full
puzzle. The guide and the [Japanese map directory](https://wikiwiki.jp/kitikumario/マップ攻略)
were consulted on 2026-10-29. The recipient course identity is independently
pinned by [the Forest catalog](forest-course-identity.md).

Both Layer 1 and Layer 2 matter. Each room's two complete bounded RATS streams
and its complete sprite list match official Demo 1-1, demoOnly1, 7hero and
cheap_demo. The checker verifies each source ROM pin before comparing bytes.
This is stronger than comparing room numbers or only the earlier 256-byte
layout fingerprint. It does not imply whole-engine or whole-course parity.

Room `046` places vanilla sprite `C5`; its eight throw blocks are in Layer 2,
not the Layer 1 buffer. Early probes entered with On/Off still zero and walked
through those blocks. That was the wrong puzzle state, not missing block code.
A temporary forced-On diagnostic proved the collision dependency, but is not
part of the accepted route. The final script instead jumps into the actual
Layer 1 On/Off block at `608,304` in room `044`.

At the settled switch samples, `$14AF` changes `00 -> 01`, and bit 7 of `$5B`
changes `0 -> 1`. In the fight, the player can then stand on a Layer 2 block,
pick it up and contact Big Boo with it. The script waits for the actual
vulnerable phase and the boss's position; it never changes them. The second
and third impacts use a jump while holding the block. The clear therefore
uses three real carried/thrown-block collisions, not a forced-defeat fixture.

## Normal route assertions

Script: `recomp/inputs/forest-shack-normal-save.script`.

| Boundary | Native and reference result |
| --- | --- |
| Existing map node | Main map, `0168/01A8`, translevel `15`; ordinary entry loads `015` |
| First existing screen exit | Room `015`, screen `02`, `44/04` -> room `044` |
| Real switch jump | `$14AF: 00 -> 01`; Layer 2 collision becomes active |
| Second existing screen exit | Room `044`, screen `00`, `46/04` -> room `046` |
| Fight initialization | Active `C5` boss, phase `02`, damage count `00`, eight Layer 2 blocks `012E` |
| First impact | Damage count `01`, phase `05`, block `$7E:E462` becomes `0025` |
| Second impact | Damage count `02`, phase `05`, block `$7E:E461` becomes `0025` |
| Third impact | Damage count `03`, phase `06`, block `$7E:E472` becomes `0025`; boss disappears |
| Real victory | `$13C6 = 01`, goal timer `$1493 = FF` |
| Normal map return | Mode `0E`, Lost Forest node `0188/0178`, four lives retained |
| Saved clear | WRAM `$1EB7` and SRAM `0015` / `01C2` change `01 -> 81` |
| Console reset / File A reload | All three clear bytes retain `81`, next node stays selected |
| Ordinary onward entry | Room `123` in mode `14`, four lives retained |

The first three block offsets above name their low Map16 planes; their high
planes also change from `01` to `00`. The other five block tiles remain intact
through the final damage sample. Moving boss coordinates differ by at most one
pixel between hosts; actor counts, IDs, statuses and all asserted semantic
fields agree. This is not full WRAM or framebuffer parity.

## Death boundary

Script: `recomp/inputs/forest-shack-death-reentry.script`.
It selects the same existing node, enters `015`, and places Mario below the
floor. The guest executes the death and map return. No death-mode or life-byte
write is used. Both hosts lose exactly one life (`4 -> 3`), retain the uncleared
byte `01` in WRAM and both save copies, and re-enter `015` in mode `14` with
three lives and On/Off reset to zero. This is a position-assisted pit boundary,
not unassisted traversal or an ordinary enemy-contact test.

## Host and source boundaries

The generic `m1.py reference` command rejects native-pack product targets.
These two routes are checked through `probe_reference.py` with the exact r13
ROM pin. This is justified only for the measured subset: every external mount
reports zero resolutions and zero executed page instructions during both native
runs. The checker rejects the comparison if any mount is used. It records the
reference frontend, core and options (`snes9x_echo_buffer_hack=enabled`).
This does not establish reference compatibility for the rest of the product.

Nineteen paired dump points pass. At every point, the four Map16 buffer regions
(each `0x1B00` bytes, `27,648` bytes total) agree byte for byte. This includes
the two Layer 2 planes and the actual removal of the three used blocks. Full
WRAM and rendered-frame equality are not claimed. No audible music comparison
or new manual acceptance is inferred.

## Reproduce and evidence

Native captures:

- `local/captures/forest-r13-shack-normal-v1`
- `local/captures/forest-r13-shack-death-v2`

Reference captures add `-ref` before the version suffix (`normal-ref-v1`,
`death-ref-v2`). The death-script v2 header removes contradictory inherited
boilerplate; both hosts were rerun with that exact tracked script. Their receipts pin the same ROM and
tracked inputs; original source captures and unsuccessful exploratory probes
under `forest-shack-*` remain intact.

Checker: `tools/qualify_forest_shack.py`.
Report: `local/reports/forest-shack-acceptance-final-v1.json`, SHA-256
`4622f2fa4b28c5bc31320903efe5546889482083505352eebf587d63b0b8f041`.
The existing unit suite passes **344/344**; log:
`local/reports/unit-tests-forest-shack-v1.log`.

For fresh native runs:

```sh
python3 tools/m1.py native --target demo11-native-product-r13 \
  --script recomp/inputs/forest-shack-normal-save.script \
  --capture FRESH-normal-v1
python3 tools/m1.py native --target demo11-native-product-r13 \
  --script recomp/inputs/forest-shack-death-reentry.script \
  --capture FRESH-death-v2
```

For reference runs, use `tools/probe_reference.py` with a local manifest whose
`target` identifies this limited same-image probe and whose `output` equals
`config/restorations/demo11-native-product-r13.json`'s output pin. Use the same
scripts and capture names `FRESH-normal-ref-v1` / `FRESH-death-ref-v2`.
Then run:

```sh
python3 tools/qualify_forest_shack.py \
  --prefix FRESH --output local/reports/FRESH.json
```

Use fresh paths: the checker refuses to overwrite an existing report.

## Remaining work

The complete shack puzzle traversal and its normal door/pipe activation remain
open. Continue Lost Forest `123`, then the remaining actual Forest courses,
secret exits, their map events and saves. The broader restoration objective,
C2, endgame, other-world catalog review, music and graphics remain open.
