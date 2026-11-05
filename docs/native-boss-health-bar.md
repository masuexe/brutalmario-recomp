# Boss health bar: the room 8B, 8A and 91 finding

## Result

Boss sprites work in these rooms. The health bar and the boss label do not
appear. The cause is a HUD refresh counter that stays at zero.

## Evidence from the captures

| Capture | Room | Mode | `$13CC` | `$0DBF` | BG3 top rows |
| --- | --- | --- | --- | --- | --- |
| product r25 | `08B` | `14` | `00` | `00` | empty |
| cheap-demo reference | `08B` | `14` | `00` | `00` | empty |

The cheap-demo reference capture also shows an empty top row. The user
provided screenshots that show the label and the bar, so the reference
capture does not reach the frame where the bar is drawn.

## The chain

1. The HUD routine at `00:8E1A` runs. Coverage confirms it.
2. The routine reads `$13CC` at `00:8F1D` and branches to `00:8E5D` when the
   value is zero. That branch skips `00:8F25`.
3. `$13CC` is fed by `32:D0E5`, which adds `$D0D3,X` to `$13CC`.
4. `32:D0E5` does not run in either capture.
5. The branch at step 2 therefore always skips the bar refresh.

## What differs between the images

| Address | demo-1-1 and demo-only-1 | boss, cheap-demo, 7hero, mazo |
| --- | --- | --- |
| `00:8F25` | `JSL $10A71D` | `INC $0DBF` |

Both forms end in `INC $0DBF`: the `demo-1-1` form reaches it at `10:A753`.
So the bar logic is the same. The difference is the wrapper only.

## Open question

The product capture and the cheap-demo capture both leave `$13CC` at zero.
The user reports that the bar shows in `cheap-demo` play. Therefore the
fixture does not reach the state that starts the refresh timer. The next
step is to find that state, not to change the HUD code.