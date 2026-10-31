# Local Japanese messages for Mazo rooms 191 and 192

Candidate `demo11-native-mazo-messages-v2` descends from
`demo11-native-mazo-cumulative-v1`. It restores room191/message2 and
room192/message1, then restores the recipient English font when the message
closes. The adapter preserves global course/save IDs and all other message selections.
The accepted product remains `demo11-native-product-r14`.

## Sources and adaptation

The source messages are version-local. The official mazo table at `03:BE80`,
with course context `30`, selects these bounded records:

| Message | Room | Official mazo address | Size |
| --- | --- | --- | ---: |
| 1 | 192 | `53:E59A` | 70 bytes |
| 2 | 191 | `53:E5E0` | 86 bytes |

Both terminate with `FE` within the original eight rows of eighteen glyphs.
The complete encoded records do not occur in the supplied newer official
7hero, Boss, demoOnly1 or Demo1-1 images. The recipe verifies those five ROMs
and repeats that audit. It uses the newest Demo1-1 renderer at
`03:BBC9..BC48` and its stripe-row table. The only renderer operand change
selects the private message data. Japanese GFX2A comes from the newer official
Boss image and matches mazo byte-for-byte. English GFX2A comes from Demo1-1.
The recipe checks it against the actual cumulative recipient font.

The candidate adds two immutable packs:

| Pack | Mapping | Size | Role |
| --- | --- | ---: | --- |
| `message-code.bin` | `89:B000..BE83` | 3,716 | Scoped routing, original rendering loop, local pointers and font upload/restore |
| `message-data.bin` | `D3:8000..90FF` | 4,352 | Two messages and two decoded 2,048-byte fonts |

Bank89 retains the source program's low WRAM and I/O mirrors after PHK/PLB.
D3 is data-only. Both banks must be unclaimed by inherited packs. The private
renderer retains the recipient's stripe-buffer operations and message timing.
It maps the selected message through local X/Y values and never writes `$13BF`.

Only two bounded ROM hooks change:

- `03:BB90`: route the two exact room/request pairs to the private renderer.
  All other requests continue through the original `10:B6A6` selector.
- `05:B11D`: restore English GFX2A in rooms191/192 on message close, execute
  the original `STZ1426` and `STZ1B88`, then resume at `05:B123`.

Font transfers use guest DMA2 to VRAM `9000..97FF`. The V2 routines save and
restore the entire 16-bit accumulator, including hidden B when M=1, and P.
They do not copy Seven's unrelated `STZ14AF` operation. Static decoder tests
check 16-bit PHA/PLA and the complete allowed I/O-store set. The adapter adds
no gameplay, health, progression, goal or save writes.

The candidate retains all 45 inherited recipes, 58 packs, 64 patches and
existing native adaptations. It has 60 packs and 66 explicit patches. The
qualifier reconciles installed payloads and inherited source/runtime identity
files before qualification.

## Prototype evidence

V2 supersedes V1. V1 displayed the intended text, but its font routines saved
only the low accumulator byte. The candidate does not accept V1. It keeps its
separate recipe, target, binaries and captures. `--legacy-probe` reproduces
that prototype explicitly. V1 and V2 have the same derived ROM bytes but different
executable packs, build identities and binaries. Do not reuse a V1 capture to
claim V2 qualification.

## Room fixtures and lifecycle

`tools/mazo_message_routes.py` generates native or official-source routes. It
uses the existing assisted primary-room, pipe and immunity prefix. For room191,
a contact-position fixture places Mario at `(192,352)`, bypassing the two
entry obstacles. The guest B0/A9 actor requests message2. The script does not
write the request or actor state. Normal B closes the box and the actor's own
transition enters room151. The English font is present after that transition.

Room192's direct pipe fixture can freeze the actor between its first and
second active ticks, producing two messages. Both hosts do this. Two normal B
presses dismiss them. The full fight ending does not require this extra
dismissal. After closure, normal rightward input touches the sphere and returns
to the map. These fixtures qualify message/contact/close boundaries, not
ordinary traversal or correct world/save assignment.

Successful room captures are:

- V2 native: `mazo-messages-v2-{191,192}-native-v1`.
- Official mazo: `mazo-messages-191-source-v3` and
  `mazo-messages-192-source-v2`.

For both rooms, the complete Japanese font and all 400 sampled message-box
tilemap bytes match the source. The 144 by 64 pixel text interior matches
exactly at common 5-bit RGB precision (the source framebuffer uses RGB565).
Native English font bytes match the recipient after close and subsequent
room151/map transitions. Both private message handlers execute, rather than
merely mounting their packs. Native course context remains `75`, while source
is `30`. The local adapter does not overwrite that identity to select text.

Earlier room191 probes did not reach contact. The project keeps their timeouts
and excludes them. The initial room192 probe dismissed only the first of its two
messages. The project also excludes it from lifecycle acceptance.

## Reproduction

```sh
python3 tools/prepare_mazo_messages.py
python3 -c "import sys; sys.path.insert(0,'tools'); import native_sprite_gap; native_sprite_gap.prepare('demo11-native-mazo-messages-v2')"
python3 tools/m1.py --target demo11-native-mazo-messages-v2 scaffold
python3 tools/m1.py --target demo11-native-mazo-messages-v2 generate
python3 tools/m1.py --target demo11-native-mazo-messages-v2 build
python3 tools/mazo_message_routes.py --room 191 --output FRESH_NATIVE.script
python3 tools/mazo_message_routes.py --room 191 --donor --output FRESH_SOURCE.script
python3 -m unittest tests.test_mazo_messages -v
```

The recipe is `config/native-content/mazo-messages-v2.json`. All ROMs, packs,
builds and captures remain ignored. Use the native runner and official mazo
reference runner/options documented in the [ending qualification](native-mazo-ending.md).
The full checker is `tools/qualify_mazo_messages.py`, which also checks the
inherited regression routes and the complete real fight/ending input.

The broader room190 route, ordinary Mazo world/save identity, unassisted fight
and later audible music remain open. This candidate does not promote the
accepted product or establish whole-game acceptance.
