# Official A2 shop restoration and native product r14

Date: 2026-10-29. Working target: `demo11-native-product-r14`.
ROM SHA-256:
`393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b`.
Native binary SHA-256:
`b309471f393ea33683f0173d63336ff3992392250ce24e4d5f5836b094cfe8cd`.

## Result and scope

The missing modern A2 program now runs on the native PC target. The ordinary
Up entrance from hollow course `11F` opens Vivian's shop in room `182`.
Four item selections and the bottom clamp work; insufficient funds produce
the original response without charging. An explicit balance fixture funds one
real 1,111-price purchase. The program deducts the price, sets ownership and
rejects a duplicate purchase without charging again.

B returns to the measured incoming position `800/352` in room `11F`; Mario
remains there after 120 frames and can enter the shop again with Up. A separate
funded route returns, reaches the existing real tape, saves and reloads File A.
Both the remaining balance and ownership are present in SRAM and survive reset.
The other A2 placement in room `104` now performs its original automatic exit
to `180`, where the parent r13 remains stuck in `104`.

These are fixture-assisted component and save boundaries. They do not establish
ordinary complete traversal, earned purchase funds, all four item purchases,
ability effects, the cleared-flag alternate room104 route, or full-game
acceptance. The earlier r13 survey's 228 playable entries and zero crashes are
not a fresh r14 survey. C2 and the broader endgame/music/graphics work remain
open. The separate named qualification candidate is
`demo11-native-forest-a2-v3`; it has the same ROM and packs as r14.

## Official source and bounded adaptations

The [hollow investigation](forest-hollow-route.md) identified the matching
modern placement in official demoOnly1. The older three-source gap census had
not checked it. Demo 1-1 has a placeholder; demoOnly1 is the newest inspected
official release retaining this program and this room182 placement.

Source ROM: `b8d86f894f6c07aeb74794c59adab8f336080285b4781a3e1c921615a2d8216b`.
The source record is `012200b735839944bfd730ecd7300000`, with init `30D7BF`
and main `30D7EC`. Source placements are `104` and `182`.

Recipe: `config/native-content/spritea2-modern-module.json`.
Preparer: `tools/prepare_forest_a2.py`.

| Resource | Identity |
| --- | --- |
| Original STAR block | `30D7B4`, 7,400 bytes including the 8-byte header |
| Original complete block SHA-256 | `55eda050abab08a1442a452392fbce05494276a6eb7fde8d42f805dcdad961bb` |
| Payload inside the header | 7,392 bytes, including its `MDK` prefix |
| Native mapping | `9DD7B4`, preserving all low 16 address bits |
| Adapted pack SHA-256 | `ccd76df8480d3c753d605720dd809db3e47739123d2f8fae8130727297eeb8fc` |
| Native record | `012200b735839944bfd79decd79d0000` |

Static admission checks 32 local entry states and 868 instruction variants.
The four-entry short dispatch after `30D85D` is explicitly bounded and pinned;
its target words are not decoded as instructions. Seven self-bank long calls
and six long data references move to bank `9D`. Unreviewed indirect control
flow, escaped bank-local references, missing relocations and changes outside
the reviewed bank operands are rejected. Dynamic WRAM pointers still require
the execution checks below.

The six direct outside calls are `0086DF`, `01801A`, `0FF780`, `10D8D0`,
`28FCC0` and `28FD6D`. Reviewed shared ranges match the parent byte for byte.
The recipient's existing GetDrawInfo helper at `28FD6D` differs at two table
operands: source `8000/8002`, recipient `FD69/FD6B`. Its recipient table is
`0C 1C 01 02`; the source locations contain `6B 00 00 00`. Those exact
differences are checked and the existing recipient helper is retained.
This is a version adaptation, not whole-engine source parity.

The program selects graphics `292..29B` by course. All ten already exist in
r13; their complete compressed and decoded bytes match demoOnly1. No graphics
payload, font, music or room layout is copied by this checkpoint.

## Return adaptation and rejected prototypes

The source return selector table contains zeroes. In both the official source
diagnostic and the direct 9D code candidate, B therefore selected secondary
`100` and reached room `000`. Room182 has no authored return in its live exit
table. The different byte at offset177 of its Layer1 allocation (`6E` in the
recipient, `71` in demoOnly1) is not evidence of an exit: it is not registered
as one by the game. An earlier screen14 pipe-action probe selected an absent
exit and is not valid route evidence.

Existing secondary `1C1` names room11F but lands at `2280/457` after settling,
beyond its current four-screen layout. It is preserved. A new secondary `1FF`
uses four formerly zero bytes to encode the measured safe incoming position:

| Address | Before | After |
| --- | --- | --- |
| `05F9FF` | `00` | `1F` |
| `05FBFF` | `00` | `16` |
| `05FDFF` | `00` | `43` |
| `05FFFF` | `00` | `68` |

The fine-position encoding follows the recipient's loader at `05DC80` and
its subsequent horizontal-screen assignment. Runtime checks confirm room11F
and `800/352`, rather than relying on the encoding calculation alone.
The preparer rejects a possible `screen/07/00/FF` incoming reference in all
403 unique protected Layer1 allocations it can validate. This conservative
scan and the zero original entry bound the allocation claim; it is not a
complete semantic parser or a proof about arbitrary dynamic engine references.

