# Native Seven Koopalings child and font lifecycle

## Result

The isolated target `demo11-native-seven-child-font-cycle` descends from
`demo11-native-seven-font-entry`. It loads the newest official Boss Demo child
program for sprite `6A` from an external pack. The child uses the custom
dispatch ID `E0`. The recipient keeps its own `6A` actor, record, and code.

The target also restores the recipient English font after a native death. A new
fight entry loads the Japanese font again.

Automated checks qualify these items:

- Six event-aligned child samples. Slots 6 and 7 match 19 actor fields between
  the donor and the native host.
- A native real death, the map return, an ordinary course re-entry, and a
  labelled pipe fixture re-entry into room `0FF`.
- 830 unchanged comparisons on three routes and four rooms with the old `6A`.
- Four rejected startup packs.
- 162 Python unit tests and 14 donor/native CPU pairs in the C boundary test.

This is not a complete fight. Music, later fight phases, the ending, and saved
completion remain open. The target does not promote the accepted head.

## Identities

| Item | Value |
| --- | --- |
| Target | `demo11-native-seven-child-font-cycle` |
| Parent target | `demo11-native-seven-font-entry` |
| Parent ROM SHA-256 | `c0cf157839e52b4571615c1aacbb5cc989378f14529645107f06fd31a94d4e64` |
| Target ROM SHA-256 | `a85dbe0609facffc75bf55b28080b7fba9ad7d376254a5914c835d7f89abc015` |
| Native binary SHA-256 | `9fcefc8956b6d9ffbcdc5e06429c61cd986cf225c9800f22d0189225b4360539` |
| Child code pack | `seven-child6a.bin`, 3,385 bytes, SHA-256 `8301000a2fed1e9c534958f06ef1d82eeb7e62f92cce9ef674b1f369c4fd0dbb` |
| Master code pack | `seven-code.bin`, 28,880 bytes, SHA-256 `e80e1102b96607c1ec73a74d75c2db64810b8a5db822239842772bdd88ee9384` |
| Graphics pack | `seven-graphics.bin`, 27,261 bytes, SHA-256 `9ed6aa8d4398b7b06195a7b250daa098af0d9bb09aa35b218e12251b3c62280f` |
| Sprite 9E pack | `sprite9e.bin`, 1,291 bytes, SHA-256 `a6654d22c2dd9f146fc117ba7dca01f9389995fcb8b75f52ba6f2c4a6b1a717d` |
| Star graphics pack | `star1-ffd.bin`, 3,001 bytes, SHA-256 `3a51dd45f2df22d1f2490ca117070a68bfdab33cb03f734ad9e97c59e581a169` |
| Preparation receipt | `local/restoration/demo11-native-seven-child-font-cycle/input-manifest.json`, SHA-256 `9d4979258685fabba8c20396c9dbcf29788390b334c34192345066c8b3c174d6` |
| Qualification report | `local/reports/native-seven-child-cycle-final.json`, SHA-256 `f63a291822bedcd2c2bbce15fc63cd0a44b1e6d7e6029b0351d696f647567c59` |

The donor is the official Boss Demo verified against `boss.ips`. See the
[source inventory](native-boss-inventory.md). The parent ROM hash, the child
record, and the pack hashes identify this target. A ROM hash alone does not
identify native content.

## Mapping

The donor record for the child is `013610003bab18401dc21e65c21e0000`. It has
init `$1E:C21D` and main `$1E:C265`. The target writes this record to the
recipient slot `E0` at file `0x189072` as
`013610003bab18401dc29e65c29e0000`. The former slot content is
`0000ffffffffffff218001218001ffff`. The child code is a protected block of
3,385 bytes at `$1E:C20E`. The runtime maps the block to `$9E:C20E`.

The recipient `6A` record `013610003b8b1840f4be203fbf200000` stays at file
`0x188912`. Its code stays at file `0x103EE5` (3,376 bytes, SHA-256
`03ea43204426c9e84df053724e577bfd346a07e1d98a9da281e4457b1f94518c`). It serves
rooms `0D8`, `0E2`, `0E3`, and `0E4`. The target changes no other ROM byte.

