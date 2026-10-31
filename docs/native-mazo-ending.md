# Assisted Mazo ending, goal and persistence boundaries

The [cumulative graphics candidate](native-mazo-cumulative.md) now follows the
actual later 9C sequence into room `192`, dismisses the message with normal B
input, touches the ordinary goal sphere by walking right and returns to the
map. No boss state or completion flag is written by the fixture. This is
assisted fight/ending evidence; ordinary world access, correct world/save
identity and unassisted traversal remain open. The accepted product stays r14.

## Official program and observed sequence

After the second boss's scripted cycle counter reaches 3, `22:8DE2` removes
the controller and creates variants 2 and `17`, then requests GFX0282.
Variant 2's handler at `22:818F` sets player action `$71=0B`, advances its
`1570` counter every 32 ticks, and runs the cutscene events. At counter `58`,
`22:8272` requests room `192` through the existing pipe-action transition.
Variant `17` follows the controller's position/orientation through
`$7FF414..416`; it is not another boss requiring independent hits.

In room `192`, official B0 code `13:89A5` ORs `80` into `$1EAF`, requests
message 1 through `$1426`, and removes itself on its second active tick. The
native custom-id adaptation runs that same program as A9. The route never
writes `$1EAF`, `$1493`, save data or the exit count.

| Boundary | Native cumulative | Official mazo |
| --- | --- | --- |
| First live room192 sample | scene077 | scene081 |
| Corridor flag before / after | 0F / 8F | 00 / 80 |
| Normal message dismissal | `$1426=0`, sphere present | same |
| Walking touches sprite4A sphere | X127, `$1493=F0` | X128, `$1493=EF` |
| Map return | mode0E | mode0E |
| Exit count before / after | 0 / 0 | 0 / 1 |
| Flag after reset/file reload | 8F | 00 |

All 160 cutscene samples are retained. Both controllers reach counter `58`
through at least 60 distinct sampled values. The complete GFX0282 upload,
airborne ground-check dodge, real message/sphere actors and normal goal timer
are also checked. Event timing differs across the two images.

## Persistence scope

Native SRAM changes 13 bytes after the actual goal. Both guest save copies
contain `8F` at offsets `000D` and `01BA`, and preserve it on reset/File A
reload. Source SRAM does not change across the goal/reset observations, and
the source flag is absent after reload. This route does not select a separate
source save prompt; it does not prove that the donor cannot save.

The native entry overrides a practice map node with translevel `075`, whereas
the source route has translevel `030`. Native does not increment the exit
count in this fixture. The donor hardcodes `$1EAF`; that numeric address alone
does not establish the intended recipient world flag. Therefore the evidence
qualifies native guest flag persistence and the goal/map boundaries, not a
correct integrated Mazo course save. Review the actual recipient course
assignment and flag meaning before accepting ordinary progression.

## Message rendering investigation

The actual ending exposes the existing room191/192 text defect. Source
GFX2A is present at VRAM `9000..97FF`; native lacks those bytes. At tilemap
`A000`, row9 contains the source's sentence, while native contains only its
blank tile `12F`. The source blank tile is `11F`. Thus uploading the font
alone cannot supply the missing text.

Both engines call message helper `03:BB90` from `05:B1A3`. The donor helper
reads `$13BF` and its message selector/pointer table at `03:BE80`, then reads
encoded text from `53:D0D4`. The recipient instead jumps from `03:BB90` to
`10:B6A6`, adds room-selection rules and reads text from `2F:C927`. The practice
entries also have different `$13BF` values. A local message adaptation must
recover the intended source message, blank encoding and font together while
preserving the recipient's global course/save identity and ordinary messages.
The later [message candidate](native-mazo-messages.md) restores those two messages and the local Japanese font. Save identity remains open.

The community [official-demo map index](https://wikiwiki.jp/kitikumario/%E3%83%9E%E3%83%83%E3%83%97%E6%94%BB%E7%95%A5)
lists the Mazo main course as `10C`, named 天空要塞 ルイージドリーム. Its numeric
identity is not transferred to the recipient by this fixture. The Fandom
walkthrough and the specific Japanese course page were unavailable during
this investigation; ending mechanics above come from the pinned official
program and actual captures.

## Reproduction and verification

`tools/mazo_ending_route.py --output FRESH` generates the native input, with
`--donor` for source or `--observe-only` for the cutscene-only control. It
extends the existing first-boss fixtures and normal second-boss jumps with
5120 frames of observation, normal B/right input, a map observation and reset.
No later position or boss/completion writes are added. All four generated
inputs exactly match the executed historical v1/v2 scripts.

Captures: `mazo-ending-{cumulative,source}-v1` (observation only) and
`mazo-ending-{cumulative,source}-v2` (goal/reset), under `local/captures`.
All reach scripted quit. Native target is `demo11-native-mazo-cumulative-v1`;
ROM and executable identities are pinned in the cumulative integration note.
Source is the official mazo ROM, with the pinned Snes9x core/frontend and
`snes9x_echo_buffer_hack=enabled`.

`tools/qualify_mazo_ending.py --output FRESH` verifies exact scripts and receipt,
binary, ROM, modules and runtime identities, dump sizes, cutscene progression,
live transfer, guest flag, normal dismissal/sphere goal, map return, actual
save-copy bytes and reset observations. It records the message mismatch and
the differing exit counts explicitly. Negative probes reject a missing goal
timer and a lost native flag after reset. Report:
`local/reports/mazo-ending-qualified-v3.json` (supersedes the earlier v1/v2
reports with current ROM and live goal-room checks). Python compilation and diff
checks pass. No audible music, complete room190 route or whole-game claim is
made.
