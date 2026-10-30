# Hollow normal exit, persistence and missing branch

Date: 2026-10-29. Target: `demo11-native-product-r13`.
ROM SHA-256:
`c02dc11e0c79c804740b38797463a1fc9645a8a05cdb4e18c7c09fff45760681`.
Native binary SHA-256:
`131b9522f4edfa4eba5793780f228a9f3ed1c7a7e040e46e00bd6f032e493be0`.

## Result

The existing route `11F -> 039 -> 043` reaches a real goal tape, returns to
Ghost Forest, saves both completion copies and survives console reset/File A
reload. Ordinary onward entry loads room `114`. The newer entrance also has an
Up-entry branch to room `182`. Its placed custom sprite `A2` has a placeholder
record in r13 and does not remain active in the measured room. A matching
placement and a protected code candidate exist in official demoOnly1.

This is assisted normal-exit/save acceptance and a reproduced branch defect,
not complete course acceptance. Position, initial map, pipe-action and immunity
fixtures bypass traversal. No actors, destinations, events, completion flags
or saves are written. No game code, ROM, resource pack or intended mechanics
changed. Five Forest normal exits now have saved boundary evidence; five more
remain, alongside full traversal, branches, collectibles and experience checks.

## Identity and existing routes

The [Forest catalog](forest-course-identity.md) identifies room `11F` as
It's Moldy Within the Hollow, translevel `43`, actual map-0 node `01B8/0158`,
index `35B`. The [Forest directory](https://brutalmario.fandom.com/wiki/Forest)
links this course, but its individual Fandom walkthrough could not be fetched
on 2026-10-29. The Japanese [map directory](https://wikiwiki.jp/kitikumario/マップ攻略)
was also consulted. No unverified puzzle description is used to infer missing
behavior or completion.

Live exits and bounded source allocations establish the following:

| Boundary | Evidence |
| --- | --- |
| Existing entrance | Actual node assignment `D35B=43`; ordinary entry `11F`, mode `14`, translevel `43` |
| Normal interior | Existing entrance screen `02`, `39/04` -> room `039` |
| Normal goal room | Existing room039 screen `18`, `43/04` -> room `043` |
| Tape | Vanilla `7B/08` -> `7B/06`; sampled at real goal timer `E0` |
| Map return | Four lives; naturally selects Ghost Forest `01E8/0188` |
| Completion | WRAM `1EE5`, SRAM `0043` and `01F0` change `0F -> 8F` |
| Reset/File A reload | All three retain `8F`; Ghost Forest remains selected |
| Ordinary onward entry | Room `114`, translevel `38`, mode `14` |

No map-position fixture occurs after the goal. Room039 also has authored exits
on screens `0C` and `12`; the `0C -> 03A` optional room was observed in a local
probe but is not accepted by this normal-route checkpoint. Entrance exits left
in the live table after a transition are not automatically authored exits of
the new room.

The checker pins six official sources: Demo 1-1, demoOnly1, boss, 7hero, mazo
and cheap_demo. The modern `11F` Layer 1 allocation is 45 bytes; older sources
have 31 bytes and lack the new screen03 branch. Their Layer 2 and sprite lists
match. Room039 Layer 1 allocations and placements match the two modern sources,
boss and 7hero; mazo/cheap_demo differ. Room043 allocations and placement match
all six. These are component identities, not whole-engine behavior parity.

Room039's Layer 1 RATS allocation is 20,849 bytes in the recipient. Allocation
bounds and hashes must not be described as a parsed semantic level extent.
Layer 2 can be a background stream; the earlier unbounded exploratory object
parser can skip a terminator and consume neighboring data. Source allocations,
bounded sprite lists and live exits take precedence over that output.

## Missing A2 branch and official candidate

Both branch controls use the same existing node and player-position fixture
at `800/352`, followed by an ordinary button input. They never write the pipe
action or a destination. Up enters `182`, mode `14`; Down remains in `11F`.
Neither clears the course, loses a life or changes either saved flag.

The current room182 sprite list is `0069d0a2ff`: a custom `A2` placement. Its
record is the type-0 placeholder `0000ffffffffffff218001218001ffff`. Native
and same-image reference both have no active actor after entry. This establishes
a missing program on an accessible branch, not its intended complete gameplay.

The earlier [gap inventory](native-sprite-gaps.md) examined only 7hero,
cheap_demo and mazo. All three lack this slot, as do boss and Demo 1-1.
Official demoOnly1 has the same room182 sprite list and an actual type-1 record:

| Candidate property | Official demoOnly1 value |
| --- | --- |
| ROM SHA-256 | `b8d86f894f6c07aeb74794c59adab8f336080285b4781a3e1c921615a2d8216b` |
| Record | `012200b735839944bfd730ecd7300000` |
| Init / main | `30D7BF` / `30D7EC` |
| Protected payload | `30D7BC`, 7,392 bytes, including its `MDK` prefix |
| Payload SHA-256 | `22d5da0dceaf8d32a0a8ce1f56af7d75f6ba542ec3f55596fe871b5723723ea3` |
| Source placements | Rooms `104` and `182` |

The header at `30D7B4` is `STAR` with mutually complemented size words.
Room182 Layer 2 matches the recipient. Its 179-byte Layer 1 allocation differs
at offset 177: recipient `6E`, source `71`. Preserve that difference. The later
[A2 review](forest-a2-restoration.md) confirms that neither value is a return
registered in the live exit table; do not interpret it as a destination merely
from the allocation tail. Matching an older
numeric A2 slot alone would not establish identity with this modern branch.

An untouched official demoOnly1 reference replay using the branch-Up input
timed out entering `11F`: mode remained `12` after 500 frames. Evidence:
`local/captures/forest-hollow-official-demoonly1-up-v1`, with its own original
receipt, ROM pin, input hash and log. It never exercised room182 or A2. The
cause of that load failure is not established here; this is not donor behavior
acceptance. No source code has been installed. Dependency closure, constructor
compatibility, graphics, both source placements and native branch behavior
still require review.

## Reproducible evidence and limits

Tracked scripts:

- `recomp/inputs/forest-hollow-normal-save.script`
- `recomp/inputs/forest-hollow-branch-up.script`
- `recomp/inputs/forest-hollow-branch-down.script`

Final captures: `forest-r13-hollow-normal-v2` and `normal-ref-v2`, plus
`forest-r13-hollow-{up,down}-v1` and `{up,down}-ref-v1`. Earlier probes and
normal v1 receipts are preserved. The final normal script settles the first
interior entry and samples the goal at the same guest timer phase rather than
assuming an identical number of host frames implies identical gameplay phase.

At all 17 paired samples, the asserted modes, rooms, lives, save flags, map
positions, goal state and four Map16 buffer regions match. The latter total
27,648 bytes per pair. Player Y and moving tape Y in room043 permit at most
one pixel; the report records actual differences at destination, before-goal
and touched samples. Other asserted actor fields and player coordinates match
exactly. These checks do not establish full WRAM/framebuffer equality or audio
acceptance.

Every external mount has zero resolutions and executed page instructions on
these routes. `probe_reference.py` therefore supplies limited same-image
subset evidence, not general emulator compatibility for the native product.
Manifest: `local/probes/forest-hollow/reference-manifest.json`; reference core
option: `snes9x_echo_buffer_hack=enabled`. The checker rejects used mounts and
validates ROM, build, binary, input and reference-host identities and completion.

Checker: `tools/qualify_forest_hollow.py`.
Report: `local/reports/forest-hollow-acceptance-v1.json`, SHA-256
`8a7aa359067f9d0b21f4697aa70940c48ec8d45fa22550ca57e1d11509292a15`.
All 344 existing unit tests pass:
`local/reports/unit-tests-forest-hollow-v1.log`.

Use fresh capture and report paths. The checker accepts `--prefix` and
`--output`; it expects normal native/reference suffixes `-normal-v2` and
`-normal-ref-v2`, with branch suffixes `-{up,down}-v1` and `-{up,down}-ref-v1`.
Run each tracked input with `m1.py native --target demo11-native-product-r13`
and with the pinned r13 `probe_reference.py` manifest before running the checker.

## Next work

The [r14 A2 checkpoint](forest-a2-restoration.md) supersedes the missing-program
status for the newer target. It restores the shop, one funded purchase and saved
ownership, a safe return/re-entry and the original room104 automatic route. All
room layouts are retained; this normal route is byte-exact against r13 at nine
full dump points. Other purchases and ability effects remain open.
Continue Ghost Forest `114` and the remaining Forest exits.
Full traversal, optional room03A, collectibles, audio and visible acceptance,
other-world identity review, C2 and complete endgame acceptance remain open.
