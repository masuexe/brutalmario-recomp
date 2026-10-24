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
goal sprite at `$1250`. The second goal sprite is the likely secret exit.

## Bay Star: room `$004`

The level is 13 screens long. The screen exits are:

| Screen | Flag byte | Destination |
| --- | --- | --- |
| 6 | `$04` | room `$048` (goal room) |
| 8 | `$04` | room `$048` (goal room) |

This agrees with the wiki route: the screen-8 pipe leads to goal room `$048`.
The parsed sprite IDs are `$0A` once, `$0B` four times, `$0E` once,
`$2C` once, `$2F` twice, `$62` twice and `$7A` eleven times. The
`$7A` sprites are the water platforms. A survey capture
(`bay-secret-survey2-ref`) also shows a `$7A` sprite with vanilla slot
`$7A`. That pair is a candidate water-level switch. The switch placements are
not resolved yet.

## Plains Star: room `$002`

The parsed sprite IDs are `$02` once, `$05` four times, `$09` once,
`$0E` once, `$10` twice, `$2C` once, `$74` once, `$77` four times,
`$80` once and `$DB` once. The `$77` sprites sit near the fourth Dragon
Coin area in the `d11-ur-coins-save-ref` capture. They are candidates for the
distinct brick that holds the P-Switch.

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
