# Official C2 shooter restoration and remaining16B loading windows

Date: 2026-10-29. Experimental target: `demo11-native-type3-c2-v2`.
Parent: `demo11-native-type3-shooters-v1`. Accepted product remains r14;
this checkpoint does not promote rejected r15 or claim a whole-game release.

## Change

C2 has the same shooter classification problem as C0/C1. Its init field points
at an ASCII `MAIN` label, while its real callback is four bytes later. Sending
the placement through normal actor initialization cannot restore it correctly.

The new recipe maps the newest retained official Boss program at91:DD21 with
the original low16 address. The complete295-byte STAR block and source record
are byte-identical in Boss and7hero. No actor code changes. Its record changes
from the recipient placeholder to `03ffffffffffffff30dd9134dd91ffff`.

The existing192-byte adapter changes only three immediate operands: its two
exclusive C2 limits become C3 and its exclusive32 shooter-number limit becomes
33. Thus C2 uses B2 and resolves to the original C2 main field. C0/C1 retain
B0/B1, native custom shooters retain81..86, and the normal E0 child and generator
handling retain their meanings. All existing hooks and allocation sizes stay.
There are50 mapped packs. The derived ROM differs from the parent only in the
C2 record; adapter code is an external immutable resource.

Recipes: `config/native-content/type3-c2-boss-lowmirror.json` and
`config/native-content/type3-shooters-c2-v2.json`.
`tools/prepare_native_type3_c2.py` verifies official donor identities, both raw
records and full protected programs, the three threshold bytes, exact parent
preimages, low-mirror allocation, record-only ROM delta and unrelated mappings.
It then uses the standard sprite-gap preparer. Ignored exploratory generators
are not needed to reproduce this target.

ROM SHA-256:
`ecc16bfd6c03222b5979bc1496a68227846a76060c488d9445c3d86a42ca17a5`.
Native binary SHA-256:
`d98a6db40648210136e258fb65520c27072e67a1f424e514a0b96fd3412ab7b5`.

## Actual C2 behavior

The callback waits for its shooter countdown to reach zero, resets it to60
(hex), and generates custom95 in phase0F. It chooses a launch point16 pixels
left or right of the shooter and horizontal velocity F0 or10 according to the
player's side. It restores its shooter position after the temporary adjustment.

Captures `type3-c2-direction-final-v1` and
`type3-c2-source-direction-final-v1` use tracked native/source-type3-c2-direction
scripts. These declare map/primary-destination/pipe, immunity, player-position
and global13/14 fixtures; read-only countdown waits align actual firing. They
write no actor, shooter countdown, completion, HP, ownership or save data.
The reference is the pinned unmodified7hero ROM/core with its recorded echo
option; exact Boss/7hero C2 program equality establishes the behavior source.

All10 paired samples stay in live, unfrozen170. Selected custom95 actor rows
(including slot, status, XY, velocity,1504 and151C), shooter positions/countdown,
and child1656/1662/166E/167A/15AC properties match exactly. The left launch is
368/319 with velocity F0; subsequent X positions367,360,336 match. The right
launch is400/319 with velocity10;401,408,432 match. A previously generated actor
is also compared where it remains present. Native B2 corresponds to source83.
Both the bank91 callback and bankA3 child program actually execute.

`type3-c2-normal-entry-v1` separately uses only a map/node/translevel fixture
and ordinary Y entry to094. It uses no primary-room/pipe/position/immunity or
actor writes. Samples entry0,16,48,240,600 remain live in170. Phase0F custom95
is present at48,240,600. This resolves the earlier crash boundary for this
candidate, and exercises genuine generated actors beyond entry. It does not
prove an unassisted course traversal or exit.

Earlier direction probes started the player in unsafe room geometry and died
in both hosts. Preserve `type3-c2-{source-,}direction-v1/v2` and native death
locator evidence; their timed-out firing waits are not acceptance.

## All six room16B placements

Fresh captures `type3-c2-all16b-final-v1` and
`type3-c2-source-all16b-final-v1` use tracked native/source-type3-all16b scripts.
There are63 retained live16B samples. Final shooter X positions are
656,1040,1248,1440,1760,3856 in both hosts; all position tables match. IDs are
normalized only through the explicit shooter representation, preserving the
extra flag: the second C0 is nativeF0 versus sourceC1. This confirms that the
adapter preserves the placed extra bit as well as loading all two C0/four C1
instances. Original modules execute and phase2/phase3 children appear.

The late loading window explicitly teleports from2048 to3600, then advances
gradually through the final C1 loading boundary. It bypasses the intervening
corridor. Earlier continuous/fixed-height probes die in both hosts; neither
those probes nor the final segmented fixture qualifies ordinary traversal.

All-six identity/position acceptance is separate from complete motion parity.
C0 phase differences remain, and late-window C1 child trajectories differ in
these fixed-time samples. The prior20 exact C1 samples retain their earlier
identities and scope; this does not extend that claim to every C1 instance.
Other source/native8C behavior and other95 rooms remain open.

## Regressions and evidence

Two fresh replays compare this candidate with its actual C0/C1 parent:
`type3-c2-reg-purchase-v1` against `type3-shooters-reg-purchase-v1`, and
`type3-c2-reg-16b-v1` against `type3-shooters-native-final-v1`. The tracked
purchase/save/reset script has20 dump points; the earlier16B script has50.
All210 complete WRAM/SRAM/VRAM dumps match byte for byte, without stack masks.
These results cover the three-byte adapter extension's unchanged paths; they
do not relabel old r14 or whole-range survey evidence as this candidate.

Report: `local/reports/native-type3-c2-v2.json`, SHA-256
`c85e88f50eab37a74a865d3aa18f86bf1a8cae7eeca7c4ef46f1057fc0ec9fa8`.
It retains exact ROM/build/script/frontend/core receipts, samples, usage counts,
admission assertions and complete regression hashes.
All363 tests pass, including four new C2 admission/rejection tests, in
`local/reports/unit-tests-type3-c2-v2.log` (115.926 seconds).

```
python3 tools/prepare_native_type3_c2.py
python3 tools/m1.py scaffold --target demo11-native-type3-c2-v2
python3 tools/m1.py generate --target demo11-native-type3-c2-v2
python3 tools/m1.py build --target demo11-native-type3-c2-v2
python3 tools/qualify_native_type3_c2.py --output local/reports/FRESH.json
```

The checker reads the named retained captures. Rerun inputs into fresh capture
directories and qualify an isolated descendant when changing code or fixtures.
Next work remains current positive E0 birth, other six95 rooms, unresolved C0/
late-C1 phase and complete routes. Earned Seven/mazo victories, music, fonts and
other restoration gaps remain. No visible/audio or full physics/timing parity
is claimed by these selected-state checks.
