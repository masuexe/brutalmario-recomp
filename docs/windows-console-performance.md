# Windows cheat console performance regression

## Finding

The built-in cheat console is present in the new Windows r14 package. The game
starts at about 3 FPS.

The console is not the cause. These cases stay at about 3 FPS:

- r14 Windows build with the console code removed.
- old runtime objects relinked with the current host.
- VSync off, audio off and window scale 1.
- `SNESRECOMP_LLE_BOUNCE=0`.
- a script with `turbo on`.

The old package executable runs the same 60-frame script in about 2 seconds.
The new executable takes about 21 seconds.

## Evidence

- Old package: `product-r14-event30-v2.zip`.
- New package: `product-r14-cheat-console-win.zip`.
- New Windows binary: `local/build-windows/demo11-native-product-r14/`.
- Test script: `wait 60 / dump / quit`.
- Logs: `tmp/old60.log`, `tmp/new60.log`, `tmp/fresh.log`.

Both runs report the same guest frame and master clock at frame 60. The new
build reports `aot_bridge_entries=3974` and `interpreted_opcodes=8037440`
before the bounce override. the old build reports 60 and 817753. With
`SNESRECOMP_LLE_BOUNCE=0` the new build reports 0 and 820072, but remains slow.

## Status

Open. The Windows package with the console is not a normal-play package until
the new build matches the old executable's speed.
## Host profile

`SNESRECOMP_HOST_PROFILE=1` isolates the slow stage on the new Windows build.

- Old package: guest mean 3.36 ms per frame.
- New package: guest mean 351 ms per frame.
- Raster, compose, upload and deadline wait stay below 2 ms.

The guest stage is about 100 times slower in the new build. Audio off and
`SNESRECOMP_APU_MASTER_CLOCK=0` do not change it. The next step is a compiled
object and link comparison, not a presentation fix.
## CPU load

A Windows process counter sampled the new executable at about 100 percent of
one CPU core during the slow guest stage. The guest stage is compute-bound, not
a sleep or deadline wait.
## Object comparison

The old and new Windows objects for `bank00_v2.c`, `interp_bridge.c`,
`common_rtl.c` and `snes.c` have the same instruction stream. Only the
`.debug$S` section and the embedded source path differ.

The 100 times guest slowdown is therefore not in the generated guest code.
The remaining difference is the host call path or the link inputs.
## Render and SDL exclusion

A test build forced `g_snes->disableRender = true` on every frame. The guest
stage stayed at 487 ms per frame. A test build linked the old SDL3 library. The
guest stage stayed at 443 ms per frame.

The guest slowdown does not come from PPU rendering or the SDL3 library.

## Local rebuild exclusion

A local Windows rebuild of the same target shows the same slow rate. This
result excludes the console patch as the cause.

| Binary | Guest stage mean |
| --- | --- |
| Shipped package executable | 3.6 ms per frame |
| Local rebuild, optimized flags | 592 ms per frame |
| Relinked fast build directory | 547 ms per frame |

The local rebuild uses the same compiler, the same flags and the same generated
guest code. The shipped executable stays fast. The slowdown therefore comes from
the build host, not from the cheat console patch.

The 60-frame script reports the same guest state in every case. The difference
is the time to reach it.
