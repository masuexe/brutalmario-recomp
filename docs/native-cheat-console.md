# Built-in practice cheat console

## Problem

The earlier practice console is a Python tool. It writes `cheats.force` and
`cheats.script`, and the runtime reads those files every frame. That workflow
needs a terminal, a live process and external files. The product must carry the
same practice controls in the game window.

## Built-in console

The runtime patch `0010-builtin-cheat-console.patch` adds an in-game console.

- Press the backquote key (`~`) to open the console. The guest freezes.
- Press Escape or backquote to close the console without a command.
- Press Enter to run a command.
- `SNESRECOMP_CHEAT_CONSOLE=1` opens the console at startup.
- `SNESRECOMP_CHEAT_CONSOLE_COMMANDS` runs a semicolon-separated command batch
  for an automated check.

The console draws a 512x448 panel. It lists the commands and shows the current
input and status.

## Commands

| Command | Effect |
| --- | --- |
| `invincible` | Toggle the held star timer |
| `swim` | Toggle air swim |
| `lives N` | Set the life counter |
| `music HEX` | Request a music slot |
| `music off` | Clear the requested slot |
| `map M X Y` | Queue a map teleport |
| `teleport ROOM` | Queue a room transfer |
| `complete` | Queue completion flags and a map reload |
| `help` | Show the command list |
| `close` | Close the console |

Map and room transfers use the same internal guest-script sequence as the old
Python console. They do not write a file.

## Verification

- The r14 target builds with the new runtime patch.
- A headless run with `SNESRECOMP_CHEAT_CONSOLE=1` writes the 512x448 panel
  through `SNESRECOMP_OVERLAY_DUMP`.
- A batch with `close` opens and closes the console, and the guest then runs
  its normal startup script.
- The unit test checks the runtime patch, the manifest entry and the command
  text.

## Limits

The console needs a desktop keyboard. It has no gamepad text entry. The
teleport, completion and music writes need a human playtest for visual and
audible acceptance. The overlay dump proves the panel, not every command.
## Status (2026-11-02)

The earlier Windows roughly 3 FPS defect is repaired. Launch-setting environment
queries were on the ROM bus path; they now run once per content load. The
console code itself is unchanged. Fresh Linux and Windows checks qualify the
performance repair and console open/close lifecycle; see
[the performance report](windows-console-performance.md) for exact identities,
regressions, bundle paths and remaining limits.

Use the new `product-r14-console-fixed-*20261102.zip` bundles recorded there.
The older `product-r14-cheat-console-experimental-win.zip` remains a preserved
slow historical build. These packages do not include the separate overworld
music ROM fix. Full command and desktop/audio acceptance remain distinct from
the headless regression results.

## User acceptance (2026-11-02)

The user reported no issues after testing the repaired console packages and
accepted this checkpoint. This supersedes the pending console playtest status
for those delivered binaries. It does not assert separate acceptance of every
command, audible output, or a complete game playthrough. The new
[product tool](product-tool.md) reuses these binaries as its first verified inputs.
