# Star World entrance survey and first-course closeout

Date: 2026-10-19. The user authorized automated first-course collectible/save
checks and a survey of the other eight star entrances. This checkpoint changes
no ROM, graphics, enemies, course exits or completion rules. It fixes a native
console-reset hook discovered while testing actual saved progress.

## First course: DK applicability and actual saving

The restored lower-left course enters `$005`, with established branches to
`$054`, `$048` and `$051`. In fresh, uncleared captures of all four rooms,
the recipient and cheap_demo have **zero loaded standard DK/dragon-coin tiles**
(`$002D/$002E`), with all 12 saved coin-bitset bytes clear. The ordinary
object loader at `$0D:B2CA..B335` supplies these tiles when an uncollected
coin object exists. The examined rooms do not provide that pickup case.

Record DK pickup/persistence as **not applicable to the loaded course path**,
not as a passed pickup test. No coin or collection bit was fabricated. This
does not qualify nonzero DK-bit persistence, a dynamically created collectible
elsewhere, or the other Star World courses. Room `$004`, for example, has
ten standard coin tiles in its donor capture, representing five two-tile coins.

Actual first-course progress was tested instead. The script follows the
existing `$005` screen `$1C` exit into `$048`, interacts with the real goal
tape and waits for the guest's save. Slot `$05` changes from `$09` to `$89`.
The resulting SRAM retains that clear through a native **cold process restart**,
File A selection and ordinary re-entry into `$005`. The reference also retains
it through console reset and File A selection. No completion, DK or SRAM bytes
are poked by this route.

```sh
python3 tools/m1.py reference --target star-world-1 \
  --script recomp/inputs/star-world-1-save.script --capture star1-save-reference-new
python3 tools/m1.py native --target star-world-1 \
  --script recomp/inputs/star-world-1-save.script --capture star1-save-native-new
```

The script uses player/map coordinate shortcuts and damage immunity to reach
the goal; this is a real save/reload test, not an unassisted course clear.
The cold-process check uses only the preceding guest-generated SRAM in a fresh
disposable working directory; its receipt records the source SRAM hash and
previous binary/ROM receipt. No ordinary player saves are touched.

Local evidence: `star1-dk-donor-054`, `star1-dk-donor-048-051`, prior recipient
branch captures, `star1-save-reference`, `star1-save-native` (negative reset
case), `star1-save-cold-native` and `star1-save-fixed-native`.

## Console-reset defect and repair

The original native console-reset route resets hardware but leaves the beam
driver's old resume PC / WAI state alive. It then fails to reboot: mode stays
`$00`, despite valid SRAM that loads correctly in a new process. This is a
host reset failure, not evidence of a corrupt save.

The scaffold registers `GameSessionReset` only as `session_reset`, whereas
`RtlReset` invokes `hardware_reset`. The project build installer now also
registers the existing `GameSessionReset` callback as `hardware_reset`. It
clears the beam driver's resume/WAI state, so the next frame boots from the
ROM reset vector. It does not change shared upstream source or guest code.
Repeated builds install the callback once.

After the fix, the actual first-course normal clear survives console reset,
File A reload and re-entry. Both original targets also pass two successive
console resets using `recomp/inputs/reset-reload.script`, returning to map
mode `$0E` each time.

Unchanged-entry regressions compare full WRAM and raw framebuffers exactly:

| Target | Prior capture | New capture | Matching scenes |
| --- | --- | --- | ---: |
| Demo 1-1 | `aot-records-full` | `reset-hook-primary-regression` | 8 |
| demoOnly1 | `hub-native-128-168` | `reset-hook-only1-regression` | 3 |
| Restored lower-left course | `restoration-star1-smoke-native` | `reset-hook-star1-regression` | 9 |

All 92 project tests pass in 120.706 seconds. This is automated qualification;
no new manual playthrough or listening acceptance is implied.

## Nine-star matrix

Every recipient probe starts with a fresh, uncleared save and transfers to
map 6 without editing completion flags. Samples are taken 180 and 600 host
frame calls after pressing Y. Both the original recipient reference and its
native build show the same sampled mode, room, translevel and life values at
every entrance. Eight nodes also match both sampled player positions exactly;
the center node differs by two Y pixels at the 180-call sample and matches at
600 calls. The report retains that difference; full timing/state equivalence
is not claimed. These runs use the **unmodified demoOnly1 ROM**; the broken
lower-left row does not describe the already restored candidate.

| Position | X, Y | Translevel / room | Unmodified recipient observation | Missing extended graphics IDs |
| --- | --- | --- | --- | --- |
| Upper-left | `$128,$168` | `$04 / $004` | Enters vertical cave; geometry/graphics corrupt during graphics initialization. | `$144` |
| Upper-right | `$1C8,$168` | `$02 / $002` | Still in mode `$12`, MARIO START, at both samples. | None found in the `$100..$FFF` table; cause unresolved. |
| Upper-inner | `$178,$188` | `$07 / $007` | Vertical stripes at entry; later returns to map with one life lost. | `$127,$208,$207,$126,$16C,$12A` |
| Middle-left | `$158,$1A8` | `$03 / $003` | Underwater opening displays; idle Mario later dies and returns. Cause/playability unclassified. | None found in the checked table. |
| Center | `$178,$1A8` | `$0A / $00A` | Enters rainbow opening and remains active; incomplete resource set. | `$10F` |
| Middle-right | `$198,$1A8` | `$09 / $009` | Still in mode `$12`, MARIO START, at both samples. | `$190,$193` |
| Lower-inner | `$178,$1C8` | `$3B / $117` | Star-platform opening remains active; full course unqualified. | None found in the checked table. |
| Lower-left | `$128,$1E8` | `$05 / $005` | Known missing-graphics failure; already repaired in its isolated target. | `$102,$103,$101` |
| Lower-right | `$1C8,$1E8` | `$08 / $008` | Still in mode `$12`, MARIO START, at both samples. | `$1B3` |

