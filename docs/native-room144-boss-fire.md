# Room 144 boss: fire check

## Result

The boss in room `144` fires. The automated run shows four projectiles.

## Evidence

The boss uses sprite slot `90`. The program is byte-identical to `cheap-demo`.

| Item | Value |
| --- | --- |
| Slot | `90` |
| Program block | `3F:CA7C`, 4133 bytes |
| Program SHA-256 | `e70e25686c6d624f` |
| Rooms | `130`, `144` |

All ten external calls resolve to the same bytes as in `cheap-demo`, except
`01:87A7`. That address is the sprite constructor hook, which differs after
every sprite port.

## The run

`recomp/inputs/native-room144-long.script` forces room `144` and runs 12720
frames. The projectile count grows and stays:

| Frame | Boss actors | Projectile actors (`0x49`) |
| --- | --- | --- |
| `entry` | 1 | 0 |
| `f060` | 1 | 1 |
| `f180` | 1 | 4 |
| `f12720` | 1 | 4 |

The game mode stays at `0x14` for the whole run. The boss does not stop.

## The magenta rectangle

The frame shows a magenta rectangle near the top center. It is not a port
defect. The level data and the background setup are the same in both images.

| Item | product r26 | cheap-demo |
| --- | --- | --- |
| Level pointer | `FCBDDC` | `FCBDDC` |
| Level header | `00 00 60 40 30 58 70 0F` | `00 00 60 40 30 58 70 0F` |
| `BG2SC` at run time | `0x33` | same source bytes |

`BG2SC = 0x33` gives a character base and a map base of `0x6000`. The two
regions overlap. The background then reads map entries as character data.
The product image changes only 32 bytes from r25, and all of them belong to
the HP row. The rectangle is therefore original behavior.