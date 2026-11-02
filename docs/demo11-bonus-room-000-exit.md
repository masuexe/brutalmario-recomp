# Bonus room 000 exit repair

## Summary

The bonus room `$000` did not start its exit after the last 1-up appeared.
The player stayed in the room with no way to leave. The cause is one
undefined register read in the bonus sprite program. One reviewed code patch
repairs it.

## Symptom and reproduction

The user reported the symptom in the current build. The room is entered when
the player collects 100 stars. The last 1-up spawns, and then the room does
not end.

The fixture `recomp/inputs/bonus-room000-pickup2.script` reproduces the
symptom. The fixture is labelled. It pokes room `$000`, sets the bonus-game
entry flag `$1425`, sets one pending 1-up, and clears the spawned 1-up slot
as a real pickup does. It writes no completion flag.

## Cause

The level loop at `$00:A1E4` starts the exit only when three conditions hold:

1. `$1425` is non-zero.
2. `$14AB` is non-zero.
3. `$14AB` is below `#$40`.

`$14AB` is the bonus-game end timer. The bonus sprite writes it in the
function at `$18:FB01`:

```
18FAFE  200EFB     JSR $FB0E      ; scan slots for a 1-up sprite
18FB01  98         TYA            ; Y = 1 when a 1-up is present
18FB02  F001       BEQ $FB05      ; write the timer only when Y = 0
18FB04  60         RTS
18FB05  A960       LDA #$60
18FB07  8DAB14     STA $14AB
18FB0A  9EC814     STZ $14C8
18FB0D  60         RTS
```

The scan function at `$18:FB0E` sets `Y = 1` when it finds a 1-up. It does
not set `Y` when it finds nothing, so `Y` keeps the value of the caller.
That value is not defined by this code.

In demo6 and demo7 the caller left `Y = 0`. The timer write ran, and the
room ended. In cheap_demo the caller leaves `Y` non-zero. The branch skips
the timer write, `$14AB` stays zero, and the exit never starts.

## Evidence

Reference host, fixture `bonus-room000-pickup2.script`, samples at
frames 150, 210, 330 and 570 after the room load:

| Version | `$14AB` after the pickup | Result |
| --- | --- | --- |
| demo6 | `58`, `49`, `2B`, then 0 | mode `0C`, left the room |
| demo7 | `58`, `49`, `2B`, then 0 | mode `0C`, left the room |
| cheap_demo | `00` at all samples | mode stays `14`, stuck |

The disassembled bonus blocks of demo6, demo7 and cheap_demo are the same
program. Only the `JSR` targets differ, because the blocks are at different
addresses. The level header, the sprite list, the engine exit code and the
pickup handler are also byte-identical. The difference is only the value of
`Y` at the scan.

A patch probe confirms the cause. When the timer write runs on every pass
(`BEQ` changed to `BRA`), the room ends. When the scan clears `Y` first,
the room also ends, and the timer value matches demo6.

## Repair

The recipe `config/native-content/sprite19-yfix-module.json` pins the
cheap_demo record and the protected program. It adds one patch of the same
length at `$18:FB0E`:

```
before: DA A2 09 BD C8 14 F0 09 B5 9E C9 78 D0 03 A9 01 A8 CA 10 EF FA 60 60
after:  DA A0 00 A2 09 BD C8 14 F0 08 B5 9E C9 78 D0 02 A0 01 CA 10 F0 FA 60
```

The patch adds `LDY #$00` at entry, so `Y` is defined for every return.
The two branch displacements change by one byte to keep the same targets.
The length is 23 bytes before and after, so no code moves.

The recipe is a separate file. The original `sprite19-module.json` is
unchanged, so the earlier targets keep their pinned hashes.

## Target

The repair is in the target `demo11-native-product-r16`. This target is a
child of `demo11-native-product-r15` and adds only the reviewed patch.

Identities:

- ROM: `9f6d845b19ad24160668633e2f30d0e846662c67b135c6cbc1bca680db20716e`
- binary: `50a062e58e56776338ea1d506bc84184acbbb275f36ca1e1453a75ebb148cd5f`
- sprite 19 pack: `ae73cf2577e20c4d659507c30d93a5268c1f7d011c55021ffe66437d9e745803`

## Verification

Native run, fixture `bonus-room000-pickup2.script`, samples at the same
frames:

| Target | `$14AB` after the pickup | Result |
| --- | --- | --- |
| r14 (before) | `00` at all samples | mode stays `14`, stuck |
| r16 (after) | `58`, `49`, `2C`, then 0 | mode `0C`, then `0E` |

The reference host cannot run this ROM because the sprite program is in the
native `$AF` module view. The native runtime is the correct check for this
target.

## Limitations

- The fixture sets `$1425` and `$1890` directly. It qualifies the exit
  boundary, not a full star-collection route.
- The route from the room exit to the map is not followed in this receipt.
- The sprite graphics of the bonus room are not reviewed here.

## Correction: the goal tape does award bonus stars

An earlier draft of this report claimed that the goal tape never awards
bonus stars in this ROM. That claim was wrong. It came from fixtures that
never touched the tape, so the tape program never ran.

The correct behaviour, measured on the reference host with the 1-1 goal
route:

1. The player touches the tape. The tape writes the star count to `$1900`.
2. The routine at `$13:5CF12` moves the stars into `$0F48`, one star per
   four frames.
