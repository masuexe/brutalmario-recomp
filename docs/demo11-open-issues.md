# Demo 1-1 open course issues

Date: 2026-10-26. This note records issues that the user reported during the
playtest of the candidate chain. These issues are not fixed.

## Level 122 (translevel 046): storm effects

The user reports that this level has a thunder effect that triggers a mosaic
effect. The candidate chain plays the level, but the user does not see the
mosaic effect.

Test result: the effect is present in both hosts. A 21-second capture of the
level shows dark lightning frames and mosaic frames after about 20 seconds.

| Frame | Mean brightness | Edge ratio |
| --- | ---: | ---: |
| normal | 75.6 | 0.43 |
| lightning with mosaic | 64.1 | 0.083 |
| mosaic only | 74.9 | 0.083 |

The native host shows the same pattern as the reference host. A 70-second
standing capture has mosaic in 13 of 42 samples (about 31 percent). The mosaic
periods last about two to three seconds and repeat every few seconds.

Screenshots: `local/captures/storm-046-long/normal.png` and
`local/captures/storm-046-long/mosaic.png`. The mosaic frames render in 8 by 8
blocks, so the striped background looks coarse.

Captures: `local/captures/storm-046-ref` and `storm-046-nat`. Script:
`local/probes/storm-046.script`. The analysis tool is
`local/probes/storm-metrics.py`.

The level stream for room `0x122` is byte-identical in most versions, and the
room header lists the same graphics IDs. The graphics batch O1 ports `30F` and
`30E` from 7hero.

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