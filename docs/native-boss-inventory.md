# Native Boss dependency inventory

The first selected Boss integration candidate is the Seven Koopalings fight
from the official `boss` demo, room `0FF`, type-1 custom sprite `2A`.
The newer Boss Demo retains the same record and protected program as `7hero`;
the two newer recipient releases have removed that record. This selection
follows the user's newest-available-code policy. It does not qualify a complete
fight or admit the program through the external-code loader yet.

At this inventory checkpoint the PC candidate remained `demo11-native-sprite9e`. This checkpoint
changes investigation tools, source pins and regression inputs only. It does
not install Boss code, change the recipient map, or promote the accepted head.
The subsequent [native opening checkpoint](native-seven-entry.md) implements
A2/A6 mapping and resolves these explicit indirect tables. It also identifies
a later dynamically spawned `6A` dependency that the placed-sprite inventory
did not capture. The [Seven child report](native-seven-child.md) is the current
runtime checkpoint. It names that child as custom `E0` and adds the font
lifecycle.

## Reproducible official inputs

The user requires comparison with `boss.ips` before accepting the batch
`Final Boss.smc`. That condition passes: applying the pinned patch to the
pinned headerless SMW base with an explicit 512-byte copier prefix produces
the same 4,194,304-byte body as both supplied ROMs, with zero differing bytes.

`config/boss-donor.json` pins the authoritative patch and base:

- `../patches/boss.ips`: 3,045,935 bytes, SHA-256
  `066e7aeca041e02bb347bd01a665283263502df0abed1f1708a3fff65b88f881`.
- Original SMW base: 524,288 bytes, SHA-256
  `0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b`.

It also pins both supplied Boss Demo files:

- Headerless SFC: 4,194,304 bytes, SHA-256
  `337fe036f943dafb0df70bdb556e588b785c58ff019b1b00c08f77743e2b3ccd`.
- Batch SMC: 4,194,816 bytes, SHA-256
  `6da68fa6ff14be9eb56f74d91cb1b3412bf1fdd9febc57640d11b2c9211ab29f`.

Removing the explicitly specified 512-byte copier prefix from the second file
produces the first file byte for byte. Preparation now rebuilds from `boss.ips`
and requires both supplied normalized bodies to equal that result byte for
byte. It preserves all originals and refuses to overwrite a different local
output. The new `local/content-versions/boss/ips-verification-receipt.json`
records this comparison; older pre-IPS receipts remain intact.
The separate Boss manifest avoids changing the older IPS-only version catalog.

`tools/audit_boss_dependencies.py` verifies prepared `cheap-demo`, `mazo`,
`7hero`, `boss`, `demo-only-1`, `demo-1-1` and the current native descendant.
It derives the SpriteTool table from the installed constructor in each image;
the table is not at one shared address across releases. It records full code
block and graphics hashes, bounded sprite lists and version-local placements.
Only explicitly selected official releases are consulted.

## Candidate comparison

| Content | Newest retained program in the inspected official set | Protected size | Status |
| --- | --- | ---: | --- |
| Seven Koopalings `2A` | `boss`, identical to `7hero` | 28,478 bytes | Selected first integration candidate |
| mazo room `151`, `9C` | `mazo` | 12,412 bytes | Native entry target qualified. See [the mazo 9C checkpoint](native-mazo-9c.md). Attack, clear and save stay open. |
| mazo room `190`, `9B` | `mazo` | 3,399 bytes | Original map entry observed; role beyond sampled behavior remains open |
| mazo corridor `B0` | `mazo` | 419 bytes | Conflicts with recipient `B0`; namespace adaptation required if recovered |

Seven Koopalings uses record
`0136000035a299440f80228d80220000`, init `$22:800F`, main `$22:808D`.
Its RATS block starts at file offset `0x110000`, SHA-256
`d070d644b5da61d4150e58f4d6603a0ccbe5d0c37b19e7a00c8ffc2d9bb1d757`.
The cheap_demo `2A` program is a different 5,652-byte block; matching numeric
slots do not establish equivalent behavior. Do not substitute it for the newer
fight. Room `0FF` still places `2A` in the recipient, despite its absent record.

Mazo `9C` uses init `$22:800F`, main `$22:8040`, with block SHA-256
`08c840b5967a51742c3037a8d9cfaeda75f6604c0ed687b6f8ecf2331dcec8d1`.
This is a different program from the Seven Koopalings program at the same
bank/offset. They cannot share an immutable mapping at that address unchanged.
The sampled dragon displays the attack title `タイダルウェイブ`; a screenshot
and matching slot establish this observation, not a complete Boss identity or
ending specification.

Mazo places `B0` in rooms `00D`, `10C`, `191`, `192`. Its record is
`01400080308300009889139d89130000`. The current native recipient instead has
`013600b73f0399448bab3c95ab3c0000` in room `003`, the restored Forest Star actor.
Never overwrite that slot globally to recover the mazo corridors. This inventory
does not yet prove that the `151` fight itself requires `B0`.

