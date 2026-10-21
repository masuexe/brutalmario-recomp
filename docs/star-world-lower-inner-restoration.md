# Lower-inner star course restoration

The map-6 entrance at `$0178,$01C8` selects translevel `$3B`, room `$117`.
The cumulative candidate restores its missing warp-star actors and 100-coin
controller on the accepted middle-left ROM. This checkpoint qualifies the
actual 100-coin exit and save, using explicit player/camera shortcuts for
the pickups. It does not claim an unassisted complete route or DK coverage.

## Data and identity

- Recipe: `config/restorations/star-world-lower-inner.json`.
- Base ROM SHA-256:
  `394c59841ce22184b4f804f4ad518f83c26190178127a471364ab615069e0388`.
- Candidate ROM SHA-256:
  `cb3e60179cf83af322ce8d0316e1f2248ef4c02b7bc2b8084cfb99a86f3a30f3`.
  The previous candidate was
  `1c35a893ec79fa369a68874b7743943c1e08532426d91bfa4ceca33e143df0e9`; the
  only difference is the interim song-slot alias described under the cap defect.
- No runtime changes, new graphics, geometry replacement or global entrance
  branch edits are included.

The donor layer-1 pointer `$F0:AA50` maps to physical offset `$382A50`,
within the 4 MiB LoROM. Its 9,333-byte terminated stream is byte-identical
to the recipient stream at `$3A:90B4`, SHA-256
`8e52976f05cfeeb1b3f538c527764c52f0b1fe729bd488ad0c5e56fb87377129`.
The 53-byte sprite lists also match, SHA-256
`28b431f0dd8724f6969495d8b069cb0d286584b8b76bfc09035234de676eb7b5`.
An earlier local handoff incorrectly classified the donor pointer as outside
the ROM; it is a valid high-bank mirror. That missing-geometry diagnosis
has been withdrawn.

| Custom slot | Role | Donor RATS block | Destination | Bytes |
| --- | --- | --- | --- | --- |
| `$30` | `hat.asm`: caps and 100-coin controller | `$1B:8000` | `$34:8000` | 1,680 |
| `$37` | `meta.asm`: warp-star movement | `$21:EC22` | `$36:EC22` | 3,428 |

The complete blocks retain their bank-local addresses. The recipe pins
the source records, empty destinations, room dependency sets and shared
helpers. The recipient constructor remains in use with separately pinned
version-specific constructor bytes. Slot `$30` is also selected by room
`$03C`; slot `$37` by `$016,$0F0,$0F1,$0F2,$0F4`. Those other rooms are
not accepted as playable by this checkpoint.

The exploratory `$00:A6AF` global entrance edit from the preceding session
is preserved locally and excluded from both the accepted middle-left
recipe and this candidate. Restoring the missing actors already lets Mario
pass the former `$0522` stop.

## Qualification

`star-world-lower-inner-route.script` uses real controls after the initial
map shortcut. Both hosts cross `$0522`, ride the warp stars and reach about
`$0D20,$0100`, retaining four lives-minus-one. It is a traversal segment.

`star-world-lower-inner-goal.script` is a separate collision fixture. Real
Start pauses permit player/camera placement at the existing coins; finite
position holds keep Mario there while the guest performs pickups. It never
writes coin totals, actor state, life totals, exit flags, the goal timer or
SRAM. The controller observes 99 coins, then the real rollover to zero,
awards the ordinary extra life and triggers its existing ending. Its code
sets `$141C=1`; this report calls it the **100-coin exit** rather than
claiming a separate normal-exit route.

| Sample, both hosts | Result |
| --- | --- |
| Before pickups | Coins 0, lives-minus-one 4 |
| Late pickup sample | Coins 99 |
| Hundred coins | Coins 0, lives-minus-one 5 |
| Ending | Guest `$1493` timer becomes nonzero |
| Overworld return | Mode `$0E`, `$13CE=1`, translevel flag `$1EDD=$8F` |
| Saved result | Both SRAM copies, `$003B` and `$01E8`, contain `$8F` |
| Reset and File A reload | Mode `$0E`, both copies and WRAM retain `$8F`; lives-minus-one 4 |

