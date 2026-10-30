# Native type-3 SpriteTool records C0, C1 and C2

## Latest experimental restoration (2026-10-29)

The [C2 descendant](native-type3-c2-restoration.md) supersedes the older C2
constructor speculation and absent-record status for its own target. C2 now
executes as a shooter in low-mirror bank91; actual two-direction generation
matches10 source samples, and normal094 entry stays live through600 frames.
All six16B shooter placements also load. Accepted product remains r14; the
older rejected targets and partial captures below keep their historical scope.
C0/late-C1 phase, E0 birth and full route acceptance remain open.

## Result

The newest official donors place three type-3 records in slots `C0`, `C1` and
`C2`. The recipient keeps the same room placements but the slots hold type-0
placeholders. This document records the static review and one bounded entry
check. It does not install the records and it does not claim behavior.

## Records

The `7hero` and `boss` images hold byte-identical records and byte-identical
protected blocks.

| Slot | Field | Value |
| --- | --- | --- |
| `C0` | Record | `03ffffffffffffffe68613ea8613ffff` |
| `C0` | Init | `13:86E6` |
| `C0` | Block | 205 bytes, SHA-256 `11db36ef4b3f6ca9d4b848173072cba0e4c08a87c776e75fd9376a9154dee92e` |
| `C1` | Record | `03ffffffffffffff17ae131bae13ffff` |
| `C1` | Init | `13:AE17` |
| `C1` | Block | 213 bytes, SHA-256 `a1b87ca2135ad18140195aa885a239eb36300815cd886ff9abee5baa2ddf6ac3` |
| `C2` | Record | `03ffffffffffffff30dd1534dd15ffff` |
| `C2` | Init | `15:DD30` |
| `C2` | Block | 295 bytes, SHA-256 `fa8c0ac51be70e188ebaf324802fd2ab9d4deec60674f6f9a3a411ec8549c509` |

Each record starts with type `03`. Bytes 1 to 7 stay `FF`. Bytes 8 to 10 hold
the init pointer and bytes 11 to 13 hold the main pointer. Bytes 14 and 15 stay
`FF`.

## Block layout

Each protected block starts with a `STAR` header. The body holds the label
`MDKINIT` and the label `MAIN`. The init field points at the `MAIN` label.
The main field points 4 bytes later, at a stub.

The stub pushes the data bank, pushes the program bank, pulls the data bank and
calls the module body. The module body returns with `RTS`. The stub then pulls
the data bank and returns with `RTL`.

The body of slot `C0` reads `$17AB` as a countdown. It exits while the
countdown is not `38`, `30`, `28` or `20`. It then compares the actor box
with the player box. If the boxes overlap, it calls `01:A9DE` and sets
`$14C8` to `08`.

## Room placements

| Slot | Donor rooms | Recipient rooms | Recipient record |
| --- | --- | --- | --- |
| `C0` | `16B` twice | `16B` twice | `0000ffffffffffff218001218001ffff` |
| `C1` | `16B` four times | `16B` four times | `0000ffffffffffff218001218001ffff` |
| `C2` | `170` once | `170` once | `0000ffffffffffff218001218001ffff` |

The level data, the sprite lists and the graphics records for rooms `16B` and
`170` are byte-identical between the donor and the recipient. The only
difference is the record type in each slot.

## Entry check

The fixture enters room `16B` and room `170` through a labelled pipe action.

| Image | Room | Actors at the first sample |
| --- | --- | --- |
| donor `7hero` | `16B` | three sprite-`00` slots and two sprite-`33` slots |
| recipient | `16B` | two sprite-`00` slots, two sprite-`33` slots and one custom `8C` |
| donor `7hero` | `170` | no actors |
| recipient | `170` | sprite `BC` and sprite `2F` |

Neither image materializes a `C0`, `C1` or `C2` actor in room `16B` or
room `170` under this fixture. The room placement alone does not spawn the
records. The type byte at `$1AB1C` reads `00` for every active actor in both
images.

