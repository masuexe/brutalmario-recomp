# Native Seven Koopalings entry

The isolated PC target `demo11-native-seven-font-entry` now loads the official
Boss Demo's Seven Koopalings program and resources from immutable external
packs. It displays the transformation, Japanese instructions and WP interface,
then accepts ordinary buttons and begins combat. This is an entry/opening
checkpoint. The complete fight, later child actors, music, ending, progression
and saved completion remain open. It does not promote the accepted head.

The authoritative donor remains `boss.ips` applied to the pinned SMW base,
byte-for-byte identical to both supplied normalized Boss ROMs. See the
[source inventory](native-boss-inventory.md). Original ROMs, saves, captures,
the ordinary recipient banks and the preceding A5/B6 content remain intact.

## Mapping and adaptations

The module recipe is `config/native-content/seven-module.json`, extended by
`config/native-content/seven-font-module.json` for the fight-local font.
`tools/prepare_seven_module.py` verifies the donor against the authoritative
patch, checks source identities and prepares packs with an unapplied recipient
plan. `tools/native_seven.py` applies that plan only to an isolated descendant,
copies the cumulative packs and configures the PC runtime.

| View | Contents | Size |
| --- | --- | ---: |
| A2 | Seven Koopalings protected program and explicit font adapter | 28,723 bytes |
| A6 | Twelve compressed graphics streams plus raw Japanese GFX2A | 25,213 bytes |
| A5 | Previously qualified sprite `9E` code | 1,291 bytes |
| B6 | Previously qualified Grassland Star graphics | 3,001 bytes |

The source program begins at `$22:8000`, protected size 28,478 bytes, SHA-256
`d070d644b5da61d4150e58f4d6603a0ccbe5d0c37b19e7a00c8ffc2d9bb1d757`.
The module retains the low 16 bits and maps the program to `$A2:8000`.
The ordinary bank `22` still contains the recipient's bytes. Low WRAM mirrors
remain available because the mapped banks are system-bank mirrors.

Three explicitly bounded inline JSR tables are reviewed:

| Table | Entries | Indirect dispatcher | Selector |
| --- | ---: | --- | --- |
| `228095` | 35 | `228115` | `$1504,x` |
| `228118` | 23 | `2281C8` | `$C2,x` |
| `22BB7B` | 21 | `22BBF7` | `$7FFFA1` |

These resolve the previously reported indirect-dispatch sites. Traversal seeded
from these tables and init/main now follows local absolute JSR and self-bank
JSL entries with their decoded M/X states: 366 entry states and 10,353 instruction
variants. No further indirect site is admitted by this recipe. This is bounded
static analysis, not a whole-program dataflow or outside-helper closure proof.

All 39 source-bank long-call sites are adapted explicitly from bank `22` to
`A2`. They include the inline JSL instructions following calls to `$10:D8D0`:
that shared scheduler copies the instructions into executable WRAM for later
execution. Updating only direct calls would leave those callbacks pointing at
the recipient's unrelated bank `22`. Their call sites and complete original/
adapted bytes are pinned in the recipe.

Twelve graphics resources receive namespace IDs `FE0`–`FEB`. Their original
IDs, compressed/decoded hashes and bounded native addresses are pinned. The
recipient's eight room `0FF` graphics selections and the module's eight dynamic
selection words are adapted explicitly. The pointer slots were unallocated
and unreferenced by the scanned room metadata; this is not a general claim
about every possible indirect resource consumer.

The recipient keeps its own generic SpriteTool constructor and initialization
hooks at `0187A7` and `07F785`, which intentionally differ from the donor.
It also keeps its death behavior. Reviewed shared byte ranges are pinned in
both images; no donor engine or map is copied over the recipient. Full
compatibility beyond the exercised opening still needs qualification.