One master patch at `$22:84D9` (native `A2:84D9`) changes `9f9eab7f` to
`2040f0ea`. The original store writes the custom-ID table. The replacement
calls the adapter at `A2F040` and then runs one NOP.

The adapter bytes are `0848a9e09f9eab7f682860`. It saves A and P, writes `E0`
to the custom-ID table, restores A and P, and returns. Two preserved sites keep
the normal `6A` contract: `A2:84D5` holds `a96a` (LDA #$6A) and `A2:A168`
holds `c96a` (CMP #$6A).

The child audit admits 32 entry states and 1,426 instruction variants. Its
external call set is `00F5B7`, `01802A`, `0187A7`, `01A7DC`, `01AB99`,
`01B7B3`, `02A9DE`, `07F7D2`, and `27FAF4`. The audit admits no indirect
transfer and no hard-coded `6A` self ID. The ten shared dependency ranges carry
a byte hash for both images. This is a bounded control-flow and reference check,
not a whole-program proof.

## Font lifecycle

The fight-local Japanese font comes from the parent A6 pack. The same pack now
carries the recipient English font. The font resource is GFX2A ID `02A` of the
official Demo 1-1 image (`314496f67caf53d1d74873333de366a07a2b2446d7bbb5f27eeeb9aa69894f32`).
Its pointer is `0981DF`. The encoded stream is 1,162 bytes
(`9f755c0571d9d640f832a3baf7f1259cee71c8eb6b330d4af57e9de6828427ff`). The
decoded bytes are 2,048 bytes
(`310facf09c5f280859dcfcf4da215c63089377af4802aabea31e49ce5f09d0fa`). The target
appends the decoded bytes to the graphics pack at native address `A6E27D`.

A main-loop hook at `A28090` replaces `20ff80` (JSR `$80FF`) with `2060f0`
(JSR `$F060`). The wrapper at `A2F060` holds
`0848da5aa571c909d00822d0d81022a0f0a27afa682820ff8060`.

The wrapper saves the registers. When the player state `$71` equals 9, the
wrapper queues the callback through the shared deferred scheduler at `$10:D8D0`.
Then the wrapper runs the original `$80FF` handler. The callback at `A2F0A0`
holds
`0848a9808d1521c220a900488d1621a901188d2043a97de28d2243a900088d2543e220a9a68d2443a9048d0b4268286b`.
The callback programs DMA channel 2 for VRAM word `4800`. The source is
`$A6:E27D`, and the size is `0800`. The transfer writes the English font to
VRAM bytes `9000` to `97FF`.

The recipient's own fight entry loads the Japanese font from the parent pack
again. This restores the Japanese glyphs on a new fight entry.

The C boundary test runs the adapter and the wrapper on the pinned interpreter.
It then runs the copied callback. It checks the DMA source, size, and trigger.
The test does not simulate the PPU.

## Verification

The native capture `seven-child-cycle-event-v1-native` uses the tracked script
`recomp/inputs/seven-child-native-event.script`. The donor capture
`seven-child-event-v1-donor` uses
`recomp/inputs/seven-child-donor-event.script` on the pinned reference host.
Both scripts use read-only event waits for the first child spawn. Both keep the
ordinary map/node fixture and the labelled pipe-action transfer.

The script also runs these checks:

- Death: lives go from 4 to 3. The map mode is `0E`. The ordinary course is
  `005`. The font after the map return matches the recipient English font.
- Fight re-entry: the labelled pipe fixture enters room `0FF`. The Japanese
  font returns. The fight controller resets to ID `2A` in slot 9.

The regression cases pair the parent captures with new captures of this target.
The routes are `star1`, `boss`, and `lifts`. The old-`6A` rooms are `0D8`,
`0E2`, `0E3`, and `0E4`. The 830 comparisons cover WRAM, VRAM, CGRAM, OAM,
SRAM, framebuffer, APU trace, PPU writes, registers, and DMA trace.

The existing-room samples show the preserved actor behavior:

| Room | Mode | Active `6A` slots |
| --- | --- | --- |
| `0D8` | `14` | 2, 3 |
| `0E2` | `14` | none |
| `0E3` | `14` | none |
| `0E4` | `12` | 9 |

Four startup cases reject the child pack: missing pack, corrupt pack, short
pack, and long pack. Each case exits with a nonzero code and the expected
`[native-seven] rejected:` message.

All 162 Python unit tests pass. The five child tests include the C boundary
test with 14 donor/native pairs. The full-run log is
`local/reports/full-unit-tests-continue.log`. The child audit rejects a changed
namespace record, a changed normal-ID contract, a missing custom-ID hook, a
namespace collision, and a changed preserved `6A`.

The checks use fixtures, not an unassisted route. The entry is a map/node
fixture plus a pipe-action transfer. The fight re-entry is a pipe-action
fixture. No check writes completion flags, invulnerability, or forced movement.

## Limitations

The child samples are event-aligned. They qualify the spawn and two later
actor states, not the whole fight. Fixed-time probes are not asserted here. A
local phase probe showed different dialogue timing between the donor and the
native host. The native host also reached a real player death inside that probe
window, and the donor capture ends before that window. The cause is not
qualified.

The death and map-return check runs on the native host only. The donor script
stops at the child samples. Do not claim donor parity for death or map return.

The checks cover the font restoration on this death, map-return, and re-entry
path only. Other fight exits and endings remain open.

Music remains open. The child source writes music value `1E` at `$1EC7CD`
(`a91e8dfb1d`). This write is not a qualified music adaptation. The room data
music value `33` and the legacy-to-modern Last Battle mapping need an actual
driver trace before any patch.

Later fight phases, the ending, and saved completion remain open.

## Reproduction

```
python3 tools/native_seven.py
python3 tools/native_seven_child.py
python3 tools/m1.py --target demo11-native-seven-child-font-cycle scaffold
python3 tools/m1.py --target demo11-native-seven-child-font-cycle generate
python3 tools/m1.py --target demo11-native-seven-child-font-cycle build
python3 -m unittest discover -s tests -p test_seven_child.py -v
python3 tools/qualify_seven_child.py --output local/reports/YOUR_FRESH_REPORT.json
```

Skip `scaffold` if the isolated experiment exists. The last command rechecks
the recorded final captures. Its report is byte-identical to
`native-seven-child-cycle-final.json` when the sources and captures do not
change. The preparation step refuses to replace a receipt with different bytes.

For new captures, use a fresh prefix:

```
python3 tools/m1.py --target demo11-native-seven-child-font-cycle native --script recomp/inputs/seven-child-native-event.script --capture PREFIX-native
python3 tools/m1.py --target demo11-native-seven-child-font-cycle native --script recomp/inputs/demo11-star1-entry.script --capture PREFIX-regression-star1
python3 tools/m1.py --target demo11-native-seven-child-font-cycle native --script recomp/inputs/demo11-hp-boss-bc.script --capture PREFIX-regression-boss
python3 tools/m1.py --target demo11-native-seven-child-font-cycle native --script recomp/inputs/native-sprite9e-room146.script --capture PREFIX-regression-lifts
SNESREF_CORE_OPTIONS=snes9x_echo_buffer_hack=enabled python3 tools/probe_reference.py --manifest config/boss-donor.json --rom local/content-versions/boss/rom.sfc --script recomp/inputs/seven-child-donor-event.script --capture PREFIX-donor
```

The old-`6A` room scripts are `recomp/inputs/seven-child-existing-0d8.script`
and the matching `0e2`, `0e3`, and `0e4` scripts. Run each one on the parent
target for the parent capture and on this target for the new capture.

The C boundary test needs the pinned source fixture
`local/captures/seven-opening-v1-donor/attack1200.wram.bin`. If the fixture is
absent, the Python test skips the C case.
