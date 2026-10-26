# Native Seven Koopalings fight music

## Result

The target `demo11-native-seven-child-fight-music` descends from
`demo11-native-seven-child-font-cycle`. It changes one music byte in the room
`0FF` level header. The header byte controls the modern music request. The
modern engine uses the header byte minus one as the request, so the changed
header requests slot `AC`. Slot `AC` holds the documented Last Battle track.

The fight now requests slot `AC`. Before this checkpoint it requested slot
`32`, which is the room's default background track. The user listening check
identified slot `AC` as the donor fight composition.

This checkpoint qualifies the music request only. It is not a complete fight,
a mix comparison, an audible-equality proof, a saved clear, or an ending.

The later [ending-boundary checkpoint](native-seven-ending.md) qualifies the
modern stop command, original test-room ending and pit death through an
explicit defeat fixture. It also restores the hidden 1-up checkpoints in that
room. A complete earned victory remains open.

## Why the header is the patch site

The donor fight theme is not selected by the ported Seven program. The donor
sets `$1DFB` to `$23` from donor object code at file `0xAAEB7` and
`0x10350F` (banks `15` and `20`). Those banks belong to the recipient in
this target, and the ported program (bank `22`) does not contain the writes.

The shared room `0FF` level header is `40 60 33` in both images. Both
engines therefore request slot `32` at room load. The donor then overrides the
music from the object code above. The header is the smallest reviewed site that
changes only this room's fight music.

## Change

The only new ROM edit is one byte:

| Item | Value |
| --- | --- |
| Level header | `$6A:E176`, file `0x356176` |
| Music byte | file `0x356178` |
| Before | `33` (request slot `32`) |
| After | `AD` (request slot `AC`) |
| Encoding | music request = header byte - 1 |
| Room | `0FF` |

No music driver, sample, or song payload changes. Slot `AC` already exists in
Demo 1-1. Its upload pointer is `27:BC43`, its count is 2,318 bytes, and its
target is ARAM `5400`.

## Identities

| Item | Value |
| --- | --- |
| Parent target | `demo11-native-seven-child-font-cycle` |
| Parent ROM SHA-256 | `a85dbe0609facffc75bf55b28080b7fba9ad7d376254a5914c835d7f89abc015` |
| Target ROM SHA-256 | `14622c254c562dcfdd5d3c8b422acec9534588bf17dbcf0e0294afed018dec63` |
| Native binary SHA-256 | `6e936e5cb63a77937882f1a27a46449a0ccc5ac3c6e9d7e9adc4d9744a7cf39a` |
| Preparation receipt | `local/restoration/demo11-native-seven-child-fight-music/input-manifest.json`, SHA-256 `8f8483f8d21e571de0e20e30f1c9b90d2d1ef5d903cc93085ffbfa32667f7b69` |
| Qualification report | `local/reports/native-seven-child-fight-music-final.json`, SHA-256 `f117d6ad6d310091050fecd4d98157fc65dd5d2f158f33268ca28b976dbfad59` |

The parent external packs stay unchanged:

| Pack | Size | SHA-256 |
| --- | ---: | --- |
| `seven-code.bin` | 28,880 | `e80e1102b96607c1ec73a74d75c2db64810b8a5db822239842772bdd88ee9384` |
| `seven-graphics.bin` | 27,261 | `9ed6aa8d4398b7b06195a7b250daa098af0d9bb09aa35b218e12251b3c62280f` |
| `sprite9e.bin` | 1,291 | `a6654d22c2dd9f146fc117ba7dca01f9389995fcb8b75f52ba6f2c4a6b1a717d` |
| `star1-ffd.bin` | 3,001 | `3a51dd45f2df22d1f2490ca117070a68bfdab33cb03f734ad9e97c59e581a169` |
| `seven-child6a.bin` | 3,385 | `8301000a2fed1e9c534958f06ef1d82eeb7e62f92cce9ef674b1f369c4fd0dbb` |

## Verification

The preparation verifies the parent ROM and packs. It also checks the room
`0FF` header bytes, the SNES-to-file mapping, and the request encoding. A
changed header byte or a changed request value stops preparation.

The qualification checks these music values:

| Sample | Native request |
| --- | --- |
| `fight180`, `fight600`, `fight1200`, `fight2400` | `AC` |
| `after_b`, `after_a`, `after_x`, `after_y` | `AC` |
| `child_spawn`, `child32`, `child96` | `AC` |
| `child_fight_reentry` | `AC` |
| `child_death` | `FF` (unchanged stop) |
| `child_course_reentry` | `38` (ordinary course, unchanged) |

The donor capture keeps `$0DDA = 0x23` across the fight samples. The number
is version-local. The report records it and does not compare it as equal to the
native request.

The report also keeps the earlier checks. It covers six event-aligned child
samples and 830 unchanged comparisons on three routes and four old-`6A` rooms.
It also covers native death, map return, the labelled pipe re-entry, and four
rejected startup packs. All 164 Python unit tests pass. The log is
`local/reports/unit-tests-fight-music.log`.

## Limitations

The listening check compared the composition only. It is not a mix comparison
or an audible-equality proof. The modern arrangement may differ from the donor.

The patch applies to every entry into room `0FF`. Room `0FF` is the Seven
fight room in this target. Do not treat this one-byte patch as a general music
retarget.

Other fight cues are not adapted. The child source still writes music value
`1E` at `$1EC7CD`. That write remains unadapted. Later fight phases, the
ending, and saved completion remain open.

## Reproduction

```
python3 tools/native_seven_child.py
python3 tools/m1.py --target demo11-native-seven-child-fight-music scaffold
python3 tools/m1.py --target demo11-native-seven-child-fight-music generate
python3 tools/m1.py --target demo11-native-seven-child-fight-music build
python3 -m unittest discover -s tests -p test_seven_child.py -v
python3 tools/qualify_seven_child.py --output local/reports/YOUR_FRESH_REPORT.json
```

Skip `scaffold` if the isolated experiment exists. The last command rechecks
the recorded captures. For fresh captures, use these prefixes:

- `PREFIX-event-v1-native` with `recomp/inputs/seven-child-native-event.script`.
- `PREFIX-regression-v1-{star1,boss,lifts}` with the tracked regression scripts.
- `PREFIX-existing-v1-new-{0d8,0e2,0e3,0e4}` with the tracked old-`6A` scripts.

This checkpoint reuses the donor capture `seven-child-event-v1-donor`. Its
identity is the pinned official Boss Demo and the tracked donor script.

The listening clips remain under `local/reports/audio-probe/`. The donor clip
is `donor-fight-bgm.wav`. The matching candidate is `modern-slot-AC.wav`.
