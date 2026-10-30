# Native code mapping correction and rejected r15 candidate

Date: 2026-10-29. Rejected candidate: `demo11-native-product-r15`.
Accepted working target remains `demo11-native-product-r14`.
ROM SHA-256:
`9f6d845b19ad24160668633e2f30d0e846662c67b135c6cbc1bca680db20716e`.
Native binary SHA-256:
`9060b07bdffe55ec7617c37fdabe9c437e98932db48cad096319b842eb6f99d7`.

## Result

Ten mapped programs used banks without the low WRAM and I/O mirrors that their
original data-bank setup requires. Product r15 moves them to compatible native
views, retaining the low 16 address bits and original program logic. Four
sampled actor families now match official cheap_demo behavior beyond entry:

- Room08B, custom32: the child appears and moves; r14 displayed only the parent.
- Room155, custom31: movement and departure match the source; r14 stays at
  `544/320` across all four held-position samples.
- Room087, custom20 and its existing1E/1F partners: sampled following and
  movement match under an explicit global-frame phase fixture.
- Room086, custom1C and its generated1D actors: sampled motion and generation
  match the source.

The main product also lacked sprite95 even though a separate pilot already
carried it. R15 installs the newest available official Boss Demo program.
It is byte-identical to the earlier7hero program used for the behavior replay.
The same actor95 identities, positions, velocities and selected state fields
match in four fresh room16B held-position samples. It remains absent from the
r14 control. The restored record is placed in seven rooms; the other six have
not received fresh r15 functional acceptance.

The existing A2 shop and purchase/save routes, and the hollow normal exit,
match r14 byte for byte at51 dump points:153 full WRAM/SRAM/VRAM comparisons.
All359 tests pass, including six new admission checks.

These are native mapping, selected actor and regression results. Full courses,
boss victories, all actor states, visible/audio acceptance and complete game
physics/timing parity remain open. R15 is rejected after the actual C0 loading
probe below; the component results do not establish a safe product target. The older r13 entry survey is not relabelled as
a fresh r15 survey.

## Why entry-only tests missed the defect

The affected main stubs begin `PHB; PHK; PLB`. Their subsequent absolute
addresses therefore use the module's program bank as the data bank. The source
programs ran in banks with low WRAM and register mirrors. BanksC0..FF lack
those standard mirrors. In the pinned runtime, `cpu_wram_offset` and hardware
register routing implement that distinction.

An init routine can still leave a plausible actor on screen, while the main
routine reads the wrong status or writes somewhere other than the intended
RAM/register. Room08B's parent-only r14 result and room155's frozen r14 actor
reproduce this problem. Their corrected child generation/movement, together
with unchanged program logic, qualify the mapping correction beyond a pack
mount or a first-frame actor list.

Native implementations may supply equivalent memory semantics through an
explicit adapter. This checkpoint uses available compatible mappings and
changes no CPU runtime or hardware timing implementation. It does not impose
cartridge or emulator compatibility as a product requirement.

## Reviewed changes

Plan: `config/native-content/lowmirror95-boss-r14.json`.
Preparer: `tools/prepare_native_lowmirror.py`.
The original recipes and r14 artifacts remain unchanged. New recipe variants
pin the same official source records, protected blocks and dispatch/call sets.

| Slot | Previous mapping | Corrected mapping | Runtime scope here |
| --- | --- | --- | --- |
|36|`C0E18D`|`9CE18D`|Static correction; diagnostic0A2 entry stalls before module use |
|32|`C1C32E`|`9BC32E`|Room08B selected parent/child behavior |
|31|`C2CD85`|`9ACD85`|Room155 held-position motion/departure |
|2D|`C3B30D`|`99B30D`|Static correction; the15D fixture does not instantiate it |
|2C|`C48000`|`988000`|Runs in05B; source trajectory comparison remains open |
|23|`C5D069`|`97D069`|Runs and generates a child in160; trajectory comparison remains open |
|20|`C6C9FF`|`96C9FF`|Controlled-phase room087 following/movement |
|1C|`C78E01`|`958E01`|Room086 movement and1D children |
|C0|`CB86D7`|`9486D7`|Static correction; callback execution remains unqualified |
|C1|`CCAE08`|`93AE08`|Static correction; callback execution remains unqualified |

