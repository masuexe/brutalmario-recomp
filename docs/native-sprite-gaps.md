# Native custom sprite gap inventory

## Current native census (2026-10-30)

The [cumulative recovery and native-aware census](native-sprite-product-reconciliation.md)
supersede the historical counts below for `demo11-native-sprite-product-v1`.
The previously omitted25/33/94 programs are now present, with27 source-matched
motion samples and741 complete unchanged parent-state comparisons. Resolving
external native sprite lists is essential: treating CA-bank pack addresses as
raw LoROM bytes invents ED/FA gaps. The new census reads all512 lists and finds
164 used custom slots with10 placeholder records. It does not establish global
official-source absence or whole-course playability.

## Source-scope correction (2026-10-29)

The historical inventory below checks only `7hero`, `cheap-demo` and `mazo`,
as declared by `DONORS` in `tools/audit_sprite_gaps.py`. Its "no donor record"
category means absent from those three sources, not absent from all official
demos. The [hollow branch review](forest-hollow-route.md) now identifies an
official demoOnly1 type-1 A2 record and a protected 7,392-byte candidate, with
the same room182 placement. The subsequent [r14 restoration](forest-a2-restoration.md)
installs its reviewed native program, qualifies the menu, one funded purchase
and saved ownership, return/re-entry and the room104 automatic exit. Other
purchases and ability effects remain open. A2 must no longer be treated as
having no official source or no native installation.
Other slots need the same chronology-aware review before any global absence
claim. The counts below preserve the original three-source audit, not a current
whole-product restoration census.

Product r14 also lacked the independently reviewed95 record. The subsequent
[r15 integration](native-lowmirror-restoration.md) adds the newest official
Boss Demo program, equal to7hero, and qualifies selected16B behavior against a
fresh source replay. The other six placed rooms need fresh r15 checks. R15
also corrects ten mapped programs' low-memory bank assumptions; this does not
convert the historical tables below into a current full-game census.

R15 is subsequently rejected for an actual C0 loading crash. The95 component
checks remain valid; accepted product r14 still lacks this record.

## Result

The recipient places 163 custom sprite slots across its rooms. Fifty-four of
those slots hold the type-0 placeholder record instead of a program. The 54
slots cover 78 rooms and 94 placements. This document records the inventory and
the donor availability. It does not install a record and it does not claim
behavior.

## Categories

| Category | Slots | Rooms | Note |
| --- | ---: | ---: | --- |
| Type-1 record in a donor | 40 | 61 | The newest donor with the slot supplies a program |
| Type-3 record only | 3 | 2 | Slots `C0`, `C1` and `C2` |
| No donor record | 11 | 16 | Slots `96`, `97`, `99`, `A1`, `A2`, `A5`, `A6`, `E8`, `E9`, `EA`, `F5` |

The type-1 group has the largest coverage. Thirty-three slots exist only in
`cheap-demo`. Three exist in both `cheap-demo` and `7hero`. Two exist only in
`7hero` and two only in `mazo`.

The eleven slots without a donor record need a source review before any
recovery. The three type-3 slots need the constructor contract from
[the type-3 review](native-sprite-type3.md).

## Largest gaps by room count

| Slot | Rooms | Donor types |
| --- | ---: | --- |
| `95` | 7 | `7hero` type 1 |
| `92` | 6 | `cheap-demo` type 1 |
| `10` | 5 | `cheap-demo` type 1 |
| `12` | 5 | `cheap-demo` type 1 |
| `55` | 5 | `cheap-demo` type 1 |
| `11` | 4 | `cheap-demo` type 1 |
| `13` | 3 | `cheap-demo` type 1 |
| `99` | 3 | none |

Slot `95` is the newest-donor case. `cheap-demo` and `mazo` hold the
placeholder, and `7hero` holds a type-1 record with a 5,144-byte protected
block.

## Installation status

All 40 type-1 slots now hold a recipe. A recipe pins the donor record, the
protected block, the native address and the install offset.

| Group | Slots |
| --- | ---: |
| Installed in one target | 35 |
| Installed in an earlier single-slot target | 5 |
| Type-3, still open | 3 (`C0`, `C1`, `C2`) |
| No donor record | 11 |

The 35-record target is `demo11-native-sprite-full`. Its ROM is
`78c4647d9d47026d7fd3316c2efda31bb3ec71d7d21e951274b9acb658414cc0`, with 37
packs and 37 module views. See [the full gap target review](native-sprite-full.md).

## Room verification classes

An actor compare needs a live room on both hosts.

| Class | Rooms |
| --- | --- |
| Exact without an offset | `00D`, `05D`, `083`, `087`, `08B`, `0AF`, `142`, `147`, `155`, `15D`, `160` |
| Phase-exact | `0A5`, `091`, `0A2`, `0B5` |
| Missing second actor | `151`, `190` |
| Different actor positions | the remaining open rooms |

## Room 0A6 and slot 80

Room `0A6` places twelve sprite entries, and every entry uses slot `80`. The
recipient record is `012800003f039944e92822002a220000`, whose init field is
`0x2228E9` and main field is `0x222A00`. No code lives at either address, so the
record cannot run.

The `cheap_demo` image holds the same slot with the record
`012800003f039944e9a82400aa240000`. Its init is `0x24A8E9` and its main is
`0x24AA00`, and a 919-byte `STAR` block starts at `0x24A8DA`. The `demo6` and
`demo7` images hold the same slot at their own addresses. The `ow`, `mazo`,
`7hero` and `boss` images hold only the placeholder.

The recipe `config/native-content/sprite80-module.json` moves the `cheap_demo`
block to bank `A0` and keeps its low 16 bits. One inner `JSR` target moves with
the block: a code patch changes `2A29` to `2AA9`.

A test target places one slot `80` entry at the start of room `155`. The module
runs (`bank=A0 resolutions=110980`), the actor holds its position, and the actor
then creates one `0x4F` actor and disappears. The run holds no `BRK`. This
matches the reported purpose: a still actor that creates a normal enemy and
dies.

Room `0A6` itself creates no actor with the pipe fixture on either host, so the
fixture cannot qualify that room. The product target holds the record and the
module, and a capture of room `0A6` on it holds no `BRK`.
## Remaining causes

Two rooms match in every frame before the donor creates a second actor. Those
rooms are `151` and `190`. The target never creates that actor.

Some rooms freeze with the pipe poke. The same freeze occurs on the unmodified
Demo 1-1 image in the reference emulator, so the entry fixture causes it.
Rooms `091` and `0A2` froze with the older two-dump fixture and ran in the
one-frame fixture, so the freeze also depends on the fixture timing.

## Room 16B

Room `16B` places slots `8C`, `95`, `C0` and `C1`. The recipient record for
`8C` exists. The other three are placeholders. A donor capture of room `16B`
shows four actors whose custom bytes read `8C`, `95`, `33` and `95`. The
recipient capture of the same fixture shows three actors, and the `95` slots
carry unrelated sprite ids.

The room `16B` donor behavior therefore depends on slots that the recipient
does not carry. A room entry check cannot pass until those slots carry a
program.

## Reproduction

```
python3 tools/audit_sprite_gaps.py
```

The report is `local/reports/native-sprite-gaps.json`, SHA-256
`954c6828d4d71f7415c3e8760c3068b37ff5fbacb69104d1842a5f8bb0e20f55`. The tests
are `tests/test_sprite_gaps.py` and pass 6/6. The full suite passes 269/269
tests. The log is `local/reports/unit-tests-status.log`.
