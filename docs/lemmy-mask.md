# Lemmy castle spotlight seams

Investigated 2026-10-18. The user reported thin vertical lines below Mario and
at the far-left edge in `tmp/Snipaste_2026-10-18_21-48-35.png`.

## Finding

The spotlight scene is room **$08C**, reached through the existing screen-5
exit of the castle entrance room $10E. Both native renderers reproduce the
seams. Their sampled framebuffers are byte-identical. The pinned Snes9x
reference reproduces the same scene and seams: every pixel matches after
reducing each displayed color channel to its original five-bit precision.
Raw output differs because the reference passes through RGB565 conversion.

The actual guest-generated window tables explain both lines. This is not
evidence of a native-only renderer regression. **ZSNES 1.51 remains untested**;
Snes9x agreement does not establish the historical ZSNES appearance.

## Mechanism

At the `next-idle` checkpoint, Mario's world position is $0070,$0150 and the
spotlight center X is $78 (120). HDMA channels 3 and 4 write the left/right
window bounds at $2126/$2127 from tables at $7F:F000/$7F:F100.

Both tables begin `01 00 70 00`: the initial region has left=right=0.
An inclusive window with equal endpoints contains one pixel, producing the
far-left seam wherever that layer is visible. The circle then expands and
contracts. Both tables finish with `01 78 00 00` at offsets $6E..$71: the last
circle row has left=right=$78, followed by the HDMA terminator. Termination
leaves the final register values in place for the remaining scanlines,
extending a one-pixel window down from the circle. Its length depends on
Mario's screen Y position.

This comes from the ROM, rather than just a suggestive source filename:

- The pinned ROM's Y/X tables are at $2B:F400/$2B:F46C; the last processed
  X-radius word at $2B:F4D6 is zero.
- The code at $2B:F646 reads the Y table; $2B:F652 reads the center and
  subtracts the X radius. The following code adds the radius for the right
  bound, loops to X=$6C, then writes the zero table terminators.
- The corresponding supplied source is
  `../references/brutalmario-data/data/data/levelasm/castle1.asm`.
  Its `CIRCLE` loop corroborates these ROM bytes and the observed WRAM tables.
- Native live registers at this checkpoint retain window bounds [120,120],
  window selection $20, main/subscreen window masks $02/$02, and HDMA mask $78.

## Reproduction and evidence

[Diagnostic input route](../recomp/inputs/demo-only-1-lemmy-mask.script).
It starts fresh at the measured castle entrance, enters normally, and uses
position/transition pokes to take an existing exit. It does not edit the exit
destination, ROM, spotlight tables, or renderer. This is a scene reproduction,
not a natural-route gameplay acceptance.

```sh
python3 tools/m1.py native --target demo-only-1 --renderer legacy \
  --script recomp/inputs/demo-only-1-lemmy-mask.script --capture NEW_NAME
```

Use a new capture name for each run. Select `--renderer optimized` for the
second renderer. For `reference`, remove the native-only `turbo on` line from
a disposable script copy and omit `--renderer`.

Local captures: `lemmy-mask-exit-5`, `lemmy-mask-optimized`, and
`lemmy-mask-reference-valid` under `local/captures/`. Each includes `next-room`
and `next-idle` captures. `local/reports/lemmy-mask-location.json` records ROM
identity, table bytes, positions, framebuffer hashes, and pixel comparisons.
The initial `lemmy-mask-reference` attempt rejected `turbo` before running;
it is not used as reference evidence. Exploratory exit-11/12 captures identify
other rooms and are likewise excluded from the comparison.

## Scope and recommendation

No rendering fix was applied. Keep the current behavior for fidelity work and
record the seams as a ROM-driven visual artifact reproduced by Snes9x.
An optional cosmetic correction would need to generate genuinely empty window
regions above and below the circle. Changing the shared PPU rule for equal
endpoints would affect other games/scenes and is not supported by this finding.

A local cosmetic correction now appears smaller than a PPU timing repair:
roughly several hours to half a day including checks at different circle
heights, screen edges, and switch states. This is an estimate, not a verified
implementation. Historical ZSNES appearance and an optional correction remain
separate open items; the earlier manual Lemmy functionality checkpoint stands.
