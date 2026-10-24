# Star World secret-exit layouts from level data

Date: 2026-10-25. This is a diagnostic note. It does not qualify an exit.

The remaining Star World secret branches need exact placements. This note
records the placements that are visible in the Demo 1-1 head level data. The
head is `demo11-star-bgm` (ROM
`8939c2ace216af9f6b8c9de365ea8b2614cc8a686b0692e86fec98608afc36c0`).

## Method

The SMW level data format from the speedrunning wiki gives the pointer tables
and record formats:

- Layer 1 pointers: three-byte entries at `$05E000`, indexed by room number.
- Sprite pointers: a two-byte word at `$05EC00` plus a bank byte at
  `$0EF100`, indexed by room number.
- Layer 1 header: five bytes. Byte 0 low five bits hold the level length in
  screens minus one.
- Objects: three-byte standard and extended records. Extended object `$00`
  is a four-byte screen exit. Extended object `$01` is a screen jump. Objects
  `$22`/`$23` are four bytes. Objects `$27`/`$29` are five to eight
  bytes. Object `$28` is four bytes. Object `$2D` is five bytes.
- New-screen flag: bit 7 of the first object byte moves the following objects
  one screen to the right.
- Sprites: one header byte, then three-byte records. Record byte 0 holds the
  Y position bits and the screen high bit. Byte 1 holds the X position and the
  screen low bits. Byte 2 holds the sprite ID.

The probe scripts are `local/probes/level-parse4.py` and
`local/probes/sprite-parse.py`. The format notes are
`local/probes/smwspeedruns-level-data.txt`.

## Cave Star: room `$007`

The level is 21 screens long. The parsed finish area contains:

| Item | Placement |
| --- | --- |
| Goal point objects `$15` | `$0FA0/$0070` and `$1240/$0070` |
| Goal sprites `$7B` | `$0FB0/$01E0` and `$1250/$01E0` |
| Music bypass object `$26` | `$0F00` top of screen, song `$82` |
| Map16 terrain objects `$27` | platforms from `$0E00` to `$1400` |

The Koopa racers are sprite `$50` at `$0080`, `$0430`, `$0670`,
`$0880` and `$0C40` (five Koopas).

The runtime samples agree with the data. The tracked goal route clears at the
first goal sprite. The low path stalls at about X=`$1026` and then falls into
a pit. A spam-jump probe stomps the late Koopa but does not reach the second
goal sprite at `$1250`.

The raw sprite entries show the variant. The first goal sprite `$7B` has
byte 0 `$F0` (extra bits 0, screen bit 0). The second goal sprite `$7B` has
byte 0 `$F6` (extra bits 3, screen bit 1). Vanilla goal-tape sprite `$7B`
uses the extra bits for the secret exit. The second sprite is therefore the
secret exit goal, not a duplicate.

A teleport probe to X=`$1250`, Y=`$01E0` fell to Y=`$032B` and did not clear.
The nearby sprites were the race display and one rival. A survey at Y=`$0320`
from X=`$1100` to X=`$1400` found no floor: the player falls, dies at about
X=`$1480`, and returns to the hub. The lower area is a pit, not a hidden
section. Probes: `local/probes/cave-secret-tape.script` and
`local/probes/cave-lower-survey.script`.

## Bay Star: room `$004`

The level is 13 screens long. The screen exits are:

| Screen | Flag byte | Destination |
| --- | --- | --- |
| 6 | `$04` | room `$048` (goal room) |
| 8 | `$04` | room `$048` (goal room) |

This agrees with the wiki route: the screen-8 pipe leads to goal room `$048`.
The parsed sprite IDs are `$0A` once, `$0B` four times, `$0E` once,
`$2C` once, `$2F` twice, `$62` twice and `$7A` eleven times. The level is
vertical, so the sprite data X and Y values are swapped. The decoded `$7A`
placements are the water platforms.

Runtime water probes:

- Poking Mario to X=`$0020`, Y=`$0C80` on the page `0B` area sets the water
target from `$0CB0` to `$0C90`. The water level animates through `$0CA6` and
`$0C9C` before it settles. The switch is a map tile, not a `$7A` sprite.
- Poking Mario to each decoded `$7A` position did not change the water target.
- Forced pokes into deep water cause drowning deaths (mode `$0B` or `$0C`)
even with damage immunity. The scan is bounded below Y=`$06D0`.

The probe scripts are `local/probes/bay-switch-probe.script` and
`local/probes/bay-switch-scan.script`. The remaining switch placements need a
new probe that follows the wiki pages with real swimming input.

Camera calibration for the frame images: the two little-endian words at
`$7E:001A` and `$7E:001C` are the camera X and Y. The known page `0B` switch
tile appears at screen (32,128) in the probe frame, which matches the camera
value `(0, $0C00)` and the world tile (`$20`,`$C80`).

A frame-color detector can find the rainbow crystal tiles. Read the BMP frame
as 24-bit pixels (bottom-up rows), classify the diamond pixels (pink
`r>180,g<70`, green `g>180,r<70`, dark purple `55<r<120,g<40,b>110`), and
accept a 16x16 tile with at least four pixels of pink and four of green. Add
the camera value to the tile screen position to get the world position.
Calibration against the known switch gives the cluster (`$20`,`$C80`-`$C96`).
Other clusters are (`$30`,`$B3D`-`$B44`), (`$110`,`$A2F`-`$A35`) and
(`$FE`-`$106`,`$C22`-`$C3E`).

