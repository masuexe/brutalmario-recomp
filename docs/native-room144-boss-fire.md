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

## Deferred issues

The frame shows a magenta rectangle near the top center. The product image
changes only 32 bytes from r25, and all of them belong to the HP row. The
rectangle is therefore older than r26. No earlier capture reached room `144`,
so the rectangle needs a separate check.