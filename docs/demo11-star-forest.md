# Demo 1-1 middle-left Forest Star course

Date: 2026-10-24. The user accepted the center warp-star checkpoint and asked to
restore the map-6 middle-left course to the old build's Forest Star, consistent
with the accepted demoOnly1-based build.

Current automatically qualified cumulative target: `demo11-star-forest`.
ROM SHA-256:
`4a4928f1603e8a209d198b31785234c12158d4f204f577d7b1758cc165082246`.
Native binary SHA-256:
`012983c334c075408327df05efaad6c04f0be3f8fd80c14e6a7ecd5c07420dfb`.
Parent: `demo11-center-route` (`917eb515…`), which the user accepted.
This port has bounded automated evidence. It does not imply a new user
acceptance.

```sh
# Starts at the middle-left entrance. Enter the course with Y:
python3 tools/play_demo_only1.py --restoration demo11-star-forest --show-location
```

The launcher creates an isolated practice save. Existing ROMs, builds, game
processes, user saves and captures stay intact. Completion turns this node into
the existing portal.

## Defect

The middle-left entrance at map 6, `$0158/$01A8` selects translevel `$03`,
room `$003`. Demo 1-1 stores the short terrain stub there. Its 34 sprite
records repeat the World 1 water course. The forest and vine course is absent.
The same stub is present in the unmodified demoOnly1 base.

The accepted demoOnly1 line restored this course as
[`star-world-forest`](../config/restorations/star-world-forest.json). Its pinned
donor is demo8. The investigation in
[middle-left identity](star-world-middle-left-identity.md) found that demo6 and
demo7 keep the same 1,734-byte object payload. demo8 keeps that course, its 14
sprite records, an updated music object and the valid sprite protections. This
port keeps the same pinned donor and data, so the course matches the old build.
A demo7 same-number-room diagnostic in that investigation shows the same
forest/vine setting.

## Port

The recipe is
[`demo11-star-forest`](../config/restorations/demo11-star-forest.json). It uses
the current head as its base and keeps the demoOnly1 forest donor pins. The
recipient sites are version-local, so the port re-derives them:

| Item | Accepted demoOnly1 forest | Demo 1-1 port |
| --- | --- | --- |
| Room `$003` Layer 1 | `$48:8008` | allocation `$38:DB0F` |
| Room `$04E` | `$51:B77D` | allocation `$38:E1E0` |
| Private Map16 bank | `$44:8000`, header `$43:FFF8` | `$41:8000`, header `$40:FFF8` |
| Map16 lookup shims | `$41:8008` | `$49:E908` |
| Graphics hook `$06:F540` | `JML $41:8008` | `JML $49:E908` |
| ActsLike hook `$06:F623` | `JSL $41:8044` | `JSL $49:E944` |
| Shims' clone bank operand | `$44` | `$41` |
| Custom sprite records B0/B1/B2 | `$10:BB8A` table | `$31:8D72` table |
| Asset/level allocation | `$24:2800` region | file `0x1C4000`, 12,288 bytes |

Everything else keeps the accepted donor data:

- Room `$003` Layer 1 object stream, 1,737 bytes.
- Layer 2 RLE, 143 bytes, including embedded `FF` bytes.
- Sprite list, 44 bytes. Custom slots `$0D`/`$47` become `$B0`/`$B2`.
- Forest palette and goal-room palette, 514 bytes each.
- Goal room `$04E`, complete 34-byte stream with its `40 60 5E` music object.
- Isolated ExGFX `$15D→$FC0`, `$14D→$FBF`, `$14E→$FBE`.
- Parrot, projectile and vine sprite blocks in banks `$3C`, `$3C`, `$35`.
- Room settings byte `$05:DE03` `$40→$00`. The water flag stays off.
- Secondary settings at `$05:F003`, `$05:F203`, `$05:F403`, `$05:F603`.

The private Map16 bank uses checked empty bank `$41`. The two shims move to
checked empty space in bank `$49`. Both hook patches keep their instruction
width and replay the overwritten bytes. The recipe changes 40,919 bytes relative
to the parent; all changes are inside the declared regions.

## Evidence

`recomp/inputs/star-world-forest-*.script` drive entry, normal, secret and
death. The attack route is
`recomp/inputs/demo11-forest-attack.script`: it keeps the original camera and
player-position fixtures and adds two real R presses. The player fires three
real projectiles. The extra shots absorb a one-frame host phase difference that
the earlier single-shot fixture shows on this line.

Reference and native captures agree with fresh demoOnly1-line captures under the
same scripts:

| Check | Demo 1-1 reference and native | DemoOnly1 forest captures |
| --- | --- | --- |
| Entry | mode `$14`, room `$003`, parrot live, water `$85=$75=0` | same |
| Projectile | one live `$B1` actor flies right after R | same |
| Attack | both live `$B2` vines reach status `$02` through real collisions | same |
| Normal clear | goal room `$04E`, tape, save `$8C` in WRAM and both SRAM copies | same |
| Save reload | room `$C7` over the saved node keeps `$8C` | same |
| Secret clear | save `$8E`; portal to map 0 at `440/488` | same |
| Death | lives `3`, hub return, fresh entry keeps lives `3` | same |

The loaded course buffers on entry are byte-identical to the fresh demoOnly1
capture: level tilemap `$7E:AD01–C0FF`, Map16/level buffer
`$7E:C800–DFFF`, and sprite data `$1C8D9–1D57C`. The visible course renders the
donor vines, blocks, clouds and parrot. Animated coin and sprite frames differ
by phase, as on other checkpoints.

Primary captures are `d11-forest-<route>-{ref,native}`; comparisons are
`d11-forest-only1-<route>-ref`. Exact receipts and measurements are in
`local/reports/demo11-star-forest.json`. The suite log is
`local/reports/demo11-star-forest-line.log`.

`tools/qualify_demo11_star_forest.py` checks the recipe replay, the four
relocated sites, the clone and shim bytes, hook bytes, level pointers, sprite
records, ExGFX payloads, every route value above and the course-buffer
equality. The Demo 1-1 line suite passes **23/23**. The whole-line audit
rebuilds 21 recipes: 105,056 changed bytes against Demo 1-1, all inside 139,242
declared region bytes, zero unexpected. The 33 restoration tests and three
preparation tests pass.

## Limits

- The fixtures teleport to the entrance and use camera and player-position
  shortcuts. They do not qualify an unassisted whole-course traversal.
- The single-shot attack of the earlier fixture is host-phase sensitive on this
  line. The tracked script uses three real shots and requires every live vine
  enemy to be defeated on both hosts.
- The course uses existing recipient song `$5D`. No new listening acceptance is
  inferred.
- The center Boss ending, other full-course/DK/death coverage, the sky secret
  and the broader restoration stay open.

## Reproduce

```sh
python3 tools/restore_star_world_1.py --target demo11-star-forest
python3 tools/m1.py scaffold --target demo11-star-forest
python3 tools/m1.py generate --target demo11-star-forest
python3 tools/m1.py build --target demo11-star-forest
python3 tools/m1.py reference --target demo11-star-forest \
  --script recomp/inputs/star-world-forest-entry.script --capture fresh-forest-ref
python3 tools/m1.py native --target demo11-star-forest \
  --script recomp/inputs/star-world-forest-entry.script --capture fresh-forest-native
python3 tools/qualify_demo11_star_forest.py
python3 tools/check_demo11_line.py
```