The three loading stalls remain in mode `$12` with reference invalid-VRAM
blocking disabled as well. No native-only loading defect is established.
A missing-ID list is only a resource-table observation, not a complete cause
or dependency diagnosis. An empty list does not establish a complete room.

Donor probes clear cheap_demo's intro-only flag and explicitly select each
same-number room candidate by adjusting the selected overworld tile's level
byte. They do **not** claim that the donor's natural map destinations match
the recipient. `$002`, `$004` and `$008` reach active, coherent openings in
these probes. Several other donor candidates later enter transition modes;
they are not accepted as complete/playable from these bounded samples.

## Selected restoration: upper-left vertical cave, room $004

Choose map 6 / `$0128,$0168`, translevel `$04`, as the second restoration
candidate. Room `$004` selects missing ExGFX `$144` through a `$FFFFFF`
pointer. cheap_demo supplies a valid 1,825-byte LZ2 stream at `$2D:F41F`,
decoding to 4,096 bytes. demo8 has the identical compressed stream; demo7's
stream differs. This is resource evidence, not a claim that demo8 is latest.

The phase captures show that the original low Map16 buffer changes at 4,839
bytes during graphics initialization. Before this damage, its low buffer
differs from cheap_demo at one byte, `$7E:E056`: recipient empty tile `$25`
versus donor ordinary coin `$2B`. The high-buffer comparison also includes
HDMA/work-area differences, so whole-buffer equality is not claimed.
Preserve the recipient's layout rather than copying the donor room wholesale.

Both versions' observed screen-exit tables send screens `$06` and `$08` to
`$048`, the already examined goal-room branch, reducing the initial dependency
surface. This survey itself did not create a second-course ROM or build.
The subsequent [cumulative cave candidate](star-world-upper-left-restoration.md)
restores the graphics and a second missing dependency, custom sprite `$7A`.
Water interactions, five actual DK pickups and nonzero-bit save/reload,
examined exits and death/re-entry now pass bounded automated qualification.
The user subsequently accepted this cave restoration after confirming normal
custom sprites and removal of the original damaged regions. Detailed coverage
limits and the accepted identity are recorded in the linked restoration report.

## Subsequent lower-right candidate

The [Snow Star restoration](star-world-lower-right-restoration.md) now reaches
active room `$008` at map 6 / `$01C8,$01E8`. Its MARIO START stall is caused
by the absent `$54` song pointer and the resulting SPC upload wait; copying
missing ExGFX `$1B3` alone does not resolve it. The new cumulative candidate
also restores missing ice Ptooie `$57`, with real slot/normal-goal,
key/keyhole secret, DK save/reload, death and Warp Star probes. The matrix
above remains the historical unmodified-ROM survey. The user subsequently
accepted Snow Star gameplay after testing normal and key exits. Listening
coverage is tracked separately during the current silent test window.

## Reproduce the survey

The subsequent [upper-right repair](star-world-upper-right-restoration.md)
resolves `$002`'s loading stall by restoring missing song `$5D`. It requires
no graphics or sprite import. Entry, actual pipe/normal goal, five DK pickups,
save/reset/re-entry and death pass bounded native/reference checks. The user
confirmed normal entry and SMB3 bricks and accepted the stage while waiving
a complete manual run. Listening remains deferred during the silent window.
The next investigation is the middle-right `$009` loading stall. The historical
matrix above continues to describe the original ROM.

The [middle-right isolation probes](star-world-middle-right-investigation.md)
subsequently identify the absent `$2E` stream and missing graphics `$190/$193`
as independent entry dependencies. A temporary song substitution is confined
to diagnostic copies; no restored middle-right target is accepted yet.

`tools/survey_star_hub.py prepare` writes 18 scripts under
`local/probes/star-hub-survey/`: nine recipient routes and nine donor variants.
Existing conflicting scripts are refused. Choose a fresh capture prefix:

```sh
python3 tools/survey_star_hub.py prepare
for script in local/probes/star-hub-survey/[0-9]*.script; do
  key=$(basename "$script" .script)
  python3 tools/m1.py reference --target demo-only-1 --script "$script" --capture "hub-repeat-original-$key"
  python3 tools/m1.py native --target demo-only-1 --script "$script" --capture "hub-repeat-native-$key"
done
for script in local/probes/star-hub-survey/donor-*.script; do
  key=$(basename "$script" .script)
  key=${key#donor-}
  SNESREF_CORE_OPTIONS=snes9x_block_invalid_vram_access=disabled \
    python3 tools/probe_reference.py \
    --manifest local/content-versions/cheap-demo/input-manifest.json \
    --rom local/content-versions/cheap-demo/rom.sfc --script "$script" \
    --capture "hub-repeat-donor-$key"
done
python3 tools/survey_star_hub.py report --capture-prefix hub-repeat
```

The report verifies pinned ROM identities, room mappings and uncleared
recipient entrance coordinates, and records exact capture receipts plus
state/resource observations. The present report uses prefix `hub` and lives
in `local/reports/star-hub-survey.json`. Additional save/reset/DK checks live
in `local/reports/star-hub-closeout.json`. Local scripts, ROMs, save files,
captures and reports remain untracked; only reusable tools, inputs and these
conclusions are committed when authorized.
