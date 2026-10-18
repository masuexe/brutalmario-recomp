# demoOnly1 boss-entry exploration

Date: 2026-10-15. The user clarified that Demo 1-1 contains one ordinary
level and no boss. Boss qualification therefore moves to a **separate
demoOnly1 experiment**, rather than assuming a boss exists in the primary
target or merging historical content into it.

Subsequent manual testing confirms normal boss behavior but found frequent
death black screens. The rebuilt target now enables legacy echo-buffer
compatibility; see [death-black-screen.md](death-black-screen.md).

The user identifies a boss at the end of Athletic Special and suggests
World 1's castle as another candidate requiring overworld-coordinate changes
(initially called Larry; the later manual encounter was identified as Lemmy).
They confirm that the large door at the top of the rainbow room
is the final pre-boss entrance, and describe the boss as a black sphere
with eyes and fangs. They warn that Mario must stay alive on the arena's
platforms long enough for the boss to appear.

## Ready-to-play native entry

From the project root, in the same desktop environment used to play Demo 1-1:

```sh
python3 tools/play_demo_only1.py --boss-door
```

The isolated demoOnly1 executable boots, automatically takes diagnostic
shortcuts through the existing room exits, and returns control at the
**top door in room `$177`**, with turbo off. Press Up to enter `$178`.
Keep jumping between the platforms after entry; standing idle can make
Mario fall and restart the room before the boss becomes visible.

For easier movement during boss practice:

```sh
python3 tools/play_demo_only1.py --boss-door --air-swim
```

Press Up at the door, then repeatedly tap the normal jump button to swim
upward. Release it to sink; use Left/Right to steer. The session keeps
`$7e0085 = 01`, enabling the guest's normal water physics in air. Mario
can still take damage and can still fall if left idle. Positions, velocities,
boss health, and attack logic are not held or replaced. Restart without
`--air-swim` to disable it. This changes gameplay physics and is for practice,
not fidelity or natural-clear acceptance.

To return to Special after accidentally warping to Star World:

```sh
python3 tools/play_demo_only1.py --special
```

`--special`, `--boss-door`, and `--air-swim` each create a **fresh practice
session** under `local/play/demo-only-1/practice/session-*/`, with separate
SRAM and savestate files. Fresh sessions start on Special regardless of the
ordinary save's current map. Existing progress is preserved; this does not
move Mario in the ordinary saved game. `--air-swim` alone starts at Special.
The launcher prints the session directory. Each new launch starts fresh.

For an ordinary start without shortcuts:

```sh
python3 tools/play_demo_only1.py
```

The launcher verifies the ROM and binary/runtime receipts. Ordinary launches
retain executable-relative config and saves in `local/build/demo-only-1/`.
Practice launches copy the ordinary config into the new session and pass that
explicit path, retaining desktop settings while keeping the working directory
inside the practice session. The binary is
`local/build/demo-only-1/BrutalMarioDemoOnly1SNESRecomp`.

The [map teleport and practice selector](level-select.md) additionally supports
`--select-level` and arbitrary map/pixel
coordinates through `--teleport MAP X Y`, all compatible with `--air-swim`.

The shortcut is **not a level-clear test**. It writes Mario's position and
door/pipe transition state to exercise existing exits, then releases all
scripted input. It does not alter ROM bytes, exit destinations, boss state,
player power, or health. Without `--air-swim`, no persistent forcepoke or
invulnerability is used.
Keyboard/controller input continues after the script ends.

Automated practice checks reach Special (map 5, mode `$0e`) and enter the
boss arena with swimming active. Repeated jump strokes raise Mario from
Y=304 to Y=174 in the arena. A separate controlled-position probe also
confirms rising and sinking. The launcher integration check creates practice
SRAM and leaves every existing ordinary save file's SHA-256 unchanged.
Local evidence: `practice-special`, `practice-swim`, and `air-swim-85` under
`local/captures/`. These checks do not establish a completed boss fight.

## Version pin and reproduction

The alternate manifest is [demo-only-1.json](../config/demo-only-1.json):

| Input/output | SHA-256 |
| --- | --- |
| Headerless stock base | `0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b` |
| Original `demoOnly1.ips` | `1080862aaf3e9bacfae97868806ee8faa53b2b4d6518fd2713aeda3c0c5e6880` |
| Prepared 4-MiB headerless ROM | `b8d86f894f6c07aeb74794c59adab8f336080285b4781a3e1c921615a2d8216b` |

Preparation uses the same verified 512-byte IPS coordinate convention.
demoOnly1 differs from Demo 1-1 at **848,021 ROM bytes**; it is not an
overworld-only edit of that target. Native generation starts again from
its own ROM, vector seeds, identity, scaffold, generated code, and build.
Only the project-owned runtime fixes/instrumentation are shared.

