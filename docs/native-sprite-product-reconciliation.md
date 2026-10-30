# Recovering three omitted sprites in the cumulative native game

## Result (2026-10-30)

The previous cumulative candidate still held placeholder records for25,33
and94, although separate historical targets had installed those programs.
The new isolated descendant `demo11-native-sprite-product-v1` carries all
three official programs and preserves the parent’s51 pack mappings exactly.
Fresh captures qualify actual25 ascent,33 horizontal/player movement and94
vertical motion/state changes, rather than appearance alone. The earlier
single-slot targets remain historical; their captures are not relabelled.

| Artifact | Identity |
| --- | --- |
| Parent | `demo11-native-seven-product-v1` |
| Parent ROM | `0f04abec07f424c482291c2aeee082bf4c41d3468f30e2483d06a728978cd8af` |
| Candidate ROM | `1daaa9411b633fb066b2b94a8970a4f12057b391819ff90b775b89b511b4ab11` |
| Candidate executable | `f4148c02b6d04f2a1b79d19b1e9a76e026b29d992e8d7ec8f18a2dfd4d11f988` |

Accepted historical product r14 remains unchanged, and rejected r15 remains
rejected. This experimental descendant is not whole-game acceptance.

## Source and mapping review

Newest official Boss Demo contains the same complete records and protected
programs as7hero. The newer demoOnly1 and Demo1-1 records are placeholders.
The new recipes select Boss;7hero supplies fresh behavior references with
matching bounded room content. Version-local IDs alone do not establish that
equivalence: the checker compares full code, records, foreground/background
allocations and sprite placements for the exercised rooms.

| Slot | Room | Official protected program | Bytes | Native mapping |
| --- | --- | --- | ---: | --- |
| `25` | `154` | `20:AB9D` | 8,801 | `8F:AB9D` |
| `33` | `0FE` | `15:ADFE` | 1,328 | `8E:ADFE` |
| `94` | `0EF` | `17:B34D` | 2,096 | `8D:B34D` |

Program SHA-256 values, in table order:

- `3557997cedcd519ecf3e6b04241c4c93ef95512bb70b837adec40874bc836ead`
- `60831043e677facacf4d3c901226973f6d67fe1e5a92a0a9b888083d6d681895`
- `4ced2fe700c642d539ba511418d1c7e35c811cb04d2e77b01d1faa08006c7693`

Old independent banks A8/A7/A6 now contain other cumulative programs/resources.
The new free banks8F/8E/8D preserve low16 address bits and source low-WRAM/I/O
mirrors after PHK/PLB. No program bytes or self-call operands need changing.
Only the three16-byte recipient records change:48 actual ROM bytes total.
No room layout, exit, map event, physics, combat timing or save code is patched.
The target mounts54 packs; all51 inherited descriptors and bytes remain pinned,
including Seven E0/controller/resources/ending hooks, mazo and C0/C1/C2.

Recipes are `config/native-content/sprite{25,33,94}-boss-product-module.json`;
the integration plan is `sprite-product-reconciliation.json` in that directory.
The preparation tool audits exact lineage, selected source programs, bounded
records, low-mirror mappings and retained descriptors. Six admission tests
reject wrong lineage, missing programs, incompatible banks, unpinned sources
and substituting another sprite’s qualified recipe.

## Fresh runtime evidence

Nine samples per room are taken at live entry, after the position fixture and
frames1/16/32/64/128/256/512. All27 native/7hero sample pairs match functional
player/room state and all19 selected actor fields plus allocated slots. There
are36 paired actor rows because94 places two actors. Fresh parent controls
lack the selected custom actors throughout these same sampled fixtures.

- Sprite `25` rises from Y240 to111 at X208 while the player stays32/160.
- Sprite `33` moves from X208 to133 at Y368, with matching player movement from128/320
  to203/320. This is game-driven movement after the initial position fixture.
- Sprite `94`’s moving actor cycles between phases0/1 and several Y positions around
  222..321; the second actor stays at176/224 with variant02.

Native banks8F/8E/8D actually execute. Foreground/background allocation sizes
are13/16 bytes for154,584/303 for0FE and513/346 for0EF; complete bounded bytes
and sprite lists match7hero. The early v1 fixtures are excluded: they left the
native high-room bit set for0FE/0EF, entering1FE/1EF, and placed Mario below
the safe154 entry. V2 fixes those fixtures and asserts full16-bit room IDs,
live mode and actual motion. The earlier failures are not evidence of a
program failure in the correct rooms.

