# Room 173 custom sprite: the wrong program

## Result

Room `173` places sprite slot `07`. Mario falls with no support and the level
ends. The product image runs an older program for slot `07`.

## Evidence

The room data is the same in both images.

| Item | product r26 | `boss` |
| --- | --- | --- |
| Room `173` level pointer | `68D398` | `68D398` |
| Level block SHA-256 | `9585952b9e745ea2` | `9585952b9e745ea2` |
| Level header | `15 0A 00 40 30 40 70 F2` | same |

The programs differ.

| Image | Slot `07` block | Size |
| --- | --- | --- |
| product r26 | `3D:F556` | 1647 bytes |
| `boss` | `20:94D1` | 5836 bytes |

The product program is the `cheap-demo` one. `cheap-demo` places slot `07` in
room `080` only. Every newer image places it in rooms `080` and `173`.

| Image | Slot `07` rooms |
| --- | --- |
| `cheap-demo` | `080` |
| `boss`, `7hero`, `demo-only-1`, `demo-1-1` | `080`, `173` |

## Product r29: the port is done

Product r29 installs the `boss` slot `07` program.

| Item | Value |
| --- | --- |
| Source block | `20:94D1`, 5836 bytes |
| Block SHA-256 | `2dc6a898ea4fe3ae291b55a0d82294ebed02f0b29c6172c0e6f91f0ddc99ebcb` |
| Native address | `84:94D1` |
| Record | `013601063f031964e094841295840000` |
| Recipe | `config/native-content/sprite07-module.json` |
| Pack | `sprite07-code.bin` |

The block is self-contained. A full decode found five entry points and no
call outside the block. It has no reference to another data bank.

### Room `173`

| Frame | r28 mode | r29 mode |
| --- | --- | --- |
| `f0300` | `14` | `14` |
| `f0600` | **`0E`** | **`14`** |
| `f1200` | - | `14` |
| `f1800` | - | `14` |

Product r28 loses the level at frame `600`. Product r29 keeps the level.
The room also plays song `1A`, which is present in the table.

### Room `080` regression

Room `080` keeps mode `14` on every frame and keeps song `19`. The slot `07`
actors continue to run.

## The difference in the code

| Pattern | product r26 | `boss` |
| --- | --- | --- |
| `LDA $010B` | absent | offset `0x14` |
| `CMP #$73` | absent | offset `0x17` |

The `boss` init at `20:94E0` is:

```
94E0  LDA #$01
94E2  STA $157C,X
94E5  LDA $010B        ; the room byte
94E8  CMP #$73         ; room 173
94EA  BEQ $94FF        ; the room 173 path
94EC  LDA $7EC10E
94F0  CMP #$77
94F2  BNE $94FE
94F4  LDA #$FF / STA $19B8
94F9  LDA #$04 / STA $19D8
94FE  RTL
94FF  LDA #$02 / STA $C2,X   ; state = 2
9503  LDA #$20 / STA $1570,X
9507  LDA #$E0 / STA $15AC,X
950B  RTL
```

Only room `173` sets state `2` at init. The other rooms leave the state at `0`.
The main routine at `20:9512` then dispatches on the state.

The product program is a different program with a different layout. It has no
room test and no state `2` handler. A one-byte patch cannot add this behavior.

## The capture

`recomp/inputs/native-room173-probe.script` forces room `173`.

| Frame | Mode | Actors |
| --- | --- | --- |
| `entry` | `14` | slot `07`, state `00` |
| `f180` | `14` | slot `07`, state `00` |
| `f420` | `0E` | none |

The frame at `f180` shows Mario over open space. The frame at `f420` shows the
overworld map, so the level ended.

## Port plan

The `boss` program needs six code blocks in bank `20`.

| Block | Size |
| --- | --- |
| `20:8001` | 5328 bytes |
| `20:AB9D` | 8801 bytes |
| `20:CDFE` | 5645 bytes |
| `20:E40B` | 5144 bytes |
| `15:8277` | 1832 bytes |
| `29:D9B7` | 3005 bytes |

The block at `20:CDFE` is already ported as sprite 34. The other five are not.

## Warning

Slot `07` also runs in room `080`. Replace the program only after room `080`
is captured as a regression baseline.