`recomp/native_seven.c` provides four fixed views with independent backing.
There is no room/PC-dependent bank replacement. All four packs and the exact
recipient image are required by hash. M1 and the practice launcher supply and
verify them, reject stale receipts, and prevent reference-host launches for
this native-only target. Builds forbid AOT nodes in `22/A2`, `25/A5`, `26/A6`
and `36/B6`; new module instructions use the interpreter fallback.

## Demo 1-1 font difference

Demo 1-1's English font overwrites the Japanese glyphs used by the older Boss
Demo's text. This is an existing release difference, not a recomp defect.
The initial native prototype consequently displayed the donor's Japanese tile
indices with English glyphs.

The font extension extracts the official donor's GFX2A, whose decoded 2,048
bytes exactly match the reference fight's VRAM range `9000`–`97FF`. It appends
those raw bytes to A6 and adds a pinned adapter at `$A2:F000`. The normal Boss
init's final `STZ $14AF` runs in that adapter, followed by an ordinary guest DMA
to VRAM word `4800`; A and P are preserved before returning to the original
init RTL. The alternate init branch retains its original behavior.

This loads the Japanese font for this fight without changing the recipient's
global GFX2A pointer or font bytes. Eight native and donor opening samples have
the exact expected GFX2A bytes in VRAM. This does not claim that every font,
HUD tile, palette or pixel is identical between the different releases.

## Identities

| Item | SHA-256 |
| --- | --- |
| Parent ROM | `3077bb3df00a1f26c0728deea091048be792ac1e09af9886cfdb5e36f8d05bb1` |
| Native entry ROM | `c0cf157839e52b4571615c1aacbb5cc989378f14529645107f06fd31a94d4e64` |
| Native binary | `09a5bab5bfb7f371d072f91f85a7b6a9a83491c88815f2565a1cbfdc81b91499` |
| A2 code pack | `e30de7380bea73d18e5eff3b79d71976714a3cbe8235076361968d5776d8f46f` |
| A6 graphics/font pack | `e6c3fcf9b3e304b8b93ab593c5a6d971a430b0928888507fba7bc68a4e8c9078` |

The earlier `demo11-native-seven-entry` prototype has the same recipient ROM
hash but different external code/resources and feature identity. A ROM hash
alone does not identify native content. That prototype and its captures remain
exploratory; use the font target and its complete receipts for this checkpoint.

Preparation receipt:
`local/native-modules/demo11-native-seven-font-entry-final/preparation-receipt.json`,
SHA-256 `2a879d99634f744c14f93c26790f411f7f878cfaedb0c728f93bd4294d406713`.

Qualification report: `local/reports/native-seven-entry-final.json`, SHA-256
`aeb2095d8e20bbf4cea6ae61a7e5850cce529b329517633dcce2303b8ab4975c`.

## Verification

`tests/seven_module_boundary_test.c` executes actual donor init and scheduler
bytes through the pinned 65816 interpreter and the cumulative native resolver.
It checks both init branches, copied RAM callback bank bytes, execution of the
copied callback, low WRAM access, synthetic NMI/RTI interruption, return stack
and DMA register programs. Its MMIO bus records writes; it does not simulate
the PPU or prove pixel output. Actual font output is checked separately in the
native game captures. Python tests reject missing deferred-call adaptations,
unknown dispatches, changed recipient hooks and namespace collisions, and
exercise missing/corrupt packs through the real loader.

All 157 Python unit tests passed, including these five new tests. The full-run
log is `local/reports/seven-unit-tests.log`.

Game captures:

- `local/captures/seven-opening-v1-{donor,native}` use tracked opening scripts.
  Both have eight samples in room `0FF`, with matching active custom actor
  slots and primary/secondary phase states. The two paused transformation
  samples additionally match all 15 sampled actor fields. Other samples have
  timer, position or random-state differences; motion parity is not claimed.
  Ordinary B/A/X/Y inputs dismiss the instructions and exercise the opening.
