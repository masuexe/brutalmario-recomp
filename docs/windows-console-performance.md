# Windows cheat console performance regression

## Finding

The built-in cheat console is present in the new Windows r14 package. The game
starts at about 3 FPS.

The console is not the cause. These cases stay at about 3 FPS:

- r14 Windows build with the console code removed;
- old runtime objects relinked with the current host;
- VSync off, audio off and window scale 1;
- `SNESRECOMP_LLE_BOUNCE=0`;
- a script with `turbo on`.

The old package executable runs the same 60-frame script in about 2 seconds.
The new executable takes about 21 seconds.

## Evidence

- Old package: `product-r14-event30-v2.zip`;
- New package: `product-r14-cheat-console-win.zip`;
- New Windows binary: `local/build-windows/demo11-native-product-r14/`;
- Test script: `wait 60 / dump / quit`;
- Logs: `tmp/old60.log`, `tmp/new60.log`, `tmp/fresh.log`.

Both runs report the same guest frame and master clock at frame 60. The new
build reports `aot_bridge_entries=3974` and `interpreted_opcodes=8037440`
before the bounce override; the old build reports 60 and 817753. With
`SNESRECOMP_LLE_BOUNCE=0` the new build reports 0 and 820072, but remains slow.

## Status

Open. The Windows package with the console is not a normal-play package until
the new build matches the old executable's speed.