The first eight records retain their existing type1 properties. Only init/main
bank bytes and necessary self-bank long-call operands change. The two type3
blocks are byte-identical to their originals, with their record/mapping banks
changed. Their current constructor is retained. C2 stays absent.

The preparer checks the parent ROM and records, old/new pack descriptors,
source records and programs, all declared relocations, low-address preservation
and compatible low-memory banks. Unexpected logic/data changes or unrelated
pack changes are rejected. The final ROM differs from r14 only in those ten
records and the explicitly recovered95 record. All room layouts, exits,
physics code, map events and save data formats are retained.

There are48 pack mappings. Every executable mapping now uses a bank with the
required low-memory mirrors; high-bank data-only mappings remain supported.
This does not prove every mapped program's complete dependency closure or
gameplay. The previous mapping-only and7hero-based integration candidates
remain separately reproducible as `demo11-native-lowmirror-v1` and
`demo11-native-lowmirror95-v1`.

## Official sprite95 integration

The newest retained code is in Boss Demo; Demo1-1 and demoOnly1 have a
placeholder. Boss and7hero records and the full protected program are equal.
Recipe: `config/native-content/sprite95-boss-module.json`.

- Protected block `20E40B`,5,144 bytes, SHA-256
  `20980e341c2877b32e286cb7053450ffcb54f1ee74f55f79f7a0b0b1236a6454`.
- Native view `A3E40B`, byte-identical program. Init `A3E41A`, main `A3E539`.
- Native record `013600003f0399641ae4a339e5a30000`.
- Placements:16B,16C,16D,16E,16F,172,1CC. No recipient layouts or other records
  in these rooms are replaced by source content.
- Admission:52 local entry states,2,086 instruction variants, the reviewed
  17-entry inline dispatch and the existing outside-call set.

Fresh source16B entry uses the older7hero input profile because the Boss image
does not reach16B under the tested simple entry fixture. The full code/record
equivalence is checked before using that behavior reference. Source and native
images, entry profiles and initial life pools differ. The95 actor comparison
does not equate whole-engine state or other actors. Actor8C has different
source/native movement in these probes; its native coordinates already match
the r14 control, so it is a separate identity/behavior review, not an accepted
source-parity result or a reason to overwrite the recipient's record.

## Evidence, fixtures and limits

Checker: `tools/qualify_native_lowmirror.py`.
Final report: `local/reports/native-lowmirror-r15-v1.json`, SHA-256
`423931b175dbd195f3f14bb4731cae18bc0a8aec82a881b7f12b160553c52df5`.

The tracked `native-lowmirror-*` scripts use explicit map, position, primary
destination, pipe-action and immunity fixtures. Room155 holds the player to
exercise the actor without the earlier probe's pit death. Room087 additionally
resets the two global frame counters at13/14 after entry. The unphased late
fall sample has a9-pixel playerY difference; equal controlled snapshots do not
qualify unrestricted physical/timing parity. Neither script writes actor AI,
HP, progression, completion flags or saved data.

The16 source/native component pairs compare selected active custom actor
identity/status/XY/velocity and the1504/151C state fields. Frame-dependent
animation fields and full source-engine state are not equated. Actual
resolutions and executed instructions are required in the corrected module
views. The four sprite95 pairs compare only the newly restored95 actor.
Both r14 defect controls remain active rather than merely timing out.

Final component captures are `low-r15-ROOM-native-VERSION` and
`low-r15-ROOM-cheap-VERSION`, with ROOM08b,155,086 at v1 and087 at v2.
Sprite95 captures are `low-r15-95-native-v1` and `low-r15-95-7hero-v1`.
Parent controls use `low-r14-{08b,155,95}-native-v1`.
Reference options: `snes9x_echo_buffer_hack=enabled`. Original source SRAM
dumps are2KiB; native dumps are32KiB. Source save parity is not claimed.

