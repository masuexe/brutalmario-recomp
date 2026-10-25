# World-by-world extended graphics restoration

Date: 2026-10-26. Nine graphics batches close every empty extended graphics
slot of Worlds 2 to 8. All graphics come from 7hero.

## Cause and result

Several levels referenced extended graphics IDs that the Demo 1-1 line never
had. The slots were empty, so the levels loaded without those tile sets. Some
rooms then returned to the map, died or showed missing textures.

After the batches:

- Every room of Worlds 2 to 8 has no empty extended graphics slot.
- Eight translevels now stay in gameplay: `047`, `041`, `037`, `016`,
  `031`, `022`, `020` and `04C`.
- Five playable translevels change their visible tile sets: `025`,
  `01C`, `02E`, `057` and `019`.
- Translevel `05F` keeps its special mode `17`.

## Batches

| Target | Base | IDs | ROM SHA-256 |
| --- | --- | --- | --- |
| `demo11-gfx-world23` | `demo11-fix-batch-p` | `183`, `355`, `353`, `354`, `115` | `c207fc76434c5a9b` |
| `demo11-gfx-world4a` | `demo11-gfx-world23` | `15A`, `158`, `159` | `b5aae804c19d2030` |
| `demo11-gfx-world4b` | `demo11-gfx-world4a` | `21A`, `219`, `21B`, `214` | `ce0f140dd80b2e0d` |
| `demo11-gfx-world5` | `demo11-gfx-world4b` | `1EB`, `1EA`, `1EC`, `185`, `11E`, `11D`, `167`, `166` | `d1931a3c2c943de3` |
| `demo11-gfx-world6` | `demo11-gfx-world5` | `195`, `194`, `192`, `191`, `18F`, `182`, `184` | `f651f57b31005aba` |
| `demo11-gfx-world7` | `demo11-gfx-world6` | `1B4`, `1B5`, `152`, `1BF` | `c892409d19b4c0d8` |
| `demo11-gfx-world8a` | `demo11-gfx-world7` | `1D6`, `1D7`, `1D8` | `e35c689e5d208dc9` |
| `demo11-gfx-world8b` | `demo11-gfx-world8a` | `105`, `108` | `82b47c0a39e7af3a` |
| `demo11-gfx-world8c` | `demo11-gfx-world8b` | `400`, `401`, `402` | `03704a35e5b80676` |

Chain end native binary:
`b729ba48d58c6d4077e9e66913ee32d30ca4e5111239b1832b69e48659eeeefe`.

## Room coverage

| World | Rooms that had empty slots |
| --- | --- |
| World 2 | `123` |
| World 3 | `11D` |
| World 4 | `113`, `071` |
| World 5 | `016`, `10D`, `072` |
| World 6 | `101`, `022`, `020` |
| World 7 | `01C`, `12F`, `10A`, `133` |
| World 8 | `019`, `128`, `13B` |

## Verification

`tools/qualify_demo11_gfx_worlds.py` checks the chain identities, the donor
data, every installed RATS block, the room dependencies, the empty-slot
coverage for Worlds 2-8, the fifteen captures and the native build identity.
The suite reports **46/46**. The whole-line audit for the chain end passes:
456,391 changed bytes inside the reviewed regions and zero unexpected bytes.

Captures: `local/captures/gfxw-*` and `local/captures/gfxwn-*`.

## Full-range survey after the batches

The full-range survey ran on the chain end. It reports 255 loads, zero
Mario Start stalls and 218 playable translevels. The head survey before the
batches reported 207 playable translevels.

| Result | Count |
| --- | ---: |
| Playable | 218 |
| Mode `0E` | 28 |
| Mode `0D` | 4 |
| Mode `0C` | 2 |
| Mode `0B` | 2 |
| Mode `17` | 1 |

Translevels `077` and `07B` still return to
Yoshi's House. Qualifier: `tools/qualify_demo11_gfx_full_range.py`.
Reports: `local/reports/demo11-course-survey-gfx-chain.json` and
`local/reports/demo11-course-survey-gfx-tail.json`.

## Limits

- The claim is bounded: no empty slots remain and the sampled scenes load and
  show the new tile sets. A full course pass is not claimed.
- The chain end is a candidate. The head is still `demo11-fix-batch-p`.