The goal captures are `lower-inner-goal-reference` and
`lower-inner-goal-native`. The bounded traversal captures are
`lower-inner-qualified-route-reference` and
`lower-inner-qualified-route-native`. Local receipts pin each ROM, input
script and executable/core identity. The generated local report is
`local/reports/lower-inner-qualification.json`.

Nine previous native routes were rerun on this candidate. All **239**
sampled full-WRAM images and raw framebuffers match their prior baselines:
lower-left, shop, bounded Athletic Special boss entry, upper-left, Snow
Star, upper-right, Sky Star, Cave Star and the middle-left water clear.
The boss-entry regression is not a complete boss-fight acceptance claim.

Death/re-entry was outside the original checkpoint above. A subsequent
fresh-session check on cumulative center ROM `e0fb3837…` confirms a real pit
death loses one life, returns to the map and permits re-entry into `$117`
with that life total retained in both hosts. See
`star-world-lower-inner-death.script` and captures
`center-cumulative-lower-inner-death-{reference,native}`. All DK coins and
an unassisted 100-coin route remain unqualified. The center damage regression and reported
cannon-distance issue are tracked in
[the center damage report](center-damage-regression.md).

## Launch

```sh
python3 tools/restore_star_world_1.py --target star-world-lower-inner
python3 tools/m1.py scaffold --target star-world-lower-inner
python3 tools/m1.py generate --target star-world-lower-inner
python3 tools/m1.py build --target star-world-lower-inner
python3 tools/play_demo_only1.py --restoration star-world-lower-inner --show-location
```

Scaffold only when the target directory does not already exist. Practice
launches use disposable uncleared saves so completion does not replace the
course entrance with a Warp Star.
## Known defect: cap pickup freezes the game

Reported 2026-10-21: in this course, eating a cap (hat) changes the music and
the game freezes some time later.

**Root cause.** The recipe restores custom slot `$30` (`hat.asm`: caps and
100-coin controller), which requests music through `$1DFB`:

| Trigger | Song id | Donor table entry | Recipient table entry |
| --- | --- | --- | --- |
| Cap picked up (sets `$7FFFD0/$7FFFD1/$7FFFD2 = $FF`) | `$22` | `30FEEC` | `13CCE2` - a *different* song |
| Cap effects expire (flag drops below `$11`) | `$21` | `13A412` | **`000000` (no song installed)** |
| 100-coin controller award | `$1E` | `0F6CE1` | **`000000` (no song installed)** |

The **recipient's** song pointer table is three bytes per id, big-endian, at
`$0F:E000` (confirmed against the four recipes that restore music). This recipe
restores no music at all, so both ids it requests are empty in the recipient.

The donor does not use the same layout. Reading donor ids through that table
returns payloads with a different destination base (`0x0410` for `$54`, against
`0x5400` in the adapted recipient payload) and some entries are not valid LoROM
addresses at all. Donor music is reached through the per-recipe `music` groups,
not by id-to-id table comparison, so a cheap_demo-to-demoOnly1 id map cannot be
built from the two tables as they stand.

The `[count][base][body][0000]` wrapper is also specific to songs the recipes
install. Only three recipient ids and one donor id pass that structural check,
while the recipient actually has 98 installed ids, so the original songs in both
ROMs use the hack's own layout. Matching a candidate song against the donor
therefore needs that original format decoded, or a runtime SPC capture of the
uploaded song, before any automatic map can be attempted.

Requesting an empty id does not fail gracefully: the guest hangs waiting for
the music engine. Minimal reproduction on `star-world-lower-inner`:

```
enter the course, then   poke 1dfb 21
```

`$1DFB` stays `$21` and is never consumed, and full WRAM is byte-identical from
30 frames after the poke through 600 frames, while the emulator keeps
advancing. Control runs: the same poke on `cheap_demo`, where `$21` is
installed, keeps running normally (5,141 bytes changed over the same window),
and poking `$22` or `$1E` on the candidate does not hang.

