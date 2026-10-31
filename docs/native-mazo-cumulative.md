# Cumulative Mazo graphics integration

Candidate `demo11-native-mazo-cumulative-v1` descends from
`demo11-native-modern-sprites-v2`, preserving its later sprite programs and
native adaptations. The accepted product remains `demo11-native-product-r14`.

## Change and reconciliation

The candidate mounts the [qualified official mazo GFX0282 stream](native-mazo-second.md)
at `D2:8000` and changes the empty extended-graphics pointer at ROM offset
`0A048E` from `FFFFFF` to `0080D2`. No other ROM bytes change.

| Identity | SHA256 |
| --- | --- |
| Cumulative parent ROM | `e431d5aa168a4a07b63fca7aa4f7ca9fba08333a3b521a8c5f59553c8be2c2c4` |
| Candidate ROM | `47466dc5d6fd53275e042091fc57705a6d6a60356c2785bb0d9336fa3ec73757` |
| Candidate executable | `8b170d0b1d88fe81f96043895d951072dfcbc48f2defa0f4103ec98c41a99f6b` |
| Official mazo ROM | `94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1` |

All 45 selected recipes, 57 existing packs, 63 existing explicit patches and
the complete native-adaptation configuration remain unchanged. There is one
new data-only pack (3344 compressed bytes) and one new pointer patch. The
checker verifies every installed pack's size and digest, compares all inherited
recipe/runtime identity files, and rejects any configuration change beyond
the declared graphics and lineage. The loader owns entire banks; the preparer
checks that no inherited pack occupies bank D2 before mounting the new pack.
Existing source packs and the historical r14 descendant are preserved.

This retains the selected type-3 mappings, modern slots `25/33/94/99/A1/97`,
their records and program bytes, the Seven adaptations and the Forest modules.
It does not substitute the older graphics pilot for the cumulative target.

## Runtime and regressions

Capture `mazo-cumulative-highhops-v1` executes the exact 240-jump assisted
route used for the earlier graphics pilot. Scripted quit completes. At
highhop222 through highhop240, the complete decoded 4096-byte graphics payload
matches VRAM `F000..FFFF`, with a live player in room `151`, cycle 3 and
variant `17` (decimal 23). The normal jump crosses the grounded forced-fall
check at timer AF and Y 281. The official-source reference remains
`mazo-second-source-highhops-v2` (120 jumps, first upload highhop108).
The hosts differ in event timing and attack choices.

Fresh candidate/parent controls use capture prefix `mazo-cumulative-reg-v1`:

| Route | Samples | Exercised content |
| --- | ---: | --- |
| 25 | 11 | Room 154 actor |
| 33 | 11 | Room 0FE actor |
| 94 | 11 | Room 0EF actors |
| 175 | 13 | Modern 99 and A1 |
| 178 | 13 | A1 motion |
| 97 | 8 | Assisted room 108 exit to 1EF |
| c0 | 74 | Type-3 C0 dense sequence |
| c1 | 94 | Type-3 C1 dense sequence |
| c2 | 15 | C2 direction fixture |
| child | 19 | Seven child, death and re-entry |
| purchase | 20 | Forest funded purchase, goal and save/reload |
| Total | 289 | 1,156 byte-identical file comparisons |

Every sample compares full WRAM, SRAM, VRAM and framebuffer files. Receipt,
ROM, binary, input, selected modules, runtime and analysis identities are
checked against the actual builds. The comparison establishes retention of
these existing native boundaries; it does not extend their original acceptance
to whole courses. Map/pipe/position/immunity, C2 direction and purchase funding
fixtures remain as declared in the inputs. Negative admission probes reject a
missing selected recipe and a removed native adaptation. Thirteen existing
graphics/modern-program tests pass, including relocation and bank-semantics
rejection tests. Python compilation and diff checks pass.

## Reproduction

```sh
python3 tools/prepare_mazo_gfx282.py --cumulative
python3 -c "import sys; sys.path.insert(0,'tools'); import native_sprite_gap; native_sprite_gap.prepare('demo11-native-mazo-cumulative-v1')"
python3 tools/m1.py --target demo11-native-mazo-cumulative-v1 scaffold
python3 tools/m1.py --target demo11-native-mazo-cumulative-v1 generate
python3 tools/m1.py --target demo11-native-mazo-cumulative-v1 build
python3 tools/mazo_second_route.py --mode highhop --hops 240 --output FRESH.script
python3 tools/m1.py native --target demo11-native-mazo-cumulative-v1 --script FRESH.script --capture FRESH
python3 tools/qualify_mazo_cumulative.py --run-side parent --prefix FRESH_PREFIX
python3 tools/qualify_mazo_cumulative.py --run-side candidate --prefix FRESH_PREFIX
python3 tools/qualify_mazo_cumulative.py --capture FRESH --prefix FRESH_PREFIX --output FRESH_REPORT.json
```

The completed report is `local/reports/mazo-cumulative-qualified-v1.json`.
The three modern pilot inputs are now tracked, with text verified against the
original capture route digests before promotion. The source mazo reference,
core, frontend and options are checked by the reused second-boss qualifier.

## Remaining work

Follow the actual transformation/cutscene into room `192` and qualify the
ordinary goal, map and save boundaries. The map override entering room `151`
is a practice fixture and cannot prove ordinary world progression or the
correct save identity. Japanese text in rooms `191/192`, later audible music,
the room `190` level route and full unassisted play remain open. No product
promotion or complete-game acceptance follows from this integration.
