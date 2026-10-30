# Sprite 95 rooms in the cumulative native candidate

The subsequent [fifth-trial mechanism checkpoint](native-sprite95-trial5.md)
adds actual switch/Koopa/shell behavior and a far-door return awarding one
Dragon Coin. Its platform-position fixtures still leave ordinary traversal
open. The earlier failed exploratory return observations below remain historical.

## Scope and identities (2026-10-30)

This checkpoint qualifies selected behavior in the six remaining sprite95
rooms of `demo11-native-seven-product-v1`. It changes no game code, ROM,
resource pack or target selection. The [Seven integration checkpoint](native-seven-product-integration.md)
defines the candidate. Accepted historical product r14 remains unchanged and
does not contain these later features; rejected r15 remains rejected.

| Artifact | SHA-256 |
| --- | --- |
| Native ROM | `0f04abec07f424c482291c2aeee082bf4c41d3468f30e2483d06a728978cd8af` |
| Native executable | `d84ff809dae79f29c2209012fda160a3beda60cd6d56575c4eeab595e3aef164` |
| Official Boss ROM | `337fe036f943dafb0df70bdb556e588b785c58ff019b1b00c08f77743e2b3ccd` |
| Official 7hero ROM | `dd7007ad45da87647bbd7e6d3bda13b8555c05b64793a92824f12b347c7a2395` |
| Complete 5,144-byte sprite95 program | `20980e341c2877b32e286cb7053450ffcb54f1ee74f55f79f7a0b0b1236a6454` |

The selected recipe remains `config/native-content/sprite95-boss-module.json`:
newest official Boss code at `20:E40B`, mounted unchanged at `A3:E40B`.
Boss and 7hero have identical complete protected programs and original records
`013600003f0399641ae42039e5200000`. The native record only changes the program
bank to A3. This permits 7hero behavior references while retaining newest-source
selection. It does not establish agreement for unrelated actor programs.

## Bounded content identity

The checker compares complete STAR-bounded allocations with the official
7hero ROM, rather than walking objects into neighboring allocations.

| Room | Foreground bytes | Background bytes | Sprite list |
| --- | ---: | ---: | --- |
| `16C` | 9,511 | 16 | exact |
| `16D` | 2,417 | 16 | exact |
| `16E` | 518 | 566 | same placements and header, reordered |
| `16F` | 251 | 1,794 | exact |
| `172` | 1,782 | 411 | exact |
| `1CC` | 82 | unqualified | exact |

The `1CC` background pointer has no immediate bounded STAR header, so no
background-identity claim is made. Room16E's reordered sprite list changes
allocated actor slots. Hub comparisons sort the 19 selected actor fields;
they do not assert equal slots. The six idle cases compare slots as well.
An unbounded object/exit parser can overrun the identical 518-byte16E stream
and report false differences; those results are not used as route evidence.

## Fresh behavior evidence

Twelve native/source pairs finish cleanly: six idle cases, one hub-loading
case and five door cases. The 86 paired samples assert player mode, room,
action, coordinates, `$14AF`, `$7FFEAF` and goal timer. Selected sprite95
comparisons cover normal ID, phase, variant, position, status, timers,
animation, direction, velocities and two interaction properties (the 19 fields
in `qualify_seven_child.FIELDS`). Module A3 actually executes in every case
except idle16E, where both hosts have no sprite95 loaded yet.

| Case | Qualified behavior |
| --- | --- |
| `16C` | All seven idle samples match; a real phase06 child exists at frame128; the moving phase04 actor reverses by frame256. |
| `16D` | Phase08/09 selected state and motion match through frame256. This does not qualify the separate custom34 program. |
| `16E` | Gradual vertical player-position fixtures load five trial doors and a return door. All six selected actor states match after slot normalization. |
| `16F` | Phase0C actor and actual layer2 Y motion match: 188,176,116,52,0,80,172 at entry/1/16/32/64/128/256. |
| `172` | Phase10 door states match through frame256; trial initialization saves the selected switch bit and clears the working switch byte. |
| `1CC` | Phase0D selected state matches through frame256. Door activation remains unresolved. |

