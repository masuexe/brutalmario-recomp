# Live practice play

The practice launcher holds a window open and reads cheat files every frame.
The console accepts cheat commands while the game runs. This is the fastest way
to exercise a live fight with ordinary controller inputs and damage immunity.

## Start

```
export SNESRECOMP_DUMP_DIR=$PWD/local/captures/live-9c
python3 tools/play_native_cheats.py --target demo11-native-product-r12 --room 0x151 --console
```

The launcher prints the session directory. The live input file is
`local/play/<target>/cheats.script`. The runtime reads the file by byte offset,
so append complete lines while the game runs.

## Console commands

- `invincible` toggles the star timer.
- `swim` treats every level as water.
- `teleport 0x151` enters a room.
- `lives N`, `music SLOT`, `help`, `quit`.

## Input script

`tools/live_input.py` appends commands to the live file:

```
python3 tools/live_input.py --play-dir local/play/demo11-native-product-r12 \
  --line 'press right 120' --line 'press up+b 24' --line 'dump live1'
```

The runtime accepts `wait`, `press`, `poke`, `turbo` and `dump`. Dumps go to
`SNESRECOMP_DUMP_DIR`.

## Room 151 practice result

The flow starts the game, the room transfer enters live `151`, and the player
moves and attacks under `1490 = 64`. A blind attack sequence from the right edge
does not end the fight.

The player reaches `y 224` with a jump, while the green orb sits near `y 86`. A
position write to `(168,80)` fails: the game returns the player to the floor. The orb needs a valid platform route or a working swim state before the
damage window. Do not claim a 9C clear from this session.

## Cautions

- Close the console with `quit` and close the terminal session when done.
- Use fresh dump names. Do not overwrite accepted captures.
- The session directory keeps saves and temporary cheat files. The files are
  local and ignored by git.
