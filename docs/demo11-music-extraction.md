# Demo 1-1 music extraction

Date: 2026-10-26. Status: extraction complete. Automated checks pass. No user
listening check exists for the rendered files.

## Objective

Extract every custom song from the accepted Brutal Mario Demo 1-1 ROM.
The extract contains the raw song data and rendered audio.

## Identities

| Item | Value |
| --- | --- |
| ROM | `local/roms/demo-1-1.sfc` |
| ROM SHA-256 | `314496f67caf53d1d74873333de366a07a2b2446d7bbb5f27eeeb9aa69894f32` |
| Tool | `tools/extract_demo11_music.py` |
| Capture host | `local/build/snesref/snesref` |
| Capture host SHA-256 | `b4ccacbbf74f4f4f` prefix (full value in the manifest) |
| Reference core | `local/upstream/snes9x/libretro/snes9x_libretro.so` |
| Reference core SHA-256 | `39aff6a57c370035` prefix (full value in the manifest) |
| Core option | `snes9x_echo_buffer_hack=enabled` |
| Output | `local/music/demo-1-1` |

The output stays in the gitignored `local/` tree. The tool, this note and the
tool tests are tracked.

## Source layout

The new-family engine keeps a 256-entry song table at `$0F:E000`. Each entry
has three bytes: the bank, the high byte and the low byte of a LoROM address.
The Demo 1-1 ROM has 100 non-null entries.

Each non-null entry points at one upload block:

| Offset | Content |
| --- | --- |
| +0 | Payload length, little-endian word |
| +2 | ARAM destination word, `$5400` for all 100 entries |
| +4 | Payload bytes |

The payload length is between 135 and 5,999 bytes. The total payload is
154,015 bytes. The block order, the entry order and the song order are
version-local.

## Method

1. Read the table and extract each payload block.
2. Copy the Demo 1-1 ROM. Set the pointer of slot `$30` to the target
   payload. Slot `$30` is the song that the capture course requests.
3. Enter that course in the pinned Snes9x reference host. Record the audio
   output.
4. Cut the recording at frame 2,161. The level load leaves a silent gap
   there. All 100 captures requested the carrier song at frame 2,196.
5. Keep at most 100 seconds after the cut. Trim a short jingle after its
   last note.
6. Write the payload file and the manifest record.

The carrier course is the ordinary Demo 1-1 overworld course that the shared
capture route enters. The ROM change is three bytes. The engine, the sprites,
the map and the course layout stay unchanged.

## Output inventory

| Path | Content |
| --- | --- |
| `payload/` | 100 payload files, `song-XX.bin` |
| `wav/` | 100 audio files, `song-XX[-title].wav` |
| `manifest.json` | Slot, payload, audio and identity records |
| `checksums.sha256` | 200 SHA-256 lines |
| `demo-1-1.m3u` | Playlist for the WAV files |
| `music-ids.txt` | Song id list with titles |
| `music-ids.csv` | Song id list for spreadsheets |
| `index.html` | Browser player for the WAV files |
| `README.md` | Short use note for the output directory |

The WAV files are stereo, signed 16-bit PCM at 32,040 Hz. The total size is
1,199,934,440 bytes. The first audible note starts 0.6 to 3.2 seconds after
the file start.

## Results

- All 100 renders contain audio. The minimum RMS is 225 and the maximum RMS
  is 4,801.
- 51 slots have a title from `config/music-mapping.json`. 49 slots stay
  untitled and keep the slot id in the file name.
- Seven entries are short jingles. The tool trims them after the last note:
  slots `01`, `0A`, `0B`, `0C`, `13`, `14` and `15`.
- The other 93 files run for 100 seconds.
- Slot `09` has periodic long rests inside the song. The rests are part of
  the song and stay in the file.

## Song ids

The table gives every custom song id. The level data music byte is the
slot id plus one. The level loader decrements this byte before it writes
`$0DDA`. A slot without a payload is not in this table. The engine plays
built-in songs for some low ids, and those songs are not table entries.

