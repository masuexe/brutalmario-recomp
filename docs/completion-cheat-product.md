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

## Tests

The tests are `tests/test_completion_cheat.py` and pass 4/4. The full suite
passes 284/284 tests. The log is `local/reports/unit-tests-cheat.log`.

## Limits

The cheat writes the running save state in WRAM. It does not rewrite SRAM
directly. An in-game save writes the current flags to SRAM. This document does not
measure that path.

The cheat starts a fresh save each time. Progress inside a cheat session does not
replace the earlier save of the player.

The cheat does not claim a course pass, a clear or an exit count.