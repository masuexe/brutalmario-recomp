# Forest course identity and linked normal-exit acceptance

Date: 2026-10-29. Target: `demo11-native-product-r13`.
ROM SHA-256:
`c02dc11e0c79c804740b38797463a1fc9645a8a05cdb4e18c7c09fff45760681`.
Native binary SHA-256:
`131b9522f4edfa4eba5793780f228a9f3ed1c7a7e040e46e00bd6f032e493be0`.

## Result

The earlier World 2 list mixed unrelated room IDs with Forest course names.
The corrected catalog has ten courses, all with an existing main-map node.
Fresh captures enter each course through that node without replacing its level
assignment. Fishing Spree and the bridge now have linked real goal-tape clears,
natural onward map movement and saved completion after File A reload. A separate
Fishing Spree run also verifies cleared-course re-entry.

This checkpoint changes the testing catalog, route scripts and evidence checks.
It changes no game code, ROM, resource pack, overworld assignment or save format.

## Corrected identities

| Room | Translevel | Course | Map 0 X / Y | Map index |
| --- | --- | --- | --- | --- |
| `113` | `37` | Fishing Spree | `00E8 / 01A8` | `2AE` |
| `111` | `35` | Thou Shalt Not Cross This Bridge | `0128 / 01A8` | `3A2` |
| `015` | `15` | A Remote Shack | `0168 / 01A8` | `3A6` |
| `123` | `47` | Lost Forest | `0188 / 0178` | `378` |
| `11F` | `43` | It's Moldy Within the Hollow | `01B8 / 0158` | `35B` |
| `114` | `38` | Ghost Forest | `01E8 / 0188` | `38E` |
| `11C` | `40` | Morton the NEET (castle entrance) | `01E8 / 01B8` | `3BE` |
| `11B` | `3F` | World of Water | `00E8 / 01D8` | `2DE` |
| `11E` | `42` | Mario the Pyromaniac | `01B8 / 0188` | `38B` |
| `129` | `4D` | The Cursed Mansion | `01B8 / 01B8` | `3BB` |