| Slot (hex) | Decimal | Level byte (hex) | Payload bytes | Title | Origin |
| --- | --- | --- | --- | --- | --- |
| 01 | 1 | 02 | 135 | - | - |
| 07 | 7 | 08 | 933 | - | - |
| 08 | 8 | 09 | 1866 | - | - |
| 09 | 9 | 0A | 215 | - | - |
| 0A | 10 | 0B | 312 | - | - |
| 0B | 11 | 0C | 567 | - | - |
| 0C | 12 | 0D | 485 | - | - |
| 12 | 18 | 13 | 729 | - | - |
| 13 | 19 | 14 | 695 | - | - |
| 14 | 20 | 15 | 316 | - | - |
| 15 | 21 | 16 | 242 | - | - |
| 1F | 31 | 20 | 832 | - | - |
| 22 | 34 | 23 | 949 | - | - |
| 23 | 35 | 24 | 1295 | - | - |
| 24 | 36 | 25 | 635 | - | - |
| 25 | 37 | 26 | 1465 | - | - |
| 26 | 38 | 27 | 1273 | - | - |
| 27 | 39 | 28 | 580 | - | - |
| 28 | 40 | 29 | 1457 | - | - |
| 29 | 41 | 2A | 1105 | - | - |
| 2A | 42 | 2B | 755 | Prophecy | Secret of Mana |
| 2B | 43 | 2C | 918 | - | - |
| 30 | 48 | 31 | 924 | - | - |
| 31 | 49 | 32 | 1726 | - | - |
| 32 | 50 | 33 | 942 | Freiluftmusik | SaGa Frontier 2 |
| 33 | 51 | 34 | 965 | - | - |
| 34 | 52 | 35 | 1109 | - | - |
| 38 | 56 | 39 | 1237 | Town Where the West Wind Blows | Wild Arms 2 |
| 39 | 57 | 3A | 1703 | Hometown Domina | Legend of Mana |
| 40 | 64 | 41 | 1922 | - | - |
| 41 | 65 | 42 | 854 | - | - |
| 48 | 72 | 49 | 1994 | - | - |
| 49 | 73 | 4A | 609 | Podol / Boundaries | Romancing SaGa 3 |
| 4A | 74 | 4B | 1549 | - | - |
| 50 | 80 | 51 | 828 | - | - |
| 51 | 81 | 52 | 2656 | Fear Factory | Donkey Kong Country |
| 52 | 82 | 53 | 3020 | Stickerbrush Symphony | Donkey Kong Country 2 |
| 58 | 88 | 59 | 1010 | Grape Garden | Kirby's Adventure |
| 59 | 89 | 5A | 3048 | Aboard the Hilda Garde | Final Fantasy IX |
| 5A | 90 | 5B | 1274 | The Moon | DuckTales |
| 60 | 96 | 61 | 1196 | Iceberg Ocean | Kirby's Dream Course |
| 61 | 97 | 62 | 806 | Rainbow Resort | Kirby's Adventure |
| 62 | 98 | 63 | 1935 | Cold Man's Stage | Mega Man & Bass |
| 68 | 104 | 69 | 1526 | Last Dungeon | Romancing SaGa 2 |
| 69 | 105 | 6A | 1009 | Ghost House | New Super Mario Bros. |
| 6A | 106 | 6B | 4172 | Krook's March | Donkey Kong Country 2 |
| 6B | 107 | 6C | 604 | Leonid's Castle | Romancing SaGa 3 |
| 70 | 112 | 71 | 904 | - | - |
| 71 | 113 | 72 | 1328 | A Child's Fantasy Realm | Pop'n Twinbee: Rainbow Bell Adventures |
| 72 | 114 | 73 | 5999 | Taking Over the Halberd | Kirby Super Star |
| 73 | 115 | 74 | 1732 | Magic Man's Stage | Mega Man & Bass |
| 78 | 120 | 79 | 324 | - | - |
| 79 | 121 | 7A | 416 | Cap Theme | Super Mario 64 |
| 7A | 122 | 7B | 2370 | Slide | Super Mario 64 |
| 81 | 129 | 82 | 900 | - | - |
| 82 | 130 | 83 | 1300 | - | - |
| 83 | 131 | 84 | 1074 | - | - |
| 84 | 132 | 85 | 1377 | - | - |
| 85 | 133 | 86 | 2171 | - | - |
| 86 | 134 | 87 | 985 | Boss / Action Track | Custom Port |
| 88 | 136 | 89 | 641 | Save Hut | Kirby Super Star |
| 89 | 137 | 8A | 1660 | - | - |
| 8A | 138 | 8B | 2417 | - | - |
| 8B | 139 | 8C | 1127 | - | - |
| 8C | 140 | 8D | 1585 | - | - |
| 8D | 141 | 8E | 2280 | Koopa's Road | Super Mario 64 |
| 8E | 142 | 8F | 766 | Castle Pandemonium | Final Fantasy II |
| 8F | 143 | 90 | 1001 | Thema | SaGa Frontier 2 |
| 90 | 144 | 91 | 1941 | Sad Freedom | Treasure Hunter G |
| 91 | 145 | 92 | 1531 | The Galaxy Reactor | Super Mario Galaxy |
| 92 | 146 | 93 | 1561 | Undersea Palace | Chrono Trigger |
| 93 | 147 | 94 | 782 | One of Them Is Hope | Secret of Mana |
| 94 | 148 | 95 | 1232 | The Savior of Those on Earth | Lufia II |
| 98 | 152 | 99 | 2057 | Go! Go! Kids! | Treasure Hunter G |
| 99 | 153 | 9A | 1444 | Final Fight | SNK vs. Capcom: Chaos |
| 9A | 154 | 9B | 3401 | Gangplank Galleon | Donkey Kong Country |
| 9B | 155 | 9C | 1884 | - | - |
| 9C | 156 | 9D | 1801 | Irwin on Reflection | Legend of Mana |
| 9D | 157 | 9E | 1284 | Masked Dedede's Theme | Kirby Super Star Ultra |
| 9E | 158 | 9F | 2351 | - | - |
| 9F | 159 | A0 | 1525 | - | - |
| A0 | 160 | A1 | 2668 | Boss Theme | Super Nazo Puyo: Rulue's Roux |
| A1 | 161 | A2 | 2478 | - | - |
| A2 | 162 | A3 | 2000 | The Flame and the Arrow | Treasure of the Rudras |
| A3 | 163 | A4 | 520 | - | - |
| A4 | 164 | A5 | 1645 | The Decisive Battle | Final Fantasy VI |
| A5 | 165 | A6 | 2881 | The Fierce Battle | Final Fantasy VI |
| A6 | 166 | A7 | 3210 | Maybe I'm a Lion | Final Fantasy VIII |
| A7 | 167 | A8 | 1852 | High Tension Wire | Trials of Mana (Seiken Densetsu 3) |
| A8 | 168 | A9 | 2247 | Nuclear Fusion | Trials of Mana (Seiken Densetsu 3) |
| A9 | 169 | AA | 5915 | - | - |
| AA | 170 | AB | 2427 | - | - |
| AB | 171 | AC | 975 | Bowser Battle | Super Mario RPG |
| AC | 172 | AD | 2318 | Last Battle | Romancing SaGa 2 |
| AD | 173 | AE | 2152 | - | - |
| AE | 174 | AF | 2181 | Battle With Magus | Chrono Trigger |
| AF | 175 | B0 | 1715 | The Sun Rises | Okami |
| B0 | 176 | B1 | 2067 | Megalomania | Live A Live |
| B8 | 184 | B9 | 1146 | The Credits Concerto | Donkey Kong Country |
| B9 | 185 | BA | 2090 | To Far Away Times | Chrono Trigger |

