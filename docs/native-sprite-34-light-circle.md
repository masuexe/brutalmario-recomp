# Sprite 34: the light circle and the room 16A question

## Result

Sprite 34 is present and correct in product r22. The light circle does not
appear in room `16A` because the program does not handle that room.

## Evidence

Product r22 executes sprite 34 in room `167` without a defect:

| Room | `$1504` state | Movement over three frames |
| --- | --- | --- |
| `167` | `0C` | `(157,259)` then `(106,274)` then `(76,334)` |
| `16A` | `00` | none; position stays at `(16,320)` |

`$1504` is the sprite state that the init program writes. A value of `00`
means that the init program returned without a write. A value of `0C` means
that the init program ran its room branch.

## Cause

The init program at `20EBDB` reads the room number and compares it with a
fixed list. The list holds these rooms:

`EA` `08` `EB` `EC` `EE` `ED` `52` `53` `69` `67`

Room `16A` is not in the list. Control therefore reaches `20EC06 RTL` and
returns. The sprite then stays dormant.

## Why room 16A holds sprite 34 at all

The recipient baseline `demo-1-1` places slot `34` in thirteen rooms, and
`16A` is one of them. The baseline record is a placeholder. Product r20
replaces that placeholder with the `cheap-demo` program.

The `cheap-demo` program handles eleven rooms. The recipient baseline names
thirteen. The two lists do not agree, so three rooms place a sprite that the
program ignores:

| Image | Rooms that place slot `34` |
| --- | --- |
| `cheap-demo` | `0EA` `0EB` `0EC` `0ED` `0EE` `108` `134` `152` `153` `167` `169` |
| product r22 | `0EA` `0EB` `0EC` `0ED` `0EE` `108` `152` `153` `15E` `167` `169` `16A` `16D` `192` |

## Which rooms show the light

Only the five rooms `0EA` to `0EE` take the circle branch. Rooms `167` and
`169` take a different branch that sets state `0C`.

## Deferred issue

Room `16A` places a sprite that the program does not handle. A correct
restoration needs a program that handles room `16A`, or a level edit that
removes the placement. Neither is part of this checkpoint.

## Rejected change

An attempt to move the program to a new bank `CB` and register it as an
external module made the room `167` frame differ from the accepted frame.
The attempt is removed. Product r22 is unchanged.