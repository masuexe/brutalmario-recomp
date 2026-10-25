# Head promotion plan: demo11-fix-batch-o2

Date: 2026-10-26. This plan promotes the candidate chain end to the line head
after the user playtest.

## Evidence

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-p` |
| ROM SHA-256 | `48891cf75b570e4118f8646f7f216d50505d047edc40341b3d0dccdc8cc3022c` |
| Native binary SHA-256 | `d8879d7e5d41692d40f1a08b501fad7156469916142d78a62a8817924113a6cb` |
| Chain recipes | 40, all reproducible |
| Chain byte audit | `--head demo11-fix-batch-o2` passes: 386,151 changed bytes, 495,263 reviewed bytes, zero unexpected |
| Suite | 44/44 |
| Survey range 001-0C0 | 207 playable and zero stalls across all 255 translevels |

## Steps

1. Read this plan and confirm the user playtest result.
2. In `tools/audit_demo11_line.py`, set `HEAD = 'demo11-fix-batch-p'`.
3. In `tools/survey_demo11_courses.py`, set the default `TARGET` to
   `demo11-fix-batch-p`.
4. Run the head audit and the suite:
   `python3 tools/audit_demo11_line.py` and
   `python3 tools/check_demo11_line.py`.
5. Update the cumulative checkpoint text in `docs/content-restoration.md` and
   add a promotion section with the evidence above.
6. Refresh `.agents/current-star-world-handoff.md`.
7. Commit and push.

The per-checkpoint qualifiers keep their own `HEAD` pins. They validate their
own targets and captures, so they stay unchanged.

## Rollback

The previous head remains an intact target (`demo11-star-bgm`). Revert the
promotion commit to return to it. No ROM or capture is discarded.

## Post-promotion checks

- `python3 tools/audit_demo11_line.py` reports the new head and zero
  unexpected bytes.
- `python3 tools/check_demo11_line.py` stays at 42/42.
- The launcher still starts every named target.