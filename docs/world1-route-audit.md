# World 1 route audit

## Recipient and migration boundary

The accepted cumulative recipient remains demoOnly1 with the isolated
`star-world-forest` restoration, ROM SHA-256
`a246c9370f71e2ee1db990724222d877c96476ba3e3dd4ff98b2db160b0d4872`.
The original Demo 1-1 target remains separate. The user reports that Demo 1-1
deliberately disconnects its first course from 1-2 and Yoshi's House.
Treat its additional course content as a prospective donor; do not import its
overworld restrictions along with that content.

## Reproduced route restriction

Fresh-save probes select map 0, X `$048`, Y `$198`, translevel `$29`
(room `$105`). In original Demo 1-1, all four direction probes remain at that
coordinate. Original demoOnly1, the accepted forest restoration, and
cheap_demo permit movement away from the node.

The loaded map has three particularly relevant differences:

| WRAM route cell | Demo 1-1 | demoOnly1 / forest / cheap_demo |
| --- | --- | --- |
| `$7E:CA84` | `$00` | `$20` |
| `$7E:CA93` | `$00` | `$04` |
| `$7E:CA95` | `$00` | `$04` |

The node itself (`$7E:CA94 = $66`) and the nearby translevel assignments
are unchanged: `$D294 = $29`, `$D296 = $28`, `$D2D5 = $2A`.

A second diagnostic sets only this node's completion/direction byte
`$1ECB` to `$8F`. Demo 1-1 still cannot move. The original demoOnly1 and
cheap_demo references and the forest native host can move right to
`$068,$198`, the Yoshi's House candidate (translevel `$28`, room `$104`).

A third diagnostic restores just the three route cells in Demo 1-1 WRAM,
in addition to the same completion/direction fixture. Its sampled endpoints
then match demoOnly1 and the forest native host:

| Direction held for 90 frames, followed by 90 idle frames | X | Y |
| --- | --- | --- |
| Down | `$048` | `$198` |
| Right | `$068` | `$198` |
| Up | `$018` | `$178` |
| Left | `$018` | `$1B8` |

Each direction starts from a new map transfer to `$048,$198`. These are
bounded movement samples, not assertions that every endpoint is an enterable
course. The observations establish that the three missing map cells are
sufficient to reproduce and remove this movement restriction in the fixture.
They do not locate the compressed ROM bytes responsible for those cells.
No production ROM or runtime changes were made by this audit.

## Evidence and replay

The three checked-in scripts are
`recomp/inputs/world1-routes-uncleared.script`,
`recomp/inputs/world1-routes-cleared-fixture.script`, and
`recomp/inputs/world1-routes-demo11-three-tiles.script`.
They contain the same guest input and fixture writes as the local survey
scripts; only their explanatory header differs.

Local captures are grouped under:

- `local/captures/world1-path-uncleared-{demo11,only1,forest,cheap}`:
  original/reference runs for all four ROMs.
- `local/captures/world1-path-cleared-fixture-{demo11,only1,cheap}`:
  original/reference runs with the completion/direction fixture.
- `local/captures/world1-path-cleared-fixture-forest`: accepted native host.
- `local/captures/world1-path-three-tiles-demo11`: original/reference run
  with the three-cell WRAM diagnostic.

Each capture has its ROM/script identity receipt and fresh save directory.
Additional tracked-script replays are
`local/captures/world1-tracked-route-demo11` (reference, three-cell diagnostic)
and `local/captures/world1-tracked-route-forest` (native, completion fixture).
Across all 11 captures, pinned ROM identities and 55 mode-`$0E` map samples
were checked, including the right-route endpoint assertions. The final replay
preceded an explanatory-comment clarification only; script commands did not
change.

Use a new capture name when replaying, for example:

```sh
python3 tools/m1.py reference --target demo-1-1 \
  --script recomp/inputs/world1-routes-demo11-three-tiles.script \
  --capture world1-three-tiles-replay
python3 tools/m1.py native --target star-world-forest \
  --script recomp/inputs/world1-routes-cleared-fixture.script \
  --capture world1-forest-routes-replay
```

## Remaining work

The completion byte above is a diagnostic shortcut. Actual 1-1 goal contact,
event processing, movement to 1-2 and Yoshi's House, and save/reload persistence
remain unqualified by these probes. Preserve those as integration checks for
any migration; do not label the complete World 1 route accepted yet.

The initial room inventory gives a bounded next investigation: room `$106`
(the 1-2 candidate) has the same 160-byte Layer 1 payload in Demo 1-1,
demoOnly1, cheap_demo and demo8, but selects missing extended GFX `$1A2` in
both recipient originals. This is a resource dependency lead, not yet a
gameplay diagnosis. Room `$105` also differs between Demo 1-1 and demoOnly1
(7,102 versus 7,091 bytes in the inventoried object stream); those bytes and
their sprite, block, ASM and audio dependencies still require interpretation
before importing any supposed new content.

Continue with actual 1-1 goal/event integration on the accepted recipient,
then the World 1 entrance/dependency survey, then an interpreted Demo 1-1
addition inventory. Let real goal and event code write progress during the
integration check; the diagnostic completion-byte scripts cannot qualify it.
Any production repair should use a separate descendant target so the accepted
forest baseline remains available.
