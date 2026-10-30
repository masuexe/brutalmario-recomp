# Seven assisted fight attack analysis

Date: 2026-10-30. Experimental target: `demo11-native-modern-sprites-v2`.
Accepted product remains r14. This checkpoint records a bounded fight probe.
It does not claim an earned victory, a saved clear or a complete fight.

## Scope

Two local assisted routes exercise the official Seven fight in room `0FF`.
Both use the tracked opening fixture, temporary damage immunity
(`1497=FF`) and ordinary button inputs. They do not write boss damage,
phase, completion or save state.

| Route | Inputs | Retained samples |
| --- | --- | --- |
| Pursue | 300 mixed Up+A/Up+B cycles, then 240 cycles at a forced player point | 24 |
| Varied | 300 mixed cycles, then 10 input types in two rounds | 20 |

The forced player point is `(120,352)`. It is a fixture, not ordinary movement.

## Result

Both routes reach joined-part tier `6` and stay in live room `0FF`. At tier
`6` the fight holds two custom `2A` parts:

| Part | Slot | Position | Damage field `1528` |
| --- | --- | --- | ---: |
| Base part | 8 | `(119,383)` | 64 |
| Moving part | 9 | varies around Y `211..304` | 6 |

Every pursue sample keeps both fields at 64 and 6. Every varied sample does
the same. The attack index `7FFEBF` takes values `0`, `1` and `4` across the
input types. The learned flags at `7FFEC0` stay at indices `88` and `96`.

The base part sits at Y `383`. The player fixture puts the player top at Y
`352`, and the feet reach Y `368`. The Up attacks therefore pass above the
base part. The fight shows no further damage, no defeat state and no save or
completion write.

## Next work

Qualify a position-correct attack. Stand on or beside the base part, or find
the intended vulnerable window. A manual play sample can identify the correct
context if automation cannot reach it. Do not infer an earned victory from
tier `6` alone.

The local captures are `seven-fight-pursue-v1-native` and
`seven-fight-varied-v1-native`. Their run logs report a clean exit.
