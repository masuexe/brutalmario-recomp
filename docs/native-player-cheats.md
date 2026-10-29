# Runtime practice cheats for the native product

## Result

`tools/play_native_cheats.py` starts the product build with practice cheats.
It reaches any room, any map position, and can hold invincibility and air swim.

```sh
python3 tools/play_native_cheats.py --menu
python3 tools/play_native_cheats.py --room 0x151
python3 tools/play_native_cheats.py --map 6 --x 0x128 --y 0x1e8
python3 tools/play_native_cheats.py --room 0x190 --invincible --air-swim
python3 tools/play_native_cheats.py --complete-all --lives 50
```

The tool checks the ROM hash and the binary hash first. It mounts the 45 content
packs and starts a normal window.

## Options

| Option | Effect |
| --- | --- |
| `--room ROOM` | Enter any room id from `0x000` to `0x1FF` |
| `--map M --x X --y Y` | Place the player on a map position |
| `--invincible` | Hold star invincibility |
| `--air-swim` | Treat every level as water |
| `--lives N` | Set the life counter |
| `--complete-all` | Open every saved level slot, event and switch |
| `--menu` | Ask for the destination and the toggles |
| `--emit PATH` | Write the host script and stop |

## Written fields

The tool builds a host script. The script writes these fields.

| WRAM | Value | Purpose |
| --- | --- | --- |
| `$19B8` | room low byte | Room transfer |
| `$19D8` | 4 plus room high byte | Room transfer page |
| `$1F11` | map id twice | Map transfer |
| `$1F17` | X, Y as two words, twice | Map transfer position |
| `$1F1F` | X>>4, Y>>4 as two words, twice | Map transfer tile |
| `$0100` | `0b` | Map loader mode |
| `$85` | `01` each frame | Water physics |
| `$1490` | `40` each frame | Star timer |
| `$0DBE` | life count | Life counter |

A room transfer enters the map 6 lower-left node first, then writes `$19B8`,
`$19D8`, `$94` and `$71`. The screen changes after the fade.

## Verification

Each row is a headless capture of the product build.

| Cheat | Request | Measured | Capture |
| --- | --- | --- | --- |
| Room | `0x151` | room `0x151`, three `9C` actors | `local/captures/cheat-room151` |
| Room | `0x123` | room `0x123` | `local/captures/cheat-room123` |
| Map | map 6, `0x128`, `0x1E8` | `$1F11`=6, X=`0x128`, Y=`0x1E8` | `local/captures/cheat-map` |
| Air swim | on | `$85`=1 | `local/captures/cheat-swim` |
| Invincible | on | `$1490`=0x40 | `local/captures/cheat-inv` |
| Lives | 50 | `$0DBE`=50 | `local/captures/cheat-lives` |

The tests are `tests/test_play_native_cheats.py` and pass 8/8.

## Limits

The script writes at the start of the session. To change the room again,
relaunch the tool. The invincible and air-swim flags hold after the script ends.
The room transfer uses the pipe fixture, so it moves the room and not the room
entrance. A completion run moves the earlier save to `save.srm.before-cheat`.

## Fast room entry

By default a --room run now uses a fast entry. The host script polls game mode
with the until command and holds Turbo during the transition, instead of the old
fixed waits. It skips the intro with a timed B press after the intro level loads.
The script turns Turbo off when the room is reached.

The measured room 190 fixture drops from 2,789 frames (about 46 s at normal speed)
to 1,807 frames (about 9-10 s with Turbo). The change only affects startup; the
level and gameplay are the same.

- --legacy-entry keeps the original fixed-wait startup.
- --fast forces the fast path (already the default for --room).

The fast startup polls title mode 0x07 and file select 0x08. With no save file it
waits for the intro level mode 0x14, waits 780 frames, presses B to skip it, then
polls overworld mode 0x0E. With an existing save file the game loads straight to
the overworld, so it polls 0x0E directly. The tool picks the variant from whether
saves/save.srm exists. It then polls each level load and
waits for the requested room number in $10B/$10C. A missing expected state exits
with code 3 after the per-step timeout, so a mismatch does not hang.