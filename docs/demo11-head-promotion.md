# Head promotion plan: demo11-fix-batch-o2

Date: 2026-10-26. This plan promotes the candidate chain end to the line head
after the user playtest.

## Evidence

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-o2` |
| ROM SHA-256 | `8bd3a8d440ea0cffff17003e85f2657af6788a1d7169cdbd8e4b0277957fc0cc` |
| Native binary SHA-256 | `63676019696575cf29144298f183d2ab43ce09e581892c877d22d4dca0d1f391` |
| Chain recipes | 39, all reproducible |
| Chain byte audit | `--head demo11-fix-batch-o2` passes: 382,653 changed bytes, 494,184 reviewed bytes, zero unexpected |
| Suite | 42/42 |
| Survey range 001-0C0 | 147 playable, zero stalls; the other 45 entries are 43 no-input deaths and 2 Yoshi's House returns |

## Steps

1. Read this plan and confirm the user playtest result.
2. In `tools/audit_demo11_line.py`, set `HEAD = 'demo11-fix-batch-o2'`.
3. In `tools/survey_demo11_courses.py`, set the default `TARGET` to
   `demo11-fix-batch-o2`.
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