The later `7hero`/`boss` `C0`–`C2` records are type 3. They are deliberately
excluded from type-1 constructor admission; see the failed earlier `C2` trial
in [the sprite investigation](demo11-level-sprites.md).

## Remaining integration dependencies

The reviewed inline dispatch tables are three-byte JSR entries. Each dispatcher
indexes the operand and performs `JMP ($0000)`. The audit validates the table
opcodes and records explicit bounds and hashes. It does not infer a table
length from adjacent data.

| Candidate | Table | Entries | Dispatcher | Table SHA-256 |
| --- | --- | ---: | --- | --- |
| Seven Koopalings | `$22:8095` | 35 | `$22:8115` | `230b268301db1f8298bbc4004b67710005b92434528967ebfd3e6c39c474ba40` |
| Seven Koopalings | `$22:8118` | 23 | `$22:81C8` | `b84554289224f70205819d44616ad59c0860b081933662305fa7471db23cf2d1` |
| Seven Koopalings | `$22:BB7B` | 21 | `$22:BBF7` | `0f4dd63099b5accb15fb52e0a380b66c509e26eb0b9393b49e7b1ca22d0e0eeb` |
| mazo `9C` | `$22:8048` | 25 | `$22:80A9` | `713aa973453f4917dbca4d821bede453ee8c614f60bc5f6077508b51b0f6afa7` |
| mazo `9C` | `$22:8923` | 13 | `$22:897E` | `f1e9a0065a3a15cc4a287dbfc25dba006da36eb98958c229014965efb913b0f7` |
| mazo `9C` | `$22:8E49` | 8 | `$22:8E7D` | `238264f6b7450df57cfd04e436d03f6353b30659b425f6d3057f2c0c54e15d28` |

The mazo primary dispatcher `$22:80A9` was not reached by the traversal seed.
The report records it as reviewed but unobserved. The other reviewed dispatchers
appear during traversal.

The expanded local JSR traversal reports 351 entry states and 10,050 instruction
variants for Seven Koopalings, and 118 entry states and 3,612 variants for mazo
`9C`. Both candidates report zero unresolved indirects. The counts remain
exploratory: the audit fixes entry M/X to 8-bit and does not expand self-bank
long calls. The Seven recipe's full decoder traversal reports 366 entry states
and 10,353 instruction variants.

The expanded traversal finds 39 source-bank long references for Seven
Koopalings and 72 for mazo `9C`. The mazo references are 71 JSL and one JML.
All 72 are calls, not data references. The executable mapping choice needs
explicit instruction patches and a complete dependency review. Keep the
existing A5 sprite and B6 graphics mappings intact.

## Mazo 9C dispatch review

The two mazo `9C` indirect dispatchers and the Seven Koopalings dispatchers are
reviewed as inline JSR tables. The table above lists their bounds, hashes and
dispatcher sites. The audit seeds both mazo tables. The traversal then reports
zero unresolved indirects and records 118 mazo entry states with 3,612
instruction variants. All 72 mazo source-bank long references are calls. No
source-bank data reference remains.

The mazo `9C` module still needs a recipe, an external-pack mapping, a review of
the room `151` and `190` graphics and gameplay qualification. This review does
not admit the module.

The static recipe is `config/native-content/mazo-9c-module.json`. It pins the
9C record, the three dispatch tables, 72 source-bank call patches and 13 outside
calls. The tool `tools/prepare_mazo_module.py` verifies these pins and writes
the adapted code pack. The adapted program SHA-256 is
`600be50a87fc8fba185f1e3d98e8d35328a9443c92a81156ed6d7f17fa0926b5`.
The receipt is `local/native-modules/mazo-9c-v1/preparation-receipt.json`,
SHA-256 `eeea0a7d7a5d7016bea76ff83b06e346714adff5e11df402325264f054aaaa58`.
The audit records 159 entry states and 4,734 instruction variants with M/X
states, 72 call patches and 71 scheduler sites. Graphics and runtime stay open.

Report: `local/reports/boss-dependencies-mazo-review.json`, SHA-256
`89a481b5165fcf47da32a382dd534203666052c5f481b107cf58a377f063519f`.

Seven Koopalings also calls outside its protected block, including `$10:D8D0`,
`$27:FB02` and `$28:FCC0`. Shared engine/helper compatibility, dynamic graphics,
HDMA, WRAM ownership and retained pointers still need review. RATS ownership
alone does not establish dependency closure.

Room `0FF` has eight decodable donor graphics streams: `28B`, `28A`, `28C`,
`28D`, `1E3`, `15C`, `119`, `28E`, totaling 13,176 encoded bytes and 32,768 decoded
bytes. Their complete hashes are in the report. The ninth metadata word `07F`
is outside the helper's supported graphics table formats; its unresolved status
is not evidence of a missing file. Modern recipient streams that the helper
cannot decode are likewise recorded as unresolved, not accepted as equivalent
by their IDs or room metadata.

