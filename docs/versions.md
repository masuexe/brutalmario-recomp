# Versions and input inventory

Inspected on 2026-10-15. Provenance is recorded as user-supplied local material. Download sites, author provenance, and official release dates have not been independently authenticated. Filesystem timestamps are not release-date evidence.

Scanned 1,746 regular files: 21 under patches, 1,724 under references, and one ROM. References includes an outer download ZIP, three inner ZIPs, and 1,720 extracted files; duplicate archive/extracted copies are not separate versions.

That count describes the initial inventory. A second base ROM,
`Super Mario World (U).smc`, was supplied afterward. Its game body is identical
to the original base; it adds a 512-byte copier header. The aligned Demo 1-1
patch result is identical to the existing research target; see the
[base comparison](compatibility.md#comparison-with-the-users-working-base).

All regular members of ten ZIPs were read and hashed, also checking ZIP CRCs. No unsafe paths or symlinks were found, and nothing was extracted. Each member has a same-hash loose file in its input tree; this is not exhaustive path-by-path authentication. All nine standalone IPS files parse successfully and match archived copies.

## Content and evidence

| Material | Confirmed contents | Status / scope |
| --- | --- | --- |
| 1-1 | ZIP contains only 1-1.ips | Primary target; level/boss list unknown |
| demoOnly1 | ZIP contains only its IPS | Historical candidate; content relationship to 1-1 unknown |
| demo6 / demo7 | Each ZIP contains its IPS | Historical candidates; dates/content differences unknown |
| cheap_demo | ZIP contains cheap_demo, 7hero, mazo, and ow IPS/readme pairs plus 7hero.xls | All four candidates are present |
| 7hero | Bundled notes describe a Bowser Castle boss test, not the final boss, with branches and unfinished content | Documentation evidence; untested |
| mazo | Bundled notes describe a final-dungeon midboss with unfinished difficulty balancing | Documentation evidence; untested |
| ow | Bundled notes describe an overworld-only test without course data | Do not treat as a complete demo |
| demo8 | Bundled notes identify an unofficial cheap_demo edit combining demo7/cheap_demo-like content, with inaccessible courses | Not evidence of an official carol successor |
| data / data1 / data2 | Different sets of sprites, level ASM, blocks, and music text | Correspondence with target ROM unknown |

Source packages do not establish a complete game source release; see [source-analysis.md](source-analysis.md). IPS size and write ranges do not prove which levels or bosses exist. A content matrix still requires ROM inspection and gameplay.

## Standalone IPS files

All have exclusive write extent `0x400200` and no explicit final-size field after EOF. See [compatibility.md](compatibility.md) for alignment/base analysis.

| Path relative to patches/ | Bytes | Records | RLE records | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| 1-1.ips | 3,861,390 | 6,001 | 139 | `6a2425d0da2d222bbb86a2a0e1c509d2ec532774467c47c7858e50a4dae1b36e` |
| cheap_demo/7hero.ips | 3,841,447 | 5,472 | 11 | `fbc1981c4e21cdffda785eeccca534e56da3e88ab53749afe1bf0d00f8bc8766` |
| cheap_demo/cheap_demo.ips | 3,838,623 | 5,267 | 12 | `9c2ff02783ec5416988dc60c2e232b0b5dd6c31e8941f127a70d9df6e96bbae2` |
| cheap_demo/mazo.ips | 3,841,249 | 5,484 | 9 | `3eea9422a0585d0c1d12e0afa8e05e5a5b007238be1df35261d28e2f0c896272` |
| cheap_demo/ow.ips | 3,841,216 | 5,465 | 9 | `c65cc8be84b5b382e88a62463737380909bad7a2a7ab38b7ea9ae4b170e22117` |
| demo6.ips | 3,836,644 | 5,233 | 6 | `569c02b13534cf02e55750bc3c759a2e29d5c6b852b89c9c5b27af71edaad8d4` |
| demo7.ips | 3,836,609 | 5,179 | 6 | `2df0c5ac2dd7196ece5aee54cf58bdddd975a22bd6eba97de3621f0654b14b99` |
| demo8/demo8.ips | 3,297,358 | 9,378 | 2132 | `480d6ed8ea59bb0104b234766497a680032e8072ac042d5edfa0a78deef6d4c7` |
| demoOnly1.ips | 3,860,889 | 6,029 | 141 | `1080862aaf3e9bacfae97868806ee8faa53b2b4d6518fd2713aeda3c0c5e6880` |

## Original ZIP archives

Entry counts include directories; expanded size sums declared member sizes. Inputs have not been reauthenticated against external download sources.

| Path | Compressed bytes | Entries | Expanded bytes | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| ../patches/1-1.zip | 1,246,513 | 1 | 3,861,390 | `17e67f9fa564901524fa39e20eea6ac9107845ad95ec3fa6e401bc352f08bc9a` |
| ../patches/cheap_demo.zip | 6,966,091 | 10 | 15,405,185 | `619cf48b14377c1543b41aee2979572ae7b2b63967c481e20637c278ec27e46e` |
| ../patches/demo6.zip | 1,325,373 | 1 | 3,836,644 | `dcd87399b9b11cfe25c91a767569e91c45ed36048f1070640764199fa2e0caf8` |
| ../patches/demo7.zip | 1,386,405 | 1 | 3,836,609 | `3bae94dcc589d4fd3aec8a3ede5ef2cb76b1f4ac199c62565cbb0efd23ad4667` |
| ../patches/demo8.zip | 1,791,895 | 2 | 3,297,949 | `efa11a69aa8890043949393e3c68d423c0d723a167c05ab269be07afd4565377` |
| ../patches/demoOnly1.zip | 1,189,740 | 1 | 3,860,889 | `d2a8949924c34ff8d0e1bfeab19429aa3d1e2e6d872b1828778300a0714de97f` |
| ../references/drive-download-20261015T041215Z-1-001/data.zip | 911,026 | 589 | 4,825,932 | `b8e4b31bd3e56bda07a9558182e19b5d4c2ae5b2c84efd9677ac69ed1636d1f4` |
| ../references/drive-download-20261015T041215Z-1-001/data1.zip | 886,461 | 547 | 4,868,057 | `a2d50af993102f318229e06cb409ade33abfbcbcc7d91c43e826769b7b7f625d` |
| ../references/drive-download-20261015T041215Z-1-001/data2.zip | 988,463 | 597 | 5,363,031 | `a5b530221dfaa6a2395d9b63bfdc3d286c164bce043b79f087354da1cf772404` |
| ../references/drive-download-20261015T041215Z-1-001.zip | 2,786,841 | 3 | 2,785,950 | `71864be38fa0ad6ee2946ed7861215d1543eb5af644330b138179f715fb58b57` |

## Unknown or uncollected

- No confirmed matching archive for Demo 7.5 or other separately named Boss Demos; do not infer inclusion from names.
- 7hero.ips is present, but correspondence with releases called `7herodemo` elsewhere is unproven.
- No authoritative per-version content lists; undefined, unfinished, and intentionally removed content remain unclassified.
- Complete per-file/member SHA-256 metadata is in `local/reports/inventory.json`, without file bodies.
