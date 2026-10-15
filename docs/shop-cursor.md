# demoOnly1 shop selection highlight

Date: 2026-10-15. Fixes the missing item-selection cursor/highlight in
Vivian's Shop, entered through the pipe at the start of Baby Yoshi Hill.
The user supplied `tmp/Snipaste_2026-10-15_20-57-38.png` and confirmed that
Up/Down still changed the item description. The rebuilt executables preserve
the existing audio-clock correction and user saves.

## Reproduction and diagnosis

A natural input route starts on Special, moves Right twice to Baby Yoshi
Hill (`$126`), enters its opening pipe, reaches shop room `$182`, and opens
the item selector. The checked-in
[input script](../recomp/inputs/demo-only-1-shop.script) uses no WRAM pokes,
imported SRAM, or savestates. It selects all four items, moves back up, and
exits the selector with B. It does not test purchases.

Both native renderers reproduced the missing highlight. Disabling the recent
APU clock correction also reproduced it: the selected row differed from the
reference at 1,190 RGB5 pixels. This is not caused by that audio change.
VRAM is byte-identical between reference and native item-menu samples, and
the selection logic/description changes work.

The shop uses HDMA channels 3–5 to change color-math control, the CGRAM
address (`$2121`), and palette data (`$2122`) along the scanline. The selected
row temporarily receives a highlight palette color; later lines restore it.
When [HDMA ownership moved to the live beam](menu-background.md), CPU and HDMA
register writes entered the raster journal, but CGRAM port writes were still
explicitly excluded. Rendering therefore used the final palette for every
line and lost the temporary row color. The apparent missing cursor is part
of that selected-row effect. This was an omission in the earlier HDMA fix.

## Fix

The project-owned [PPU patch](../patches/runtime/0001-fix-mosaic-and-raster-restore.patch)
now journals `$2121/$2122` writes from CPU, DMA, and HDMA. Each field snapshot
includes the 256 palette colors and the shared CGRAM port address, byte latch,
and pending-second-write flag. Raster rendering restores the field's starting
palette and replays changes in beam order. At RenderEnd it restores the live
palette and port state, including writes from the following field.

This extends the existing register/latch preservation instead of reintroducing
render-time DMA execution. PPU structure layout, regular savestate format,
guest instructions, ROM data, selection logic, and purchases are unchanged.
Source/patch/result hashes are updated in
[runtime-patches.json](../config/runtime-patches.json). Both game targets are
rebuilt because the PPU is shared.

## Validation

- The natural shop route has **18 matching reference/native RGB5 pictures**,
  including all four selected rows, moving back up, and B exit. Corresponding
  shop WRAM differences are confined to the stack page; full-state equality
  is not claimed.
- The same 18 pictures match with `NewRenderer=1, NoSpriteLimits=1`, covering
  the user's interactive sprite-limit setting.
- Six stable item-menu samples match the reference with each native renderer.
  Before the fix they differed by 1,142–1,190 RGB5 pixels; after it all six
  have zero differing RGB5 pixels.
- The primary Demo 1-1 6,104-call route preserves all eight sampled full WRAM
  and raw framebuffer images byte for byte against the APU-clock-fixed build.
- All 80 dense transition samples retain byte-identical full WRAM and raw
  pictures, including the MARIO START interval. demoOnly1's three-death route
  still returns to overworld mode `$0e` each time, with lives decreasing from
  five to two.
- All **20 project tests pass**. The new ROM-free test renders a temporary
  scanline palette band with both renderers, replays ordinary CPU/DMA uploads,
  splits a CGRAM color's two writes across lines, preserves a new-field palette
  overwrite and a half-written port, and repeats rendering/idle fields. Its
  pixel assertion fails against the pre-fix PPU.

The test references are pinned Snes9x 1.63 captures with demoOnly1's echo
compatibility enabled. ZSNES 1.51 remains the user-reported historical baseline;
it has not been run locally. On 2026-10-16 the user retested the rebuilt
version and reported no issues, completing manual confirmation of this fix.
Buying items, complete demoOnly1 fidelity, and the deferred victory
black screen are outside this fix.

## Reproduction and evidence

```sh
python3 tools/m1.py build
python3 tools/m1.py build --target demo-only-1
python3 -m unittest discover -s tests -v

python3 tools/m1.py reference --target demo-only-1 \
  --script recomp/inputs/demo-only-1-shop.script --capture shop-ref-new
python3 tools/m1.py native --target demo-only-1 --renderer optimized \
  --script recomp/inputs/demo-only-1-shop.script --capture shop-native-new
python3 tools/compare_captures.py \
  local/captures/shop-ref-new local/captures/shop-native-new
```

Use fresh capture names. Normal interactive startup remains:

```sh
python3 tools/play_demo_only1.py
```

Local evidence includes `shop-menu-reference`, `shop-menu-native`,
`shop-menu-old-clock`, `shop-menu-legacy`, `shop-menu-fixed`,
`shop-menu-fixed-legacy`, `shop-selection-reference`, `shop-selection-fixed`,
`shop-selection-unlimited`, `shop-palette-primary-regression`,
`shop-palette-transitions`, and `shop-palette-only1-deaths` under
`local/captures/`. Comparison/negative-test reports are under
`local/reports/shop-*.json`; captures retain route, ROM, binary, runtime-patch,
and relevant configuration identities.