## Checks

- A repeat render of slot `30` and slot `69` gives the same payload SHA-256
  and the same WAV SHA-256. The render is deterministic.
- Every capture requested the carrier song at frame 2,196. The cut frame is
  2,161 for every capture. The cut is inside the level-load gap.
- No render is silent. The peak range is 10,327 to 26,321.
- `tests/test_extract_demo11_music.py` passes 10 checks. The checks cover the
  table reader, the naming, the cut selection and the level statistics.
- The earlier room 106 audition render of slot `33` matches the new render.
  The 0.1-second RMS envelope correlation is 0.511 at a 40.3-second lag. The
  same measure between slot `33` and slot `38` is 0.171. This bounds the
  identity check to level and section similarity. It is not a waveform
  comparison.

## Limits

- Each file is a fixed excerpt. The tool does not find the song loop point.
  A song that loops after more than 100 seconds has a cut loop in the file.
- The render uses one carrier course. A song that changes with the course
  context needs a separate render.
- The output is not sample-identical to ZSNES 1.51. The echo compatibility
  option keeps the legacy driver alive. Without it, the driver stops after
  about three seconds for some payloads.
- The extraction covers the 100 table entries. It does not cover the
  built-in engine songs for low ids. It does not cover sound effects.
- No user listening check exists. A WAV render is not proof of an intended
  audible match.

## Reproduce

Run these commands from the repository root:

    python3 tools/extract_demo11_music.py --force --jobs 8 --seconds 100
    python3 -m unittest tests.test_extract_demo11_music -v

The tool refuses an existing output tree without `--force`. A bounded test
run uses `--slots 30,69 --out tmp/music-test`.

## Next steps

1. Find the song loop points and write loop-trimmed files.
2. Survey the requested song id for every course. Use the result to name the
   49 untitled slots.
3. Extract the built-in low-id songs from the SPC program image.
