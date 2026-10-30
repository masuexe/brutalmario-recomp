# Cumulative integration of the qualified Boss Seven program

Date: 2026-10-29. Experimental target: `demo11-native-seven-product-v1`.
Parent: `demo11-native-type3-c2-v2`. Accepted product remains r14. Whole-game
restoration and earned boss victory/save acceptance remain open.

## Missing cumulative feature

The old fixed-slot E0 wait failed because the cumulative target did not contain
the previously qualified feature. Its E0 record was the type0 placeholder, and
the child pack was absent. Its A2 controller and A6 resources were the older
7hero variant:28,478 and23,165 bytes. They lacked the later official Boss
controller integration, child namespace, font lifecycle and ending adaptations.

The source still appeared to run a Seven opening, so pack execution and a
same-parent fight-window regression did not reveal the loss. In the old window,
the player eventually reached174 with other actors instead of the expected E0
birth. Those previous captures remain valid observations of that older program,
not qualification of the intended newer Boss feature.

The isolated [child checkpoint](native-seven-child.md) and
[ending/hidden-1up checkpoint](native-seven-ending.md) had already qualified the
newest retained official Boss program. This change carries their reviewed
feature into the cumulative game, following the official source chronology.
It does not change the child's logic to make an old wait pass.

## Reviewed integration

Source target: `demo11-native-seven-ending-1up`, ROM
`941f2d0c7ac3ac7ba955d26590778a665e23af1d9cdbbb546d80ec065d0e8a64`.
The independent source has111 changed ROM bytes relative to the shared
sprite9e foundation. Most are already present in the cumulative target. The
preparer compares each changed byte against both versions and rejects any
conflicting cumulative edit. Only seven remaining bounded spans are applied:

| File offset | Size | Feature |
| --- | ---: | --- |
|007294|5|Room17B hidden-checkpoint shim hook |
|02EA71|2|17B background pointer correction |
|0A2CFC|3|Unused ExGFX FFC pointer for the local blank-pole clone |
|0A5C69|17|17B graphics bypass record |
|189072|16|E0 record with child init90:C21D/main90:C265 |
|356175|1|0FF ending destination174→17B |
|356178|1|Previously qualified modern fight-music header adaptation |

The existing A2/A6 descriptors now select the exact qualified source master
and graphics packs:28,965 bytes SHA
`e9061413696935c854f3c20cac6b8fb6e1ae00886d56cb9bdf23629cb2f6c9de`, and31,366
bytes SHA `43cecea3a2201336d135466e5bb160a91115fd8b6c95223fd1b01ab95cbf7cf7`.
They retain the accepted stop command, deferred font restoration, local ending
graphics and scoped checkpoint shim without a new controller-code edit.

The3,385-byte child is byte-identical to the official Boss block at1E:C20E
and to the qualified pack (SHA
`8301000a2fed1e9c534958f06ef1d82eeb7e62f92cce9ef674b1f369c4fd0dbb`). It maps
to90:C20E with low-memory mirrors. The earlier9E mapping conflicts with the
cumulative mazo9B bank allocation; no child code relocation is necessary beyond
the record bank bytes because the child's qualified program has no source-bank
long self reference. Normal sprite ID6A remains unchanged. The recipient6A
record and full3,376-byte program remain pinned and byte-identical.

All other mappings, C0/C1/C2 adapters, mazo code, layouts, exits and save formats
are retained. The ending-specific changes are the explicitly reviewed prior
adaptations above, not an entire donor layout or engine replacement. There
are51 mapped packs. Recipes and admission tool:

- `config/native-content/seven-product-integration.json`
- `config/native-content/seven-product-child.json`
- `tools/prepare_seven_product.py`

## Fresh current-target qualification

ROM SHA-256:
`0f04abec07f424c482291c2aeee082bf4c41d3468f30e2483d06a728978cd8af`.
Binary SHA-256:
`d84ff809dae79f29c2209012fda160a3beda60cd6d56575c4eeab595e3aef164`.
Report: `local/reports/seven-product-v1.json`, SHA-256
`6cd9ffc705471c6874f39a3a78a18d5ad64f165f083099040c0a89611f22ecbe`.

Fresh `seven-product-child-{native,source}-v1` use the original tracked
seven-child-native/donor-event scripts and exact official Boss reference.
They declare map/pipe entry fixtures and write no actor, HP, completion or save
state. The real spawn now satisfies the read-only slot6 E0 wait after15 frames.
Two active E0 children match source6A across19 fields at spawn,32 and96 frames:
six exact actor pairs, including animation, velocity and state. Their normal ID
stays6A and phase stays15 hex. Bank90 actually executes235,256 instructions.
Japanese fight-font bytes match the source. The modern music request is AC;
this is a request check, not fresh audible acceptance.

The same run reaches real death without a death flag, loses one life, returns
to the map, enters ordinary course005, and re-enters0FF through the labelled
pipe fixture. English font bytes return on map/course re-entry; Japanese bytes
return for the fight. The controller resets. The prior fixed-slot failure was
not evidence that these expected children had merely changed slots.

Fresh `seven-product-ending-v1` / `seven-product-ending-source-v1` explicitly
inject final tier and damage. They qualify ending mechanics only, not an earned
win. The native transition reaches accepted17B at16/352; the source reaches
174. Ten subsequent ordinary right-walk positions match. Both reach the pit at
744/456, die, lose one life and return to the map. English font bytes are
restored at the native ending/map boundaries.

Fresh `seven-product-ending-mushroom-v1` / `seven-product-mushroom-source-v1`
use the corresponding ending fixture, then ordinary right input. Both spawn
a real green mushroom at sample17 and award one life at sample28. The later
pit consumes that life. Native starting lives4 and source19 are retained and
recorded separately; only the event times and relative life change are equated.
No life, completion flag or saved-clear byte is written to prove this result.

Four unchanged current-parent regressions cover109 dump points: funded A2
purchase/save/reset20, C2 direction15 (including startup), all-six16B loading68
(including startup), and original6A room0E4 entry6. All327 full WRAM/SRAM/VRAM
comparisons are byte-identical, without stack exclusions. Original6A room0E4
uses a fresh parent control. The other three original6A rooms are statically
preserved but not freshly replayed in this checkpoint.

All368 unit tests pass in `local/reports/unit-tests-seven-product-v1.log`
(115.987 seconds), including five new bounded-integration rejection tests.
This does not qualify whole-engine/image/audio equality, every combat phase,
earned Seven victory or saved completion, other95 rooms, C0/late-C1 phase or
complete course traversal. The older r13 survey is not current-target evidence.

```
python3 tools/prepare_seven_product.py
python3 tools/m1.py scaffold --target demo11-native-seven-product-v1
python3 tools/m1.py generate --target demo11-native-seven-product-v1
python3 tools/m1.py build --target demo11-native-seven-product-v1
python3 tools/qualify_seven_product.py --output local/reports/FRESH.json
```

The checker reads the named pinned captures. Use fresh capture names and an
isolated descendant for new runtime/fixture changes. Reconcile other previously
qualified features against cumulative records, packs and hooks before claiming
they are integrated. Continue other95 rooms and genuine fight/route acceptance;
do not mistake a regression against a missing-feature parent for restoration.
