# Custom sprite coverage audit

## Method

1. Read the sprite record table at ROM file offset `0x188272`.
2. Read the level placement data and list the rooms that place each slot.
3. Compare each placed slot against the `cheap-demo` record.
4. Report the slots that a room places but that have no program.

Target: `demo11-native-product-r29`.

## Result

| Measure | Count |
| --- | --- |
| Slots placed in at least one room | 167 |
| Slots with a real program | 157 |
| Slots with a no-op stub | 10 |
| Slots with no record | 0 |

## The ten stub slots

All ten are also no-op stubs in `cheap-demo`. The game itself does not run a
program from them.

| Slot | Rooms |
| --- | --- |
| `0x96` | `1F0` |
| `0xA5` | `056`, `102` |
| `0xA6` | `00C` |
| `0xE0` | `192` |
| `0xE8` | `111`, `119` |
| `0xE9` | `1CF` |
| `0xEA` | `1F3` |
| `0xED` | `192` |
| `0xF5` | `1E2` |
| `0xFA` | `184` |

## Two empty slots

Slots `0x2E` and `0x49` are stubs in the product and have real programs in
`cheap-demo`. Neither slot appears in any room placement, in either image.
They need no port.

| Slot | `cheap-demo` program | Rooms that place it |
| --- | --- | --- |
| `0x2E` | `21:9D15`, block 9768 bytes | none |
| `0x49` | `1E:8E22`, block 1322 bytes | none |

## Conclusion

After product r29, no room uses a custom sprite slot that has no program.
The sprite restoration has no open gap that a room reference reaches.

## Engine call check

Both empty slots call standard engine routines. Every one of those routines is
byte identical between `cheap-demo` and the product, except `$0187A7`. That
address is the sprite constructor hook, and it differs in every build on
purpose.