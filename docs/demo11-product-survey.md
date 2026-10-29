# Product-line course load survey

Date: 2026-10-29. Target: `demo11-native-product-r12`. ROM SHA-256
`d29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552`.

## Result

The native product loads all 255 translevels. No Mario Start stall remains.
The survey finds one crash. The crash is at translevel `094` (level `170`),
and the base ROMs load the same level.

| Result class | Count |
| --- | ---: |
| Playable (`14`) | 227 |
| Map return (`0E`) | 11 |
| Death states (`0B`, `0C`, `0D`) | 14 |
| Loading state (`13`) | 1 |
| Unexpected state (`17`) | 1 |
| Crash (`00`) | 1 |

## Method

The scripts are the ones from the [course survey](demo11-course-survey.md).
Each script enters one translevel through the map 6 lower-left node and
overrides the node level byte. Each capture starts from a fresh session. This
run uses the native runtime with the product packs.

- Captures: `local/captures/r12-survey-TTT`, 255 directories.
- Report: `local/reports/demo11-course-survey-r12.json`.
- Text table: `local/reports/demo11-course-survey-r12.txt`.
- Reproduction:

```sh
python3 tools/m1.py native --target demo11-native-product-r12 \
  --script local/probes/demo11-course-survey/course-094.script \
  --capture r12-survey-094
python3 tools/survey_demo11_courses.py report --first 0x001 --last 0x0FF \
  --target demo11-native-product-r12 --prefix r12-survey- \
  --report local/reports/demo11-course-survey-r12.json
```

## Comparison with the reference survey

The closest reference survey is `demo11-sprites-room8f-boss`
(`local/reports/demo11-course-survey-r8fb.json`, 255 entries).

| Result class | Reference | Product native |
| --- | ---: | ---: |
| Playable | 232 | 227 |
| Map return | 14 | 11 |
| Death states | 6 | 14 |
| Other | 3 | 3 |
| Crash | 0 | 1 |

Nine translevels differ. Eight differ only in death or return timing. The
samples show gameplay at frame 240 and a lost life at frame 600 on one host
and not the other. Those entries are not stalls.

| Translevel | Reference at 600 | Native at 600 | Note |
| --- | --- | --- | --- |
| `008` | playable | `0B`, one life lost | No-input death. |
| `060` | playable | `0C`, one life lost | No-input death. |
| `075` | playable | `0D`, one life lost | No-input death. |
| `086` | playable | `0D`, one life lost | No-input death. |
| `087` | playable | `0C`, one life lost | No-input death. |
| `088` | map return, one life lost | `0C`, one life lost | Same death, later state. |
| `089` | map return, one life lost | `0D`, one life lost | Same death, later state. |
| `08A` | map return, one life lost | playable | Same class, earlier state. |

## The crash at translevel 094

The crash is the only product-specific failure.

| Image | Host | Translevel 094 result |
| --- | --- | --- |
| `demo11-star-bgm` | reference | Room `170`, mode `14` |
| `demo11-sprites-orphan-cleanup` | reference | Room `170`, mode `14` |
| `demo11-native-sprite9e` | reference | Room `170`, mode `14` |
| `demo11-native-product-r12` | reference | Mode `00`, garbage room |
| `demo11-native-product-r12` | native | Mode `00`, garbage room |

The native log holds eight `BRK` entries. The first reads `$80:B0E3`.

The product ROM carries the type-3 records `C0`, `C1` and `C2`. The `C2`
record points to `CD:DD30`. Room `170` places slot `C2` once. Room `16B`
places `C0` and `C1`, and translevel `08F` loads with room `16B` normally.

The [level sprite batch](demo11-level-sprites.md) recorded this failure before
the type-3 install. A 7hero test chain with the `C2` record produced a black
screen, mode `00` and garbage WRAM on level `094`. The chain without `C2`
loaded the level normally. The record needs its own investigation.

The product installed the records with adapted bank pointers and without the
constructor patch. The crash remains. The [type-3 report](native-sprite-type3.md)
qualified the records-only install through a pipe fixture into rooms `16B` and
`170`. That fixture did not exercise the normal load of level `094`.

## Limits

The survey uses a map node override. It does not claim map routes, course
completion, saves or audio. A load result is not a play result. The reachability
of level `094` on the real map is not verified by this run.

## Next actions

1. Remove the `C2` record and pack from a product descendant. Rerun the
   translevel `094` capture. This confirms the cause.
2. If the removal restores the load, keep `C2` out of the product until the
   constructor work succeeds. Keep `C0` and `C1`, which room `16B` loads.
3. Rebuild the product game with the fix and rerun the full-range survey.
4. Run the same survey on each new candidate before a release decision.
