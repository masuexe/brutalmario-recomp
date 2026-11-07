# Boss room probe results

## Purpose

These probes check whether each boss room starts and generates child actors.
Each probe forces its room and runs up to 1920 frames.

## Results

| Room | Boss slot | Boss appears | Child actors | HP row on BG3 |
| --- | --- | --- | --- | --- |
| `03B` | `74` | yes | `04`, `01` | not checked |
| `083` | `A0` | yes | none | yes, `68` at columns 11 to 22 |
| `086` | `1C` | yes | `1D` x 8 | not checked |
| `087` | `20` `1F` `1E` | yes | `01`, `00` | not checked |
| `15D` | `13` `2D` | `13` only | `B9` | not checked |

## Room `083`

The boss program is the full `cheap-demo` program.

| Item | Value |
| --- | --- |
| Recipe | `config/native-content/spritea0-module.json` |
| Pack file | `spritea0-code.bin`, 14550 bytes |
| Pack SHA-256 | `4079a5f3a49b213e` |
| Native address | `A79AD8` |
| Bank `A7` resolutions | 9,709,034 |
| Bank `A7` executed instructions | 1,578,909 |

The pack mounts and runs. The ROM block at `27:96DC` is unrelated data.

### The boss does start its attack path

The init at `9AE7` writes `$15AC` and the scroll registers.

The state handler at `A74F` follows this sequence:

```
A74F  LDA $9D
A751  BNE $A773          ; return while the game is paused
A753  LDA $15AC,X
A756  CMP #$FE
A758  BEQ $A774          ; return while the timer is FE
A75A  LDA $77
A75C  AND #$04           ; the down button
A75E  BEQ $A773          ; return when down is not held
A760  LDA #$01
A762  STA $7FF111        ; set the start marker
A766  STZ $1412
A769  LDA #$01
A76B  STA $C2,X          ; set the state
```

A probe that holds down reaches this path. The capture shows the result.

| Frame | `$7FF111` | `$1412` | `$77` |
| --- | --- | --- | --- |
| `f060` | `00` | `01` | `00` |
| `f420` | `01` | `00` | `04` |
| `f1020` | `01` | `00` | `04` |
| `f1920` | `01` | `00` | `04` |

The marker stays at `01`, so the handler took the branch and the boss left
state `0`. The program works.

`$1504` is not the state table for this sprite. Read `$7FF111` and `$1412`
instead. An earlier note that the state stayed zero used the wrong variable.

The boss spawns no child actors because this boss attacks directly.

### The HP row

The capture shows the `MARX` label at columns 4 to 8 and tile `68` at columns
11 to 22. The row is present. The bar uses a red palette in this room.

## Rooms `009` and `07E`

Slot `28` also places in rooms `009` and `07E`. The probes show that these
rooms do not set the bar flag.

| Room | Boss actor | `$7FFFDF` | Bar buffer |
| --- | --- | --- | --- |
| `009` | yes (slot `28`) | `00` | all zero |
| `07E` | none | `00` | all zero |
| `08A` | yes (slot `28`) | `01` | `1E 15 1D 12 16 0A` |

The slot `28` room dispatch writes the bar data only for room `08A`. The r26
gate therefore covers exactly the rooms that request a bar.

## Room `15D`

The room table lists slots `13` and `2D`. Only slot `13` appears. Slot `2D`
does not. This needs a separate check.

## Regression check

The r26 image must not change the rooms that the user already accepted.

| Room | Before | r26 | Result |
| --- | --- | --- | --- |
| `167` | 4 actors, slot `34`, state `0C` | same | no change |
| `16A` | 4 actors, slot `34` at `0E` | same up to frame `420` | no change |

Room `16A` ends at frame `1020` in the probe. The probe does not follow the
moving light circle, so Mario falls. The wiki describes this behavior.

## Limits

- The probe presses few buttons, so a boss that waits for input stays idle.
- The probe does not damage the boss, so it cannot reach later phases.
- A child actor count shows that a program runs. It does not prove correct
  behavior.