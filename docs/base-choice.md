# Base ROM choice: one restoration base, Demo 1-1 as donor

Date 2026-10-23. Answers the question of whether demoOnly1 and Demo 1-1 both need
to be kept as restoration bases. Tool: `tools/audit_base_portability.py`; report
`local/reports/base-portability.json`.

## What the two builds actually are

Measured, not assumed:

| Property | Demo 1-1 | demoOnly1 |
| --- | ---: | ---: |
| Levels with more than 16 bytes of layer1 | 489 | 489 |
| Star World courses (`002`-`00A`) | - | **byte-identical** |
| Rooms `106`, `120`, `138`, `010`, `0CB` | - | **byte-identical** |
| World 1-1 (`105`) layer1 | 7,101 bytes, 24 screens | 7,090 bytes, 20 screens |
| Castle (`10E`) layer1 | 13,777 bytes, 23 screens | 12,176 bytes, 13 screens |
| Extra extended graphics | `29E 29F 2A0 2A2` | absent (now imported) |
| Extra music slots | `69 6A 6B 86 B0` | absent |

The versions share almost the same content set. Of the 22 levels whose layer1
differs, eleven are near-identical small edits, one pair is a pure relocation
(`04F` in Demo 1-1 == `00C` in demoOnly1), one level (`168`) is a stub in demoOnly1,
and only **World 1-1 and the castle are genuine rewrites** - the newer content the
user identified.

## Cost of rebasing the chain onto Demo 1-1

`audit_base_portability.py` re-checks every pinned `before` byte of every
restoration patch against a candidate base:

| Recipe | Sites agreeing on Demo 1-1 |
| --- | ---: |
| `star-world-forest` | 9 / 9 |
| `world1-next-course` | 2 / 3 |
| `world1-room138`, `world1-room138-audio` | 1 / 1 each |
| `star-world-lower-inner` | 1 / 7 |
| `star-world-center`, `star-world-lower-right`, `star-world-upper-left` | 0 / 1 each |
| `world1-room138-sprite` | 0 / 1 |
| **Total** | **14 / 25 (56%)** |

56% agreement means rebasing is **not** a rename: eleven sites land on different
data in Demo 1-1, so their patches, allocations and captures must be re-derived,
and the whole chain re-qualified. The tool treats agreement as a lower bound, so
real cost is higher.

## Recommendation

Keep **one restoration base**: demoOnly1. Keep Demo 1-1 only as a pinned **donor**, a
role it already plays for the graphics import. Keeping both as product bases would
duplicate qualification and save state for two courses' worth of difference.

Why demoOnly1 rather than Demo 1-1:

- Engine, save-format, Boss, shop and map work already qualified on demoOnly1.
- Star World, room106/120/138/010/0CB are byte-identical, so Demo 1-1 gains nothing
  there.
- Demo 1-1's genuinely newer content is exactly two courses plus resources, and
  resources can be imported without changing base.

## Consequence: how the newer World 1 content gets in

1. Resources first - done for `29E 29F 2A0 2A2` in `demo11-extra-graphics`.
2. Then an isolated descendant that replaces room `105`'s layer1, sprite list and
   graphics record with Demo 1-1's, re-patching the shared pointer tables.
3. Re-qualify 1-1's goal/save chain and the 1-1 -> room106 -> room120 links, which
   currently pin the older layout.
4. Only then consider the castle, which is a ten-screen extension plus `2A2`.

Step 2 is a content replacement, not a dependency recovery: it changes the course
the player sees. It therefore needs the user's explicit go-ahead; the old layout
remains reproducible from the pinned demoOnly1 input ROM.

## What "keep both" would mean if chosen instead

Both ROM files stay under `local/content-versions/` either way - they are pinned
inputs, not maintained products. The real question is how many *candidate lines*
are qualified. Keeping two lines doubles the qualification surface for a handful of
differing rooms and should be avoided unless a later decision requires Demo 1-1's
engine behaviour itself.
