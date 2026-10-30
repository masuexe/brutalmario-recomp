# Native C0/C1 shooter dispatch checkpoint

Date: 2026-10-29. Experimental target: `demo11-native-type3-shooters-v1`.
Accepted product remains `demo11-native-product-r14`. The rejected r15 artifacts
remain intact. This checkpoint qualifies an adapter and bounded behavior, not
a replacement whole-product baseline.

## Problem and change

The [low-memory review](native-lowmirror-restoration.md) restored motion and
child generation for several previously inert programs. Actual gradual loading
then exposed a different C0 failure: the recipient treats C0 as a normal actor,
calls its init pointer, and executes the ASCII `MAIN` label. The frame2943
instruction trace proves the subsequent stack corruption and BRK80:BF86.

The official7hero loader uses C0..CF for custom shooters; the recipient uses
E0..E5, with E6..E7 reserved for generators. Simply changing the global threshold
would conflict with native normal E0, which carries the Seven child program.
Copying the constructor continuation does not correct this classification.

The adapter instead changes three bounded instruction spans and adds a192-byte
immutable executable pack at92:8000. No source actor program, constructor,
room sprite list, physics routine, combat parameter or save format changes.

| Hook | Original bytes | Replacement | Adapter behavior |
| --- | --- | --- | --- |
|31:80B1|`c9e09038`|`5c008092`|Only placed customC0/C1 use the shooter loader; native E0..E7 classification remains |
|31:8114|`9d8317a504`|`5c408092ea`|Encode these shooters as B0/B1 in1783,X; retain native81..86 encoding |
|31:8141|`293f1869df`|`5c808092ea`|Resolve low shooter numbers30/31 to recordsC0/C1; retain other native mappings |

Recipe: `config/native-content/type3-shooters-v1.json`. It contains the complete
payload and exact preimages. Three entries occupy offsets0000,0040,0080; EA
padding separates them. The raw-payload recipe is reproducible with the normal
sprite-gap preparer, without the ignored exploratory generator.

At offset0000 the adapter compares C0/C2, tests the existing custom-placement
bit via[$CE],Y, derives the original80 custom-shooter flag, restores Y, and
jumps to02:A8D8. Noncustom C0/C1 use31:80ED. Other IDs execute the original
E0/E8 comparisons. Offset0040 retains STA1783,X and encodes C0/C1 by subtracting
90; other IDs subtract DF. Offset0080 masks3F, adds90 only for30/31, otherwise
adds DF, and rejoins31:8146. Long jumps preserve the existing call stack and
DB semantics. Normal E0 record pointers and generator handling stay intact.

C2 is not included. B0/B1 are shooter representations, not changed room or
normal-actor IDs. Both hosts still use the original eight shooter slots,
position tables, countdown bodies and source95 child program.

## Qualification and limits

ROM SHA-256:
`f130983d3c6c0dd8c6f201793197c54e8eb6f321206158f4db2d855ce3ee896c`.
Binary SHA-256:
`0510413e1fd1c9c13735edba21ab621a555f84ec4d4df6578b42a7150c3ee832`.
Report: `local/reports/native-type3-shooters-v1.json`, SHA-256
`9b3b8c898afce737349cf9c97e732531b776ffa69164d4e04c4bfb6548bcecb9`.

Fresh paired captures `type3-shooters-{native,source}-final-v1` use the tracked
native/source-type3-shooters-16b scripts. They declare map/primary-destination,
pipe, immunity, gradual/held player position and global13/14 phase fixtures.
They write no actor, shooter countdown, completion, ownership or save state.
The reference is the exact official7hero image and pinned unmodified core with
the recorded echo option. Boss and7hero C0/C1 records/programs are identical;
source version IDs alone are not used as identity evidence.

Across45 retained samples both hosts stay in live, unfrozen16B. One C0 and two
C1 instances load with corresponding positions. Native B0/B1 correspond to
source81/82. The native94/93 views actually execute12,181/9,079 instructions.
C0 counts down, resets, and generates phase2 custom95 at the source launch
column656. Its fixed-time motion samples differ in phase, so they do not
qualify cycle-exact motion or a complete mechanism match.

For C1, all20 held-window samples match the generated phase3 actors' sorted
status, XY, velocity and151C values exactly. Slot indices are intentionally
retained separately in the report and not equated: another source/native8C
actor difference already exists in r14. Animation, other actor families,
complete courses and all remaining16B loading windows are not accepted here.

Three fresh native regressions compare against r14: the hollow normal saved
exit12 samples, the A2 funded purchase/save/reset20 samples, and a Seven fight
window13 samples. All45 SRAM and45 VRAM dumps match completely. WRAM matches
except the explicitly listed inactive CPU stack residue within01BC..01DE.
The checker checks each differing address is below the active SP at the retained
frame in both runs; it does not claim full byte-identical WRAM. The hooks add
instructions and can change which NMI return bytes remain below SP.

The historical fixed-slot Seven child wait times out on this candidate.
A replacement read-only fight-window replay matches fresh r14 gameplay state
through the same window, but does not prove an E0 birth. Positive current-target
E0 birth qualification remains open; the normal E0 record/code is unchanged.
Failed fixed-slot and C0 event-alignment probes remain in ignored captures.

All359 unit tests pass in `local/reports/unit-tests-type3-shooters-v1.log`.
No complete victory, ending/save route, full physics/timing parity, visible
graphics or audible music acceptance follows from these checks.

## Reproduction and next work

```
python3 -c "import sys; sys.path.insert(0,'tools'); from native_sprite_gap import prepare; prepare('demo11-native-type3-shooters-v1')"
python3 tools/m1.py scaffold --target demo11-native-type3-shooters-v1
python3 tools/m1.py generate --target demo11-native-type3-shooters-v1
python3 tools/m1.py build --target demo11-native-type3-shooters-v1
python3 tools/qualify_native_type3_shooters.py --output local/reports/FRESH.json
```

Use fresh capture names/directories when rerunning the tracked scripts; update
the checker capture names in an isolated descendant rather than overwriting a
receipt. Report generation itself reads the pinned retained captures.

Next, qualify C0 event/timer phase and the remaining16B loading windows, obtain
a current positive normal E0 birth check, and test the other sprite95 rooms.
Then address C2 with its actual placement classification and low-memory needs.
Promote a cumulative product only after those relevant acceptance boundaries
are stated and checked. Broader Forest routes, earned Seven/mazo victories,
music, fonts and the remaining sprites are still restoration work.


## Subsequent C2 descendant

The [C2 checkpoint](native-type3-c2-restoration.md) extends this adapter by only
three threshold bytes, restores the original C2 program in bank91, qualifies
actual left/right generation and normal094 loading, and exercises all six16B
placements. Its210 full parent comparisons include this target's original16B
route. This document's earlier identities and acceptance limits remain intact.
