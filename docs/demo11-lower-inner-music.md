# Demo 1-1 lower-inner cap-expiry freeze and music correction

Date: 2026-10-24. The user reproduced a freeze when a lower-inner cap effect
expires and confirmed the intended selections: course `$60`, caps `$79`.
This is the same donor bank-local music dependency already corrected on the
demoOnly1 line; the safe Demo 1-1 sprite port had retained the donor's requests.

User-tested cap-music checkpoint: `demo11-lower-inner-music`.
ROM SHA-256:
`10f8af337eafbfe2c42454087723587c4f8f41455dabe7517152272be37ce909`.
The user tested this checkpoint and reported no issues before requesting the
[Star World visual follow-up](demo11-star-visuals.md), which is the newer cumulative head.
Parent `demo11-star-sprites-safe` remains intact at
`11ad648a7885ea7c4792dd818229debead6adf3d238ffaea03f182d41e565887`.

```sh
python3 tools/play_demo_only1.py --restoration demo11-lower-inner-music --show-location
```

Start a new instance using this command; an already running instance retains
its older ROM. The launcher uses a fresh isolated practice save at the lower-inner
node. Existing games, saves and captures are preserved.

## Reproduction and bounded fix

On both parent hosts, an initialized test cap collides with Mario and its
invisibility timer decrements naturally to `$10`. At that point the controller
queues `$21` into `$1DFB`. The global `$21` song slot is empty. WRAM, including
the guest frame counter and effect timer, remains byte-identical across the
following 180 host frames; the pending request remains `$21`. This reproduces
the reported freeze without forcing an effect timer or music request.

The donor's `$21/$22` requests are selections within an already uploaded song
bank, not recipient global IDs. The [earlier music investigation](lower-inner-music.md)
records that distinction. The Demo 1-1 port must apply the accepted selection
adaptation at its actual relocated code addresses.

The [new descendant recipe](../config/restorations/demo11-lower-inner-music.json)
changes exactly **seven bytes**:

| Trigger | Address | Before | After |
| --- | --- | --- | --- |
| Room `$117` header | `$3A:B524` | `$41` (song `$40 + 1`) | `$61` (song `$60 + 1`) |
| Three cap pickup immediates | `$3A:8085/80C6/8104` | `$22` | `$79` |
| Three final-expiry immediates | `$3A:83A5/8429/8469` | `$21` | `$60` |

No payloads, music driver, cap timers, geometry, sprite placements, exit or save
logic change. The cap controller is also placed in room `$03C`; its behavior
there has not been requalified. This checkpoint exercises room `$117`.

The existing Demo 1-1 songs are byte-identical to the previously accepted
demoOnly1 correction, including their complete upload wrappers:

| Song | Upload bytes | Upload SHA-256 |
| --- | --- | --- |
| `$60` | 1,204 | `92f4443ae1a8ec1bbe6c85e63204b44eca33d5286423c7eee498c70a8a5d5947` |
| `$79` | 424 | `33cbc7984922765efeadb1e5246fb36101e7eb4c4032a9c672256382f1a443b8` |

## Verification

`tools/qualify_demo11_lower_inner_music.py` pins the ROM, parent, recipe,
build, capture scripts and host binaries, checks script completion and dump
sizes, and verifies:

- The parent freeze reproduces on reference and native with a real fixture-cap
  collision and natural expiry; complete WRAM is frozen for at least 180 frames.
- Invisibility, metal and wing caps each initialize, become active, expire
  naturally and leave all three effect timers zero. Both corrected hosts remain
  in room `$117`, mode `$14`, retain four lives-minus-one and keep advancing
  during the subsequent 180-frame observation. `$1DFB` is consumed normally.
- The reference request sequence is exactly course `$60`, then three pairs of
  pickup `$79` and expiry `$60`.
- Native SPC RAM during an active cap matches all **416** song `$79` body bytes;
  final post-expiry SPC RAM matches all **1,196** song `$60` body bytes. This
  verifies loaded music beyond selection bytes. No new listening acceptance
  is claimed; the user already confirmed the intended tracks.
- The existing actual-input warp-star route is replayed on both corrected
  hosts. Its six player-position samples remain within 8 pixels of the safe
  parent, and both hosts reach X at least `$0D00`.
- The descendant rebuilds byte-for-byte and differs from the parent only at
  the seven declared selection bytes. The ancestry-derived whole-line audit
  now reproduces all **17** recipes with zero unexpected changed bytes.
  The integrated suite passes **20/20**; its earlier qualifiers still refer
  to their own frozen targets.

The cap scripts initialize a test cap in free sprite slot 0, set its subtype
after initialization, and place Mario for actual collision. They never write
effect timers, music queues, completion flags or SRAM. These are explicit
pickup/expiry fixtures, not natural traversal to each cap block. The warp-star
regression is a route segment, not a full 100-coin clear or DK/death check.

Primary evidence:

- `local/captures/d11-cap-freeze-base-{ref,native}` and tracked
  `demo11-star-cap-expiry-freeze.script` reproduce the parent failure.
- `d11-cap-music-fixed-{ref,native}` use tracked
  `demo11-star-lower-inner-music.script` for all three effects.
- `d11-cap-music-active-native` uses tracked `demo11-star-cap-active.script`
  for the active-cap SPC snapshot.
- `d11-cap-music-route-{ref,native}` replay the existing
  `star-world-lower-inner-route.script`.
- Exact receipts and assertions: `local/reports/demo11-lower-inner-music.json`.
  Build identity: `local/build/demo11-lower-inner-music/m1-build.json`.
  Suite log: `local/reports/demo11-lower-inner-music-line.log`.

```sh
python3 tools/restore_star_world_1.py --target demo11-lower-inner-music
python3 tools/m1.py scaffold --target demo11-lower-inner-music
python3 tools/m1.py generate --target demo11-lower-inner-music
python3 tools/m1.py build --target demo11-lower-inner-music
python3 tools/m1.py reference --target demo11-lower-inner-music \
  --script recomp/inputs/demo11-star-lower-inner-music.script --capture fresh-cap-music-ref
python3 tools/m1.py native --target demo11-lower-inner-music \
  --script recomp/inputs/demo11-star-lower-inner-music.script --capture fresh-cap-music-native
python3 tools/check_demo11_line.py
```

The broader restoration remains open. The center-node mapping investigation
and other unqualified course routes retain the limits in the
[safe sprite checkpoint](demo11-star-sprites-safe.md).