The unchanged routes are `low-r15-reg-{normal,menu,purchase}-v1` against
`forest-a2-r14-{normal,menu,purchase}-v1`. All named dump points in their
unchanged tracked input scripts compare in full, including boot and save/read
boundaries. This is native-to-native r14 regression evidence, distinct from
the different-image official source comparisons.

All359 existing/admission tests pass; log:
`local/reports/unit-tests-lowmirror-r15-v1.log`. Reproduction:

```sh
python3 tools/prepare_native_lowmirror.py
python3 tools/m1.py scaffold --target demo11-native-product-r15
python3 tools/m1.py generate --target demo11-native-product-r15
python3 tools/m1.py build --target demo11-native-product-r15
# Replay tracked inputs into fresh captures before checking them.
python3 tools/qualify_native_lowmirror.py --output local/reports/FRESH.json
```

Earlier diagnostics remain under `local/probes/low-bank-audit` and their own
capture directories. In particular, the0A2 load stall and uninstantiated2D
fixture are not failed gameplay acceptance reclassified as successful entry.
The160 and05B source/recipient random states and projectile trajectories differ;
their complete patterns are not qualified here.

Continue fresh coverage of the other95 rooms and real C0/C1 triggers, review
the still-missing C2 with matching source evidence, and refresh the current
missing/stale record census. Complete Forest routes, other-world identities,
earned Seven/mazo victories, music/graphics and full traversal remain open.

## Superseding C0 loading failure and diagnosis

The earlier held/teleported room16B probes skipped the loading windows even in
7hero. Their zero callback resolutions cannot qualify the type3 records.
A gradual position fixture now actually loads C0 and crashes r15. Preserve
`low-r15-callback-scroll-v1`, `low-r15-crash-locate-v1` and
`low-r15-crash-trace-v1`; the last trace uses M1_TRACE_FRAMES=2939:2943 and
`local/probes/low-bank-audit/c0-crash-v1.csv`. Inputs and exact binary identities
are recorded in those captures. No shooter/actor/timer/clear/save writes occur.

At frame2943 the recipient constructor returns an init pointer94:86E6. Its
caller31:803E jumps through that pointer. This address contains ASCII `MAIN`,
not an init program. Execution starts partway through the following main stub,
pulls an unrelated DB value, corrupts the return stack, and reaches BRK80:BF86.
The trace proves this failure; the prior constructor-continuation theory alone
did not establish the correct fix.

The official7hero loader10:AF87 classifies customC0..CF as shooters and D0..DF
as generators. The recipient31:80B1 uses E0..E5 for shooters and E6..E7 for
generators. A placed C0 is therefore incorrectly sent through normal actor
initialization. The normal constructor's byte versus word implementation is
not the primary cause of this observed crash. No constructor transplant is
justified by this trace.

An isolated experimental descendant, `demo11-native-type3-shooters-v1`, adds a
192-byte bank92 adapter with three bounded hooks. It classifies only placed
customC0/C1 as shooters, assigns reserved shooter IDs B0/B1, and resolves those
IDs to the original C0/C1 main records. Existing native shooter IDs81..86,
generator dispatch and normal E0 Seven child records retain their meanings.
The source modules, eight shooter slots, positions and countdown code remain
unchanged. This explicit representation difference requires paired behavior
checks; the experimental target is not promoted by its successful build.
C2 remains absent. See `config/native-content/type3-shooters-v1.json`.


The adapter now has a [bounded qualification report](native-type3-shooters-restoration.md):
actual C0/C1 execution/generation,20 exact normalized C1 actor samples, and45
native r14 regression dump points with explicit inactive-stack exclusions.
This advances the experiment; it does not promote r15 or replace r14.
