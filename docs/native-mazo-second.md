# Mazo second-boss ground check and later graphics

This continues the [reflection qualification](native-mazo-reflection.md).
The accepted product remains `demo11-native-product-r14`. The experimental
`demo11-native-mazo-gfx282-v1` is an older r14 descendant; it must not replace
the cumulative modern sprite candidate.

## Grounded death and normal jump control

The official mazo program's main 9C variant 1, phase 8, runs at `22:8BBE`.
At attack timer `15AC=B8`, `22:8BD2` tests `$77 & 04`. If the player is
grounded, `22:937D` creates variant `0D` at the player's X and Y `0168`, with
`151C=1`. Its handler at `22:8635` freezes the player, then `22:8653` writes
`02` to `$97`. The player falls below the arena and dies. Persistent `$1497`
immunity does not prevent this mechanic.

Ending the first-boss placement fixture and leaving the player grounded
reproduces that sequence on both hosts. Starting a normal 16-frame B jump at
timer `C0`, eight ticks before the check, avoids the fatal child. At the
sample after the jump, both players are airborne at Y 281; neither creates
the flagged variant `0D`. Both survive the following 64-frame observation.
The orb can be recollected during this jump, causing another cutscene freeze;
that freeze alone is not evidence of a stalled boss.

| Control | Native | Official mazo |
| --- | --- | --- |
| Fatal child while idle | late104 | late197 |
| Death below arena | late105, Y 592 | late199, Y 593 |
| Jump crosses ground check | timer AF, Y 281 | timer AF, Y 281 |

Captures are `mazo-second-{native,source}-{idle,jump}-v1` under
`local/captures`. Each completed with scripted quit. This qualifies one
attack boundary, not survival through the entire fight.

## Later sequence

Ground-triggered 24-frame B jumps recollect the orb and allow later attacks.
Short two-frame hops did not reach the orb. The strengthening window permits
phase 5, whose variant `14` can reset the `$7FF410` shield field. Phase 3
increments `$7FF413` in scripted cycles. Do not label that field as health.

In official-source capture `mazo-second-source-highhops-v2`, 120 jumps reach
cycle values 1, 2 and 3 at highhop048, highhop080 and highhop101. At
highhop108 through highhop120, all 4096 decoded bytes of official GFX `0282`
match VRAM `F000..FFFF`. The player remains alive in room `151`, with later
variant `17` (decimal 23) present. This is a later transformation, not a clear.

Native capture `mazo-second-native-highhops-v4` completes 240 jumps and reaches
the same full upload at highhop222 through highhop240 (19 samples), with live
room `151`, cycle 3 and variant `17`. The source has 13 matching samples. The
decoded SHA256 is `18670aa7d1518e2428937c09e9d30b1c2a20d37d1cb17120b7a721eae5a76acb`.
Attack choices and elapsed times differ; this is not whole-fight timing parity.
Native 80- and 160-jump captures ended before the request. The interrupted
native highhops-v2 run is incomplete and is excluded from qualification.

## Reproduction and identities

`tools/mazo_second_route.py --mode idle|jump|highhop --hops N --output FRESH`
generates native inputs; add `--donor` for the official source. The first-boss
prefix uses five cycles on native and six on source, with the previously
declared entry, position and immunity fixtures. There are no additional
position writes after that prefix. No boss state, health, progression or
completion flags are written. Later jumps use normal input; RNG is unforced.

Run native with `tools/m1.py native --target demo11-native-mazo-gfx282-v1`.
Run source with `tools/probe_reference.py --manifest config/mazo-donor.json`
and `SNESREF_CORE_OPTIONS=snes9x_echo_buffer_hack=enabled`.

`tools/qualify_mazo_second.py --output FRESH` checks both idle and jump controls.
Optional `--source-highhops NAME --source-hops N` and
`--native-highhops NAME --native-hops N` check complete later-resource captures.
It verifies exact generated inputs, completion logs, dump sizes, receipts,
current build/module/runtime identities, grounded death, the jump boundary,
and the full decoded graphics payload with live later actors when requested.
Negative probes reject a grounded jump sample and an idle control missing the
fatal child.
Another negative probe changes a graphics byte outside the old distinctive
64-byte slice and is rejected. Combined report:
`local/reports/mazo-second-qualified-v1.json`.

Pinned ROM SHA256:

- Official mazo: `94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1`.
- Native: `626a5c5c3fee9ae54962c448e04dcb24b4b962ee87d9edfeb2279ef4a324c186`.
- Native executable: `656a0be24ab09de7050de16d796dfbb756431d49b2302ebbe19b34cd23ef3902`.

Full victory, saved completion, unassisted traversal, later music and cumulative
integration remain open. No game or runtime behavior was changed here.
