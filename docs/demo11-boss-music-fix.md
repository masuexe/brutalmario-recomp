# Boss room music retarget: the middle boss door black screen

Date: 2026-10-26. The user reported that level `0x15F` (translevel `083`) is
correct, but walking right into the middle boss room after the switch gives a
black screen. The user also said the course music is already wrong and asked
to defer music quality work.

## Root cause

The middle door leads to room `0BC`. That room level data holds a music
object `40 60 2E` at file offset `0x289369`. The loader decrements the
parameter, so the room requests music slot `0x2D`. Slot `0x2D` is null on this
line. The music upload then waits for the SPC acknowledgement, the game stays
in Mario Start mode `0x12`, and the screen stays black.

This is the same stall class as the earlier course music retargets. It is not a
terrain, sprite or graphics defect.

## Fix

The recipe `demo11-boss-music-retarget` changes one byte: the music
parameter `2E` becomes `1F`, so the room requests the working slot
`0x1E` (the parent level song). No song data is installed. The music stays a
placeholder, which matches the user decision to defer music quality.

- Base: `demo11-sprites-level1`
- ROM: `69ea041faa64f83407865b885331fa5704c882530883e1d8b7a1bfa5b2949b0f`
- Native binary: `a2d42dafea5365f5765793d31e20e5d1d52b0fc992de71053994189f26a1df65`

## Evidence

A scripted sweep of the level `083` corridor presses Up in front of each arch:

| Capture | Step 33 | Step 42 |
| --- | --- | --- |
| Before (`sweepold-083`) | mode `0x12`, room `0BC`, music `0x2D` | still mode `0x12`, black |
| After (`sweepfinal-083`) | mode `0x12`, room `0BC`, music `0x1E` | mode `0x14`, music `0x1E`, visible room |

The whole-line audit on the chain end reports 589,496 changed bytes and zero
unexpected bytes. The suite reports **56/56**; the space budget passes.

## Scope and limits

- The middle boss room now loads. The other two doors of the corridor are not
  tested.
- The music itself is still wrong and is deferred by the user.
- The switch music event is deferred with the music work.
