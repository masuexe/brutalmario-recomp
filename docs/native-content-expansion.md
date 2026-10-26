# Native content expansion

## Delivery decision

The user requires the completed game to run on PC. A single SFC image and
emulator compatibility are not acceptance requirements. The requested scope
includes Demo 1-1, demoOnly1, cheap_demo, 7hero, boss and mazo content. Preserve
the existing official donor chronology and newest-available-code policy.

Use external content packs and explicit native runtime integration to remove
the cartridge storage constraint. Preserve the working engine and restoration
recipes. This is a direction decision, not a completed loader implementation
or a claim that every donor is complete or compatible.

The [first external graphics pilot](native-content-pilot.md) now implements a
bounded native data-bank split with matching entry/movement and unchanged Boss
route captures. Executable-module expansion is the next unqualified boundary.

## Frozen comparison checkpoint

- Target: `demo11-sprites-orphan-cleanup`.
- ROM SHA-256: `eccde6612343e9513e6903264f21b80d3a9a02d7f11199100e5907531232ff40`.
- Native binary SHA-256: `d79f5940d04f2a40ae82cc30c858c74f10d11c71ab201269f8a638b28e815985`.
- Recorded whole-line suite: 78/78; these are prior results, not a new run.
- This decision does not promote the chain head or alter user saves.

See the [space saturation investigation](demo11-sprite-space-saturation.md)
for the failed allocation trials. Unknown references make raw-data relocation
unsafe. A large protected RATS block is not evidence of unused space. Code
compression ratios, reclaimable capacity and future boss sizes need measurement.

## Proposed architecture

Store content outside the cartridge image, with manifests pinning donor hashes,
source ranges, payload hashes, dependencies and reviewed adaptations. Identify
content by source version and component identity; original room, sprite and
music numbers are local to each version. Generated packs stay under ignored
local storage; tracked recipes and tooling reproduce them.

Provide separate interfaces for resource loading and executable modules.
Resources should enter the existing decode, graphics, collision and audio
paths where practical. Executable modules need an explicit address and dispatch
contract, including bank-local references, shared calls and low WRAM mirrors.
The current sprite installer deliberately enforces those constraints in
`tools/restore_star_world_1.py:restore_sprite`; an external file alone does not
remove them. Keep interpreter execution available for newly mapped code and
qualify AOT only against the matching module bytes.

Choose a mapping only after reviewing the pilot's dependencies. Do not assume
an unused bank, silently replace a whole donor engine, or swap cartridge bytes
solely from the current room number. Multiple actors, shared routines,
interrupts and retained pointers can need different content concurrently.
External storage removes the total cartridge budget; each execution window
still needs a bounded, conflict-free mapping. More content may require further
loader or native-code adaptation.

The final integration retains one intended progression and save model, with
explicit routes to recovered content. A menu launching separate donor versions
is a separate feature and does not establish integrated restoration.

## Inspected integration boundaries

The local upstream checkout is clean at the pinned SNESRecomp revision
`a6be9756285f26ccc74539c811d4d23d57d8c33d`.

- `runner/src/snes/cart.c`: `cart_getRomPtr` resolves cartridge pointers;
  `cart_readLorom` uses it for cartridge reads.
- `runner/src/common_rtl.c`: `RomPtr` delegates to that resolver. Project
  runtime overrides also contain this path.
- `runner/src/cpu_state.c`: CPU reads use `RomPtr`; ROM word reads access
  `p[1]` directly. A byte-only hook cannot handle all overlay boundaries.
- `runner/src/snes/dma.c`: DMA and HDMA use `snes_read`. Audit these alongside
  direct pointers, interpreter fetches and generated code before claiming
  complete mapping coverage.
- `runner/src/cpu_state.c`: dispatch and mirror resolution, including
  `cpu_aot_rom_mapping_matches`, depend on cartridge identity and mappings.
  Changed executable bytes must never reuse an incompatible AOT routine.
- `docs/MSU1.md` and `runner/src/snes/msu1.c`: data streaming already exists.
  No MSU-1 requirement is introduced for this PC-only plan.

These observations identify work areas; they are not an exhaustive runtime
audit or a validated module design. Keep upstream checkouts unchanged and use
the project's pinned runtime patch mechanism for any implementation.

## First implementation milestones

1. Create an isolated native target descending from the frozen checkpoint.
   Externalize a known, bounded resource with identical bytes at first. Record
   input, manifest, pack, runtime patch, build and capture identities. Demonstrate
   that reads actually use the pack and reject a corrupt or mismatched pack.
2. Compare the exercised resource's decoded output and gameplay against a fresh
   native control. Cover the access boundaries used by the implementation and
   run unchanged-content regressions. This qualifies external delivery only;
   it does not yet prove expanded executable capacity.
3. Add a currently blocked custom sprite with its dependency closure through
   the chosen executable-module contract. Verify source behavior, spawning,
   gameplay, death/re-entry, room transitions, mapping lifetime and old content.
4. Port one complete boss, then qualify the fight, ending, map return and save
   persistence before scaling to other releases.

Use original donor emulation and existing captures as behavioral evidence when
their identities support the claim. Native-only candidates need no matching
emulator image. Test their integration in the native host, distinguish donor
differences from runtime defects, and preserve explicit limitations. A successful
boot or interpreter/AOT agreement alone does not prove a correct course or boss.

The first resource-delivery milestone is qualified separately in the
[pilot report](native-content-pilot.md). The next concrete action is to select
a blocked custom sprite and review its executable mapping and dependency
closure. The fixed graphics bank must not be treated as a general code loader.
