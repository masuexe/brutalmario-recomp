# Native record restores for rooms 0x8F and 0x13C

Date: 2026-10-26. The user reports that the room `0x8F` boss drops coins
without end. They suggest that demo 1-1 may not contain this boss and that
demoOnly1 may hold the correct one.

## Finding

Room `0x8F` places custom sprite `0x42`. The cheap-demo
record for `0x42` is a coin boss. The record tables of demo 1-1 and
demoOnly1 hold the default record for `0x42`, so neither demo has this
custom boss. A native demoOnly1 capture of room `0x8F` shows the default
inert sprite. A native demo 1-1 capture of the room shows no boss at all.
The cheap-demo port was wrong for this line.

A full-range survey of the chain found one more regression. In room 
`0x13C` the ported sprite `0x3D` kills Mario, and the level
ends in mode `0x0C`. Demo 1-1 keeps the default record for `0x3D`,
so that record is also a wrong port.

## Change

The recipe `demo11-sprites-native-records` restores the default record
for sprites `0x42` and `0x3D` with two 16-byte patches. The
installed code blocks stay in the ROM but are not referenced.

- Base: `demo11-sprites-blocked-four`
- ROM: `63389cabd0bd901acd7cea58dc9a21c4a10095984929e01f746a1ad4b3e1c606`
- Native binary: `f62c23f717a525d3c0d317b5caa825bf0c339ab28dabbee7de63ed7a2c7399e3`

## Evidence

- Room `0x8F` frame is byte-identical to the pristine demo 1-1 capture,
  including the HUD. The coin children no longer spawn.
- Room `0x13C` stays in mode `0x14` with four lives, and sprite
  `0x3D` stays inactive.
- `tools/qualify_demo11_sprites_native_records.py` passes.
- Whole-line audit: 1,023,076 changed bytes, zero unexpected.
- Suite **76/76**; space budget passes.

## Full-range survey

The new survey `local/reports/demo11-course-survey-b4.json` covers all 255
translevels. Results: 231 playable, 14 mode-0E, 5 mode-0C, 2 mode-0D, and
one each of mode-17, mode-13 and mode-0B. The comparison with the earlier
survey shows two changes: translevel `060` (room `0x13C`) changed
from playable to mode-0C before this fix, and translevel `069` (room
`0x145`) changed from mode-0C to playable.

## Limits

- Other cheap-demo ports can hold the same version-local mismatch. The user
  must playtest the remaining sprite rooms.
- The installed block space for the two restored records is not reclaimed.
