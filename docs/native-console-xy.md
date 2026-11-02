# In-level coordinate teleport

## Commands

Use `xy X Y` or its alias `tp X Y` in the built-in console. Coordinates are
world pixels within the current room: X increases rightward, Y downward.
Decimal is the default, including leading-zero values; an explicit `0x` or
`0X` prefix selects hexadecimal. Both arguments must be integers in 0..65535.
Missing, malformed, overflowing or extra arguments leave WRAM unchanged.

Examples:

```
xy 256 320
tp 0x100 0x140
```

Execution requires game mode 14, normal player action, no sprite lock, no game
pause flag and no goal countdown. Title/menu/map/loading/death/pipe/ending
states are rejected. The console's own pause is permitted. The command operates
immediately while the simulation is frozen and does not reload the room.
It synchronizes current/next positions at $94/$96 and D1/D3, and clears horizontal/
vertical velocity and position fractions. Room IDs, exits, water flags, saves
and progress are preserved. Gravity/collision resume normally afterward;
coordinates are not clamped to room geometry. Camera behavior remains native.
`teleport ROOM` remains the separate inter-room command.

## Implementation and checks (2026-11-02)

Pinned runtime patch 0013 extends the existing teleport/swim repair chain and
adds the command to the console help/panel. The user accepted the preceding
swim repair after testing; that does not imply manual acceptance of this new
command.

`tests/test_console_xy.py` materializes the pinned runtime, compiles the actual
command handler and checks exact full-WRAM writes. Cases cover decimal/hex,
leading zeros, zero/65535 boundaries, malformed/oversized numbers, every
non-gameplay mode and each action/lock/pause/goal gate. Successful writes touch
only the position/momentum/fraction fields; rejected commands touch no WRAM.
Twelve targeted tests pass, including the existing swim, inter-room transfer,
patch upgrade, product integrity and launch-setting checks.

Both candidate binaries pass shared product verification. On each platform,
12 closed-console startup dump files remain byte-identical to the swim parent.
A fresh complete suite was not run; the earlier eight stale demoOnly1 host
receipt failures remain deferred and are not counted as passing here.

`recomp/inputs/console-xy-position.script` checks a live coordinate-write boundary
in room 00F on both platforms. This is an assisted entry/write fixture, not an
automated console-keyboard test. Script writes span simulation boundaries;
the compiled-handler test separately checks exact atomic arrival at 256/320.
The live boundary sample reads 256/324 after gravity resumes, the next sample
256/326, then ordinary Right reaches 285/352 and later 297/352. Camera X progresses
121, 123, 178, 191. Room 00F remains active. This checks normal simulation after the
write, not arbitrary room geometry or a course clear.

## Identities and delivery

- Target r14; ROM
  `393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b`.
- Linux executable
  `21d933afe073c192cb1cd052144007a630a3deabc72719e738c4960e755dc14b`.
- Windows executable
  `22a09e2bd62c659a6f3f56af7acfd6b567c6d48d94a34c90380f734056ae7b0f`.
- Linux archive `local/release/product-r14-xy-linux-v1.zip`, SHA-256
  `b715c1226282dd523a74015624626862b6ca5f71b46ca36d56cca37c1754284e`.
- Windows archive `local/release/product-r14-xy-windows-v1.zip`, SHA-256
  `131703ed1388f1cd654ab75f415cd653ec35edcd7a01a77417207880fcb7d1e9`.

Source materialization, compile/link commands, exact input/ROM/binary receipts,
profiles, regression results and test logs are under
`local/diagnostics/xy-command-v1/`. The new host object reuses the previously
qualified remaining link inputs. Existing packages and saves remain intact.
The Windows folder and ZIP are delivered under `D:/tmp/product-r14-xy-windows-v1`.
Launch `play.bat` in that folder; Python 3 is required. This is still r14 without
the separate overworld-music ROM repair. Broader restoration remains open.
