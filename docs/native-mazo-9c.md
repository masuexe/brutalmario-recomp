# Native mazo 9C entry and module view

## Result

The target `demo11-native-mazo-9c` descends from `demo11-native-sprite9e`. It
installs the official mazo 9C record and runs the protected program from an
immutable A2 view. The recipient already supplies the room 151 level data, the
sprite list and eight matching decoded graphics streams. This target needs no
graphics pack.

The checkpoint qualifies these items:

- The room 151 entry with two active custom 9C actors.
- The same actor slots and positions as the donor.
- The map return inside the same sample window.
- The A2 module view execution.
- 830 byte-identical regression comparisons.

## Adaptation

The record install changes one 16-byte sprite table slot. The recipient slot
holds the type-0 placeholder `0000ffffffffffff218001218001ffff`. The installed
record is `0122008035a399440f80a24080a20000`. The init and main banks change
from `22` to `A2`. The file offset is `0x188C32`.

The module recipe is `config/native-content/mazo-9c-module.json`. It pins these
items:

| Item | Value |
| --- | --- |
| Source program | `22:8000`, 12,412 bytes, SHA-256 `08c840b5967a51742c3037a8d9cfaeda75f6604c0ed687b6f8ecf2331dcec8d1` |
| Adapted program | SHA-256 `600be50a87fc8fba185f1e3d98e8d35328a9443c92a81156ed6d7f17fa0926b5` |
| Call patches | 72 sites: 71 JSL and one long JMP |
| Dispatch tables | `22:8048`/25, `22:8923`/13, `22:8E49`/8 |
| Outside calls | 13 shared helpers |

The runtime reuses the immutable external-pack runtime. The target mounts three
packs:

| Pack | Bank | Address | Size |
| --- | --- | ---: | ---: |
| `mazo-9c-code.bin` | `A2` | `A28000` | 12,412 |
| `sprite9e.bin` | `A5` | `A595CD` | 1,291 |
| `star1-ffd.bin` | `B6` | `B68008` | 3,001 |

Room 151 selects the extended graphics IDs `1F5`, `1F4`, `1F2`, `014`,
`280`, `27F`, `281` and `000`. The first seven decoded streams are equal in
both images. The `000` stream is a shared global graphic and is version-local.
The recipient already loads it. The `07F` word is outside the helper table in
both images. The donor and the recipient use the same room 151 level pointer,
sprite pointer and sprite list.

## Verification

The donor capture is `local/captures/boss-deps-final-mazo-fixture-v1`. It uses
the mazo ROM SHA-256
`94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1` and the
tracked script `recomp/inputs/boss-dependency-mazo151-entry.script`. It shows
three active 9B actors in room `190` and two active 9C actors in room `151`.
The 9C slots are `7` and `9` at positions `(168,272)` and `(144,320)`.

The native capture is `local/captures/mazo-9c-entry-v1-native`. It uses the
tracked script `recomp/inputs/mazo-9c-native-fixture.script`. It reaches room
`146` first. It then enters room `151` in mode `14` with the same two 9C
slots and positions. The A2 view reports 1,227,003 resolutions and 196,398
executed page instructions. The runtime rejects no pack.

Both hosts return to mode `0E` by the `fight1200` sample. The donor reaches
fade mode `0D` at `fight600`. The native host reaches mode `0E` at that
sample. The report records this timing difference.

Seven unchanged native routes compare against fresh parent captures. The parent
is `demo11-native-sprite9e`. The routes are Star 1 entry, the Boss route, the
sprite `9E` lift route and custom `6A` rooms `0D8`, `0E2`, `0E3` and
`0E4`. The comparison has 830 byte-identical files.

The module receipt is
`local/native-modules/demo11-native-mazo-9c-final/preparation-receipt.json`,
SHA-256 `5329efdb8ed9f7561b169916df4f56ea87bcb80c0a3f8eb34d82c78d4b87878b`.
The target ROM SHA-256 is
`7d690e9b35493ba49e7f98bb2d63d77ec79ac0c3a78181e4771eb1d6ce012396`.
The native binary SHA-256 is
`51eec706caebc4352dee1502e21d021cd51c2c9f731aa5a9ed3413ee45b17375`.
The qualification report is `local/reports/native-mazo-9c-final.json`,
SHA-256 `d7cbad73707c7f4ab340dff7e198f51f3eb3b87de58f7c5785bcd579f1de027f`.
An independent rerun reproduces this report byte for byte.

The module tests pass 6/6. The full suite passes 182/182 tests. The log is
`local/reports/unit-tests-mazo-9c.log`.

## Limits

The entry window ends at the first map return. It does not prove attack damage,
a fight clear, an ending, a save state or completion writes. The room `190`
9B program and the `B0` corridors remain separate modules. Shared-helper
version behavior and the full attack sequence stay open.

The runtime keeps the variable name `BM_SEVEN_CODE_PACK` for compatibility with
the existing pack loader. The name does not describe the mazo content.

## Reproduction

```
python3 tools/prepare_mazo_module.py
python3 -c "import sys; sys.path.insert(0, 'tools'); import native_seven; native_seven.prepare('demo11-native-mazo-9c')"
python3 tools/m1.py --target demo11-native-mazo-9c scaffold
python3 tools/m1.py --target demo11-native-mazo-9c generate
python3 tools/m1.py --target demo11-native-mazo-9c build
python3 tools/m1.py --target demo11-native-mazo-9c native --script recomp/inputs/mazo-9c-native-fixture.script --capture YOUR_FRESH_ENTRY_NAME
python3 tools/qualify_mazo_9c.py --prefix YOUR_FRESH_PREFIX --parent-prefix YOUR_FRESH_PARENT_PREFIX --output local/reports/YOUR_FRESH_REPORT.json
```

For the parent regressions, run each tracked regression script with
`--target demo11-native-sprite9e` and with
`--target demo11-native-mazo-9c`. Use fresh capture names for both. The
qualifier checks both capture receipts and then compares every dump file.

Skip scaffolding an existing experiment. The runtime refuses a missing, short,
long or corrupt pack. The target does not change ordinary saves or completion
flags.