Only A2's hollow variant1 selector byte at `30F3C7` changes `00 -> FF`.
The original `07` secondary-exit flags and the room104 special handler remain.
Every other ROM byte outside the A2 record and four new entrance fields matches
r13. All 46 previous pack mappings and bytes remain; A2 adds the 47th pack.

The first D2 prototype crashed after entering its module. D2 does not provide
the source bank's low WRAM/IO mirrors; the program uses PHK/PLB and absolute
RAM/register accesses. Final admission requires a bank with those mirrors.
The new 9D mapping qualifies the exercised paths. The failed prototype and
the earlier 9D candidate with the incomplete return remain under ignored
`local/probes/forest-a2/prototype-{d2,9d}` and their original capture directories.
They are not registered as playable restoration targets. Other existing
high-bank modules need a separate audit before extending this finding to them.

## Runtime and save evidence

Thirteen official-source/native menu and purchase pairs agree on asserted
room, life, selector, phase, currency and ownership fields and on the complete
384-byte message tile buffer at each pair. The source is entered through a
clearly labelled forced destination/translevel fixture from naturally entered
Baby Yoshi Hill because its untouched hollow entry stalls in mode12. Source
and recipient images differ. NPC motion, full VRAM/framebuffer and audio are
not equated; screenshots retain the source's garbled message glyphs.

The balance fixture writes only currency `2222`. The original guest program
charges `1111`, changes ownership byte `$7F:1811` from `00 -> 01`, and leaves
`1111` after a duplicate attempt. After the real goal, the observed one-unit
gain makes `1112`, matching the one-unit gain in the unchanged normal control.
The guest saves that balance at SRAM `0809..080B` and
ownership at `0811`. Before the clear these SRAM bytes remain zero. After the
clear and console-reset File A reload, WRAM and SRAM agree on `1112` and `01`.
The normal completion copies are `1EE5`, SRAM `0043/01F0`, `0F -> 8F`.
Ordinary onward entry loads Ghost Forest `114`.

The unfunded return/re-entry route preserves four lives, no owned items and
the uncleared `0F` completion/save state. Room104 uses a separately labelled
destination/pipe fixture. Its live A2 and actual pipe action match the source;
both reach `180` without setting the clear flag. Entry playerY differs by
three pixels, and destination moving actors are not compared. The parent
control remains in `104` with the placeholder record.

The unchanged hollow normal route matches parent r13 exactly at nine samples:
full WRAM (131,072 bytes), SRAM (32,768 bytes) and VRAM (65,536 bytes), 27
complete dump comparisons. It never uses A2. Menu, purchase and gate captures
log actual bank9D resolutions and executed instructions, with every other
external mount unused. This is native integration evidence; no same-image
emulator compatibility is claimed.

## Reproduction

The tracked `forest-a2-*` input scripts describe their fixtures. Native routes
are `menu-return`, `funded-purchase-save` and `gate104`; the unchanged control
uses `forest-hollow-normal-save.script`. The source scripts are separate and
never represent ordinary recipient traversal. Captures and original receipts
are preserved under `local/captures`.

```sh
python3 tools/prepare_forest_a2.py
python3 -c "import sys; sys.path.insert(0, 'tools'); from native_sprite_gap import prepare; prepare('demo11-native-product-r14')"
python3 tools/m1.py scaffold --target demo11-native-product-r14
python3 tools/m1.py generate --target demo11-native-product-r14
python3 tools/m1.py build --target demo11-native-product-r14
# Use fresh native capture names and the tracked scripts, then:
python3 tools/qualify_forest_a2.py --prefix FRESH --output local/reports/FRESH.json
```

Default final native prefix: `forest-a2-r14`, suffixes
`-{menu,purchase,gate104,normal}-v1`. Official source captures:
`forest-a2-source-menu-v2`, `forest-a2-source-purchase-v1` and
`forest-a2-source-gate104-v1`. Parent controls retain their own r13 identities.
The checker verifies exact ROM delta, inherited mappings, pack bytes,
preparation pins, current build/binary and executed input identities before
checking the outcomes.

Report: `local/reports/forest-a2-r14-acceptance-v1.json`, SHA-256
`32cc67cacc6c72b854768dc8e0c2e131e69fa9f5d456a82236b1d0740515f8d5`.
The 353-test suite passes, including nine new
admission tests for missing data relocations, corrupted dispatch, unwanted code
changes, helper changes, bank mirrors and return encoding. Log:
`local/reports/unit-tests-forest-a2-v1.log`.

Continue Ghost Forest `114`, other Forest routes, full traversal and remaining
purchase/ability checks. Audit the low-memory assumptions of other mapped
programs with concrete runtime probes; this checkpoint does not certify them.

The subsequent [r15 checkpoint](native-lowmirror-restoration.md) corrects ten
such mappings and adds the missing95 dependency. Its fresh A2 menu/purchase and
hollow normal replays match the original r14 captures across51 dump points,
153 full WRAM/SRAM/VRAM comparisons. The r14 evidence above retains its original
identity. R15 was subsequently rejected for an actual C0 loading crash; r14
remains the accepted working target. These A2 regressions remain valid bounded
component evidence, not a safe-product claim.
