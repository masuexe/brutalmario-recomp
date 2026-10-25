# Cartridge space and the boss expansion question

Date: 2026-10-26. The user asks for an expansion scheme that can hold the 7hero
boss and the mazo boss without a 4 MB limit.

## Hard limit

The project runs on the SNES memory map, in the native recompilation host and in
the reference Snes9x host. LoROM maps at most 4 MB of cartridge data:

- banks `00`-`3F` and their mirrors `40`-`7D` map `8000`-`FFFF` to ROM,
- banks `7E` and `7F` are WRAM,
- the remaining banks mirror the same data.

There is no spare address range for a larger cartridge on this mapping. An
8 MB ExHiROM conversion would reassign every bank reference in the hack. The
reference core support is also uncertain. The project rejects this option.

## Measured space on the current chain

Source: `local/probes/capacity-audit.py` on `demo11-sprite-windows`.

| Item | Bytes |
| --- | ---: |
| Zero bytes in the pinned base ROM | 1,366,994 |
| Bytes in RATS blocks added by this line | 641,650 |
| Changed bytes against the base | 482,104 |
| Zero bytes left in the chain end | 820,765 |
| Free bytes inside one bank below `0x40` | 135,284 |
| Largest contiguous free run | 21,275 |

The base figure counts every zero run of 256 bytes or more, so it is an upper
bound. The chain consumed about 640 KB. About 800 KB remains, but the free
ranges are small and the sub-bank ranges are the scarce resource for custom
sprite code.

## Boss content budget

A later boss port needs these parts:

| Part | Typical size |
| --- | --- |
| Boss sprite code blocks | 2 KB to 12 KB |
| Boss graphics streams (LZ2) | 4 KB to 40 KB |
| Level data | 2 KB to 12 KB |
| Music group | 8 KB to 20 KB |

Two bosses therefore need roughly 40 KB to 160 KB. The remaining space covers
this range with margin. The real constraint is not total size but the aligned
window for sprite code: the last five sprite ports needed 16 graphics block
relocations to free five windows.

The suite now runs `tools/check_space_budget.py`. The guard fails when
the total free bytes fall below 500,000, the aligned free bytes below
60,000 or the largest run below 16,384.

## Options

### 1. Budget, dedup and relocation (recommended)

- Keep one allocator service for every new recipe. It records every claimed
  range and every RATS block.
- Deduplicate identical blocks. Many donors share the same engine and graphics
  blocks.
- Relocate our own graphics and music blocks when an aligned window is needed.
  `apply_relocations` already does this for the Star World graphics, and the
  Star World rendering stays byte-identical.
- Add a capacity guard to the suite. The guard fails when the free bank-aligned
  space falls below a reviewed threshold.

This option keeps both hosts valid and keeps reference parity.

### 2. Native-only virtual cartridges (unlimited, native host only)

The delivered product is the native executable. The runtime can reserve one
unused bank range as a window and serve its reads from an embedded asset pack.
Guest code reads a normal 24-bit address, and the runtime returns the expanded
asset bytes. This removes the 4 MB limit for native play.

Costs and limits:

- The reference host cannot run the expanded content. Reference parity for
  those assets is impossible.
- Validation must use semantic checks (WRAM, sprite state, audio) or a
  temporary packed validation ROM built when the content fits.
- The runtime must intercept reads in the window bank and handle LZ2 streams
  that cross the window boundary.

This option is feasible in this project because the runtime is ours. It is not
free and it weakens the reference-parity argument. Use it only when option 1
runs out.

### 3. ExHiROM or bank-switched cartridge (rejected)

Both need a full bank remap of the hack or new cartridge hardware emulation.
They break the reference host and the current recipe model.

## Decision

Continue option 1. Measure the real 7hero boss and mazo boss assets before
claiming a shortfall. Add the capacity guard to the suite. Revisit option 2
only when a measured boss port does not fit.

## Limits

- The free-space figures are upper bounds. Zero runs inside data blocks count
  as free.
- Boss sizes are estimates until the donors are measured.