```sh
python3 tools/prepare_rom.py --manifest config/demo-only-1.json \
  --base '../roms/Super Mario World (U) [!].smc' \
  --ips ../patches/demoOnly1.ips --output local/roms/demo-only-1.sfc

# Fresh scaffold only; existing directories are refused.
python3 tools/m1.py scaffold --target demo-only-1
python3 tools/m1.py generate --target demo-only-1
python3 tools/m1.py build --target demo-only-1

python3 tools/m1.py reference --target demo-only-1 \
  --script recomp/inputs/demo-only-1-boss-probe.script --capture boss-reference-new
python3 tools/m1.py native --target demo-only-1 --renderer optimized \
  --script recomp/inputs/demo-only-1-boss-probe.script --capture boss-native-new
python3 tools/compare_captures.py \
  local/captures/boss-reference-new local/captures/boss-native-new
```

The default `tools/m1.py` target remains Demo 1-1. The alternate experiment
is `local/experiments/BrutalMarioDemoOnly1SNESRecomp`; subsequent generation
and build logs use `local/reports/demo-only-1/`. Captures include explicit
target and ROM/binary/route/runtime receipts. `tools/probe_reference.py`
also supports exploratory reference runs against an explicit target manifest.

## Located route and evidence

| Room | Observed role | Existing exit used for the diagnostic shortcut |
| --- | --- | --- |
| `$134` | Initial Athletic Special area | Screen `$13` to `$174` |
| `$174` | Long platforming section | Screen `$1e` to `$175` |
| `$175` | Star/platform section | Screen `$14` to `$176` |
| `$176` | Star staircase/door section | Screen `$15` to `$177` |
| `$177` | Rainbow room; large top-center door | Normal Up input at the top door to `$178` |
| `$178` | User-identified boss arena, blue spherical platforms | Observe survival and boss behavior; not qualified yet |

Both cores reach the pre-boss handoff at host frame **3155**, in gameplay
mode `$14`, room `$177`, Mario **X=120, Y=112**, with five lives. All handoff
pixels match after RGB5 quantization. Raw color bytes and full WRAM are
not identical (36 differing WRAM bytes); this is not a complete-state claim.

The original 6,104-call smoke script also boots demoOnly1 and enters `$134`
in both cores. It is not a valid natural route through this level: Mario
falls, and the final reference/native scenes diverge (reference overworld
mode `$0e`, native overworld-loading mode `$0c`). This remains a separate
reproducer; booting is not whole-version acceptance.

The boss-entry probes reach `$178` in both cores. Idle Mario repeatedly
falls and re-enters, so those samples **do not establish boss absence or
a completed attack cycle**. Custom sprite slot 9 is active with ID `$a1`;
the observed sprite starts to the right at X=320 and later moves left.
Numeric correspondence with supplied sprite lists is not established.
Additional position-clamped captures are diagnostic only and do not count
as gameplay acceptance. Boss health/state was not patched.

Both guessed World 1 castle positions have been withdrawn. Map 1 /
`$0058,$0088` loads `$101` (user-confirmed World 6); map 0 / `$0018,$01B8`
starts loading `$010` but the user also rejected it as the intended castle.
Its native/reference loading stall is a wrong-node observation only. On
2026-10-18 the user manually found the intended castle and reported normal
**Lemmy** boss functionality. Their subsequent stationary reading identifies
map 0 / `$00A8,$01A8`; the restored `--level world1-castle` shortcut uses this
observed position. The on-map `$1C5` room value is stale, not the castle room ID.
See [level-select.md](level-select.md#recorded-lemmy-castle-entrance).

## Current checkpoint and remaining validation

The user reports a successful boss defeat with air swimming enabled. The
boss-functionality checkpoint therefore passes under that practice setting.
Victory turns the screen black without "MARIO STAGE CLEAR". At the user's
request, investigation of this behavior is deferred. Their suggestion that
the original does the same is unverified; the post-victory flow is not passed.

The user also confirmed that several deaths all returned to the overworld
without a black-screen hang. The death-return checkpoint passes, completing
this round of basic functionality validation with the accepted victory-screen
limitation. A recorded reference comparison of a full fight would be needed for stronger fidelity
claims. Preserve ZSNES 1.51 as the historical baseline; it has not been run
locally. An unassisted clear is not required for this practice checkpoint.

The existing **17 project tests pass**, and source/ROM checks pass for both
targets. Do not mark full boss fidelity, the complete victory/exit flow, or
demoOnly1 completion as passed yet.

Ignored local evidence includes `demo-only-1-native`, `athletic-room-chain-*`,
`athletic-top-door`, `boss-door-handoff-reference`, `boss-door-handoff-native`,
and `demo-only-1-door-*-final` under `local/captures/`. The handoff comparison
is `local/reports/boss-door-handoff-comparison.json`. Exploratory scripts
and negative attempts remain under `local/probes/` for traceability.