This matches the report exactly: the music changes on pickup (`$22`), then the
game freezes when the caps expire and `$21` is requested.

**Interim mitigation (applied).** The recipe now aliases both empty slots to the
course's own level theme: `0FE063` (`$21`) and `0FE05A` (`$1E`) are set to the
three-byte entry of `$40`, currently `15EFEE`, through equal-width
`code_patches`. Re-running the reproduction keeps the game alive (`$1DFB`
returns to zero, full WRAM keeps changing) instead of hanging, and the
100-coin exit still qualifies. This removes the crash; it does **not** play the
donor tracks, so it stays documented as an interim measure.

**Proper fix direction.** Restore the songs `hat.asm` depends on - `$21`, `$1E`
and, for fidelity, `$22` - the same way the lower-right, middle-right,
upper-right and center recipes restore their tracks: one `music` block per song
with its own allocation, `pointer_address` (`0FE063` for `$21`, `0FE05A` for
`$1E`, `0FE066` for `$22`) and reviewed relocations. Do not leave the empty
slots permanently aliased to
an existing track: that plays the wrong music and is not a faithful
restoration. Do not patch the sprite to skip its music request either.

**Until then.** Grabbing a cap in this course freezes the game. The 100-coin
exit fixture does not grab caps, which is why the qualification passed.

**User acceptance (2026-10-21).** The user re-tested in game and reports: eating
a cap switches the music, and when the cap expires the music returns to the
course theme with no freeze. The interim alias is therefore confirmed to remove
the crash while leaving the proper track restoration open.

### Runtime SPC capture makes a faithful fix feasible

The diagnostic core can now dump the full 64 KiB SPC/APU RAM at a chosen host
frame (`BM_APURAM_FRAME`, `BM_APURAM_FILE`). A dump taken while this course's
level theme is playing shows a complete, already-relocated song sequence at
ARAM `0x5400`:

```
@0x5400: 67 54 77 54 FF 00 02 54 00 ...
```

A captured lower-inner image at `0x5400` reads `67 54 77 54 FF 00 02 54`:
pattern pointers `$5467`/`$5477`, the `FF 00` marker and sequence pointer
`$5402`, which is exactly `base + 2` as the music recipe format requires. That
proves the capture is a genuine relocated song image rather than sample data. A
full track walk still needs the precise pattern-header and loop semantics that
`adapt_music` encodes, so lifting a donor song as a payload is the next step,
not a finished capability.

That is the two pattern pointers, the `FF 00` marker and the `$5402` sequence
pointer, i.e. the same base the music recipes write. Because the image in ARAM
is fully relocated, songs can be compared across ROMs byte-for-byte without
decoding either static format, and a donor song can be lifted as a payload with
`destination_base` `0x5400` and installed through the existing `music` block
with no relocation review.

Concrete plan for the proper restoration: force the intended donor id to play,
dump ARAM, take the sequence image at `0x5400`, and install it at `0FE063`
(`$21`) and `0FE05A` (`$1E`). The same technique gives the cheap_demo-to-
demoOnly1 id map for the wider wrong-music question: fingerprint the `0x5400`
image per id in both lineages and match identical images, falling back to
similarity for arrangements that changed between demos.

### SPC capture: what it does and does not yet give us

Follow-up probing narrowed the claim above.

