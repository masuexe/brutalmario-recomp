# Cumulative center candidate and remaining completion boundary

The current center candidate includes all eight qualified surrounding hub
courses, the center graphics/sprite/music dependencies, the powered-Mario
damage rollback and the controlled cannon-flight qualification. The center
boss ending is an accepted exception, preserved as the donor left it (see
[below](#accepted-exception-the-unfinished-boss-ending)); this is not a claim
that all nine courses have completed-clear acceptance.

Current candidate SHA-256:
`da880e47ec0aa81f06af8596e5b4c813bd3a934631041ffb9feba6a272a590b9`.
Its base is lower-inner ROM
`359b4c3fb1b4c33d4ba73cc4f9e09db642e5864517aa5e9658a87e41e252cbb5`.
The [lower-inner music correction](lower-inner-music.md) changes seven music
selection bytes relative to center `509d119f…`: course/expiry `$60`, caps `$79`.
The music report records fresh checks for this identity; the broader center
qualification described below was recorded on the preceding checkpoint.
The earlier center-only baseline `6db0bb2e…` is retained in the damage and
cannon reports as the identity originally tested there.

## Current checks

Fresh native and reference runs on ROM `da880e47…` check all three cap
pickups and natural expiry, then the assisted lower-inner 100-coin ending,
overworld return, both SRAM copies and reset/File A reload. The audio
captures cover the corrected existing songs; diagnostic ARAM checks confirm
which payload is actually loaded. The user confirmed the corrected music is
completely normal on 2026-10-21, closing the scoped listening check. See
[the music report](lower-inner-music.md) and
`local/reports/lower-inner-music-qualification.json` for exact scope and receipts.

The regular native executable SHA-256 is
`7159f1a1d61ea642145cf8826c727fde1632cd204adf8c6862ad3ff66336848a`.
Only seven selection bytes differ from the preceding ROM; no runtime code,
geometry, coin, goal or save logic changed.

### Historical broader checkpoint

`local/reports/center-cumulative-qualification.json` pins preceding ROM
`509d119fe3eb69bb151e87fae8faee6d1ea86c39cfb1f8a91cf1f6e8935f98bf`.
It records 239 exact prior-route WRAM/framebuffer samples and bounded checks
for powered damage, cannon/DK travel, five DK pickups, boss phases,
death/re-entry and the lower-inner saved ending. The boss-phase fixture
uses position/immunity shortcuts and does not qualify victory. The five-DK
fixture does not qualify saving that center result. Separate upper-inner and
lower-inner death/re-entry captures also remain historical evidence.

These broader results are not presented as fresh tests on the seven-byte
music follow-up. Capture prefixes `center-cumulative-*` and the old build
hashes belong to those earlier receipts. The historical 900-second capture
limit accommodates the roughly five-minute native assisted 100-coin script;
this limit was already in place before the music correction.

## Boss ending

The installed custom `$24` RATS block is 3,603 bytes, SHA-256
`d9ac74c7c0f05ba26dcfff5c2a09da94dff42d57cafe25361c4343fdcd1f448f`.
cheap_demo and demo8 contain exactly this block. Room `$079` selects its
boss class; the source's `$71=6` transfer belongs to the separate room
`$078` item class. The room `$079` level-ASM stub is `RTL`.

The matching source dispatches boss states 0, 1 and 2. Four real hits enter
state 2. That state stops the blue-block spawner, creates its orbiters,
then repeats its movement/attack cycle. There is no implemented terminal
victory state or level-end store in this program. Additional hits would
fall back to the state-0 handler rather than select a completed ending.
The restored block has not been truncated, and the recipe has not invented
a goal, boss-state write or save result.

The bounded phase captures remain in room `$079`, mode `$14`, with goal
timer zero and the center's completion byte unchanged. `$13CE` can already
be set by the preceding room transfer, so it is not used alone as evidence
of boss victory. A completed clear would require the real ending, correct
overworld return and a retained SRAM completion result.

A survey of the nine prepared versions found the matching star program in
cheap_demo and demo8, with identical code. Demo6 and demo7's same-number
room `$00A` has a different 2,756-byte object stream and no custom sprites;
it is not a drop-in completed version of this star course. No completed
corresponding boss donor has been identified. The local survey is
`local/reports/center-donor-program-survey.json`; signature absence is not
treated as proof that another version cannot contain a differently
identified program.

The subsequent `tools/audit_star_boss_donors.py` search derives each version's
SpriteTool table from its installed constructor, examines every type-1 slot,
and scans every valid RATS block rather than relying on sprite `$24` or room
`$079`. A candidate requires the known code hash or at least three reviewed
markers: the hit-counter load/store, graphics slot `$1D4`, and the paired
item/boss room initialization. Marker hits outside protected blocks are also
reported; none were found in the nine inputs.

| Prepared version | Installed type-1 records | Valid RATS blocks | Related programs found |
| --- | --- | --- | --- |
| demo-1-1 | 12 | 2,199 | 0 |
| 7hero | 12 | 2,366 | 0 |
| cheap-demo | 148 | 2,301 | 1: the unchanged `$24` program |
| mazo | 3 | 2,305 | 0 |
| ow | 1 | 2,229 | 0 |
| demo6 | 141 | 1,833 | 0 |
| demo7 | 137 | 1,884 | 0 |
| demo8 | 148 | 2,268 | 1: the unchanged `$24` program |
| demo-only-1 | 12 | 2,147 | 0 |

Both newer supplied `star.asm` copies are 39,310 bytes and have SHA-256
`ee1eb8ee79618c50c6866cbb32f78e33956b010135775b48575a1c9c813988d4`.
They contain the same phase-2 cycle and no subsequent mode-3 handler. The
19,321-byte data1 source is a different star program without this boss
dispatcher. All three extracted sources match the corresponding entries in
the original source ZIPs. This adds no completed matching donor. The
fingerprint remains a heuristic: differently implemented code can evade it,
and the inventory does not establish room correspondence or playability.

Reproduce the read-only search after preparing the pinned version images:

```sh
python3 tools/audit_star_boss_donors.py
```

The report is `local/reports/center-alternate-program-audit.json` and records
each input hash, derived table, candidate and archived source match. This
research does not change the cumulative ROM or its accepted checks.

### RetroAchievements donor images

Three additional images were prepared after the table above was written and
are stored under `local/content-versions/`. They are **not** registered in
`config/content-versions.json`: the originating session verified each BPS
patch checksum and the produced image hash before the patches were discarded,
so this checkout can hash the images but cannot re-derive them. They are
audited through the `--extra` option instead of a pinned receipt.

| Image | SHA-256 | Installed type-1 records | Valid RATS blocks | Related programs |
| --- | --- | --- | --- | --- |
| `ra-mario-complete` | `508bafbf8619cad8…` | 148 | 2,306 | 1: the unchanged `$24` program |
| `ra-luigi` | `0d6e09b2d1c107b7…` | 64 | 649 | 0 |
| `ra-bowser-castle` | `6e95b6a7c77be912…` | 12 | 2,368 | 0 |

`ra-mario-complete` carries the same 3,603-byte block, SHA
`d9ac74c7c0f05ba26dcfff5c2a09da94dff42d57cafe25361c4343fdcd1f448f`, at
physical offset `0xF0000` in slot `$24` — byte-identical to `cheap-demo` and
`demo8`. It does not contain a completed boss program. `ra-luigi` uses an
unrelated engine (2 MiB, no reviewed marker present) and `ra-bowser-castle`
holds only the unpaired counter-store marker, so neither is a boss donor.

Its boss room `$079` layer-1 stream is also byte-identical to `cheap-demo`
(16 bytes, `80 50 73 40 10 07 00 01 08 04 00 78 40 60 13 FF`), so the room
that needs a finished ending is unchanged. Six other rooms (`$077`, `$086`,
`$0C0`, `$0FD`, `$108`, `$152`) differ between the two lineages, which reads
as ordinary drift rather than a targeted ending hook; the streams were not
decoded far enough to attribute individual objects.

Reproduce, with the images present:

```sh
python3 tools/audit_star_boss_donors.py \
  --output local/reports/center-alternate-program-audit.json \
  --extra ra-mario-complete=local/content-versions/ra-mario-complete/rom.sfc \
  --extra ra-luigi=local/content-versions/ra-luigi/rom.sfc \
  --extra ra-bowser-castle=local/content-versions/ra-bowser-castle/rom.sfc
```

Unregistered entries are hashed but marked `"unregistered": true` and are
not checked against a patch receipt. Adding a third independent negative
result narrows the completed-donor search but does not prove that no
differently implemented program exists anywhere.

### Community documentation of the unfinished boss

Our binary and source findings say the Special Warp Star boss program stops
after its phase-2 cycle. Public community documentation agrees, which matters
because it turns "no completed donor was found locally" into "the author
never finished this boss in any released demo".

- The [boss listing](https://brutalmario.fandom.com/wiki/Boss) defines an
  asterisk as *"that boss is still incomplete"* and lists the `★-9 Special
  Warp Star` boss as `Giant Starman*`.
- The [Special Warp Star](https://brutalmario.fandom.com/wiki/Special_Warp_Star)
  article names `Giant Starman*` as that level's boss.
- The one claim of a fully finished build,
  [Demo 9.5](https://brutalmario.fandom.com/wiki/Hoaxes), is documented as a
  hoax: an anonymous user invented the article and the accompanying video was
  edited, not captured from a ROM.
- [Boss Demo](https://brutalmario.fandom.com/wiki/Boss_Demo) is sometimes
  suggested as a completed build, but it showcases the finished **7
  Koopalings' Fusion Boss**, a different encounter, so it does not supply
  this ending.

Treat this as community documentation, not as an authority: it is external,
unversioned wiki text and it was not used to change any ROM. It is consistent
with the local audit of all twelve prepared images and with the archived
`star.asm` sources, and it is the third independent line of evidence that no
completed Giant Starman program is available to copy. It does not by itself
prove that no unreleased or differently implemented program exists.

## Accepted exception: the unfinished boss ending

**Decision (2026-10-21):** the center course ships with the donor's unfinished
ending preserved as-is. This is an explicit, deliberately scoped exception,
chosen to respect the original work. No new clear condition, goal trigger,
boss-state write or save result was authored; the recipe still invents nothing.

**Covered:** Mario can reach room `$079` and fight Giant Starman through its
implemented phases (states 0, 1 and 2). The eight surrounding courses keep their
qualified exits, and the center's graphics, cannon/DK, coin, damage and
Boss-phase dependencies stay qualified.

**Not covered:** a center victory, an overworld return, or a retained SRAM
completion result from this course. No later document may claim a center clear.
`$13CE` being set by the preceding room transfer is not such a claim.

**Why an exception rather than another restoration attempt:** the donor program
has no terminal victory state, all twelve prepared images agree, the archived
`star.asm` sources agree, and community documentation marks the boss
incomplete. Closing this differently would mean authoring new content, which is
out of scope for a project that copies a verified playable donor.

## Launch

```sh
python3 tools/play_demo_only1.py --restoration star-world-center --show-location
```

Restart the command after rebuilding to replace an already-running older
process. The practice launcher still creates a disposable uncleared save.

Cascade check: the same freeze reproduction (`poke 1dfb 21`) on the centre
candidate `5882080f…` also keeps running - full WRAM keeps changing over 600
frames - so the inherited `$21` track survived the rebuild rather than only
existing in the standalone lower-inner image.
