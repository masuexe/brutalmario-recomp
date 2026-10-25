# Manual playtest evidence

## Candidate chain practice sessions

Start a fresh practice session at any translevel of a candidate chain:

```
python3 tools/play_demo_only1.py --restoration demo11-fix-batch-o2 --translevel 0x09E
```

The script transfers to the map 6 lower-left node, writes the translevel to the
node level byte, and enters the level. The game stays interactive after the
script ends. The session uses a fresh practice save.

Useful test points:

| Translevel | Coverage |
| --- | --- |
| `0x09E` | Low song id `02` |
| `0x046` | Low song id `03` and new graphics |
| `0x0A6` | Song id `6D` |
| `0x097` | Low song id `1A` and new graphics |
| `0x05D` | Low song id `06` |
| `0x0BE` | Low song id `05` |
| `0x02B` | Earlier music batch |
| `0x068` | Earlier music batch |

Close the game window to end the session.


Last full-stage manually accepted baseline: [Sky Star / middle-right](star-world-middle-right-restoration.md),
room `$009` with destination `$09B`. The user reports that another agent
completed the work and their playtest found no problems. They also report