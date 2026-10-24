# Demo 1-1 exact map-node BGM dispatch

Date: 2026-10-24. The user accepted the Forest Star checkpoint. A music trace of
that checkpoint then showed that the new middle-left node played slot `0x33`,
which is the room106 track. It did not play the forest donor track `0x5D`.

Current automatically qualified cumulative target: `demo11-node-music`.
ROM SHA-256:
`77a4b7a970125db9c6b53d0619f6f9441c47538bd938bce6a8ee7c862de7240a`.
Native binary SHA-256:
`6d31a9ede8ffc5591d525d8c5178b3b3ac0b60262adb785a7ac2e0f48bad8d63`.
Parent: `demo11-star-forest` (`4a4928f1…`).

```sh
# Starts at the Star World middle-left Forest Star entrance:
python3 tools/play_demo_only1.py --restoration demo11-node-music --show-location
```

`--level world1-room106` starts at the room106 node instead. The launcher
creates an isolated practice save. Existing ROMs, builds, game processes, user
saves and captures stay intact.

## Defect

The accepted [room106 music fix](world1-room106-music-investigation.md) patched
the level-default BGM dispatch at `$00972B`:

```
$00972B: LDY $1F17      ; current map-node X
$00972E: CPY #$58       ; room106 node
$009730: BNE +6
$009732: LDA #$33
$009738: STA $1DFB
```

The dispatch runs with 8-bit index registers. `LDY $1F17` therefore loads only
the low byte of the map-node X word. `CPY #$58` then matches every node whose X
low byte is `$58`. The Star World middle-left node is at X `$0158`, so it also
selected slot `0x33`. That masked the forest donor request `0x5D`.

The user-accepted room106 result stays valid: it needs slot `0x33` on the
room106 node only.

## Repair

The recipe is
[`demo11-node-music`](../config/restorations/demo11-node-music.json). It is a
descendant of the forest checkpoint and changes 38 bytes:

- The 13-byte dispatch at `$00972B` becomes `JML $49:EA08` plus nine `NOP`s.
- A 25-byte private shim sits in a checked empty block at `$49:EA00`:

```
REP #$20          ; A -> 16
LDA $1F17         ; full map-node X word
CMP #$0058
SEP #$20          ; A -> 8
BEQ fire
LDA $0DDA         ; original request passes through
JML $009738
fire:
LDA #$33          ; room106 node only
JML $009738
```

The shim keeps the data bank and index size unchanged. It restores the original
8-bit A state before the jump back. The room106 node keeps slot `0x33`. The
room120 node keeps its original `0x49` request. Every other node passes its
original `$0DDA` request.

## Evidence

| Check | Reference | Native |
| --- | --- | --- |
| Forest node request | `$1DFB=0x5D` only; no `0x33` | ARAM holds the restored `0x5D` payload |
| Forest entry state | mode `$14`, room `$003`, `112/352`, water `$85=0` | same |
| Forest movement | `x=137`, `y=337…` | same |
| Room106 node | `$0DDA=0x33`, room `$0106` | same |
| Room120 node | `$0DDA=0x49`, room `$0120` | same |

The native forest ARAM matches the restored `0x5D` upload body (940 bytes).
That body is byte-identical to the demoOnly1-line forest payload, so the new
line now plays the accepted old-build forest track.

Forest entry and movement values match the previous checkpoint capture
`d11-forest-entry-ref` in every field except the music selection. That capture
shows the leak as `$0DDA=0x33`; the new captures show `$0DDA=0x5D`.

Primary captures are `d11-node-music-forest-{ref,native}` and
`d11-node-music-both-{ref,native}`. Receipts and measurements are in
`local/reports/demo11-node-music.json`. The suite log is
`local/reports/demo11-node-music-line.log`.

`tools/qualify_demo11_node_music.py` checks the recipe replay, the 38 reviewed
bytes, the shim bytes, both hosts' forest music request and state, the room106
and room120 nodes, and the native ARAM payload. The Demo 1-1 line suite passes
**24/24**. The whole-line audit rebuilds 22 recipes: 105,084 changed bytes
against Demo 1-1, all inside 139,275 declared region bytes, zero unexpected.
The 33 restoration tests, three preparation tests and 18 launcher tests pass.

## Limits

- The node tests use explicit map teleports. They qualify the dispatch boundary,
  not ordinary overworld travel.
- The room106 slot `0x33` choice remains the user-auditioned decision. This
  repair does not revisit it.
- The check covers the forest node and the two room106/room120 nodes. Any other
  node whose map-node X word is exactly `$0058` keeps the accepted `0x33`
  behavior; nodes with only a matching low byte now pass their original request.
- No new listening acceptance is requested. The change restores the old-build
  forest track and keeps both user-confirmed room106/room120 selections.

## Reproduce

```sh
python3 tools/restore_star_world_1.py --target demo11-node-music
python3 tools/m1.py scaffold --target demo11-node-music
python3 tools/m1.py generate --target demo11-node-music
python3 tools/m1.py build --target demo11-node-music
python3 tools/m1.py reference --target demo11-node-music \
  --script recomp/inputs/star-world-forest-entry.script --capture fresh-node-forest-ref
python3 tools/m1.py native --target demo11-node-music \
  --script recomp/inputs/star-world-forest-entry.script --capture fresh-node-forest-native
python3 tools/qualify_demo11_node_music.py
python3 tools/check_demo11_line.py
```
