# Snow Star: lower-right Star World restoration

Date: 2026-10-20. This candidate builds on the accepted upper-left cave
restoration and retains both previously restored courses. The new entrance
is map 6 / X=`$01C8`, Y=`$01E8`, translevel `$08`, room `$008`.
The user has accepted gameplay after testing both normal and key exits.
Listening coverage was not separately reported; it is tracked in the
[audio acceptance queue](audio-acceptance-queue.md).

```sh
python3 tools/play_demo_only1.py --restoration star-world-lower-right --show-location
```

The launcher selects the node with a fresh, isolated, uncleared practice save.
Enter normally. Restart the command for a fresh attempt; `--complete-all` is
rejected for this preset because completion can turn the course into a portal.
The regular executable is
`local/build/star-world-lower-right/BrutalMarioStarWorldLowerRightSNESRecomp`.
Original targets, accepted restoration targets and ordinary saves remain separate.

The user identified the [Snow Star walkthrough](https://brutalmario.fandom.com/wiki/Snow_Star)
as a possible route reference. It describes the three matching goal-point
symbols for the normal exit and a bomb match for the key/keyhole secret.
Those descriptions guided real input probes; the ROM interactions and saved
outcomes below supply the technical evidence. Release chronology is not inferred.

## Three missing dependencies

### Music causes the loading stall

The original and native recipient both remain at MARIO START, mode `$12`.
Copying missing ExGFX `$1B3` alone does not resolve it. A read-only diagnostic
reference trace instead finds the CPU looping at `$0F:C347/$0F:C34A`, waiting
for an SPC upload acknowledgement. The requested song `$54` has a null
bank/high/low pointer at `$0F:E0FC`. The uploader consequently reads an invalid
source and never finishes. Substituting an existing song proves this cause,
but that diagnostic substitution is not part of the candidate.

cheap_demo uses a different song-group layout. Its upload at `$44:A008`
contains 6,128 bytes destined for SPC `$6800`, including four songs. The
candidate extracts the reviewed 700-byte slice for the first song, `$54`
(Jingle Bells), and adapts it for the recipient's single-song `$5400` buffer.
The adapter walks reachable tracks and subroutines, relocating 20 sequence,
channel and call pointers. Notes, command parameters, instruments and tempo
remain intact; unused neighboring-song headers are cleared. It rejects
unsupported commands, escaping pointers, changed sequence layouts and a
pointer graph different from the reviewed recipe. A test specifically keeps
an `$E9` echo parameter as data while relocating an actual `$E9` call.

The adapted upload is 708 bytes, RATS-protected at physical
`$1E5000..$1E52CC` (exclusive end), with source `$3C:D008` installed in song
slot `$54`. The existing recipient music driver, sample handling and all other
song pointers remain intact. Other rooms requesting the shared `$54` slot
also gain the track; this checkpoint qualifies only the examined Snow Star
routes. The native APU's loaded `$5400..$56BC` bytes
match the adapted song exactly. Native/reference captures continue producing
non-silent music after 1,200 active frames; this is automated audio evidence,
not listening acceptance or complete donor-driver equivalence.

### Missing graphics

Room `$008` selects missing ExGFX `$1B3`. The candidate copies cheap_demo's
2,970-byte compressed stream from `$36:EF8B`, decoding to 4,096 bytes.
The same stream exists in demo7 and demo8. Only room `$008`'s word at
`$14:AE16` changes to unused `$FFB`; the global `$1B3` pointer stays untouched.
The RATS block occupies physical `$1E3000..$1E3BA2` (exclusive end).
The original recipient layout and its other graphics selections are preserved.

### Missing ice Ptooie sprite

The recipient custom-sprite `$57` record is empty. The donor supplies its
767-byte RATS block at `$1E:FC95`. The candidate copies it to `$3E:FC95`,
keeping bank-local addresses unchanged, and installs its record at `$10:B5FA`
with relocated INIT/MAIN banks. Existing penguin `$58` and Santa/slot `$09`
implementations are retained; live probes exercise both alongside the import.

This is a shared missing slot: all 512 recipient sprite lists were checked,
and `$57` is referenced by rooms `$008,$01A,$01C,$0C3,$10A,$118,$140,$141`.
The builder pins that dependency set. The other seven rooms gain this code
but are not accepted as complete/playable by this migration. Shared helper
ranges are checked in both ROMs. The differing SpriteTool constructor entry
`$01:87A7` and its per-version implementation are individually pinned; calls
continue to use the recipient's constructor and table layout.

The three allocations do not overlap the accepted repairs or any existing
RATS allocation. The recipe pins every source/output hash, original selection
and destination slot. Object layout, sprite placements, level code, exits,
completion rules and shared runtime remain unchanged. A header `$80` diagnostic
was unnecessary; the recipient sprite-list header remains `$00`. Large
teleports can skip sprite-spawn columns, so enemy qualification uses gradual
scrolling rather than treating missed diagnostic spawns as a missing asset.

## Real gameplay transitions and saved results

The tracked scripts use fresh disposable saves, player-coordinate shortcuts
and damage immunity. They do not write slot results, enemy states, exit
mappings, goal flags, DK counters/bitsets or SRAM.

| Script under `recomp/inputs/` | Bounded result |
| --- | --- |
| `star-world-lower-right-entry.script` | Loading reaches active room `$008`; low Map16 data survives graphics initialization; Mario stands and ordinary movement works. |
| `star-world-lower-right-enemies.script` | Gradual camera scrolling loads ice Ptooies (`$57`, including their generated `$C2=1` projectiles) and existing penguins (`$58`). |
| `star-world-lower-right-coins-save.script` | Five real DK collisions increment counters 1 through 5 and grant one life. Real right input crosses the end wall into `$026`; timed real jumps stop all three slots on the goal-point result. The generated `$4A` sphere is touched, and the guest clears/saves the course. Console reset, File A load and re-entry preserve the clear/DK bit, with no remaining DK tiles. |
| `star-world-lower-right-secret.script` | Another timed match triggers Santa's hidden reward, reveals a real key/keyhole, and lets Mario carry the key into it. The resulting Warp Star reaches map 0 / `$0128,$0048`. |
| `star-world-lower-right-death.script` | Falling loses one life, returns to the hub and allows entry into `$008` again. |

Normal completion sets slot `$08` from `$0A` to `$8A`; it remains a course
when re-entered. The secret sets `$8B` and enables the portal. Normal map
return automatically moves to the neighboring hub node; the reload test
transfers back to the original node before entering it. The five-coin saved
bit is `$1F30=$80`, also present in actual SRAM at `$07D1`, with checksum
`$59DA`. Loading a file resets the life count in both hosts; life persistence
is not claimed. The key is actually carried (`$1470=1`), and no secret-clear
or map destination byte is fabricated.

Same-number donor probes also complete the actual slot/goal and key/keyhole
routes. Their initial/completion flags and map integration differ: donor slot
`$08` remains `$0F`. Recipient rules are preserved; donor Warp Star behavior
is not claimed to match the recipient's successful portal check.

## Qualification and user acceptance

All 105 project tests and 191 selected local assertions pass. The suite
finishes in 118.330 seconds, including six music-adaptation
safeguards and practice-launcher coverage for the new isolated target.
All 36 existing lower-left, upper-left water, shop and Athletic Special
Boss-door full-WRAM/raw-framebuffer samples match their previous captures.
This does not qualify another full Boss fight or the other unrestored rooms.

Identity receipts, selected checks, audio measurements and capture names live
in `local/reports/lower-right-checkpoint.json`. Failed header/large-teleport
hypotheses, a nonexistent door at the end decoration, the temporary alternate
song and the off-screen `$026` goal-tape shortcut are diagnostic attempts,
not acceptance evidence. The final route uses the actual end wall and slot
reward. The user subsequently reported that normal and key exits both work
and authorized continuing. This accepts the gameplay milestone and makes
`star-world-lower-right` the cumulative gameplay baseline. The verified native
executable matches its build receipt with SHA-256
`096318c7c040fbafa7c398fa9cb773a47afd65c382d1616f6c6c819f59190708`.
No independent user hash or itemized sound report was supplied.

The user is now in a silent environment and will notify us when sound is
available again. Continue visual/gameplay acceptance and automatic audio
checks; defer human listening to a combined later session. No new AOT
variants are required; Demo 1-1 stays
at its accepted 68 variants.

Candidate SHA-256:
`92cb99a4c48baf9493af7d37f0eddb3305dd6ccf617d2c5d21cf7c15ddc51fd8`.
The [recipe](../config/restorations/star-world-lower-right.json) builds on the
accepted cave hash `7bffb1c7eb369297cd8dc2f6e84c908e718a5f06a5c445c722512f2e67e7aa37`.
ROMs, donor assets, builds, captures and saves remain untracked.

```sh
python3 tools/restore_star_world_1.py --target star-world-lower-right
# Scaffold once in a fresh workspace.
python3 tools/m1.py scaffold --target star-world-lower-right
python3 tools/m1.py generate --target star-world-lower-right
python3 tools/m1.py build --target star-world-lower-right
python3 tools/m1.py native --target star-world-lower-right \
  --script recomp/inputs/star-world-lower-right-coins-save.script --capture snow-star-repeat-native
```