- Poking `$1DFB` does **not** reliably force a song. On the candidate the
  current-song byte `$0DDA` stays at `$40` after poking `$21`, `$1E` or `$22`;
  on the donor a poke of `$21` leaves `$0DDA` at `$1E`. Forcing songs therefore
  needs a different mechanism (for example patching the level's music id), not
  a single `$1DFB` write.
- The upload base is **not** shared. A donor capture taken in level with
  `$0DDA=$1E` has nothing at ARAM `0x5400`, while the candidate has a valid
  image there. The donor's sequence headers cluster around `0x298D` onward at
  8-byte spacing, and the candidate also shows headers at `0x1486`/`0x1548`
  besides `0x5400`. The two lineages do not upload songs to the same offset.
- Consequence: byte-comparison of `0x5400` images is valid **only** for songs
  the recipes install at `destination_base 0x5400`. Using it as a general
  cross-lineage matcher requires first learning the donor driver's own upload
  layout, which this round did not establish.

Nothing here changes the shipped candidate: the interim alias stays, the cap
freeze stays fixed, and the user's accepted behaviour is unaffected.

### Where the course music id comes from

PC tracing pinned the mechanism without needing a song-table guess. During the
level load, `$0D:F130` runs:

```
F130  A5 57     LDA $57
F132  F0 04     BEQ +4
F134  3A        DEC A
F135  8D DA 0D  STA $0DDA
F138  A5 59     LDA $59
F13A  F0 04     BEQ +4
F13C  3A        DEC A
F13D  8D DA 0D  STA $0DDA
F140  60        RTS
```

So `$0DDA` is `$59 - 1`, and `$59` is filled by the header parser at `$05:860F`
(`SEP #$30 / LDA [$65],Y / STA $0A / ... / STA $59`), i.e. the **third byte of
the level header** pointed to by the 24-bit `$65/$66/$67`. A capture taken on
the frame `$0DDA` becomes `$40` shows that pointer as `$3A:B528` with
`$0A=$01`, `$0B=$02`, `$59=$07`, so the parser is also invoked for headers other
than the one that finally sets the music; identifying the exact level-header
address for room `$117` needs another step.

Practical upshot: force a song by patching the level header's third byte, not by
poking `$1DFB`, and validate by watching `$0DDA` rather than assuming the write
landed. That mechanism is the next concrete step for song fidelity; it is not
required for the accepted freeze fix.

### Verified: forcing a song through the level header

The header pointer captured at the music write is a real ROM address, and
patching its music byte reliably changes the played song.

- Course level header: **`$3A:B522`** (file offset `0x1D3522`), bytes
  `40 60 41`, so header byte 2 is `music id + 1` and the course plays `$40`.
- Patch byte 2 to `0x0D` in a probe ROM, enter the course: `$0DDA` becomes
  `0x0C` with mode `$14`, i.e. the forced id actually plays.
- The captured ARAM image at `0x5400` changes with it: `$40` gives
  `67 54 77 54 FF 00 02 54`, `$0C` gives `C5 55 D5 55 FF 00 02 54`. The base
  and the `base + 2` sequence pointer stay the same, so the capture is the
  relocated song for the forced id.

This is the reliable forcing mechanism the earlier `$1DFB` pokes lacked. It
gives a general capability: force any installed id, then capture that song's
relocated image. Probe ROM: `local/probes/lower-inner-music.sfc`.

Still required before a donor song can be installed: the donor uses a different
upload base, so its image must be captured on the donor side (same technique,
after locating the donor's own level header) and its internal pointers rebased
to `0x5400` before it can be written as a `music` payload.

### Donor upload base found: `0x6800`

Scanning a donor capture for the sequence-header signature (`[pat][pat] FF 00
[base+2]`) finds it at ARAM **`0x6800`**:

```
@0x6800: 29 6B 29 6B FF 00 02 68 E4 6E
```

`0x6802` is `base + 2`, exactly the same relationship the candidate shows at
`0x5400`. That base equals the `source_base` (`0x6800` / 26624) that the four
music recipes already use for donor groups, which ties the static recipe format
to the runtime upload. The two lineages therefore share the song format and the
header layout, and differ only in upload base: donor `0x6800`, candidate
`0x5400`.

Consequence: a donor song captured at `0x6800` can be turned into a candidate
payload by rebasing its internal pointers by `0x5400 - 0x6800 = -0x1400` before
writing it with `destination_base 0x5400`. No format conversion is needed, only
the pointer walk plus a constant shift.

Donor level-header candidates were located at `$5C:D885` and `$5C:D91B` (both
have byte 2 = `music id + 1` = `$25`, so the donor course plays `$24`). Patching
both to `$21` did not change `$0DDA` in a 2500-frame capture - the dump still
showed `$24` with mode `$0F` - so the donor-side forcing needs a later capture
or a second header site before it can be trusted.

### Why single-song transplant is harder than it looked

Extracting the donor image at ARAM `0x6800` does not yield one song. The
header-signature scan finds sequence headers at `0x6800`, `0x6808`, `0x6810`,
`0x6818` - consecutive 8-byte records - so the donor uploads a **sequence
table**, not a single relocated song. Walking from the first record also runs
into non-song data (`0xDE` at offset 350) and the layout leaves no zero gap
between the 8-byte header and the following bytes, unlike the candidate image
at `0x5400`, which has the recipe's `8 + 56 zeros + data` shape.

Consequently the donor's ARAM capture is not a drop-in payload even though the
upload base and header relationship are now known. Turning it into one song
requires the donor's own `sequence_offset` / `source_data_offset` pair for that
id - the same per-song parameters the existing recipes already pin for `$54`,
`$2E`, `$5D` and `$16` - and those were derived per song, not from a table.

Also recorded: the donor's in-level music for this course is `$1E` (not `$24`,
which is what the loading-frame sample showed), so the donor's `$1E` track is
present in any donor capture taken in level. That is the cheapest target if
single-song extraction is continued, because no forced playback is needed.

### The donor group holding `$1E` is in ROM at `$3F:A004`

Searching the donor ROM for the `$1E` sequence header bytes (`29 6B 29 6B FF 00
02 68`) finds exactly one hit, at file offset `0x1FA00C` (LoROM `$3F:A00C`).
The enclosing group header sits at file `0x1FA004`:

```
0x1FA004: F0 17 00 68          count 0x17F0 (6128), base 0x6800
0x1FA008: 29 6B 29 6B FF 00 02 68   sequence 0
0x1FA010: E4 6E F4 6E FF 00 0A 68   sequence 1
0x1FA018: 65 78 75 78 FF 00 12 68   sequence 2
```

Count + 8 = 6136, exactly the `source_group.size` the existing music recipes
pin, and the base `0x6800` is the runtime upload base found earlier. Sequences
are 8-byte records at offsets 0, 8, 16, ... so a song's `sequence_offset` is
`8 * k` in this group.

Remaining step to build a payload: the song's `source_data_offset` and
`song_size`, i.e. where its track data begins after the sequence table. Those
can be derived from the pointers the sequence uses (the lowest address reached
by the pattern block and `0xE9` loops bounds the data start), and the result can
then be verified mechanically: install the payload, force the candidate to play
`$1E`, and compare the captured ARAM `0x5400` image against the donor image at
`0x6800` shifted by `-0x1400`.

### The last blocker: the reviewed music command subset

The `$1E` group is located, but adapting it with the existing tool stops
immediately. `tools/restore_star_world_1.py`'s `adapt_music` only walks the
command subset it has reviewed:

```
lengths = {0xda:1, 0xdb:1, 0xe0:1, 0xe2:1, 0xe7:1,
           0xe9:3, 0xef:3, 0xf0:0, 0xf1:3, 0xf2:3}
```

Walking the `$1E` sequence reaches **`0xDE`**, which is outside that subset, so
`adapt_music` raises `unsupported music command`. The four songs the recipes
already restore happened to stay inside the reviewed subset; this one does not.

So finishing the real-song transplant needs one of two things, both larger than
a data edit:

1. **Extend `adapt_music`** with the missing commands and review the resulting
   relocations for this song, then add the `music` block. This is a reviewed-tool
   change, so it needs the same care as the existing pins.
2. **Add a raw-payload path** that installs a captured image unchanged by
   uploading it to the donor base (`0x6800`) instead of rebasing to `0x5400`.
   That avoids pointer rewriting entirely but needs a new recipe mechanism and a
   check that the candidate driver does not already use ARAM `0x6800`.

Neither is required for the accepted freeze fix. This is recorded so the next
attempt starts from the real constraint rather than re-deriving the group.