3. The stock handler at `$00:8F5E` sees `$0F48 >= #$64`, sets `$1425`
   to `#$FF`, and subtracts `#$64`.
4. The bonus game then starts and writes `$14AB`.

Measured samples for a 1-1 clear with the counter seeded to 99:

| Sample | `$1900` | `$0F48` | `$1425` | `$14AB` |
| --- | --- | --- | --- | --- |
| tape contact | `08` | `63` | `00` | `00` |
| transfer | `07` | `00` | `FF` | `00` |
| bonus game | `00` | `07` | `85` | `25` |

The star count wraps because 99 plus 8 passes 100. The stock code subtracts
100 and keeps the remainder.

Only the tape contact awards stars. A level clear without a tape contact
awards coins instead.

### Fixture rule

The star counter must be seeded to 99, not 100. A value of 100 is consumed
by the stock handler at once, and the flag is cleared again before the bonus
game can start.

## Route qualification

The 1-1 goal route qualifies the entry path. The fixture
`recomp/inputs/bonus-room000-w1-1-transfer.script` enters World 1-1, seeds
99 stars, flies to the far end with labelled swim and invulnerability
fixtures, disables those fixtures, and then touches the tape with normal
physics.

The exit path is qualified separately by
`recomp/inputs/bonus-room000-pickup2.script`, because the native product
cannot play the bonus room program through the reference host.

## Full end-to-end verification

The route is now qualified from the real goal tape to the room exit, on the
native product builds.

Fixture: `recomp/inputs/bonus-room000-full-route.script`. It enters World
1-1, seeds 99 bonus stars (labelled cheat), flies to the far end with
labelled swim and invulnerability fixtures, disables those fixtures, and then
touches the tape with normal physics.

Measured samples for the patched target r16:

| Sample | Mode | Room | `$0F48` | `$1425` | `$14AB` |
| --- | --- | --- | --- | --- | --- |
| tape contact | `14` | `105` | `63` | `00` | `00` |
| star transfer | `14` | `105` | `08` | `FF` | `00` |
| bonus room | `14` | `100` | `08` | `FF` | `00` |
| timer set | `14` | `100` | `08` | `FF` | `39` |
| room exit | `0E` | `100` | `08` | `00` | `00` |

The same fixture on the unpatched target r14 stops at the bonus room:

| Sample | Mode | Room | `$0F48` | `$1425` | `$14AB` |
| --- | --- | --- | --- | --- | --- |
| tape contact | `14` | `105` | `63` | `00` | `00` |
| star transfer | `14` | `105` | `07` | `FF` | `00` |
| bonus room | `14` | `100` | `07` | `FF` | `00` |
| final sample | `14` | `100` | `07` | `FF` | `00` |

The room does not change and the timer stays at zero. This is the reported
symptom.

### The sprite slot evidence

The bonus room uses sprite 19 in slots 8 and 9. At the moment the bonus
sprite reaches state 9 with no 1-up pending:

- r16: slot 9 is removed, and `$14AB` becomes non-zero.
- r14: slot 9 stays alive in state 9, and `$14AB` stays zero.

The patch changes exactly that branch, so this is a direct confirmation of
the cause.

### Both 1-up cases are covered

This route awards no 1-up, so `$1890` is zero when the scan runs. The
fixture `recomp/inputs/bonus-room000-pickup2.script` covers the other case:
it seeds three pending 1-ups, and the room exits only after the last one is
cleared. Both cases show r16 leaving the room and r14 staying inside.

### The bonus room here is room 100

World 1-1 leads to bonus room `$100`, not `$000`. Both rooms use the same
sprite 19 record, so the same patch covers both.

## Regression use

Three fixtures cover the repair. Two of them need a native build, because the
bonus sprite program lives in the native code view.

| Fixture | Covers | Build |
| --- | --- | --- |
| `bonus-room000-full-route.script` | Goal tape, star award, bonus room entry, room exit | native |
| `bonus-room000-pickup2.script` | The case with pending 1-ups | native |
| `bonus-room000-w1-1-transfer.script` | The star transfer chain in detail | reference host |

Run one fixture against a patched target and one against an unpatched target:

```
python3 tools/play_native_target.py \
    --target demo11-native-product-r16 \
    --script "$PWD/recomp/inputs/bonus-room000-full-route.script" \
    --play-dir "$PWD/local/play/full-r16"

python3 tools/play_native_target.py \
    --target demo11-native-product-r14 \
    --script "$PWD/recomp/inputs/bonus-room000-full-route.script" \
    --play-dir "$PWD/local/play/full-r14"
```

The launcher writes its dumps to `local/captures/play-<target>`. Clear that
directory before each run. A stale dump from an earlier run reads as a
current result and gives a wrong answer.

Then check the pair:

```
python3 tools/qualify_bonus_room_exit.py \
    --patched   local/captures/play-demo11-native-product-r16 \
    --unpatched local/captures/play-demo11-native-product-r14
```

The check asserts four conditions:

1. Both runs set the bonus-game flag `$1425`.
2. The patched run writes the end timer `$14AB`.
3. The patched run reaches the map mode `$0E`.
4. The unpatched run keeps `$14AB` at zero and stays in the level mode.

A control run with the same directory on both sides fails on condition 4.
