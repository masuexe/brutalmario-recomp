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

## Checks

- A repeat render of slot `30` and slot `69` gives the same payload SHA-256
  and the same WAV SHA-256. The render is deterministic.
- Every capture requested the carrier song at frame 2,196. The cut frame is
  2,161 for every capture. The cut is inside the level-load gap.
- No render is silent. The peak range is 10,327 to 26,321.
- `tests/test_extract_demo11_music.py` passes 9 checks. The checks cover the
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
