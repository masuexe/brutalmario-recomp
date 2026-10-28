# All-levels cheat for the native product target

## Result

The product target has a completed-progress cheat. The cheat opens every saved
level slot, every overworld event and every switch. The map then reloads, and the
player takes control with all warp stars open.

Run this command.

```sh
python3 tools/play_native_target.py --complete-all
```

## How the cheat works

The launcher starts the game in a session directory and applies a script. The
script waits for the overworld map, writes the progress fields, and then requests
a map reload through loader mode `$0B`. The script then exits, so the player
controls the game.

The session directory is `local/play/<target>`. If an earlier save exists, the
launcher moves it to `save.srm.before-cheat` and starts a fresh save.

## Written fields

These values come from the earlier demoOnly1 practice cheat and from the same
engine. The capture in the verification section confirms them on the product target.

| WRAM range | Bytes | Purpose |
| --- | --- | --- |
| `$1EA2` to `$1F01` | 96 bytes of `$9F` | Mark each saved level slot clear, keep the direction bits, clear the deny and midway bits |
| `$1F02` to `$1F10` | 15 bytes of `$FF` | Activate every overworld event |
| `$1F27` to `$1F2A` | Four bytes of `$01` | Activate the four switch palaces |
| `$1F2E` | `$60` | Set the synthetic completion counter |
| `$1F2F` to `$1F3A` | 12 bytes of `$FF` | Mark every saved coin bit |
| `$7F:182C` to `$1843` | 24 zero bytes | Clear the two custom midway masks |

The script uses WRAM offset `$1182C` for the last range, because both script
readers address that page from WRAM.

## Cheat build identity

The cheat is a script on the product build. It is not a separate image. The
launcher starts the same ROM and the same binary as a normal start. It writes the
progress fields after the map appears.

| Item | Value |
| --- | --- |
| ROM | `b8dca891b068763cdf91278a5d64bc75934754f11c7212cb3ad9f2cfed6279b5` |
| Packs | 43 |
| Sprite records | 36 type-1 records and 3 type-3 records |

Every content fix in the product build therefore also applies to the cheat
session.
One example is the slot `80` record for room `0A6`. See
[the gap inventory](native-sprite-gaps.md).

The script ends after the map reload and does not quit, because the player takes
control at that point. A headless capture of the script therefore never stops on
its own.
## Verification

The script is `recomp/inputs/cheat-complete-all.script`. The capture is
`local/captures/cheat-verify2`.

| Test | Result |
| --- | --- |
| `$1EA2` after the reload | `$9F` |
| `$1F02` after the reload | `$FF` |
| `$1F27` after the reload | `$01` |
| `$1F2E` after the reload | `$60` |
| Game mode after the reload | `$0E`, the overworld |
| `BRK` entries in the run log | 0 |

The plain capture `local/captures/cheat-baseline` runs the same inputs without
the writes. The two map frames differ by 23964 pixels, so the map redraws from the new
flags. The images are `local/captures/cheat-baseline/plain_map.png` and
`local/captures/cheat-verify2/cheat_map.png`.

A second script enters the level below the player. The game reaches mode `$14`
with three actors, so level entry still works after the cheat.

## The Special Zone map

The Special Zone is overworld map `5`. The player reaches it at
`$0118/$0128`.

| Node | Map position | Result of a press on A |
| --- | --- | --- |
| Center big star | `$0178/$01A8` | Enters the Giant Starman boss course `$00A` |
| Lower-inner node | `$0178/$01C8` | Warps to map `3`, which is World 8 |

On the demoOnly1 donor image the center node warps to map `5` at
`$0118/$0128`. The product build enters the boss course instead, so the center
warp is an open gap in this build.

Run this command to reach the Special Zone map with control.

```sh
python3 tools/play_native_target.py --special-zone
```

The launcher applies the completion flags and moves the player to map `5` at
`$0118/$0128`. The script then stops, so the player keeps control.

A run on the built target gives these results. The player moves from
`$0118` to `$0138`, and a press on A enters a course in mode `$14`. The map
therefore works as a normal map with playable courses.

## Why the startup script can fail

The startup input script assumes a new save file. If a save file exists at
start, the boot flow differs, the script does not reach the overworld and the
completion flags never apply.

The launcher now moves any save file aside in both cheat modes. Each cheat run
therefore starts from a new save and applies the flags.

## Why the warp can stop working

The startup input script assumes a new save file. If a save file exists at
start, the boot flow differs, the script does not reach the overworld and the
completion flags never apply. The lower-inner node then stays a normal course.

The launcher now moves any save file aside in both cheat modes. Each cheat run
therefore starts from a new save and applies the flags.

## Tests

The tests are `tests/test_completion_cheat.py` and pass 7/7. The full suite
passes 289/289 tests. The log is `local/reports/unit-tests-specialzone.log`.

## Limits

The cheat writes the running save state in WRAM. It does not rewrite SRAM
directly. An in-game save writes the current flags to SRAM. This document does not
measure that path.

The cheat starts a fresh save each time. Progress inside a cheat session does not
replace the earlier save of the player.

The cheat does not claim a course pass, a clear or an exit count.