The room dependency table shows the cause. Room `16B` also places slot `95`.
The recipient holds a type-0 placeholder for `95`, while `7hero` holds a
5,144-byte type-1 program. See [the gap inventory](native-sprite-gaps.md).

## Type admission

The recipient constructor at `31:8177` reads the record type at `$7FAB1C`.
When the type byte is not zero it jumps to a second path at `31:81D1`. That
path copies bytes 1 to 7 directly into RAM and copies bytes 10 to 13 into
`$7FAB28` and `$7FAB34`. It does not read the init and main pointers.

The donor constructor at `10:B059` reads the same type byte. When the type byte
is not zero it copies bytes 1 to 9 and bytes 10 to 13 as three words.

The two constructors therefore disagree on the layout that follows the type
byte. A record transplant must also carry the constructor contract.

## Constructor patch plan

The two constructors read different bytes of a type-3 record. The table below
gives the byte each store consumes. Each read uses `LDA table,Y`, with `Y` set
to the record offset.

| Store | Donor `10:B059` | Recipient `31:8177` |
| --- | --- | --- |
| `$00` | record byte 8 | record word at byte 8 |
| `$01` | record byte 9 | record word at byte 8 |
| `$02` | record byte 10 | record byte 10 |
| `$7FAB28` | record byte 15 | record byte 14 |
| `$7FAB34` | record byte 16 | record byte 15 |

The two paths read the same table base plus `Y`, so the one-byte shift comes
from the number of `INY` steps, not from the table base.

The donor path is `10:B0C0` to `10:B0E7`, which is 40 bytes. The recipient path
is `31:81D1` to `31:81F0`, which is 32 bytes. The donor path does not fit in
the recipient span.

The patch therefore has two parts.

1. Add the donor path to a native code pack, with the table base changed from
   `10:B15D` to `31:8272` and the `$7FAB` stores unchanged.
2. Replace the 4 bytes at `31:81D1` with `JML` to the pack address.

The second part is a ROM patch of 4 bytes. The first part is a module of 40
bytes. The construction ends with `PLP`, `PLB`, `PLY` and `RTL`, so a `JML`
entry keeps the stack contract of the original path.

Donor bytes from `10:B0C0`:

```
b95db18500c8b95db18501c8b95db18502c8c8c8c8
b95db19f28ab7fc8b95db19f34ab7f28ab7a6b
```

Recipient bytes at `31:81D1`:

```
c220b97a828500e220b97c828502b980829f28ab7fb981829f34ab7f28ab7a6b
```
## First install attempt

A first target exists: `demo11-native-type3` with ROM
`41ae1b0ed5546a6dde29825caee072e1bdba8e0dd6a6c912c9b1d07933ee8252`. It holds
four packs.

| Pack | Bank | Bytes | Role |
| --- | --- | ---: | --- |
| `type3-constructor` | `CE` | 40 | The donor path with the table base `31:8272` |
| `type3-c0` | `CB` | 205 | Block `13:86D7` |
| `type3-c1` | `CC` | 213 | Block `13:AE08` |
| `type3-c2` | `CD` | 295 | Block `15:DD21` |

The 4-byte patch at `31:81D1` now holds `5c 00 80 ce`, which is `JML CE:8000`.

## First install result

The target builds and the module runs: the capture reports `bank=CE
resolutions=122`. The game then stops: the run log holds 8 `BRK` entries and the
mode reads `0x36`.

The cause is the register state at the branch. The donor reaches its type path
with `Y` advanced by eight steps. The recipient reaches `31:81D1` with a
different `Y` and a different `X`. A copied body therefore reads and writes the
wrong record bytes and later executes a bad opcode.

The next attempt must set `Y` and `X` at the module entry. One option is `TYA`,
`AND #$F0`, `TAY` followed by `TXA`, `AND #$0F`, `TAX`. Another option copies the
whole constructor instead of the type path alone.
## Records-only install

A second target holds the three records and the three blocks with no
constructor patch: `demo11-native-type3b`, ROM
`d568f18f77692babfbac898b93f5e72d18e656408be918039285a36c02870b3c`.

