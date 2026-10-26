# Native mazo B0 corridor plan

## Result

The mazo `B0` corridor actor has a static module review. The corridor rooms are
not in the recipient. This document records the measured data and the next
steps. It does not qualify playability.

## Module

| Item | Value |
| --- | --- |
| Record | `01400080308300009889139d89130000` |
| Init | `13:8998` |
| Main | `13:899D` |
| Block | `13:8989`, 419 bytes, SHA-256 `b98c2ce2014d4cff3e8fcbb75eec936b8e04446e503f541ce9efdff85b8846e8` |
| Native view candidate | `A2:8989` |

The audit finds 6 entry states and 177 instruction variants. The module has no
dispatch table and no call patch. It has no source-bank long reference. Its 6
absolute operands stay inside the block. The four outside calls are
`01A7DC`, `01ACF9`, `01B7B3` and `0285BA`.

The recipe is `config/native-content/mazo-b0-module.json`. The module receipt
is `local/native-modules/mazo-b0-v1/preparation-receipt.json`, SHA-256
`188fc1bb41bf1a95af89c17889049c007fe110ba4201ab398bac927afa137b5c`.

## Corridor data

| Room | L1 bytes | L2 | Sprite list bytes |
| --- | ---: | --- | ---: |
| `00D` | 21 | empty (`FF`) | 16 |
| `10C` | 6 | empty (`FF`) | 517 |
| `191` | 105 | sentinel `FFDE54` | 472 |
| `192` | 99 | sentinel `FFDE54` | 8,290 |

Each room also has a 32-byte graphics and palette record. The level streams and
the sprite lists total 9,526 bytes. The records total 128 bytes. One external
bank of 32 KiB has enough room.

The donor L1 streams are raw object streams that end with `FF`. The `FFDE54`
L2 values are empty-layer sentinels. Copy the values, not layers.

The recipient rooms differ. Rooms `00D` and `10C` point at other level and
sprite data. Rooms `191` and `192` point at the empty level `0x068000`. The
recipient has 49 level entries that point at `0x068000`.

## Namespace

The recipient `B0` slot is the ForestStar room `003` actor. Keep that slot.
The donor `B0` program needs a free SpriteTool slot.

A room sprite entry carries the custom id in byte 2 when bit 3 of byte 0 is
set. The imported lists need byte 2 changed from `B0` to the new id. A raw
bit-3 scan over all rooms misreads standard sprites. The corrected scan is the
next task.

## Next steps

1. Run a corrected custom-id scan and choose a free SpriteTool slot.
2. Copy the four rooms into one A7 data pack. Choose four free recipient level
   slots. Patch the level, sprite and metadata tables.
3. Add a target with the A2 code pack, the A7 data pack, the A5 sprite pack and
   the B6 graphics pack.
4. Capture a fixture entry into the imported rooms. Qualify the actors and the
   room graphics.
5. Never overwrite the recipient `B0` slot.

## Reproduction

```
python3 -c "import sys; sys.path.insert(0, 'tools'); import prepare_mazo_module as p; from pathlib import Path; p.prepare(Path('local/native-modules/mazo-b0-v1').resolve(), Path('config/native-content/mazo-b0-module.json').resolve())"
python3 -m unittest discover -s tests -p test_mazo_module.py -v
```
