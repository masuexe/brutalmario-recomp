# Legacy donor music layout

Date: 2026-10-26. This note records the legacy-family music layout that the
Demo 1-1 restoration uses. The findings come from static analysis and from the
reviewed song restorations.

## Two music families

| Family | Versions | Music storage |
| --- | --- | --- |
| New | `demo-1-1`, `demo-only-1`, and the restoration line | Single-song payloads in a 3-byte pointer table at `$0F:E000` |
| Legacy | `cheap-demo`, `demo6`, `demo7`, `demo8`, `7hero`, `mazo`, `ow`, `ra-*` | Four-song upload groups in fixed ROM blocks |

The new-family table entries are bank, high byte and low byte. A null entry
stalls the SPC upload, so the game stops at Mario Start.

## Legacy group storage

A legacy ROM holds 21 groups with a stride of 0x2000 bytes:

| Groups | Addresses |
| --- | --- |
| 10 | `$29:8008` to `$2B:A008` |
| 7 | `$3E:B008` to `$3F:E008` |
| 4 | `$44:8008` to `$44:E008` |

Each group has this layout:

| Offset | Content |
| --- | --- |
| 0 | Count, two bytes |
| 2 | Source base, two bytes, normally `0x6800` |
| 4 + 8*k | Sequence header for slot k, four slots |
| Count + 8 | Group end, including a trailer |

The song data area starts at source base + 64. Group total size is
count + 8, normally 6136 bytes.

## Extraction recipe

`tools/derive_legacy_song.py` walks the reachable command graph with the same
rules as `restore_star_world_1.py` `adapt_music`. It prints the reviewed
config fields and the payload identity.

Validated cases:

| Group | Slot | Result |
| --- | --- | --- |
| `$44:A008` | 0 | Song size 700, payload SHA `bc134773...`; matches the reviewed Snow Star song 0x54 config exactly |
| `$29:8008` | 1 | Matches the reviewed room 138 song 0x7E config exactly |
| `$44:A008` | 3 | Payload SHA `1d293f8e...`; matches the installed song 0x57 payload exactly |

These cases validate the group layout and the slot order.

## Open point: song id to group and slot

The legacy family does not use the new-family table at `$0F:E000`. The bytes
at that address are identical across all legacy versions, so they are shared
data, not a pointer table. The mapping from a song id to a group and a slot is
not resolved yet.

- The SNES side sends only the song id to APU port 2. See the request handler
  at file offset 0x179 and the upload activation routine at `$34:9B00`.
- The activation routine reads a DMA descriptor table at `$7F:FB00`. The
  writer of that table is not resolved yet.
- The legacy group order is not a simple id order. Group `$44:A008` starts at
  song 0x54, and group `$29:8008` has song 0x7E in slot 1.

## Donor probing limit

The recipient map 6 overworld tile override does not work on `cheap-demo`. A
25-translevel probe all entered room `0x14B`, so the donor map layout and the
tile address differ. The donor survey must locate the donor map tile address
before it can select courses by level number.

## APU RAM trace tooling

The reference frontend already supports a changed-byte APU RAM trace. The
snes9x core does not expose APU RAM by default, so this repository carries a
diagnostic core patch.

| Item | Value |
| --- | --- |
| Core patch | `patches/diagnostic/snes9x-apuram.patch` |
| Patch effect | Adds APU RAM as libretro memory id 0x100, size 0x10000 |
| Capture helper | `tools/capture_apu_trace.py` |

Use these steps:

1. Apply the patch to `local/upstream/snes9x`.
2. Rebuild the core: `make -C local/upstream/snes9x/libretro -j4`.
3. Restore the upstream source tree. The pinned repository check expects a
   clean tree. The rebuilt core stays in place.
4. Run `tools/capture_apu_trace.py` with a manifest, a ROM, a script and a
   capture name.

The trace is a JSON-lines changed-byte log. The first frame writes a full
0x10000-byte snapshot. Later lines record per-frame changes.

### Trace validation

A frame-20 snapshot from the donor run matches the donor ROM at 186 places.
The first match is ARAM 0x500 against ROM file offset 0x70004. The SPC program
image therefore starts near ROM file offset 0x70000. This validates the trace
and the byte replay.

### Trace findings (cheap-demo)

- Frames 1-17 upload the SPC program image.
- The map idle probe, the in-level standard music probe and the custom
  request probe (song 0x2E poked into `$1DFB`) never show group bytes
  verbatim in APU RAM. The standard probes had no upload, as expected.
- The custom request probe changed game mode to 0x0F and then room 0x14C. The
  request path for an arbitrary poke is not a clean upload trigger yet.
- A 64-byte window of group `$44:E008` appears at ARAM 0x2A11 at frames 620
  and 1000. That is one weak hit and not a group identification.

## Next steps

1. Trigger a real custom-song upload. A donor course that plays a custom song
   is the reliable way. The donor map tile address must be found first.
2. Search the trace with a full-window scan and accept only long exact
   matches.
3. Use the DSP register trace to select the slot. Compare the donor trace with
   the four candidate payloads.
4. Resolve the id to group and slot table. Then restore the remaining songs.
