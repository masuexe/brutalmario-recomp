# Demo 1-1 extra graphics import

Date 2026-10-23. First executable step of the selective Demo 1-1 migration. The
[inventory](demo11-additions-inventory.md) showed that Demo 1-1's versions of
World 1-1 (`105`) and the castle (`10E`) select extended graphics that demoOnly1
does not have at all.

## What was missing

| Graphics id | Demo 1-1 pointer | Compressed / decoded | demoOnly1 |
| --- | --- | --- | --- |
| `29E` | `239B8D` | 1,597 / 4,096 | absent |
| `29F` | `23A1D2` | 2,757 / 4,096 | absent |
| `2A0` | `23AC9F` | 2,639 / 4,096 | absent |
| `2A2` | `23BD6E` | 2,924 / 4,096 | absent |

## Change

New descendant target `demo11-extra-graphics` on `world1-room0cb-gfx`:

- donor is `demo-1-1` for this target (the recipient stays `demo-only-1`);
- the four donor streams are relocated into the free region at file `0x18D000`
  (bank `$31`) as protected RATS blocks, 9,949 bytes total;
- only the four pointer slots are written, and each slot was `FFFFFF` before, so
  no selector is patched.

8,400 bytes differ from the base, all inside the allocation or the four pointer
slots.

## Identity

- Recipe `config/restorations/demo11-extra-graphics.json`.
- Base `world1-room0cb-gfx` `e66b05983af43412b87eb248b675645cf3baeb42e12875255d5ac1353dc0bb84`.
- Candidate `b8da320e34e8f1614dd7b3a69716f04ee693ad757e14f7bdb7ea97bd94d28e39`.
- Binary `local/build/demo11-extra-graphics/BrutalMarioDemo11ExtraGraphicsSNESRecomp`.

## Verification

`python3 tools/qualify_demo11_graphics.py` passes. Report
`local/reports/demo11-extra-graphics-qualification.json`. It checks that every
recipient slot was empty, that **no recipient room selects the imported ids**, the
donor pointers and stream pins, that each relocated stream decompresses to the
donor image, the protected payloads, and that every changed byte lies in the
allocation or a pointer slot.

## Why this is safe, and what it does not do

Because no recipient room references the new ids, this target **cannot change
gameplay**; it only makes the resources available. It does not import any Demo 1-1
level layout, sprite list, music or header data.

Consuming them is the next step and is a genuine content replacement: Demo 1-1's
World 1-1 layer1 stream differs from the beginning (first byte `D7` vs `D3`, i.e.
24 vs 20 screens), so it is not an append. That change must be its own isolated
target with a full dependency closure and re-qualification of the existing 1-1
goal/save evidence.