The [version-specific name directory](https://wikiwiki.jp/kitikumario/ステージ名一覧)
identifies the Demo 1-1 family names. In particular, `123` is Lost Forest,
`129` is The Cursed Mansion, `121` is Red Switch Palace and `126` is Baby Yoshi
Hill. The general [map directory](https://wikiwiki.jp/kitikumario/マップ攻略)
also includes older names and scrapped courses; it must be read by version.
The [Forest overview](https://brutalmario.fandom.com/wiki/Forest) corroborates
course membership. These pages were consulted on 2026-10-29.

The corrected `config/world-map.json` World 2 list is backed by
`config/forest-course-identity.json`. Other worlds in that older catalog remain
provisional. Historical reports generated from the old list are not retroactive
World 2 acceptance evidence. The seven assisted boundaries in
[the earlier inventory](world2-route-inventory.md) remain valid room checks;
most of their source rooms are not Forest courses.

## Evidence beyond matching numbers

The checker verifies all of the following:

- The actual node's translevel in the map-mode `$D000` table. It does not use
  that table from a gameplay dump, where the memory can serve other purposes.
- The node coordinates, ordinary entry button, mode `14`, room number,
  translevel, four remaining lives and a changing guest frame counter.
- The 19-byte name record, complete bounded sprite list and the first 256
  bytes of the Layer 1 stream. These fingerprints are pinned in the catalog.
- Official input ROM identities from `config/content-versions.json` for
  Demo 1-1, demoOnly1, 7hero and cheap_demo. Name and sprite bytes match all
  four sources. The layout windows match the two modern baselines in all ten
  cases. The older room `11F` windows differ; this is recorded, not replaced.

The name loader is the installed routine at `03:BB20`, called at `04:8E81`.
It uses translevel * 19. Its long table read at `03:BB56` selects a
version-local address: `15:947E` in the recipient, `19:DEFD` in demoOnly1,
`17:F62C` in 7hero and `13:85F0` in cheap_demo. The checker validates the
multiplier and read instruction instead of treating these addresses as shared.
The 256-byte layout windows are identity fingerprints, not complete layout or
behavior comparisons.

## Fishing Spree normal goal and persistence

The [Fishing Spree guide](https://brutalmario.fandom.com/wiki/Fishing_Spree)
describes the sky-platform course and its separate key route. This checkpoint
checks the normal tape; it does not exercise the secret route.

`recomp/inputs/forest-fishing-normal-save.script` uses a map-coordinate fixture
to the existing node, held player position near the final platform and damage
immunity. It does not edit node assignments, destinations, actors, completion
flags, events or SRAM. The actual rightward guest input touches the tape.

| Boundary | Native result |
| --- | --- |
| Fresh node and course | Clear byte `$1ED9 = 05`, four lives |
| Before goal | Room `113`, active vanilla goal tape `7B`, status `08` |
| Tape touched | Goal timer `$1493 = F0`, tape status `06`, no lost life |
| Map return | Mode `0E`, completion byte `85`, next bridge node `0128 / 01A8` |
| Guest save | SRAM `0037` and `01E4` both become `85` |
| Console reset and File A reload | Both SRAM copies and WRAM retain `85`; bridge node remains selected |
| Cleared-course re-entry | Room `113`, mode `14`, four lives, clear byte `85` retained |

These are assisted goal, map and save boundaries. Walking through the complete
course, the five Dragon Coins, secret key exit and heard music remain open.
The other eight courses have node/entry evidence only. The bridge also has
the linked normal-exit evidence below.

## Linked first and second normal exits

`recomp/inputs/forest-first-two-normal-save.script` continues after the first
clear at the actual bridge node. It presses the normal entry button without
another map fixture, enters room `111`, and uses a labelled position/pipe-action
fixture on its existing screen `0B` exit (`2E/04`) to reach goal room `02E`.
Held player position and rightward guest input touch that room's real tape.
The bridge guide describes this exit pipe at the end of the donut-block course;
walking through the autoscroll itself remains untested.

| Boundary | Result |
| --- | --- |
| First clear -> normal bridge entry | Map `0128/01A8` -> room `111`, translevel `35` |
| Existing bridge exit | Room `111`, screen `0B` -> room `02E`, mode `14` |
| Bridge tape | Active `7B/08` -> goal timer `DF`, tape status `06` |
| Second clear | Natural map movement to shack node `0168/01A8` |
| First saved clear | WRAM `$1ED9`, SRAM `0037` and `01E4` retain `85` |
| Second saved clear | WRAM `$1ED7`, SRAM `0035` and `01E2` change `03 -> 83` |
| Reset and File A reload | Both clear bytes and all four SRAM locations persist |
| Normal entry after reload | Actual shack node -> room `015`, translevel `15`, four lives |

The bridge byte is `03/83` in the linked run, versus `01/81` in the isolated
probe: the first clear unlocks a direction bit before the bridge is cleared.
The checker retains that difference. No map-coordinate or game-mode fixture
is permitted after the first clear in the linked script. No completion, actor,
exit destination, event or SRAM write is used. These are assisted normal-goal
and progression boundaries, not complete traversals or secret-exit acceptance.

## Captures, checker and reproduction

- Ten native entry captures: `local/captures/forest-r13-ROOM-node-v1`.
- Native clear/save captures: `local/captures/forest-r13-fishing-normal-save-v1`
  and `forest-r13-first-two-normal-save-v1`.
- Scripts: `recomp/inputs/forest-roomROOM-node-entry.script` and
  `recomp/inputs/forest-fishing-normal-save.script` and
  `recomp/inputs/forest-first-two-normal-save.script`.
- Checker: `tools/qualify_forest_course_identity.py`.
- Final report: `local/reports/forest-course-acceptance-v1.json`, SHA-256
  `9e34b87dc1423bacddd42675052341a6ef04425ca127e295074787579f0d89ec`.

The report pins ROM, build, runtime packs, binary, original and executed input,
WRAM, SRAM and framebuffer identities. It checks script writes against the
position/immunity fixture scope. Use fresh capture names and report paths:

```sh
for room in 113 111 015 123 11f 114 11c 11b 11e 129; do
  python3 tools/m1.py native --target demo11-native-product-r13 \
    --script recomp/inputs/forest-room${room}-node-entry.script \
    --capture FRESH-${room}-node-v1
done
python3 tools/m1.py native --target demo11-native-product-r13 \
  --script recomp/inputs/forest-fishing-normal-save.script \
  --capture FRESH-fishing-normal-save-v1
python3 tools/m1.py native --target demo11-native-product-r13 \
  --script recomp/inputs/forest-first-two-normal-save.script \
  --capture FRESH-first-two-normal-save-v1
python3 tools/qualify_forest_course_identity.py \
  --prefix FRESH --output local/reports/FRESH.json
```

The checker requires all ten entry captures under the chosen prefix. It rejects
an existing output rather than rewriting an older receipt.

Two cheap_demo reference probes (`forest-cheap-fishing-normal-save-v1` and
`forest-cheap-fishing-goal-v2`) did not establish entry: their startup sequence
left the introduction active. They are retained as failed exploratory evidence,
not donor gameplay qualification. Static official-source identities above remain
valid. No same-image reference parity or source full-clear parity is claimed.

The existing unit suite passes **344/344**, with log
`local/reports/unit-tests-forest-identity-v1.log`. The new evidence checker also
passes ten identities, two linked normal clears/saves, File A reload and onward
shack entry. The prior identity-only reports remain preserved separately.

## Subsequent shack checkpoint

[The shack report](forest-shack-route.md) now qualifies a real On/Off change,
three real Big Boo impacts and victory, normal save/reload, onward Lost Forest
entry and a separate real death/re-entry on native and a limited same-image
reference route. These assisted boundaries supersede its earlier entry-only
status. Seven other course clears and the full shack puzzle traversal remain
open.

## Subsequent Lost Forest checkpoint

[The Lost Forest report](forest-lost-route.md) now checks all eight correct
maze choices, a wrong-color reset control, the real tape, normal save/reload and
onward hollow-course entry. This supersedes its earlier entry-only status.
The first log/P-switch puzzle traversal remains open; six other course clears
remain to be checked.

## Next work

Continue the hollow course at room `11F` and its connected rooms.
Resolve the actual secret routes and the remaining course chains in order.
Use the On/Off ghost-house and other relevant guides when their mechanics are
exercised. Keep C2 restoration, endgame acceptance and music/graphics work open.
