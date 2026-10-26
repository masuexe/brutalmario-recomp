# Native mazo attack window

## Result

The two mazo rooms run short scripted windows. Both rooms exit on their own
after the pipe entry. The capture scripts give no further input.

The checkpoint records these items:

- The room 151 persistent 9C parts match.
- The first room 151 wave follows the same trajectory.
- The native first wave starts 23 frames after the donor wave.
- Later room 151 attack cycles differ.
- The room 190 persistent 9B parts match at the sampled positions.
- The room 190 transient intro actors differ.

## Fixtures

The room 151 pair uses `recomp/inputs/mazo-9c-align-fine-donor.script` and
`recomp/inputs/mazo-9c-align-fine-native.script`. Both scripts use the labelled
pipe entry. After the room load they force Mario to `(512,320)` with zero
speed. The stationary Mario is an explicit fixture. The scripts sample every 5
frames from `fight060` to `fight200`, then the later cycles.

The room 190 pair uses `recomp/inputs/mazo-9b-donor-fixture.script` and
`recomp/inputs/mazo-9b-native-fixture.script`. These scripts use the labelled
pipe entry and no forced state.

The fixtures write no invulnerability, HP, phase or completion value.

## Room 151

Both hosts enter mode `14` in room `0x151`. The persistent 9C parts are slots
`7` and `9` at `(168,272)` and `(144,320)`.

The first wave actor occupies slot `6`. The donor first shows it at
`fight125` with X `276`. The native host first shows it at `fight145` with
X `285`. Both hosts then decrease X by 3 pixels per frame.

The value `X + 3 * frame` is constant for each host during the first wave. The
donor constant is `651`. The native constant is `720`. The difference is
`69`, which equals 23 frames at this speed. The first wave therefore follows
the same trajectory with a 23-frame phase offset.

Later cycles differ. The donor keeps slot `6` at X `144` at samples
`fight420` to `fight600`. The native host has no slot `6` at `fight420` or
`fight450`. It then shows slot `6` at X `208`, `-32` and `112` at
samples `fight480`, `fight540` and `fight600`.

## Room 190

The persistent 9B slots are `6`, `7` and `9` at `(96,208)`, `(120,120)`
and `(128,8)`. Both hosts hold those values at `fight150` and `fight600`.

Both hosts return to mode `0E` at `fight1200`. Transient intro actors in slots
`0` to `5` differ in 58 sample and slot observations.

## Evidence

The report is `local/reports/native-mazo-attack-final.json`. Its SHA-256 is
`3b1e6c5d9d0bd4413e50449938b12015292b397ee0948e753cd64a805a5358e2`. An
independent rerun reproduces the report byte for byte.

The captures are `local/captures/mazo-9c-align-fine-v2-{donor,native}`,
`local/captures/mazo-9b-entry-v2-donor` and
`local/captures/mazo-9b-entry-v3-native`.

The full suite passes 184/184 tests. The log is
`local/reports/unit-tests-mazo-phase.log`.

## Limits

This check records observations. It does not prove player damage, a fight
clear, an ending or a saved completion. The 23-frame phase offset and the later
cycle content stay open. A shared-helper review must explain them. The `B0`
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
