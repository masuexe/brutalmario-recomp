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

## Position sweep

A second probe repeats the 300-cycle setup. It then attacks from four forced
points: `(120,368)`, `(120,384)`, `(120,400)` and `(112,384)`. Each point
uses Up+A, Up+B, B and Down+B. The 16 retained samples stay at tier `6`. The
two main damage fields stay at 64 and 6. Several samples show extra custom `2A`
parts with value 0 or 107. The fight shows no defeat state and no room change.

## Natural-floor test

A third probe reaches tier `6`, then releases the player at X `120` from Y
`32`. The player lands at Y `160`. The base part stays at Y `383` with
damage field 64. Eight cycles each of Up+B, Up+A, B and Down+B keep both fields
at 64 and 6. The base part is 14 tiles below the arena floor. A simple attack
cannot reach it.

## WP cheat check

A fourth probe reaches tier `6` with the aligned opening prefix and then holds
the WP maximum and current value at `99`. It runs 80 cycles of Down+B, B,
Down+A and Up+B. The base part field stays at `64` and the moving part field
stays at `6`. The transient custom `2A` parts show values `255`, `154` and
`120`, then clear. A forced WP value does not damage the base part. A fifth probe also moves the
player to the exact base position `(119,383)` with WP `99`. It runs 80 cycles of
Down+B, B, Down+A and Up+B. The base field stays at `64` and the moving field
stays at `6`.

A tier `6` floor scan drops the player at X `64`, `96`, `112`, `120`, `128`,
`144`, `160` and `192` from Y `96`. The player settles at Y `154` to `160`, or
stays at `96` on the two high platforms. No opening reaches the base part at
Y `383`.

## Terminology

The lower chamber means the area below the arena floor that holds the custom
`2A` base part. It is not the next course after a Seven defeat. Room `0FF`
screen 0 has a screen exit to room `174`. The ending candidate retargets that
exit to the reserved room `17B`. Neither route proves an earned defeat. A simple diagram is at
`local/captures/seven-floor-diagram-v2.png`.

## Next work

Qualify a position-correct attack. A reachable forced position, the tested
input types and a natural floor control do not damage the base part. The base
part sits below the arena floor. Find the lower-chamber path or the intended
trigger. Ask the user for a short manual fight sample if the next automatic
attempt fails. Do not infer an earned victory from tier `6` alone.

The local captures are `seven-fight-pursue-v1-native` and
`seven-fight-varied-v1-native`. Their run logs report a clean exit.
