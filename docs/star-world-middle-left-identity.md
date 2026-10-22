# Middle-left star: duplicated donor content

The map-6 middle-left entrance at `$0158,$01A8` selects translevel `$03`,
room `$003`. The user noticed that its enemies duplicate a World 1 water
course even in unmodified demoOnly1, where its terrain is missing.

The observation is confirmed in the pinned inputs. cheap_demo itself contains
the duplicated water course in `$003`; the restoration did not substitute
room `$120` for it. The existing restoration's gameplay/save qualification
does not establish that a distinct original forest course has been restored.

## Direct comparison

Inputs are verified against `config/content-versions.json`:

- cheap_demo: `f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822`.
- demoOnly1: `b8d86f894f6c07aeb74794c59adab8f336080285b4781a3e1c921615a2d8216b`.

| cheap_demo data | Room `$003` | Room `$120` |
| --- | --- | --- |
| Layer-1 pointer | `$60:8061` | `$1C:D27F` |
| Protected object payload size | 9,769 bytes | 9,769 bytes |
| Sprite pointer | `$60:A89C` | `$1C:FABA` |
| Sprite records | 34 | 34 |
| Graphics selection record | Identical | Identical |

All 34 three-byte sprite records match as a multiset: ids, coordinates and
encoded flags are identical. Only their storage order differs. These records
include enemies and other actors, so this is broader than an enemy-count match.

The object payloads differ at just four byte offsets: `$261D,$2620,$2621,$2624`.
The differences exchange the two trailing four-byte screen-exit records
`06 04 00 2A` and `0D 04 00 8E`. Normalizing that order makes the complete
payloads identical. There is no different terrain hidden in the donor copy.

Room `$003` object SHA-256 is
`6e7c68eeee9ffb5874376874505a16b59aa6165bae3e9684a572591003fb89b2`,
which is exactly the stream pinned by the restoration recipe. Room `$120`
has SHA-256 `19dd16614c5721478345bcc37fdb48f39c3f8902d0e49b8df5105c509f14b726`.

In demoOnly1, `$003` and `$120` have byte-identical sprite lists, SHA-256
`f4aca24ffc3000ec1b3662c639c15cbf882f89754f8114bf4758f3c6c6c1f602`.
Room `$003` has only the short terrain stub, while `$120` retains a substantial
water-course stream. This explains why the original already duplicated the
enemy layout despite its missing terrain.

Reuse is proven; whether the author intended a temporary placeholder or
permanent reuse cannot be inferred from those bytes alone.

## Other prepared versions

| Prepared version | Room `$003` protected object payload | Sprite count | Sprite multiset equals its room `$120` |
| --- | ---: | ---: | --- |
| demo6 | 1,734 bytes | 14 | No |
| demo7 | 1,734 bytes | 14 | No |
| demo8 | 1,737 bytes | 14 | No |
| cheap-demo | 9,769 bytes | 34 | Yes |
| ow | 9,769 bytes | 34 | Yes |
| mazo | 9,769 bytes | 34 | Yes |
| 7hero | Short stub | 34 | Yes |
| demo-only-1 | Short stub | 34 | Yes |
| demo-1-1 | Short stub | 34 | Yes |

demo6 and demo7 share the 1,734-byte object payload with SHA-256
`b3f9b88e8b3366e0ccea6ae1f6d4ac0d49bcdc633e9e45ba98c20a4f517ee65e`.
They provide a distinct candidate for restoring the forest course instead
of keeping the repeated water course. This inventory alone does not qualify
their complete traversal, exits, resources or migration compatibility.

A fresh demo7 reference diagnostic reaches room `$003`: the first sample is
the No-Yoshi entrance, a transition sample is black, and the later active
sample shows a forest/vine setting, coins and yellow platforms. The diagnostic
selects same-number room `$003` through an overworld tile fixture; it does not
prove a natural donor-map route or a full clear. cheap_demo's already captured
active room `$003` shows the duplicated underwater cavern.

Local evidence:

- `local/probes/middle-left-identity/room-comparison.json`.
- `local/probes/middle-left-identity/version-survey.json`.
- `local/captures/hub-donor-158-1a8/entry600.*` (pinned cheap_demo).
- `local/captures/middle-left-demo7-identity/entry1200.*` (fresh demo7).
- Converted diagnostic screenshots under `local/probes/middle-left-identity/`.

No ROM, sprite, terrain, exit or restoration recipe is changed by this
investigation. The subsequent [independent Forest Star restoration](star-world-forest-restoration.md)
qualifies that course separately using demo8's retained forest data. It keeps
the water restoration and cumulative center target as available baselines.
