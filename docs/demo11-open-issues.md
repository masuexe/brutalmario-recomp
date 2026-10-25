# Demo 1-1 open course issues

Date: 2026-10-26. This note records issues that the user reported during the
playtest of the candidate chain. These issues are not fixed.

## Level 122 (translevel 046): storm effects

The user reports that this level has a thunder effect that triggers a mosaic
effect. The candidate chain plays the level, but the user does not see the
mosaic effect.

Evidence so far:

- The level stream for room `0x122` is byte-identical in Demo 1-1, cheap-demo,
  7hero and most other versions (276 bytes).
- The room header lists the same graphics IDs in all versions:
  `30F`, `19`, `17`, `14`, `6`, `13`, `1`, `0`, `30E`.
- The graphics batch O1 ports `30F` and `30E` from 7hero.
- Entry screenshots show the striped storm background and the normal HUD.

The effect may come from a level-specific sprite or from an engine path that
the recomp host does not cover. This needs a reference and native comparison
at the moment of a lightning strike.

## Level 122 (translevel 046): Dragon Coin glitch

The user reports that collecting a Dragon Coin causes a vertical-line
graphics glitch.

The Dragon Coin is a sprite. Its animation uses the sprite graphics set, not
the extended tile IDs that batch O1 ports. The glitch may come from the recomp
host, or from a graphics set that differs from the intended version.

## Next steps

1. Capture level 122 on the reference host for a longer interval. Check for
   mosaic frames during a lightning strike.
2. Compare the reference and native captures at the same frame.
3. List the sprites of room `0x122` and identify the storm sprite.
4. Ask the user which version shows the expected effect. A newer or older
   version may hold the intended graphics or behavior.
