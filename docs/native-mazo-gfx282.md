# Room 151 boss extended graphics 0x282

Date: 2026-10-30. Candidate: `demo11-native-mazo-gfx282-v1`. Parent:
`demo11-native-product-r14`. The accepted product stays r14.

## Finding

The room 151 boss sprite 9C code holds this sequence at pack offset `E0A`:

```
C2 30        REP #$30
A9 82 02     LDA #$0282
8F 90 FF 7F  STA $7FFF90
E2 30        SEP #$30
DA           PHX
22 80 F7 0D  JSL $0DF780
```

This is an explicit extended graphics request for id `0282`. The product
pointer at file offset `0A048E` is `FFFFFF`. The mazo pointer is `3F:B5C8`,
and its stream decodes to 4096 bytes.

Id `027E` is also empty. The mazo pointer is `3F:80D5` and decodes to 4096
bytes. No code request for `027E` appears in the supplied packs.

Capture `mazo-9c-gfx282-window-v2` shows the sibling sets in VRAM on every
sampled fight frame: `027F` at `E000`, `0280` at `F000` and `0281` at `D000`.
Id `0282` does not appear. The product already holds `027F` to `0281` byte equal
to mazo, so `0282` is the only empty member of the family. The missing set likely
fills VRAM `C000`.

## Change

The candidate adds one data-only pack and one pointer patch.

| Item | Value |
| --- | --- |
| ROM | `626a5c5c3fee9ae54962c448e04dcb24b4b962ee87d9edfeb2279ef4a324c186` |
| Binary | `0ee9b3ff9458b9da6e610b5ee08b0a00b6c3ee5c505f0831a650fd0e70b34dd2` |
| Pack | `local/native-modules/mazo-gfx282-v1/gfx282.bin`, 3344 bytes |
| Pack address | `D2:8000` |
| Pointer | offset `0A048E`, `FFFFFF` to `0080D2` |

The first candidate used `D1:9000`. The native host rejects two packs in one bank,
so the pack moved to `D2:8000`.

`tools/prepare_mazo_gfx282.py` builds the candidate from the r14 config. It
verifies the parent ROM and the mazo stream before it writes the config.

## Verification

- The ROM delta from r14 is exactly the three pointer bytes.
- The pack equals the mazo compressed stream and decodes to 4096 bytes.
- `tests/test_mazo_gfx282.py` pins both facts.
- No sampled room 151 frame executes the request. The request likely belongs to
  a 9C phase that needs boss damage. Automation cannot damage 9C, so the runtime
  frame stays open. This is the same blocker as the phase music.

## Next work

Reach the 9C attack phase with a manual sample or a damage route. Then check VRAM
for the decoded `0282` data. Decide on `027E` only after a requester appears.
Do not promote this candidate.
