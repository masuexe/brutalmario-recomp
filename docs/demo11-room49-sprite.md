# Room 049 custom sprite

Date: 2026-10-26. The user reports that the big door of level `0x109` leads to
room `0x49`, and that room's custom sprite probably has no code.

## Evidence

- Room `0x049` has a valid level header and its own level data.
- Its sprite list places custom sprite `0x48` (bit 3 set in the record).
- The target record for `0x48` is the default record.
- cheap-demo defines `0x48`: record `01360000fda3394557b61c62b61c0000`,
  a 593-byte code block at donor offset `0x1cb648`.

## Port

The target `demo11-sprite-room49` descends from
`demo11-boss-music-retarget` and installs the record and the code block
at bank `0x2F` offset `0x3648`. The shared dependencies and the
versioned dependency are verified. The record slot changes from the default
record to the donor record.

- ROM: `ce129957bde37fd0d4d0044a67fca2565013bb04f32151f0866a44d9bb9c96a2`
- Native binary: `2e357a9682dc0a926fcbf6facd93f20148ecc75907f6570712236c8d4bc83b07`
- Suite **57/57**; whole-line audit: 590,070 changed bytes, zero unexpected.

## Limits

- The port is verified statically (record, block, dependencies, placement).
- A scripted walk of level `0x109` does not reach the big door: the corridor
  wall stops the route. The runtime effect needs the user playtest through the
  door.
