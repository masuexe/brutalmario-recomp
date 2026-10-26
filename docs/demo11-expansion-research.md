# Expansion research: what other projects do

Historical assessment. The [native content expansion plan](native-content-expansion.md)
supersedes the recommendation below: the user requires PC delivery only.
The pinned SNESRecomp revision already includes the MSU-1 data implementation
and register routing; the statement below that it must be added is incorrect.
This does not establish a working Brutal Mario data-streaming driver. MSU-1
is optional, and streaming data alone does not solve executable addressing.

Date: 2026-10-26. The user asked for existing GitHub and community answers to
the 4 MB cartridge limit, because later boss ports may exceed it.

## The limit again

LoROM maps 4 MB of cartridge data. The native host and the reference Snes9x host
both run the SNES memory map, so a plain bank remap cannot exceed it. The table
below lists what other projects do.

## 1. MSU-1 data streaming (best fit, supported by our reference host)

The MSU-1 is an emulator expansion chip by Near (byuu). It adds a data file and
audio streaming through registers at `$2000`-`$2007`.

- The data file can hold up to 4 GB and is used as extra ROM.
- It supports general data streaming, not only CD audio.
- It is supported by Snes9x, higan, bsnes, SD2SNES and FX Pak.
- The reference build in this repo already contains the Snes9x MSU-1 code:
  `local/upstream/snes9x/msu1.cpp` and the `MSU1_STATUS` strings in the
  libretro core.

References:

- MSU-1 abridged specifications: <https://zumi.neocities.org/stuff/msu1_notes/>
- SnesLab MSU-1 page: <https://sneslab.net/wiki/MSU1>
- Snes9x MSU-1 implementation: <https://github.com/snes9xgit/snes9x/blob/master/msu1.h>
- Community thread on non-audio use of the data file:
  <https://www.zeldix.net/t2066-using-msu1-for-non-audio-non-fmv-additions>

Fit for this project:

- The guest needs a small loader that seeks through `$2000`-`$2003` and reads
  bytes from `$2001`. Assets stay in a sidecar `.msu` file.
- The reference host reads the same sidecar, so reference parity is possible.
- The native runtime must add the MSU-1 data registers. That is a small,
  well-specified device, unlike a new CPU.
- Limits: the data file is ROM only (not save RAM) and one PCM track at a time.

## 2. SA-1 Pack (8 MB ROM, but a full engine conversion)

The SA-1 Pack by Vitor Vilela is the established SMW GitHub project for larger
ROMs. Its README lists "Increase the maximum ROM size to 8 MB", 256 KB of
BW-RAM, a 10.74 MHz co-processor and up to 22 sprites on screen.

Reference: <https://github.com/VitorVilela7/SMW-SA1-Pack>

Fit for this project: poor in the short term. The SA-1 has a different memory
map and the pack rewrites large parts of the SMW engine. The native recompilation
host would also need an SA-1 CPU model.

## 3. ExHiROM (8 MB, no modern SMW tooling)

ExHiROM games exist (Tales of Phantasia, Star Ocean). Snes9x has partial ExHiROM
support in `memmap.cpp`, but no current SMW tool expands a hack to ExHiROM, and
every bank reference in the hack changes. Rejected.

## 4. Standard Lunar Magic expansion (4 MB, not more)

SMW hacks are normally expanded from 512 KB to 4 MB. This is the current base
size. It does not answer the question.

Reference: the community example "SMW Expanded to 4MB ROM":
<https://neoromhacking.net/hackpage.php?id=6300>

## Recommendation

1. Continue the budget, dedup and relocation allocator. Measured free space is
   about 820 KB, and two bosses need an estimated 40 KB to 160 KB.
2. When the budget is not enough, add MSU-1 data streaming as the native and
   reference supported expansion. Do not convert to SA-1 or ExHiROM.

## Limits

- The MSU-1 sidecar changes the deliverable format: a ROM plus a data file.
- Reference parity for streamed assets needs the native MSU-1 data device.
- The size figures are estimates until the boss donors are measured.
