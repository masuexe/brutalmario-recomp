# Windows practice cheats and the ROM identity rewrite

## Purpose

This document records how to start the native product on Windows with the same
practice cheats that the Linux launcher supports. It also records the one
Windows-specific step that this approach needs, and the limits that remain.

## The problem

The Linux launcher starts the built binary directly. The Windows bundle bakes
the SHA-256 digest of one ROM into the executable. Three copies exist:

1. A hex string for the launcher warning.
2. A binary array in the generated program module.
3. A binary array in the mod catalog target.

The runtime compares the selected ROM with these copies. A different ROM stops
the start with this message:

```
ROM SHA-256 mismatch.
mods: plan rejected: The selected ROM does not match this mod catalog target.
```

## The solution

The tool `tools/play_windows_target.py` does three steps:

1. It copies the shipped Windows executable to the session directory.
2. It replaces the three baked digests with the digest of the selected ROM.
3. It starts the copy with the same host script that the Linux launcher writes.

The rewrite changes only the launcher identity bytes. The generated guest code
and the content packs stay byte-identical to the shipped bundle. The tool
refuses an executable that does not contain the expected digest.

## Command

```
python3 tools/play_windows_target.py --target demo11-overworld-music
```

Add switches for practice cheats:

| Switch | Effect |
| --- | --- |
| `--map M --x X --y Y` | Transfer to overworld map M at position X, Y |
| `--room ROOM` | Enter a room from 0x000 to 0x1FF |
| `--air-swim` | Treat every level as water |
| `--invincible` | Hold the star invincibility timer |
| `--complete-all` | Open every level, event and switch |
| `--lives N` | Set the life counter |
| `--stars N` | Seed the bonus star counter one time |
| `--music SLOT` | Request a music slot |
| `--fast` | Poll the game mode and skip the intro |
| `--existing-save` | The save file already holds an overworld file |
| `--dry-run` | Prepare the files and stop before the start |

The tool writes `cheat.script`, `config.ini` and `saves/` in the session
directory. The default directory is `local/play/<target>-windows`.

## Reuse of the Linux encoding

`tools/play_windows_target.py` calls `tools/play_native_cheats.py` for the
script text. The two hosts therefore use one cheat encoding. The music switch
stays local to the Windows tool because the Linux tool has no music switch.

## WSL interop detail

When the tool starts from WSL, two conditions apply:

1. The Windows process reads only Windows paths for the content packs. The tool
   converts each pack path with `wslpath`.
2. WSL interop does not forward ordinary environment variables. The tool sets
   `WSLENV` to the list of pack variables, so the variables cross the boundary.

Without `WSLENV`, the start stops with `[native-seven] rejected: <variable>`.

## Verified results

These results come from headless runs on Windows with `SDL_VIDEODRIVER=dummy`
and the shipped Windows executable after the digest rewrite.

| Check | Result |
| --- | --- |
| ROM accepted | Start completes with exit code 0 |
| Map transfer | `$1F11` = 2, X = 296, Y = 488 |
| Room transfer | `$10B` = 0x151, game mode 0x14 |
| Invincibility | `$1490` = 0x40 |
| Water physics | `$85` = 0x01 |
| Completion flags | `$1F02` = 0xff |
| Life counter | `$0DBE` = 0x32 |
| Music slot | `$1DFB` = `$0DDA` = the requested slot |
| World 6 map music | `$1DFB` = 0x23 |
| World 4 map music | `$1DFB` = 0x22 |

The two music rows match the corrected overworld table. See
`docs/demo11-overworld-music.md`.

## Limits

- The tool rewrites a shipped binary. It does not rebuild the target. A rebuilt
  Windows binary for this ROM exists at
  `local/build-windows/demo11-overworld-music/`, but it runs at about 1.8
  frames per second on this machine. A relinked fast build shows the same slow
  rate. The shipped executable keeps about 129 frames per second.
- The tool does not deliver an interactive cheat console. The shipped
  executable has no `SNESRECOMP_CHEAT_CONSOLE` support. The console build runs
  at about 3 frames per second, so it is not a playable option.
- The digest rewrite is valid only for a ROM whose generated code matches the
  shipped build. The World 4 and World 6 music repair changes four data bytes,
  so the generated code is unchanged except for the ROM identity. A ROM with
  different code needs a new build.
- The tool patches the binary each time it starts a session. Keep the shipped
  bundle unchanged and use a separate session directory for each run.

## Files

| Path | Purpose |
| --- | --- |
| `tools/play_windows_target.py` | The Windows launcher and digest rewrite |
| `tests/test_play_windows_target.py` | Review gates for the script text and the rewrite |
| `tools/play_native_cheats.py` | The shared cheat encoding |

## Later console repair (2026-11-02)

The console-unavailable and rebuilt-binary performance limits above describe
the earlier packages. Isolated new Linux/Windows console bundles now avoid
per-ROM-access environment queries and pass fresh state/performance checks.
See [the repair report](windows-console-performance.md). This launcher still
uses the preserved shipped executable; its identity-rewrite restrictions remain.