The earlier pilot's16C three-pixel discrepancy was a loading-phase comparison.
These fresh scripts wait for live mode14 before measuring motion; selected
state now matches exactly at all seven idle samples in the current candidate.

After assisted hub loading and positioning, ordinary Up activates each of the
five doors. No actor, switch, progress, completion or save values are written
by these fixtures. The game itself records the selected bit and enters the
following destinations in both hosts:

| Door | Player X | Actual destination | `$14AF` in trial | `$7FFEAF` in trial |
| --- | ---: | --- | --- | --- |
| 1 | 16 | `150` | `01` | `00` |
| 2 | 64 | `16F` | `02` | `00` |
| 3 | 112 | `170` | `04` | `00` |
| 4 | 160 | `171` | `08` | `00` |
| 5 | 208 | `172` | `00` | `10` |

These are door-entry bits, not proof of a completed trial or collected coin.
The [community Bowser Keep walkthrough](https://brutalmario.fandom.com/wiki/Finish%21_Bowser_Keep)
describes five trials and five Dragon Coins. Its fifth trial protects a Koopa
with switch blocks and then uses its shell. This supplies route context;
the room identities and branch results above come from actual local captures.

## Reproduction and limits

```
python3 tools/qualify_sprite95_rooms.py --prepare
```

This generates 24 immutable scripts in ignored
`local/probes/sprite95-rooms-v1/`. Cases are `idle-16c`, `idle-16d`, `idle-16e`,
`idle-16f`, `idle-172`, `idle-1cc`, `hub` and `door-1` through `door-5`.
Run each side into a fresh capture directory, substituting CASE:

```
python3 tools/m1.py native --target demo11-native-seven-product-v1 --script local/probes/sprite95-rooms-v1/native-CASE.script --capture sprite95-rooms-CASE-native-v1
SNESREF_CORE_OPTIONS=snes9x_echo_buffer_hack=enabled python3 tools/probe_reference.py --manifest config/7hero-donor.json --rom local/content-versions/7hero/rom.sfc --script local/probes/sprite95-rooms-v1/source-CASE.script --capture sprite95-rooms-CASE-source-v1
python3 tools/qualify_sprite95_rooms.py --output local/reports/FRESH.json
```

Existing v1 captures must be retained. Fresh reruns need new names and a
correspondingly reviewed checker update. The checker pins actual executed
scripts, ROM/build/binary/content identities, reference core/options, bounded
source data, module execution and successful quit logs. It regenerates inputs
immutably, so changed templates cannot silently relabel prior captures.

Report `local/reports/sprite95-current-rooms-v2.json` and its byte-identical
`sprite95-current-rooms-recheck-v2.json` have SHA-256
`5bb0b062c75713865b348f526188e1b4bd56d74b9bcf5c0bdaff78fb244f85ec`.
The new checker compiles and all six low-mirror admission tests pass. The
previous 368-test suite belongs to the unchanged Seven integration build;
it is not a new full-suite run at this checkpoint.

All cases use explicit primary-room/pipe/immunity/player-position fixtures;
the hub scroll uses gradual position writes. They qualify exercised behavior,
not ordinary full-course traversal. No full audio, framebuffer, physics,
other-family actor or save-persistence parity is claimed.

Separate exploratory `sprite95-current-1cc-return-*-v1/v2` captures did not
activate the door in either host. `sprite95-current-door5-return-*-v1`
activated the beginning door in172 and restored switch10, but returned to172
and cleared the working byte again; this is a self-loop, not a trial exit.
The v2 attempt to traverse directly to the far door died in both hosts and
proves no exit. These observations stay outside the passing twelve-case
qualification; their original scripts/captures remain ignored and intact.

Next: qualify actual trial mechanisms and exits, especially the172 Koopa/shell
route, and resolve1CC interaction without faking collision or completion.
Seven and mazo earned victories/save, remaining Forest routes, C0/late-C1
motion, missing content, graphics and music remain part of the open objective.
