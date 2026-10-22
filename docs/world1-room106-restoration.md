# World 1 room 106 graphics recovery

Date: 2026-10-22. This isolated resource-recovery candidate descends from the
accepted `star-world-forest` ROM and preserves that target. Entrance: map 0 /
`$058,$1D8`, translevel `$2A`, room `$106`. Its intended course number is not
established; do not call this a completed 1-2 restoration.

## Failure and correction

Both original recipients select extended graphics `$1A2` in room `$106` but
have an absent `$FFFFFF` pointer. cheap_demo has the resource. All three have
the same 160-byte inventoried Layer 1 stream and 14 placed sprite records.
In the unrepaired reference, loaded Map16 buffers contain unrelated data and
Mario falls after the opening message. This is not merely cosmetic.

Relocating just that resource restores the loaded terrain and normal movement.
There are no object, sprite placement, collision definition, engine, music,
goal, event or save changes.

| Item | Value |
| --- | --- |
| Donor | Pinned cheap_demo |
| Source graphics | `$1A2`, ROM `$35:F39D` |
| Compressed / decoded size | 3,138 / 4,096 bytes |
| Private destination graphics | Previously unselected `$FBD` |
| Destination | `$49:8008`, RATS header at physical `$248000` |
| Selector | Room `$106` graphics record `$14:CDC8`, word at offset 14 |
| Change boundary | Protected graphics allocation, three-byte pointer, two-byte selector |

All 2,590 differing bytes from the accepted forest ROM are inside that
footprint. Original `$1A2` remains absent, so unrelated rooms are not silently
enabled. The recipe verifies source hashes, empty allocation, unused
destination graphics ID and original selector.

## Automatic checks and limits

`python3 tools/qualify_world1_room106.py` checks pinned ROM/build/script
identities and writes `local/reports/world1-room106-qualification.json`.

- Room `$106`: after message dismissal, walking, jumping and landing remain
  active in reference, native and unmodified cheap_demo. Player coordinates
  match within two pixels. Low/high Map16 cells for all 11 horizontal screens
  match the donor exactly at all four samples.
- Native has one difference at unused high-buffer tail byte `$7F:FD04`,
  outside the room's 4,752 active cells per buffer. The report records it;
  these checks do not assert whole-WRAM equality.
- First-course room `$105`: an assisted traversal reaches the real goal.
  `$1493` becomes nonzero without goal/completion/event/SRAM writes; both
  hosts return to the map with clear flag `$8A` and event bit `$40`. SRAM
  copies `$0029/$01D6` retain `$8A` after reset and File A reload.
- House: the existing entrance leads to room `$180`. Real movement exits to
  the map, then walking left reaches `$048,$198` on both hosts.
- Forest: fresh reference/native entry and later samples remain in room
  `$003`, mode `$14`, with water flags `$85/$75` zero.
- Existing restorer and launcher suites pass: 30 plus 18 tests. The new
  practice entrance is appended to preserve existing menu selection numbers.

The first-course traversal uses air-swim, invincibility and one initial timer
write. Air-swim and invincibility are disabled before the map transition;
this is not an unassisted playthrough.
House and room `$106` use initial map-coordinate fixtures, not a natural
unlocked map route. Complete room `$106` exits, collectibles, death/re-entry
and newly heard music remain unqualified.

Final capture directories under `local/captures/`:

- `world1-106-qualified-entry-candidate` and `world1-106-qualified-entry-cheap`.
- `world1-106-qualified-entry-native-v2`.
- `world1-106-qualified-{goal,house,forest}-{reference,native}-v2`.

Some preceding non-v2 captures contain empty/truncated artifacts and are
excluded. Process output alone is insufficient: the qualifier checks complete
WRAM/SRAM snapshots and route completion. No capture was overwritten.

## Unresolved integration and next work

The ordinary exit from room `$105` automatically leads left to map 0 /
`$018,$1B8`, whose translevel `$10` still stalls in Mario Start in the accepted
recipient. Flag `$8A` also does not open the rightward route to the House.
This inherited behavior is unchanged. House-to-first-course movement works;
the complete bidirectional unlocked route is not repaired.

Next, identify intended World 1 node/course correspondence and normal-exit
direction/event dependencies against donor maps. Do not substitute arbitrary
completion flags or rename room `$106` to 1-2 to make integration appear
complete. Qualify remaining room `$106` behavior before promoting this
candidate to the next accepted cumulative base.

Demo 1-1 room `$105` also needs an interpreted addition inventory: it places
44 sprites versus demoOnly1's 39; several graphics selections and secondary
headers differ. Its layout stream differs substantially despite being only
11 bytes longer. A length difference is not an 11-byte feature patch. Sprite
IDs must be interpreted against each version's code table before migration.

## Identity and replay

Recipe: `config/restorations/world1-room106.json`.

ROM SHA-256:
`faec11a6f1c12b6a1b667b4bdf6bb8b0169027bda7d19ec4445d7084b4e462fc`.

Binary SHA-256:
`d7ea94d1701b46a7fb7e17a4fe670b671630687ac4a33048db4a12d9f19c5d2a`.

```sh
python3 tools/restore_star_world_1.py --target world1-room106
# Scaffold only if the isolated experiment directory does not already exist.
python3 tools/m1.py scaffold --target world1-room106
python3 tools/m1.py generate --target world1-room106
python3 tools/m1.py build --target world1-room106
python3 tools/play_demo_only1.py --restoration world1-room106 --show-location
```

Fresh captures use `recomp/inputs/world1-room106-entry.script`,
`world1-first-goal-save.script`, `world1-house-return.script` and the existing
forest entry script. The prior accepted launch remains
`python3 tools/play_demo_only1.py --restoration star-world-forest --show-location`.

This checkpoint qualifies the graphics dependency and listed regressions,
not a complete new course, repaired map, or additional user acceptance.
