# Boss room probe results

## Purpose

These probes check whether each boss room starts and generates child actors.
Each probe forces its room and runs 1920 frames.

## Results

| Room | Boss slot | Boss appears | Child actors | Note |
| --- | --- | --- | --- | --- |
| `03B` | `74` | yes | `04`, `01` | The boss runs. |
| `083` | `A0` | yes | none | The boss appears and stays. No child actors. |
| `086` | `1C` | yes | `1D` x 8 | The boss generates eight children. |
| `087` | `20` `1F` `1E` | yes | `01`, `00` | All three slots appear. |
| `15D` | `13` `2D` | yes (`13` only) | `B9` | Slot `2D` does not appear. |

## Findings

Room `083` places one boss actor and no child actors. The `cheap-demo` program
for slot `A0` is 14550 bytes. The product program is 2961 bytes and comes from
the `demo-1-1` baseline. The shorter program cannot run the longer fight.

Room `15D` places slot `13` but not slot `2D`. The room table lists both.

## Limits

- The probe does not press buttons, so it cannot confirm that a boss fires.
- The probe does not damage the boss, so it cannot reach later phases.
- Child actor counts show that a program runs, not that it behaves correctly.