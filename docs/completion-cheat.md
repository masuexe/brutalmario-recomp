# demoOnly1 all-completion practice cheat

Date: 2026-10-17. The [practice launcher](../tools/play_demo_only1.py) now offers
an optional **all levels + DK coins** completion cheat, compatible with map
teleport, named destinations, the boss-door shortcut and air swimming.

```sh
python3 tools/play_demo_only1.py --select-level --complete-all
python3 tools/play_demo_only1.py --teleport 6 0x178 0x1a8 --complete-all --air-swim
python3 tools/play_demo_only1.py --complete-all
```

In the destination menu, enter **`c`** to toggle the completion cheat before
choosing a destination. The displayed state starts OFF unless `--complete-all`
was supplied. The last command above starts a completed practice session on
Special. Ordinary launches remain unchanged.

## Target-specific completion state

The cheat writes the pinned demoOnly1's saved progress fields after fresh-game
startup, then runs the ordinary map fade/reload before continuing to the selected
destination. All writes are one-shot; they do not freeze gameplay variables.

| CPU WRAM range | Value | Purpose |
| --- | --- | --- |
| `$1EA2–$1F01` | 96 bytes of `$9F` | Mark saved level slots clear, retain `$10`, and open all four direction bits |
| `$1F02–$1F10` | 15 bytes of `$FF` | Activate overworld events |
| `$1F27–$1F2A` | Four bytes of `$01` | Activate switches |
| `$1F2E` | `$60` | Synthetic completion counter for 96 saved level slots |
| `$1F2F–$1F3A` | 12 bytes of `$FF` | Mark every saved per-translevel DK/dragon-coin bit collected |
| `$7F:182C–1843` | 24 zero bytes | Clear the two custom midway masks |

The script uses WRAM offset `$1182C` for the final range so both native and
reference script readers accept it. The values are a synthetic practice state,
not evidence of natural clears or a measured natural exit total.

Filling the level-status table with `$FF` would be incorrect for this target.
ROM routine `$03:BA50` rejects level entry when both `$80` and `$20` are set.
The clear handler at `$10:CE2A` sets `$80`, clears the `$40` midway bit and
clears custom midway masks. The chosen `$9F` mask clears both `$20` and `$40`.
The DK check at `$4F:8C45` and the coin-spawn check at `$0D:B2CA` read the saved
`$1F2F` bitset. The custom save/load code at `$13:9ABA` / `$10:D303` copies
12 bytes of that bitset. These are observations of the pinned ROM, rather
than assumptions imported from stock SMW or unrelated source packages.

Each invocation creates a fresh session below
`local/play/demo-only-1/practice/session-*/`, with its own configuration copy,
SRAM and savestates. The cheat is applied only inside that session. It does not
import or rewrite ordinary progress. Restarting without the flag/toggle starts
a practice session without the synthetic completion state. Loading an older
in-game save or savestate can replace the one-shot state; this option is not
a permanent memory freeze or a save-conversion tool.

## Withdrawn castle preset

Updated 2026-10-18: both guessed World 1 castle positions were wrong. Map 1 /
`$0058,$0088` loads `$101`, which the user identified as World 6. Map 0 /
`$0018,$01B8` starts loading `$010` but was also rejected by the user as the
intended castle. Its native/Snes9x loading stall cannot qualify the intended
castle or establish original ZSNES behavior. `--level world1-castle` has been
removed until the actual location is captured.

The user manually entered the correct castle and reported normal **Lemmy**
boss functionality. The coordinates were not recorded. Use the
[location readout](level-select.md#capture-the-real-castle-location) to capture
the map node and entered room next time. This is a bounded manual checkpoint;
no specific victory, death-return or cheat-setting report was supplied.

Milky Way Wishes and End of Special Zone remain separate cases with
user-confirmed original MARIO START hangs. Completion flags unlock progression
checks; they do not establish that every room is playable.

## Validation

The complete project suite passes **41 tests**, including completion-flag
policy, optional menu toggling, applying flags before boss entry, destination
bounds and session isolation.

Native and reference runs both complete the following sequence with the new
cheat: Star World at map 6 / `$0178,$01A8` -> Warp Star -> Special at map 5 /
`$0118,$0128` -> Warp Star -> the original Star World position. All samples
remain in overworld mode `$0E`, with all DK bits retained. Without completion
flags, the same initial node does not take the intended warp and instead
starts a gameplay entry. This is a tested progression-unlock effect.

The native boss practice route also reaches `$177` and enters active gameplay
in `$178` with all DK bits retained and air swimming enabled. This is an entry
check, not a new fight/victory acceptance.

Both cores enter Baby Yoshi Hill (`$126`) and return to its map entrance after
a diagnostic death with every level-status byte still `$9F`, every event byte
`$FF`, all DK bits set and counter 96. The misidentified map 0 node was separately checked without the cheat; its
loading stall belongs only to that node.

A real interactive launcher smoke test toggles `c`, chooses custom Star World
coordinates with air swimming, and uses the Warp Star to Special. It creates
its own `saves/save.srm`; hashes of the ordinary SRAM, backup SRAM, configuration
and bindings remain unchanged. Only its disposable config is overridden for
SDL dummy/software-renderer testing.

Local scripts: `local/probes/completion/`. Captures include
`completion-star-baseline`, `completion-final-star-native` / `-reference`,
`completion-final-hill-native` / `-reference`, `completion-larry-correct-plain`,
`completion-larry-correct-full` and `completion-larry-correct-reference`.
Reports include `local/reports/completion-tests-final.log`,
`completion-checkpoints.json` (including ROM byte anchors), and
`completion-launch-smoke.json`. The `completion-larry-correct-*` artifact names predate the location correction
and refer to the wrong map 0 node. User confirmation of the new completion
option remains pending; Lemmy functionality was reported separately.
