# Recompilation feasibility and M1 experiment

Initial assessment on 2026-10-15, retained below as the experiment plan. **M1 has since reached native boot and a scripted level segment; fidelity and boss acceptance remain unproven.** See [m1.md](m1.md) for pinned source revisions, actual commands, measured results, and limitations.

## Verified upstream boundaries

- The [SNESRecomp README](https://github.com/RetroPortingToolKit/snesrecomp) describes 65816-to-C compilation, modeled hardware, and interpreter fallback. It lists standard LoROM as supported and ExLoROM as unsupported. The candidate Demo 1-1 is 4 MiB with map byte 0x20; expansion alone does not imply ExLoROM.
- [Project setup documentation](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/docs/GAME_PROJECT_SETUP.md) requires game-specific frame driving and interrupt delivery after generation. Use a separate local experiment directory and disable publishing/remote creation; do not execute the wizard's default end-to-end flow blindly.
- The [LLE-first analysis contract](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/docs/LLE_FIRST_ANALYSIS.md) models PC and M/X states and retains LLE for unproven execution. This supports the experiment, not a claim that the fallback bridge works for Brutal Mario.
- Selected reads of [cpu_state.c](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/runner/src/cpu_state.c) and [cart.c](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/runner/src/snes/cart.c) show CPU routing to WRAM, hardware, and cartridge memory. This is not a complete runtime audit.
- The [SMW project README](https://github.com/mstan/SuperMarioWorldRecomp) and [regen.sh](https://github.com/mstan/SuperMarioWorldRecomp/blob/main/tools/regen.sh) establish game-specific configuration and runtime integration. Swapping ROMs cannot establish reuse of stock function boundaries, HLE, or audio assumptions.
- Current [SNESRecomp](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/LICENSE) and [SMW](https://github.com/mstan/SuperMarioWorldRecomp/blob/main/LICENSE) license files say PolyForm Noncommercial 1.0.0; dependencies have separate notices. No upstream code was copied into this repository.

Initial limitation: the M0 browser references were mutable and unpinned. M1 resolved this by downloading local checkouts and recording exact commits in `config/upstreams.json`. Source inspection also corrected an outdated assumption: the current analyzer is Rust-only, and the current scaffold supplies a shared beam-aligned frame driver. Some upstream design documents retain older status text; use the pinned implementation and execution evidence in [m1.md](m1.md).

## Risks and open questions

| Issue | Evidence / status | M1 response |
| --- | --- | --- |
| IPS alignment | Headerless base; Demo 1-1 uses +512 coordinates | Pin hashes and preparation steps; retain original checksum fields |
| Dynamic entry points and M/X | Custom ASM is present; exact target behavior unknown | Analyze vectors and record unresolved entries/fallbacks; no silent stubs |
| WRAM code | Supplied levelasm constructs instructions; target correspondence unproven | Obtain target traces and test execution/return bridging |
| Frame and NMI/IRQ delivery | Required by upstream integration contract | Validate boot, interrupts, and frame progression separately |
| PPU/APU compatibility | Cheap Demo notes older-core dependencies; Demo 1-1 unverified | Replay a reference run and find the first divergence |
| Source correspondence | Packages differ and lack dependencies | Require byte/address correspondence before using symbols |
| Excessive interpretation | Fallback may run a game without meeting the recompilation objective | Report AOT/interpreter coverage and time separately |

## Concrete M1 experiment

1. Obtain and pin SNESRecomp and the SMW reference checkout, licenses, dependencies, and build-tool versions. Read actual CLI help, configuration parsers, and examples before recording exact commands. No checkout is available yet, so no untested scaffold command is presented as verified.
2. Add a local ROM preparation tool: verify base/IPS hashes, add a 512-byte prefix to a copy, apply only `1-1.ips`, remove the prefix, and write `local/roms/demo-1-1.sfc`. Refuse to overwrite input files. Require 4,194,304 bytes and the candidate SHA-256 in compatibility.md; a repeat build must match. Do not merge historical patches.
3. Verify title, game start, and a level segment in a reference core. Save inputs and initial state. If this fails, investigate alignment/compatibility before expanding static analysis.
4. Create `local/experiments/demo-1-1/` with enhancements disabled. Seed actual RESET/NMI/IRQ vectors rather than importing all stock SMW configuration. Record analysis duration, entry/variant counts, unresolved indirect targets, WRAM execution, and fallback use.
5. Build the native host, verify boot and frame/interrupt delivery, then enter a level. Resolve necessary dispatch configuration from traces; do not edit generated C to conceal gaps.
6. Select one custom boss actually reachable in Demo 1-1, record the route, and exercise a full attack cycle. Do not assume 7hero or Marx is present.

## Acceptance and stopping criteria

- Preparation: unchanged inputs, reproducible output hash, recorded commits and dependencies.
- Analysis: convergence or actionable failure within a first-run budget of 10 minutes and 4 GiB. Save logs and reduce scope if exceeded. These are experiment limits, not performance estimates.
- Boot: a native executable reaches gameplay and runs at least 3,600 frames with working input and no unexplained fatal diagnostics. Compilation alone does not pass.
- Gameplay: complete a level segment and a custom boss attack cycle. Compare logic, video, and audio against the same-input baseline; document differences and fallback coverage.
- If mapping, frame driving, or the fallback bridge blocks progress, or the same failure persists after two evidence-based repair attempts, produce a focused reproducer and assess framework changes or another route. Do not substitute indefinite attempts or silent HLE for a result.

Toolchain pinning, ROM preparation, initial code generation, native compilation, and boot smoke tests are now implemented. The next work is isolating observed reference/native divergences before expanding static coverage or testing a custom boss. Historical content integration remains deferred until Demo 1-1 is stable.
