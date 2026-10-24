# Upper-right Star World: room $002

Date: 2026-10-20. This cumulative candidate adds the upper-right course to
the accepted Snow Star gameplay baseline. Entrance: map 6, X=`$01C8`,
Y=`$0168`, translevel `$02`, room `$002`. The user accepted this restoration
stage after confirming entry and SMB3 brick behavior, together with the
automated route checks. A complete manual traversal was explicitly waived;
this is not a full playthrough report. Human listening is deferred during
the user's silent test window, as recorded in the
[listening queue](audio-acceptance-queue.md).

```sh
python3 tools/play_demo_only1.py --restoration star-world-upper-right --show-location
```

The isolated launcher selects a fresh, uncleared node. Enter normally and
play the vertical course as desired. Restart the command for a fresh attempt.
Completion practice flags are rejected because they can replace Star World
courses with portals. No further full manual run is required for this stage;
audible confirmation can wait until sound is available.

The user reported that the long course was too time-consuming to finish
manually. They confirmed normal entry and working SMB3 bricks, then agreed
to accept the stage using those observations plus the bounded automated
pipe/goal/DK/save/death checks. `star-world-upper-right` is now the accepted
cumulative restoration baseline. Manual coverage remains limited to those
reported interactions; complete traversal and listening are unconfirmed.

## Missing song, intact course data

The unmodified recipient requests BGM `$5D` while remaining at MARIO START,
mode `$12`. Its bank/high/low music pointer at `$0F:E117` is zero. The
recipient's existing music uploader cannot finish with that missing stream.
Restoring the selected donor song lets both the reference and native build
reach active mode `$14`, room `$002`.

The room has no missing extended graphics pointer in the checked table. Its
sprite list is byte-identical to cheap_demo's same-number room and contains
no custom-sprite entries. Loading the repaired course preserves the low
Map16 buffer through graphics initialization. A complete byte-range audit
finds changes only in the three-byte song pointer and one new RATS block;
all layout, graphics selections, sprites, exits and runtime remain intact.

cheap_demo's `$44:E008` upload contains four songs, `$5C..$5F`, in a
6,128-byte SPC `$6800` group. `$5D` uses the second eight-byte sequence
header, at offset 8, and track/subroutine data `$6E46..$71B2` (exclusive end).
The builder selects that header and the 876-byte data window, preserves
56 bytes of header padding, and relocates 29 sequence/channel/call pointers
into the recipient's `$5400` buffer. The resulting song is 940 bytes;
its complete upload is 948 bytes. Six channels are active. Notes, instruments,
tempo and command parameters are preserved, including the zero-operand
`$F0` command. No track from the other three songs is imported.

The adapter rejects pointers into neighboring headers or omitted data,
unsupported commands, an escaping data window and a changed pointer graph.
Three new tests cover grouped-song extraction, `$F0` and invalid boundaries.
The preceding Snow Star `$54` recipe still produces the same pinned ROM.

The RATS block occupies physical `$1E6000..$1E63BC` (exclusive end), and
song `$5D` now points to `$3C:E008`. Its adapted upload SHA-256 is
`f2cab1c9f90bbecb26f29c98291c155f59bca3c21723801be7d8976006018add`.
Other rooms requesting the shared `$5D` slot also gain the track; this
checkpoint does not qualify those courses as playable.

## Actual interactions and persistence

The three tracked scripts under `recomp/inputs/` use disposable fresh saves.
They use map/player/camera shortcuts and, where stated, damage immunity.
They never write coin counters, Dragon Coin bits, enemy states, exits, goal flags or
SRAM. No imported savestate is used.

| Script | Bounded result in native and reference hosts |
| --- | --- |
| `star-world-upper-right-entry.script` | Active room `$002`; intact low Map16 through graphics loading; ordinary walk/jump input; remains active at later samples. |
| `star-world-upper-right-coins-save.script` | Five actual Dragon Coin collisions; real up/jump input enters the existing downward-facing pipe into `$048`; real right input touches its goal tape; guest-generated clear/Dragon Coin save survives console reset, File A load and re-entry. |
| `star-world-upper-right-death.script` | A fall loses one life, returns to the hub and permits a fresh entry. |

Five Dragon Coins increment both counters from 1 through 5, set `$1F2F=$20`
and award one life. Normal completion changes slot `$02` from `$06` to
`$86`. Actual SRAM contains `$07D0=$20`, with checksum `$5A3A`; both clear
and Dragon Coin progress survive reset/reload. Re-entering `$002` has no remaining
standard Dragon Coin tiles. File loading resets the life count in both hosts;
life persistence is not claimed.

The original exit on vertical screen `$0A` points to `$048`. The pipe test
positions Mario below its real mouth, releases all position writes and uses
up/jump input. It does not fabricate pipe state or a destination. Same-number
cheap_demo probes also collect all five coins, enter `$048` and clear through
its actual goal. Donor slot `$02` remains `$06` afterward; recipient `$86`
completion/save integration is retained. No secret exit is accepted by this
checkpoint, and automated coordinate shortcuts do not establish an unassisted
full traversal.

Early diagnostic large teleports caused camera clamps and crush deaths.
They are excluded from acceptance. The final collectible route uses real
Start pauses before relocating Mario and both camera coordinates, waits out
the pause debounce, then unpauses. Every relocation's pause state is checked.
Collision rules and the camera implementation are unchanged.

## Qualification boundary and reproduction

All 108 project tests pass in 134.700 seconds; 242 selected local assertions
pass. Sixty previous scene samples match full WRAM and raw framebuffers:
lower-left entry (9), shop (18), Athletic Special Boss door (1), upper-left
water (8), and Snow Star's DK/normal-clear/reset route (24). This does not
claim another full Boss fight or a replay of every Snow Star secret branch.
Original target checks and all earlier candidate identities remain valid.
No AOT variants or runtime patches are added; Demo 1-1 remains at 68.

Native APU `$5400..$57AC` matches the adapted song exactly after 1,200 active
frames. Late five-second native/reference PCM windows are non-silent. These
checks establish loaded data and generated audio, not human listening
acceptance, donor-driver equivalence or output-device continuity. SDL output
diagnostics report underruns in both concurrent and isolated runs; the earlier
Snow Star diagnostic also reports them. Generated PCM is identical across the
two new native runs. This is not a listening pass or an established new
content regression. Capture receipts and device statistics are retained in
`local/reports/upper-right-checkpoint.json`. The user will report when sound
becomes available; listening does not block this gameplay candidate.

Candidate ROM SHA-256:
`c96a9f5c5abd01e7749c493f615c8a398365dba2ed9076a33523e3b35ec56c0a`.
Accepted base SHA-256:
`92cb99a4c48baf9493af7d37f0eddb3305dd6ccf617d2c5d21cf7c15ddc51fd8`.
Regular native executable SHA-256:
`8cc74c66ea524546f047ab59a9e3e35a2deba82f4746596a8ba8a2138b30b2c1`.
The [recipe](../config/restorations/star-world-upper-right.json) pins sources,
data windows, pointer graph, allocation and output. ROMs, builds, assets,
captures and saves remain untracked.

```sh
python3 tools/restore_star_world_1.py --target star-world-upper-right
# Scaffold once in a fresh workspace.
python3 tools/m1.py scaffold --target star-world-upper-right
python3 tools/m1.py generate --target star-world-upper-right
python3 tools/m1.py build --target star-world-upper-right
python3 tools/m1.py native --target star-world-upper-right \
  --script recomp/inputs/star-world-upper-right-coins-save.script \
  --capture upper-right-repeat-native
```