| Check | Result |
| --- | --- |
| `BRK` count in room `16B` | 0 |
| Game mode at the first sample | `0x13` |
| Game mode at the second sample | `0x14` |

The game reaches normal play with the three records installed. No actor carries
a `C0`, `C1` or `C2` type byte, so the placement still does not create those
actors.

Room `16B` differs from the donor in one way: the target holds two actors with
custom id `95`, because this target keeps the type-0 placeholder for slot `95`.
The 35-record target carries the slot `95` program instead.

## Which install to keep

Keep the records-only target. It installs the three records, runs without a
crash and leaves the room as it was. The constructor patch stays an open
experiment: it crashes and it is not necessary to install the records.

## Normal load of level 094

The records-only install is not safe for every room. The product target
`demo11-native-product-r12` carries the three records with adapted bank
pointers. A normal entry to translevel `094` (level `170`) crashes. The
native log holds eight `BRK` entries and the game state reads mode `00`.

Room `170` places slot `C2` once. Room `16B` places `C0` and `C1`, and
translevel `08F` loads normally. The [product survey](demo11-product-survey.md)
records the captures and the base-ROM controls.

The earlier [level sprite batch](demo11-level-sprites.md) recorded the same
failure for the 7hero `C2` record. That batch kept `C2` out of the demo11
line.

Keep `C0` and `C1`. Do not include `C2` in a product candidate until the
constructor work succeeds.

The candidate `demo11-native-product-r13` removes the `C2` record and its
pack. Translevel `094` then loads room `170` in mode `14`, and the
full-range survey reports 228 playable entries and no crash. The correct
restoration of `C2` stays open.

## Later memory-contract review (2026-10-29)

The [r15 review](native-lowmirror-restoration.md) identifies a separate mapping
problem: CB/CC lack the source programs' low WRAM/I/O mirrors after PHK/PLB.
C0/C1 now use94/93 with the original code and constructor retained. The tested
native16B fixtures still do not execute those callback views, so this is static
memory-contract correction, not complete mechanism acceptance. Sprite95 is now
present in the product and has fresh selected actor checks.

The earlier094/C2 crash is established evidence; its sole cause was not isolated
between constructor and mapping assumptions. Future C2 work must check both
against actual source and recipient execution rather than treating the earlier
constructor theory as proof. C2 remains absent from r15 until a safe, source-
qualified integration is demonstrated.

## Reproduction

```
python3 tools/audit_sprite_type3.py
```

The report is `local/reports/native-sprite-type3.json`, SHA-256
`7e35f68ac13d5d65552b8b8843cb2521adb950569c05e837ce2cdb9ca3faa950`. The tests
are `tests/test_sprite_type3.py` and pass 8/8. The full suite passes 272/272
tests. The log is `local/reports/unit-tests-type3c.log`. The captures are
`red-c0c2-room16b-donor-v1`, `red-c0c2-room170-donor-v1`,
`type3-room16b-native-v1` and `type3-room170-native-v1`.

## Superseding actual C0 loading trace (2026-10-29)

The gradual loading fixture in [the low-memory review](native-lowmirror-restoration.md)
actually executes C0 in r15 and crashes. The recipient classifies C0 as a normal
actor because its shooter ID range starts atE0, while7hero starts atC0.
Normal init dispatch then jumps to the `MAIN` text label94:86E6, corrupting the
stack. The prior recommendations to keep records-only C0/C1 are superseded:
entry-only captures skipped loading, and r15 is rejected. R14 remains the
accepted baseline, with this latent integration issue still open. A native
loader/store/dispatch adapter is being checked in an isolated descendant.
Do not infer that a constructor continuation transplant fixes this failure.


The [isolated shooter adapter](native-type3-shooters-restoration.md) now passes
bounded actual C0/C1 loading and generation checks. C1 has20 exact normalized
selected-actor samples. C0 phase, remaining windows, E0 birth and C2 remain open;
this experiment is not a promoted cumulative product.
