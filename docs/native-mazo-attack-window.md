# Native mazo attack window

## Result

The two mazo rooms run short scripted windows. Both rooms exit on their own
after the pipe entry. The capture scripts give no further input.

The checkpoint records these items:

- The room 151 persistent 9C parts match.
- The first room 151 wave moves with the same slope in both hosts.
- The native wave sits 69 pixels to the right of the donor wave.
- Later room 151 attack cycles differ.
- The room 190 persistent 9B parts match at the sampled positions.
- The room 190 transient intro actors differ.

## Fixtures

The room 151 pair uses `recomp/inputs/mazo-9c-align-donor.script` and
`recomp/inputs/mazo-9c-align-native.script`. Both scripts use the labelled pipe
entry. After the room load they force Mario to `(512,320)` with zero speed.
The stationary Mario is an explicit fixture.

The room 190 pair uses `recomp/inputs/mazo-9b-donor-fixture.script` and
`recomp/inputs/mazo-9b-native-fixture.script`. These scripts use the labelled
pipe entry and no forced state.

The fixtures write no invulnerability, HP, phase or completion value.

## Room 151

Both hosts enter mode `14` in room `0x151`. The persistent 9C parts are slots
`7` and `9` at `(168,272)` and `(144,320)`.

The first wave actor occupies slot `6`. Its X position is `216`, `126`,
`36` and `-54` in the donor at samples `fight090` to `fight180`. The native
values are `285`, `195`, `105` and `15`.

Both hosts decrease the X position by 90 pixels per 30 frames. The native value
is exactly 69 pixels greater at each sample. The first wave ends in both hosts.

Later cycles differ. The donor keeps slot `6` at `(144,320)` at samples
`fight360`, `fight420` and `fight480`. The native host has slots `[7,9]`
at `fight360`, slots `[6,7,9]` at `fight420` and slots `[4,5,6,7,9]` at
`fight480`.

## Room 190

The persistent 9B slots are `6`, `7` and `9` at `(96,208)`, `(120,120)`
and `(128,8)`. Both hosts hold those values at `fight150` and `fight600`.

Both hosts return to mode `0E` at `fight1200`. Transient intro actors in slots
`0` to `5` differ in 58 sample and slot observations.

## Evidence

The report is `local/reports/native-mazo-attack-final.json`. Its SHA-256 is
`c4f126774d1fc7e4b8d1783621102631fbb7e5f8619962029f30393516b84efd`. An
independent rerun reproduces the report byte for byte.

The captures are `local/captures/mazo-9c-align-v2-{donor,native}`,
`local/captures/mazo-9b-entry-v2-donor` and
`local/captures/mazo-9b-entry-v3-native`.

The full suite passes 184/184 tests. The log is
`local/reports/unit-tests-mazo-attack.log`.

## Limits

This check records observations. It does not prove player damage, a fight
clear, an ending or a saved completion. The 69-pixel wave offset and the later
cycle timing stay open. A shared-helper review must explain them. The `B0`
corridor recovery needs the donor level data and a separate course batch.

## Reproduction

```
python3 tools/qualify_mazo_attack.py
python3 -m unittest discover -s tests -p test_mazo_module.py -v
```

For fresh evidence, run the two tracked script pairs with
`tools/probe_reference.py` on the mazo donor ROM and with
`tools/m1.py --target demo11-native-mazo-9c native` or
`--target demo11-native-mazo-9b native`. Use fresh capture names. Then update
the report paths.
