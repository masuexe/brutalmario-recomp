# Head promotion: demo11-fix-batch-p

Date: 2026-10-26. The candidate chain end is now the line head.

## Promoted target

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-p` |
| ROM SHA-256 | `48891cf75b570e4118f8646f7f216d50505d047edc40341b3d0dccdc8cc3022c` |
| Native binary SHA-256 | `a00a993d366b0cf5ba5cc7498e9df0c5d639d1bb13015825b56ac420e47f1875` |
| Previous head | `demo11-star-bgm` (kept as an intact target) |
| Chain recipes | 41, all reproduced by the audit |

## Changes in this promotion

- `tools/audit_demo11_line.py`: `HEAD` is now `demo11-fix-batch-p`.
- `tools/survey_demo11_courses.py`: the default `TARGET` is now
  `demo11-fix-batch-p`.

The per-checkpoint qualifiers keep their own `HEAD` pins. They validate their
own targets and captures, so no capture is re-recorded.

## Verification after promotion

| Check | Result |
| --- | --- |
| Head audit | chain ends at `demo11-fix-batch-p`; 386,151 changed bytes inside 495,263 reviewed bytes; zero unexpected bytes |
| Suite | **45/45** |
| Full-range course survey | 255 translevels load; 207 playable; zero stalls; 46 no-input deaths; 2 Yoshi's House returns |
| Dragon Coin column fix | Five assisted pickups, extra life, tilemap parity with Snes9x in both renderers and interpreter mode |
| Storm mosaic | Closed by the user: it matches original Demo 1-1 |

## Rollback

The previous head is an intact target (`demo11-star-bgm`). Revert the promotion
commit to return to it. No ROM or capture is discarded.

## Limits

- The head claim is bounded: course loading, the reviewed game flows and the
  Dragon Coin runtime fix. Full manual course clears and audible checks remain
  separate claims.
- Other historical builds need a rebuild before use with the updated runtime
  patch manifest.