Legacy music `33` maps to modern `AC` (Last Battle), per
[the verified music mapping](music-mapping.md). Locate actual donor music writes
and verify the recipient upload/sample path before patching; a selection byte
does not qualify an audible match. Complete fight phases, ending, recipient map
return, real death/re-entry and saved completion remain open.

## Donor evidence and boundaries

Two tracked input scripts reproduce the reviewed captures:

- `recomp/inputs/boss-dependency-seven-entry.script`
- `recomp/inputs/boss-dependency-mazo151-entry.script`

They start with fresh saves, dismiss the original introduction, and enter the
donor's selected map course. A labelled pipe-action fixture then transfers to
`0FF` or `151`. There is no overworld-map transfer, invulnerability, forced
movement or completion-flag write. The 7hero readme warns that changing
overworld maps disables most custom sprites; do not import the recipient's
map-transfer practice route into this donor test.

Captures `local/captures/boss-deps-final-{boss,mazo}-fixture-v1` pass eight checks:

- Boss Demo enters `108`, then the fixture reaches `0FF` with two active custom
  `2A` actors at the first two samples and seven at the last sample. The later
  screenshot shows the combined Boss and WP display.
- Mazo enters `190` with three active custom `9B` actors. The fixture reaches
  `151` with two active custom `9C` actors; subsequent idle samples reach modes
  `0D` and `0E` after the attack. These are sampled donor transitions, not a
  qualified death/re-entry cycle or fight clear.

`tools/check_boss_dependency_evidence.py` verifies original ROM and script
identities, current reference binary identities, completed input logs, dump
sizes, game modes, room numbers, active actor status and the custom-sprite bit.
It records receipt, framebuffer, WRAM and VRAM hashes. Reference options are
explicitly `snes9x_echo_buffer_hack=enabled`; the capture receipts pin the core
and frontend. No audible-output or same-image native parity claim is made.

Earlier `stock-v1`, `buttons-v1`, `select-v1` and `castle-v1` exploratory
captures remain untouched. In particular, the original stock script stopped
at the introduction and does not qualify entry despite its zero exit code.
The initial `boss-deps-{boss,mazo}-fixture-v1` captures also remain intact;
the final captures use corrected fixture comments in fresh directories.

Reports for this checkpoint:

- `local/reports/boss-dependencies-ips-final.json`, SHA-256
  `fb06a9e89986868321b4a137c46a79d555e49fadf8318d0f813d8aad9eb899d8`.
- `local/reports/boss-donor-entry-ips-final.json`, SHA-256
  `1989f983c50ebff7059a7c04f7674bb2d707a0d0b3e9b93d5f0b524797c7a08d`.

All 152 Python unit tests pass, including four new inventory boundary/rejection
tests. The four inventory tests also pass after adding authoritative IPS
preparation. Existing native mapping tests run within the full suite. No new native game
build or gameplay regression capture was needed for this read-only checkpoint;
the previous native gameplay qualification retains its original identities.

The route investigation consulted the community
[Seven Koopalings walkthrough](https://brutalmario.fandom.com/wiki/Seven_Koopalings)
and [Japanese Boss list](https://wikiwiki.jp/kitikumario/%E3%83%9C%E3%82%B9).
Only Brutal Mario behavior is relevant; the separate VIP Mario section is not
an authorized code or asset source. Local source-package assembly is orientation
only until correspondence to the pinned official ROM is established.

## Reproduction and next action

```
python3 tools/audit_boss_dependencies.py --output local/reports/YOUR_FRESH_inventory.json
python3 tools/check_boss_dependency_evidence.py --output local/reports/YOUR_FRESH_entry_check.json
python3 tools/prepare_mazo_module.py
python3 -m unittest discover -s tests -p test_boss_dependencies.py -v
python3 -m unittest discover -s tests -p test_mazo_module.py -v
```

For new captures, use `tools/probe_reference.py` with each tracked script,
the corresponding prepared donor ROM and pinned output manifest. Supply
`SNESREF_CORE_OPTIONS=snes9x_echo_buffer_hack=enabled`. Use a fresh prefix and
`PREFIX-{boss,mazo}-fixture-v1`, then check it with `--prefix PREFIX`.
The Boss manifest is `config/boss-donor.json`; the mazo probe manifest must
contain `target` and the pinned `output` from `config/content-versions.json`.

Next: resolve Seven Koopalings' remaining indirect dispatches and self-bank
long calls, trace its shared helpers/dynamic graphics/music/ending, and define
a bounded native mapping with explicit adaptations. Only then install it into
an isolated descendant and qualify a complete fight and persistence. The
broader content-restoration objective remains open.
