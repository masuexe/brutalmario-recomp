# Demo 1-1 course playtest issues

The latest dispositions supersede the earlier speculative storm notes. See
[the Dragon Coin runtime fix](demo11-storm-dragon-coins.md) for reproduction,
identities and bounded automated evidence.

## Level 122 (translevel 046): storm mosaic — user accepted

The user confirmed that the mosaic effect appears later in gameplay and
matches original Demo 1-1. They requested no further investigation. Parity
with cheap_demo remains unproven and is not a condition of this acceptance.
Death-transition mosaic is a separate observation.

Earlier reports called 13 of 42 standing screenshots "mosaic frames" based
on image brightness and edge metrics. Those metrics do not establish mosaic;
inspected register dumps show MOSAIC `$03`, a 1x1 setting. The previous
assertion that these captures prove a periodic 8x8 rain-layer effect is
withdrawn. Keep the captures intact as historical observations.

## Room 126: Baby Yoshi growth — recorded, deferred

The user reports that a baby Yoshi in Baby Yoshi Hill (room `$126`) does not
grow into an adult Yoshi when it eats a flower or a feather.

Likely cause: Demo 1-1 overrides the related growth code. The user expects a
difficult fix and asked to record the issue first.

Evidence to collect:

- the Baby Yoshi sprite and its growth routine in the Demo 1-1 ROM,
- the same routine in demoOnly1,
- the point where Demo 1-1 replaces the routine,
- a scripted reference/native feed test.

Status: open, deferred. Room data and sprite code are not inspected yet.

## Level 122: Dragon Coin column — automatically fixed

The user reported a persistent column of garbage 8x8 tiles at the collected
coin's position, including the second coin near a green Koopa. Scrolling the
area out and back removes it. This was reproduced on the old native build
and in interpreter-only mode. The Dragon Coins here are Map16 objects,
not sprites; the earlier sprite/OAM explanation was speculation.

The runtime now rejects invalid visible-field HDMA VRAM writes while retaining
ordinary CPU/DMA upload compatibility. Five real pickups, the extra life,
both Map16 planes and the full tilemap match default Snes9x in both native
renderers and pure interpreter mode. The old binary remains an explicit
negative control. This is automated qualification, not a new user playtest,
full-course clear or save/reload claim.

The cumulative ROM remains `demo11-fix-batch-p`; head promotion and the broader
full-game restoration remain open. Level `09E` is a user-identified test room
that normally does not appear during ordinary play.