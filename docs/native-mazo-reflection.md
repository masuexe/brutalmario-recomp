# Mazo 9C reflected impacts and second-boss arrival

Date: 2026-10-30. Experimental target `demo11-native-mazo-gfx282-v1`, descended
from r14. Accepted product remains r14. This qualifies assisted progression in
room 151, not an earned complete fight, ending, saved clear or music listening.

## Mechanism recovered from official mazo

The [orb sequence](native-mazo-gfx282.md#superseding-orb-qualification-2026-10-30)
provides the `$7FFE00` strengthening window. Ordinary attack button sweeps are
not needed for the counterattack exercised here:

- At `22:91A4`, an active window starts `$7FFE01` reaction and sets the main
  controller's `1540` to `80`. This check runs at attack timer `C8`.
- At `1540=7E`, `22:91C2` creates variant 9 with `C2=1`, X `FFD0` (-48) and
  Y equal to Mario Y + 16. An unreflected variant 9 instead starts at X `0110`,
  moves left and can hurt Mario.
- The reflected variant 9 moves right at speed `50` (5 pixels/frame). At its
  `15AC=30` tick, `22:8568` checks nonzero Y high byte and Y low byte at least
  `30`. On success it increments `$7FF400` and spawns variant 10, the impact
  effect at `(176,352)`. The sampled return projectiles are at Y 352. This is
  a timed return/height check, not a direct stomp on the main actor.
- `$7FF400` is a progression counter with a scripted increment. At 3,
  `22:8F39` selects controller phase 2. `22:8FB2` then creates variant 11 and
  increments the counter to 4. That increment is not another reflected hit.
- Five actual impacts produce counter transitions `0->1`, `1->2`, `2->3`,
  `4->5`, `5->6`. At 6, `22:8F43` starts phase 7. The following sequence
  introduces the second boss (main variant 1). Never label this as six hits or
  interpret every progression field as health.

Only the supplied official mazo program is used for these findings. Source
ROM SHA256 is `94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1`.
The existing restored 9C program is unchanged.

## Reproduction and verification

`tools/mazo_reflect_route.py` generates the native input, or the donor input
with `--donor`, into a fresh ignored path. It takes the tracked orb entry
prefix and performs twelve cycles of a player placement at `(180,250)` followed
by 1536 frames. Entry, repeated player placement and persistent `$1497=FF`
immunity are explicit fixtures. No boss state, health, hit counter, strengthening
flag or completion flag is written. RNG and attack choices remain unforced.

Run the generated native script with `tools/m1.py native --target
 demo11-native-mazo-gfx282-v1 --script PATH --capture FRESH`. Run the donor script
with `tools/probe_reference.py`, `config/mazo-donor.json`, the official mazo ROM
and `SNESREF_CORE_OPTIONS=snes9x_echo_buffer_hack=enabled`.

Captures: `local/captures/mazo-reflect-long-native-v1` and
`local/captures/mazo-reflect-long-source-v1`. Each contains 385 complete
WRAM/VRAM sample pairs and reaches scripted quit. The checker
`tools/qualify_mazo_reflection.py --output local/reports/FRESH.json` verifies
ROM, binary, module, runtime, source core/frontend and exact generated-input
identities, dump sizes, the live room up to arrival, all progression values,
reflection actors plus impact effects, the separate scripted marker, phase 7
and the second-boss actor. Report: `local/reports/mazo-reflection-v2.json`.

| Event | Native sample | Official mazo sample |
| --- | --- | --- |
| Impact 1, counter 1 | c01f17 | c04f11 |
| Impact 2, counter 2 | c01f23 | c04f23 |
| Impact 3, counter 3 | c03f12 | c05f07 |
| Scripted marker, counter 4 | c03f15 | c05f11 |
| Impact 4, counter 5 | c04f12 | c05f16 |
| Impact 5, counter 6 | c05f09 | c06f26 |
| Second-boss actor | c07f05 | c08f22 |

Attack choices and event times differ between hosts. This is behavior-boundary
qualification on different images, not whole-fight timing or image parity.
Native ROM is `626a5c5c3fee9ae54962c448e04dcb24b4b962ee87d9edfeb2279ef4a324c186`;
binary is `656a0be24ab09de7050de16d796dfbb756431d49b2302ebbe19b34cd23ef3902`.
All capture identities remain in the original receipts.

## Limits and next work

Both long routes later die: native leaves live mode at c07f25; source at
c10f05. Neither death is a clear. The repeated orb-position fixture continues
after the first-boss transition and is not a second-boss traversal strategy.
The next route must stop repeating those placements after the transition and
qualify the second boss's mechanics and survival independently. `$7FF413`
changes in second-boss code but is not yet established as health.

The distinct decoded `0282` slice still has zero VRAM hits on both hosts. Its
request at `22:8E0A` belongs to the later second-boss sequence; this checkpoint
does not accept that resource at runtime. Later phase music, full clear, save
and unassisted traversal remain open. Any integration must preserve the modern
sprite candidate's later modules; this older r14 fork must not replace them.