Five regressions compare247 unique samples and741 complete WRAM/SRAM/VRAM
files against the qualified parent, with no masks or tolerances:

| Retained feature | Samples |
| --- | ---: |
| Fifth-trial ordinary platform/vine return | 80 |
| Seven child birth, death, fonts and re-entry | 19 |
| Hollow shop purchase/save/reload | 20 |
| C2 direction/child generation | 15 |
| Explicit ending fixture and hidden green-mushroom award | 113 |

The inherited trial5 script emits `activated` at both doors. Only its final
far-door file survives; it is compared and counted once. This regression does
not claim comparison of the overwritten initial-hub file. The independent
[five-door check](native-sprite95-current-rooms.md) retains that branch evidence.
The ending fixture still does not prove an earned Seven victory or saved clear.

## Native-aware remaining-record inventory

`tools/audit_native_sprite_placements.py` resolves each sprite-list pointer
through verified native packs before falling back to LoROM. Four room lists
(`183`,`184`,`191`,`192`) live in `mazo-b0-corridor.bin`. Treating their CA-bank
addresses as raw ROM offsets reads unrelated bytes and invents missing slots
such as ED/FA. The new census parses all512 lists within their mapped allocation
or ROM bank and verifies all54 pack files. Three tests cover allocation bounds,
partial records and these actual external-list identities.

The corrected static census finds164 used custom slots and these10 placeholder
records. This describes placed records, not playability, intended missing
content, or absence from every official donor:

| Slot | Rooms |
| --- | --- |
| `96` | `1F0` |
| `97` | `1EF` |
| `99` | `174`,`175`,`176` |
| `A1` | `175`,`176`,`178` |
| `A5` | `056`,`102` |
| `A6` | `00C` |
| `E8` | `111`,`119` |
| `E9` | `1CF` |
| `EA` | `1F3` |
| `F5` | `1E2` |

These slots need a chronology-aware official-source and room-mechanism review.
The old three-donor “no record” label cannot establish global source absence.

## Reproduction and scope

```
python3 tools/prepare_sprite_product_reconciliation.py
python3 tools/m1.py scaffold --target demo11-native-sprite-product-v1
python3 tools/m1.py generate --target demo11-native-sprite-product-v1
python3 tools/m1.py build --target demo11-native-sprite-product-v1
python3 tools/qualify_sprite_product_reconciliation.py --prepare
```

The generator immutably verifies scripts in ignored
`local/probes/sprite-product-v2/`. For SLOT25/33/94, run `native-SLOT.script`
on the candidate into `sprite-product-SLOT-native-v2` and on the parent into
`sprite-product-SLOT-parent-v2`. Run `source-SLOT.script` with
`config/7hero-donor.json` and `snes9x_echo_buffer_hack=enabled` into
`sprite-product-SLOT-source-v2`. Preserve all existing scripts/captures.

The five additional candidate captures are `sprite-product-reg-KEY-v1`, using
the exact input paths and parent controls in the checker’s `REGRESSIONS` table.
Check with:

```
python3 tools/qualify_sprite_product_reconciliation.py --output local/reports/FRESH.json
python3 tools/audit_native_sprite_placements.py --output local/reports/FRESH-CENSUS.json
```

Qualification report `local/reports/sprite-product-v3.json` and its identical
recheck have SHA-256
`dcb4986bf367ffc4b793634fafa8098cac6b23c6e9563d7d7571b83ef24984e7`.
The standalone census report `sprite-product-placement-census-v2.json` has
SHA-256 `300c69b8ea747f1e1537eed4db99f1b6701a086e99e452ac6f8ee96a3750ef9d`.
All377 unit tests pass in121.596 seconds, including the six integration
admission tests and three native-list tests. The log is
`local/reports/unit-tests-sprite-product-v2.log`. The preceding374-test run
also passed before the native-list tests were added.

These room-entry/immunity/player-position fixtures qualify selected motion
and state behavior. Full rooms, attacks or child generation beyond the sampled
mechanisms, exits, audiovisual equality, earned Seven/mazo victories, saved
completion, remaining Forest routes and the other missing assets remain open.
