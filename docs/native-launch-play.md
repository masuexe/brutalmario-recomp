# Launch a native product build for play

`tools/launch_native.py` starts a native product build in interactive mode.
It sets the content pack variables that the build needs. A direct start of
the binary fails because the packs stay unset.

## Symptom of a direct start

A direct start of the binary prints this line and stops:

```text
[native-seven] rejected: BM_SEVEN_CODE_PACK
```

The runtime rejects the pack because the variable is absent. The stage code
in `tools/m1.py` sets about 60 `BM_*` variables. A manual start cannot
reproduce that set.

## Command

```sh
cd /home/harp/projects/sfc/brutalmario-recomp
python3 tools/launch_native.py --target demo11-native-product-r22
```

Use `--target demo11-native-product-r20` for the accepted product line.

## Options

| Option | Function |
| --- | --- |
| `--target` | Names the build and the ROM. Default is `demo11-native-product-r22`. |
| `--rom` | Overrides the ROM path. |
| `--config` | Overrides the configuration path. |
| `--extra` | Passes the remaining arguments to the binary. |

## What the tool does

1. It reads the target identity from the same modules that `tools/m1.py` uses.
2. It builds the environment for that target.
3. It starts the binary without a script, so the user can play.

## Confirmed start output

These lines show that every content system mounted:

```text
[native-seven] mounted immutable A2/A5/A6/B6 views
[native-sprite-gfx] mounted packs=2
[native-region] mounted demo11-product-r19-music regions=6 bytes=27431
```

## Deferred issue

The build prints `rom.cfg:1: Expecting [section]`. The file is a JSON
document, not an INI document. The runtime then uses default values for
scale, renderer and output. The window still opens and the game runs. This
warning does not block play.