# Rebuild a stale sprite gap target

## Symptom

A test such as `tests/test_sprite_10_14.py` fails with:

```
ValueError: combined gap target ROM size/SHA-256 does not match pinned input manifest
```

`python3 tools/m1.py generate` and `build` fail with the same message.

## Cause

Two separate drifts exist.

1. The local build output is older than the config that pins it.
2. The tool files changed after the preparation receipt was written.

The second drift makes `write_verified` refuse to replace the receipt. The
guard is correct. Do not bypass it.

## Procedure

1. Confirm that the ancestor chain is consistent. Walk each
   `base_restoration` from the target down to `demo11-base` and compare each
   `rom.sfc` with its `output` block.
2. Preserve every file that the tool refuses to replace. Rename it with a
   `-superseded-<date>` suffix. Do not delete it.
3. Run `native_sprite_gap.prepare(target)` again. Repeat step 2 for each
   refusal.
4. Compare the new `rom.sfc` with `config['output']['sha256']`.
5. Run the related test.

```
python3 -c "import sys; sys.path.insert(0,'tools'); \
  import native_sprite_gap; \
  print(native_sprite_gap.prepare('demo11-native-sprite10-14'))"
```

## Result for `demo11-native-sprite10-14`

Six files were preserved. The preparation then completed.

| Item | Value |
| --- | --- |
| Rebuilt ROM SHA-256 | `1a0cc34578cb65da83d666a91369f632962dee5f6c0e178f5d0e90558aff55f0` |
| Config `output` SHA-256 | same |
| `tests/test_sprite_10_14.py` | 6 tests pass |
| Full suite | 533 tests pass |

The rebuilt image is byte identical to the pinned value. The chain was never
inconsistent. Only the local build output was stale.

## Files preserved

- Four `preparation-receipt.json` files in the four module directories
- `rom.sfc` and `input-manifest.json` in the target directory