- `local/captures/seven-regression-v1-{star1,boss,lifts}` match the historical,
  identity-verified `native-sprite9e-final` native controls in **590 comparisons**
  across 59 dump points. Comparisons cover WRAM, VRAM, CGRAM, OAM, SRAM,
  framebuffer, APU trace, PPU writes, registers and DMA trace. The lift route
  includes the previously qualified transitions and native death/re-entry.
- Five `seven-opening-v1-reject-*` frontend captures reject missing code,
  missing graphics, corrupted code, truncated code and extended code.

The opening uses explicit map/node and pipe-action fixtures, fresh saves and
no invulnerability, forced movement or completion writes. It is not ordinary
unassisted traversal. Reference options explicitly enable the echo-buffer hack.
Receipt, ROM, script, binary, feature and dump identities are checked by
`tools/qualify_native_seven.py`. The ordinary banks and parent content are
preserved; no same-image or audible-match assertion is made.

Earlier exploratory captures remain intact. In `seven-entry-v1-native`, the
pipe-action fixture ran before level load and was discarded; the route stayed
in `146`, so that capture does not qualify Seven Koopalings entry. The corrected
`seven-entry-v2-native` reached `0FF` but still used the Demo 1-1 English glyphs.
Only the final font target's opening captures qualify the entry here.

## Open dependencies and next action

The longer `attack1200` sample is intentionally outside the accepted opening:
native reaches room `174`, while the donor remains in `0FF` at a subsequent
phase with custom `6A` actors. This is preserved failed evidence for later flow,
not a fight clear or a qualified return/death cycle. It does not establish a
complete causal explanation for the divergent transition.

The source at `$22:84D5` explicitly creates custom sprite `6A`. That dependency
was absent from the earlier placed-sprite inventory:

- Newest retained Boss Demo `6A`: record
  `013610003bab18401dc21e65c21e0000`, protected block size 3,385 bytes,
  SHA-256 `8301000a2fed1e9c534958f06ef1d82eeb7e62f92cce9ef674b1f369c4fd0dbb`.
- Current restored `6A`: record `013610003b8b1840f4be203fbf200000`,
  protected size 3,376 bytes, SHA-256
  `03ea43204426c9e84df053724e577bfd346a07e1d98a9da281e4457b1f94518c`.
  It is placed in `0D8`, `0E2`, `0E3`, `0E4` and must not be overwritten globally.

Next, review the newer child program and its resources, namespace the Boss
Demo's dynamic child dependency, and retest the longer phase transition.
Preserve the existing `6A` actor and both qualified external-content pilots.

Music also remains open. The mapping reference identifies legacy `33` to modern
`AC` for Last Battle, but the actual room data contains `40 60 33`. Trace the
effective commands through both audio engines before choosing a patch; a table
number or a surviving selection byte is not an audible match. No music change
or audio acceptance is included here. Full fight phases, ending, map return,
real death/re-entry for this Boss and saved completion remain to be qualified.

## Reproduction

```
python3 tools/native_seven.py
python3 tools/m1.py --target demo11-native-seven-font-entry scaffold
python3 tools/m1.py --target demo11-native-seven-font-entry generate
python3 tools/m1.py --target demo11-native-seven-font-entry build
python3 -m unittest discover -s tests -p test_seven_module.py -v
python3 tools/qualify_native_seven.py --output local/reports/YOUR_FRESH_REPORT.json
```

Skip scaffold if its isolated experiment already exists. The last command
rechecks the recorded final captures without replacing them. For fresh captures,
run M1 native with `recomp/inputs/native-seven-native-opening.script` and the
reference probe with `recomp/inputs/native-seven-donor-opening.script`, using
fresh `PREFIX-native`/`PREFIX-donor` directories. Collect the three regression
scripts in fresh directories as well, then supply both prefixes to the qualifier
and use `--collect-rejections` once for the fresh opening prefix.

The practice launcher accepts `--restoration demo11-native-seven-font-entry
--room 0xFF --show-room`. This exposes an experimental opening for investigation;
it is not an integrated overworld route or full-game completion checkpoint.
