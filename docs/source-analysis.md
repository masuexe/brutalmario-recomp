# Initial source analysis

Inspected on 2026-10-15. Only local files and archive contents were read; no third-party tools or assemblers were executed.

Reference directory: `../references/brutalmario-data/`. The outer download ZIP contains `data.zip`, `data1.zip`, and `data2.zip`. Every regular member of these packages has a matching SHA-256 among the existing extracted files; this verifies content matches rather than relying on filenames.

| Package | Extracted source root | Regular files | ASM | CFG | TXT | Other |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| data.zip | data/data/ | 584 | 330 | 176 | 77 | blk/blk.dsc |
| data1.zip | data1/ | 543 | 299 | 167 | 77 | None |
| data2.zip | data2/ | 593 | 325 | 191 | 77 | None |

Contents include `sprites/` (`sprites - kopie/` in data2), `levelasm/`, `blk/`, `custommusic/`, and sprite-number lists. Candidate boss sources include `7hero.asm` and `marx.asm`. Names alone do not establish correspondence with Demo 1-1 binaries.

## Package differences

Compare relative paths and original bytes, normalizing only data2's sprite directory to `sprites/`. Line endings, encodings, and list filenames are not normalized.

| Comparison | Same path and bytes | Changed at same path | Only in first | Only in second |
| --- | ---: | ---: | ---: | ---: |
| data to data1 | 432 | 71 | 81 | 40 |
| data1 to data2 | 471 | 71 | 1 | 51 |

Changed sources include `7hero.asm` and `ark.asm`. Sprite ID `0F` names nova in data/data1 and starship in data2. Sprite IDs cannot be shared blindly. Package names and ZIP timestamps do not establish official chronology or coverage.

## Toolchain clues and missing dependencies

- Sprite sources use entry markers such as `dcb "INIT"`; CFG files reference ASM; hexadecimal sprite lists reference CFG files. This suggests a traditional sprite-insertion workflow but does not identify the exact tool or release.
- Syntax includes `dcb`, `dcw`, `org`, `.W`, and absolute addresses. Compatibility with xkas, Asar, or another assembler remains untested.
- `levelasm/night.asm` uses `org $2BFC00`; `thunder.asm` uses `org $2D9410`. Relocation and integration require address and dependency analysis.
- No assembler executables, build scripts, separate `.inc`/`.bin` assets, or license files were found in these three packages. They are not established as complete rebuildable projects. Music insertion tooling for `custommusic/*.txt` remains unknown.
- On a case-sensitive filesystem, every package's pumpkin.cfg references `Pumpkin.asm` while the file is `pumpkin.asm`. Additionally, data1 lacks CFG-referenced `test2.asm`, `roto_disc.asm`, and `test.asm`; data2 lacks `test2.asm` and `test.asm`. These are package-local path checks, not proof that those CFG files participate in an actual build.

## Evidence relevant to recompilation

`data/data/levelasm/levelasm_code.asm` constructs instructions starting at WRAM `$7F:FFF0` and executes `JSL $7FFFF0`. Runtime-generated code is explicitly present in the supplied source. A ROM-only translation must account for WRAM execution if this mechanism is used by the target.

The file also contains `JSL $777777`; its meaning and possible insertion-time replacement are unknown. An initial adjacent-machine-code signature search did not match the in-memory Demo 1-1 candidate. **This source has not been proven to be the implementation executed by the target ROM.**

Next, locate actual Demo 1-1 entry points and connect sources through bytes, addresses, and execution traces. Do not treat unverified source labels or constants as authoritative analysis configuration.

See `tools/analyze_m0.py` for reproducible comparisons. Full changed-path lists, missing references, and signature-search results are in `local/reports/analysis.json`.