Contact probes with plain position pokes and 60-frame waits changed the water
target only for the known (`$20`,`$C70`-`$C80`) switch. The other clusters did
not change it. They are likely decorations or need a different interaction.
The probe scripts are `local/probes/bay-switch-grid.script` and
`local/probes/bay-crystal-probe3.script`;
the detector is `local/probes/switch-detect3.py`.

Frame images help locate the switches. The capture dumps include
`.fb.bmp` frames. Convert them with `ffmpeg -i frame.fb.bmp -vf scale=512:448:flags=neighbor frame.png`
and inspect the result. The crystal switches are visible as rainbow diamond
objects. One sits near the page `0B` bottom-left region (the known
(`$0020`,`$0C80`) tile). A second crystal is visible in the page `06` view
taken from (`$00A0`,`$0580`). That view puts the crystal at about
(`$0131`,`$0611`), but pokes at (`$0120`,`$0600`), (`$0140`,`$0620`),
(`$0100`,`$05F0`), (`$01B0`,`$0620`) and (`$01C0`,`$0610`) did not change
the water target. The screen estimate needs the exact camera position.

More probes did not resolve the other switches:

- Holding Mario at each decoded sprite position (ids `$0A`, `$0B`, `$0E`,
  `$2C`, `$2F`, `$62`, `$7A`) did not change the water target. The sprites are
  not the switches.
- Held-position sweeps at Y=`$0080` and Y=`$0400` drop Mario into water or
  crush him in solid tiles. The mode changes to `$0B`/`$0C` and the probes
  stop. A safe scan needs real swimming input and the current water level.
- Probe scripts: `bay-sprite-contact.script`, `bay-held-sweep.script`,
  `bay-ceiling-sweep.script`.

## Plains Star: room `$002`

The parsed sprite IDs are `$02` once, `$05` four times, `$09` once,
`$0E` once, `$10` twice, `$2C` once, `$74` once, `$77` four times,
`$80` once and `$DB` once. The `$77` sprites sit near the fourth Dragon
Coin area in the `d11-ur-coins-save-ref` capture. They are candidates for the
distinct brick that holds the P-Switch.

A teleport probe placed Mario on each `$77` position. The sprite did not
change and no P-Switch sprite appeared. Mario fell to a platform at about
Y=`$0F80`, so the `$77` sprites sit above the reachable floor. A real jump
probe from that floor is the next step. The probe is
`local/probes/plains-brick-probe.script`.

## Cave race state

The race state lives in two long-memory bytes.

| Address | Role |
| --- | --- |
| `$7FFD01` | Race flag. It is 0 outside the course and 1 during the race. |
| `$7FFD02` | Race counter. The tracked normal route shows 6, 5, 4, 3, 2, 1 in order. |

The initializer at physical `0x16BEF8` writes `$7FFD01=1` and
`$7FFD02=$14`.

Sprite `$45` is the race display. Its RATS block is at `$34:8493`. The code
reads `$7FFD01`, copies Mario X and Y to itself, and draws the `$7FFD02`
digit. It also uses the long tables at `$7FFFA2` and `$7FFFA3`. The display
sprite is not the gate itself.

Code sites that change the race state:

- `0x176F5A`: sets `$7FFD02=6` and `$7FFD01=1` at race start. When
  `$7FFD02==1`, it also sets the ON/OFF state `$14AF=1`.
- `0x176FA9`, `0x176FD7`, `0x177005`, `0x177033` and `0x177061`:
  five copied rival handlers. Each handler sets one long byte
  (`$7FFA00`, `$7FFA10`, `$7FFA20`, `$7FFA30` or `$7FFA40`) to 2 and
  decrements `$7FFD02` when its rival reaches the finish test.
- `0x16BF0B`: compares the coin counter `$0DBF` with `$7FFC01`. When the
  counter changes, it records the new value and decrements `$7FFD02`. When
  `$7FFD02` becomes 0, it sets the level end timer `$1493=$FF`.

Runtime samples show the counter at 6, 5, 4, 3, 2, 1 as the zone resets
happen. The ON/OFF state `$14AF` becomes 1 when the counter is 1. The tracked
normal route reaches 1 before the normal goal and still clears with `$81`.
The second goal sprite at X=`$1250` stays closed. The low path stalls at
X=`$1026`. The ON/OFF state at the finish is 1, not 0. A probe that sets
`$14AF` to 0 and back did not change the loaded Map16 buffer
(`local/probes/cave-onoff-probe.script`). The finish wall is not a visible
ON/OFF block in the loaded screens.

Next probe: test whether the finish gate is an ON/OFF block that needs state 0,
and whether `$7FFD02` can reach 0. Probe scripts:
`local/probes/cave-stomp-probe.script`, `cave-race-survey.script` and
`cave-spam-race.script`; the code dumps are `cave-stomp-probe-ref` and
`cave-race-survey-ref`.

## Limits

- The parser is a diagnostic probe. It does not prove runtime behavior.
- The screen exits and placements are recipient-local.
- No secret exit is accepted by this note.
- The next step is a runtime probe at the recorded coordinates for each
  candidate switch, goal sprite or brick.
