# World 1 Yoshi's House (room $104): restoration state

Date 2026-10-24. Status: **partial restoration built (`demo11-yoshihouse-sprite`),
two open dependencies documented**. The user asked to restore the house as the
last World 1 side item and asked what the room's custom sprite does.

## What the room contains

The Demo 1-1 line's room `$104` is a **34-byte stub**: two `mark_sub` (pixi
id `A2`) spawn entries (cmd `08` xy `00`, cmd `18` xy `42`) and almost no
geometry - matching the user's Lunar Magic view (4x2 blocks + one custom
sprite). Entering it on the accepted head renders **black** (mode `$14`,
music request `$1E`, no audio) - and room `$104` has never rendered in any
capture of either restoration line.

**What A2 does** (source `brutalmario-data/data2/sprites - kopie/mark_sub.asm`,
"Sub of Mark"): a falling marker block. Init is empty; the main routine is
non-interactive (`$1686=0x99` disables Mario contact), draws a single 8x8
tile (`$88`), and has three modes driven by `$1528,x`: stand still, fall at
`$28/frame`, or fall at `$B0/frame`, destroying itself once it reaches a
depth threshold (`$14D4`/`$D8` checks). In the house the two spawns are the
"falling block" presentation pieces, not gameplay.

## What the candidate ports

`demo11-yoshihouse-sprite` (descendant of the accepted
`demo11-castle-sprite06`, candidate SHA-256 `49639f2b181fe91f…`):

1. **Sprite A2 port** - demo6 carries the only assembled `mark_sub` in a
   compatible format (464-byte pixi block + 16-byte record
   `01 36 00803a031944 $1FA4CF $1FA4D4`; demo7 differs only in label bytes).
   The block relocates to `$34:A4C0` and the record lands in the
   `$31:8272+A2*16` slot with the engine rebasing the two entry pointers.
   demo6's RATS complement byte is adapted to this engine's convention
   (`0xFE30 -> 0xFE2F = count^0xFFFF`) via a reviewed donor shim
   (`local/probes/demo6-ratsfix.sfc`).
2. **Song `1E` port** - the `$0DDA=1E` request (the 100-coin cue family,
   previously "absent in both; engine-special") is backed by cheap_demo's
   private block (RATS at mirror-physical `0x30EA7E`, 1,131 bytes, reached
   through the bank-`$E1` mirror pointer `$E1:$6C0F`); the copy installs at
   `$29:E000` with song-slot `0FE05A` repointed.

## Open dependencies (blocking full restoration)

- **The 7hero house stream is not portable yet.** 7hero's room `$104` is the
  intact house (renders fully: green roof, YOSH! sign, sprites alive) and its
  41-byte object stream ports via the level-data primitive, but the stream
  requests four custom sprites (`8A/8B/8C/B9` runtime) whose records exist
  **only in 7hero's own sprite system** - their 16-byte-format slots are empty
  in demo6/7/cheap/demo8, so the loader stalls at Mario Start (mode `$12`)
  even with the music byte adapted back to this line's request.
- With the stub, the room stays black and silent exactly as the accepted head
  does (both ROMs rms 0.0 at the house); the candidate changes nothing
  observable until the house stream can follow.

## Verification

- Candidate builds with 1,374 changed bytes, all inside the reviewed block,
  record, song and slot regions.
- `tools/check_demo11_line.py` remains **14/14** on the accepted head; the
  candidate is a descendant awaiting the user's decision on the remaining
  sprite ports.
- Probes: `d11-yh-entry*-ref` (entry states), `d11-yh-7hero` (donor render
  reference), `d11-yh-aram` (ARAM cursor), `d11-yh-base` (baseline audio).
