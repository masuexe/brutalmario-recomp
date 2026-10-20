# Middle-right Star World: dependency isolation

Date: 2026-10-20. The accepted cumulative baseline is now
[`star-world-upper-right`](star-world-upper-right-restoration.md). The user
accepted that stage after checking entry and SMB3 bricks, explicitly waiving
a full manual run. Listening remains deferred during the silent window.

The next course is map 6, X=`$0198`, Y=`$01A8`, translevel `$09`, room
`$009`. The historical original/native survey stalls at MARIO START. This
checkpoint isolates its missing dependencies; it does not produce or accept
a new playable restoration target. The diagnostic ROMs remain under ignored
`local/probes/middle-right/` and do not replace accepted builds or saves.

## Independent missing dependencies

The original graphics selection at `$14:AE28` matches cheap_demo's room
record. It selects ExGFX `$190` and `$193`, whose recipient pointers are both
`$FFFFFF`. The donor provides valid 4,096-byte decoded streams:

| ID | Donor source | Compressed bytes | Diagnostic destination ID |
| --- | --- | ---: | --- |
| `$190` | `$34:844A` | 1,298 | `$FFA` |
| `$193` | `$34:BF08` | 1,569 | `$FF9` |

The graphics-only diagnostic uses the existing checked builder, pins both
streams, checks the destination IDs against all room selections and preserves
the layout/sprite/exit data. New RATS blocks occupy physical
`$1E7000..$1E7B43` (exclusive end). Only room `$009`'s selection words at
record offsets 4 and 10 change; the global missing graphics slots stay empty.

The stalled recipient requests BGM `$2E`; its bank/high/low pointer at
`$0F:E08A` is zero. For diagnosis only, two copies point that slot at the
already restored `$5D` stream, `$3C:E008`. This is an explicit temporary
song substitution, not the final soundtrack repair. No music driver, physics,
enemy, completion or exit code is changed.

All three fresh reference runs use
[`star-world-middle-right-survey.script`](../recomp/inputs/star-world-middle-right-survey.script).
The script transfers an uncleared disposable save to the node, captures mode
`$12` before initialization finishes, and samples after 180 and another 420
guest-frame calls. It does not poke progress, enemy or physics state. Separate
echo compatibility is enabled and invalid-VRAM blocking is disabled, as in
the earlier restoration probes.

| Diagnostic | Mode at both later samples | Low Map16 bytes changed from loading sample | Conclusion |
| --- | --- | ---: | --- |
| Graphics only | `$12` | 0 | Graphics imports alone do not resolve the loading stall. |
| Substitute music only | `$14`, room `$009` | 4,863 | Bypassing the missing stream resolves loading, but missing graphics still corrupt the loaded terrain buffer. |
| Graphics plus substitute music | `$14`, room `$009` | 0 | Both independent entry dependencies are isolated; no buffer corruption in these samples. |

All samples retain the initial four extra lives. Visual inspection confirms
vertical stripes in the music-only run and restored dotted surfaces in the
combined run. This qualifies sampled entry data only; it does not establish
that the entire course, every sprite, exit or secret works.

## Evidence and next implementation boundary

Twenty-five selected local assertions pass, including input/ROM receipt
identities, bounded completion, sampled states, Map16 comparisons and an
audit allowing only reviewed pointer/selection/RATS changes. Evidence is in
`local/reports/middle-right-investigation.json`; captures are
`middle-right-graphics-only`, `middle-right-music-substitute` and
`middle-right-combined-substitute`.

| Diagnostic | ROM SHA-256 |
| --- | --- |
| Graphics only | `05f53d20d6ba23107e63ca93ed5d2190a8dde7e9e70041c259cb0823e684a334` |
| Substitute music only | `92e7eade1a4bc6f7d244b7edcef34a87cb8b2985274fcd174624539532456a08` |
| Combined | `8116dff03d2fd06612c284cdc552abf530320763f64d69e8eb93f1ffa1346297` |

The accepted base remains
`c96a9f5c5abd01e7749c493f615c8a398365dba2ed9076a33523e3b35ec56c0a`.
No runtime, native build or accepted ROM changes in this investigation. Only
documentation and the bounded survey input are committed; the existing 108
project-test result belongs to the unchanged preceding code checkpoint.

Next, locate and verify the actual donor `$2E` upload and adapt its sequence
and command graph. The current song adapter supports the reviewed single
pattern loops used by `$54/$5D`; a candidate donor group for `$2E` has distinct
intro/loop patterns and needs further verification rather than assuming the
old recipe applies. Then audit sprite dependencies, qualify actual exits,
collectibles, saving and death in both native/reference hosts, and run earlier
route regressions. The temporary `$5D` substitution must not ship as a
restoration. No new user playthrough or listening request is needed for this
diagnostic checkpoint.
