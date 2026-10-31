# Mazo primary entry and completion ownership

Experimental candidate `demo11-native-mazo-primary-entry-v3` descends from
`demo11-native-mazo-messages-v2`. The accepted product remains r14. This work
qualifies an assisted entry/goal/save boundary, not an earned Mazo victory or
ordinary traversal through room190.

## Reproduced product problem

The default r14 map hook writes `B4` to node `D1F0`, replacing the ordinary
translevel `30`. It enters room190 but changes the course/save identity as
well. Capture `mazo-node-save-boundary-v1` enters through that actual main-map
node, then uses an explicit primary pipe-action fixture to skip room190 into
room192. Two ordinary B presses close the directly entered messages. Ordinary
right input touches the goal sphere. No completion, goal, translevel or save
bytes are written by the script.

The real goal returns to the map with `$1F56: 0F -> 8F`, the location indexed
by `1EA2+B4`. That address also overlaps the backup WRAM flag block at
`1F49+0D`; its value alone cannot distinguish the goal write from flag copying. The original node30 completion byte `$1ED2` and its SRAM copies
remain zero. The exit count remains zero. B0 independently sets its original
hardcoded `$1EAF` flag, which is saved. The old control cannot establish a
correct Mazo course30 save.

The recipient's map routines at `04:96BE..96CE` and `04:9950..995E` read
`7ED000+node`, then update `1EA2+translevel`. This explains why changing the
node's level selector also changes completion ownership. It also explains the
[old room126 fixture's wrong-owner save](world2-course126-route.md).

## Bounded loader adaptation

The candidate keeps the original node value30. A generated target capability,
`BM_MAZO_PRIMARY_ENTRY`, suppresses the legacy B4 table edit only for targets
that select `BM_MAZO_PRIMARY_ENTRY_PACK`. Other targets retain their existing
compiled branch. This changes source identities; historical captures retain
their original build receipts and are not relabelled as current-source runs.

One four-byte hook replaces the `JSL $13EDA2` call at `05:D8B1` with a call
to a 70-byte immutable program at `88:8000`. The adapter first calls the same
existing helper. It saves A/P and checks original context `$13BF=30`, player
selection `$0DD6=0`, main map `$1F11=0`, and map coordinates `(0100,00F0)`.
Only that entry selects loader locals `$17BB=90`, `$0E=90`, and return A=01.
The caller's original `STA $0F; REP #$30` remains in place. The existing loader
then writes room0190 and obtains its normal layouts, sprites and metadata.

The adapter never replaces recipient room10C's tables and never writes
`$13BF`, node assignments, completion flags or saves. X/Y and hidden B
survive. Bank88 has the needed low WRAM mirrors. All inherited programs and
native adaptations remain selected. The original secondary-entry jump at
`05:D83B` still reaches the intact `REP30` at `05:D8B7`.

## Rejected early prototype

V1 hooked `05:D8A2` and changed the early accumulator selector. The existing
Lunar Magic helper at `13:EDA2` later reconstructs `$17BB/$0E` from `$13BF`,
overwriting that early choice. Capture `mazo-node-save-boundary-v2` does not
prove a correct room190 entry. Its subsequent pipe fixture can still reach
room192, which would hide the failed primary adaptation if only the goal were
checked. V1 recipes, packs, build and capture remain separate evidence.
`legacy_program()` and `build(legacy_recipe)` reproduce its payload and ROM.

V2 hooked the local selector after that helper. It entered190 correctly, but
covered the shared `D8B7` branch entry. Secondary transitions jumped into the
replacement instruction operand and reached BRK at `05:D841`. Captures v3/v4
preserve that failure. `program_v2()` reproduces it. V3 wraps the complete
helper call instead, leaving the secondary branch entry intact.

The final route waits for playable mode14 before sampling the actual primary
room. It therefore cannot accept that prototype's mode13/room10C sample as a
successful entry.

## Verification and remaining gates

`tests/test_mazo_primary_entry.py` compiles the pinned real 65816 interpreter.
It models the unchanged helper return and compares the original caller
boundary with the adapter across 28,672
course/flag/scope cases, including each rejected guard, both index widths,
decimal/carry flags, hidden B, X/Y, data bank, stack and all non-stack memory.
Admission rejects an altered scope, an unmirrored bank and an altered hook.
A separate check preserves the actual secondary jump target and its REP30.

The route and checker are:

```sh
python3 tools/prepare_mazo_primary_entry.py
python3 -c "import sys; sys.path.insert(0,'tools'); import native_sprite_gap; native_sprite_gap.prepare('demo11-native-mazo-primary-entry-v3')"
python3 tools/m1.py --target demo11-native-mazo-primary-entry-v3 scaffold
python3 tools/m1.py --target demo11-native-mazo-primary-entry-v3 generate
python3 tools/m1.py --target demo11-native-mazo-primary-entry-v3 build
python3 tools/m1.py native --target demo11-native-mazo-primary-entry-v3 --script recomp/inputs/mazo-node-save-boundary-settled.script --capture FRESH
python3 tools/qualify_mazo_primary_entry.py --candidate FRESH --output local/reports/FRESH.json
```

The checker reconciles inherited recipes/packs/patches, validates installed
payloads and current candidate identities, and checks actual native execution
of bank88. The r14 control is explicitly a frozen earlier-source build with
its own exact ROM, binary, build receipt, script and completion log.

B0's hardcoded
course0D flag still needs its recipient-world meaning resolved. Ordinary map
travel, room190 traversal, earned fight, complete world progression and audible
music remain open. No product promotion follows from this boundary alone.


## Verified boundary result

Current candidate capture `mazo-node-save-boundary-v5` reaches playable room190
with `$13BF=30`, follows the declared pipe fixture into192, dismisses the
messages and touches the real goal sphere (`1493=F0`). It returns to the map
with course30 `$1ED2=80`. Both SRAM copies (`0030`, `01DD`) and backup WRAM
`1F79` hold80 after the real goal and reset/File A reload. The current-runtime
control `mazo-node-save-boundary-control-v1` reaches190 with contextB4 and
leaves those course30 bytes zero. Both use the same settled-entry input.

The native exit count remains zero on both builds. The loaded recipient event
byte `$1DEA` is `FF`; the official Mazo ending capture has `1DEA=30` and an
exit-count increment. The primary loader reads that event from its existing
recipient course table at `05:D608+13BF`. This candidate preserves that table.
It does not copy the donor event30 onto the recipient world or claim that the
complete Mazo map event/save flow is integrated. B0's course0D flag also stays
unchanged, including its backup copy at1F56.

The failed first-playable-frame pipe fixture (`mazo-node-save-boundary-v3`)
and the settled retry (`v4`) both expose V2's shared-branch bug; extra waiting
does not repair it. V3 uses the same settled input and passes. The project
preserves both failed captures and their exact inputs.


## Retained content and paired regressions

The candidate retains45 recipes,60 packs,66 explicit patches and all native
adaptations from the qualified message parent. It adds one70-byte pack and
one four-byte hook (61packs/67patches). All installed payloads and selected
source programs reconcile. The old parent manifest header is unchanged. A
separate current-runtime control target is built with `--control`, preserving
the original parent builds and their evidence.

Fresh `mazo-primary-reg-v1-{126,child,purchase}-{candidate,control}` captures
provide49 paired samples:10 room126 clear/save/reload,19 Seven child/death/
re-entry,20 funded shop purchase/return/save/reload. All147 full-file SRAM, VRAM and
framebuffer comparisons match byte-for-byte. WRAM allows only the intended main-map
node byte and29 explicitly enumerated inactive stack addresses, always below
the compared stack pointer. It does not claim full WRAM byte equality.

One Seven sample, `child/fight180`, has an additional decompression cut-point
difference. Timing receipts give candidate PC `00:B933` and control `00:B987`,
with22 master ticks between the sampled clocks. The control has already fetched
source byteFE from the shared pinned A6 resource at8138; it has not yet advanced
X/input pointer or returned from the read-byte helper. Its active return address
is B932. The candidate has advanced to8139 and returned, with the same decoded
output and full VRAM/framebuffer. Replaying the original `INX; BNE; STX8A; RTS`
makes the CPU and pointer states converge exactly. The real-interpreter unit
harness independently executes those four instructions and verifies the result.
The checker pins their actual ROM bytes, validates the source byte, return
address, modes and clock bound, and permits this one identified sample only.
All other sampled CPU register sets match directly. This is bounded functional
regression evidence, not exact instruction-phase or audio-clock parity.

The full unit suite passes417 tests (`local/reports/unit-tests-mazo-primary-entry-v3.log`).
The three focused tests pass again with the decompressor replay assertion.
Negative probes reject a missing course30 flag, missing backup SRAM flag,
missing actual goal, gameplay-coordinate mutation, active-stack mutation and
an invalid decompressor return address. The current room192 message tiles,
common-precision text pixels and Japanese font also match the pinned official
Mazo source; English font returns after close, map return and reset.

- Candidate ROM SHA-256: `28da206c0bfeb7c7ed9a9c10a3eadb6377e128edb132b6984e725fb1de497ff5`.
- Candidate binary SHA-256: `11b54a24e8f3eb9eb77258788ac09ba75f680bafcac2682051f0927e929e6c4b`.
- Native code SHA-256: `210836ed144151a0e0b2ac6421f70c7a055dcbfc3b7a7cf4d57e7a6682ef6850`.
- Final report: `local/reports/mazo-primary-qualified-v5.json`.
- Report SHA-256: `a93ea0b129f9719f71523aa408d7eb1e84cd9799680361fbc814a352aaf7c14e`.

The primary adapter executes58 instructions in the successful ending capture.
The accepted r14 ROM and binary retain their release-note hashes. Source ROMs,
accepted builds, saves and earlier captures remain intact. Next, reconcile the
source00D corridor (relocated to183), its native recipient00D course and the
Mazo event mapping before accepting complete world progression.
