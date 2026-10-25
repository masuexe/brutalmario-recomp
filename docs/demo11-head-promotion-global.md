# Head promotion plan: global graphics chain

Date: 2026-10-26. This is a plan. The chain is not promoted yet.

## Candidate

- Target: `demo11-gfx-global13`
- ROM: `86d3a5cd5e2feebbd189e98b84deb3300f670128c3062901b64d1a7d106d691f`
- Base: `demo11-fix-batch-p`
- Suite: **54/54**; whole-line audit: 581,481 changed bytes, zero
  unexpected; space budget passes.

## Evidence

- Full-range survey: 255 loads, zero stalls, 233 playable translevels.
- User playtests: room `0x11D` is fine and room `0x116`
  completes normally on `demo11-sprite-final`. The global chain contains
  that chain plus the global graphics batches.
- The user accepted `0x023` on the global chain (correct image, the third
  question block gives a bomb). The user must still accept `0x083`, 
  `0x02D` and `0x069`.

## Promotion steps

1. Change the head constants: `tools/audit_demo11_line.py` HEAD,
   `tools/survey_demo11_courses.py` TARGET,
   `tools/world_parity.py` and `tools/frame_phase.py` defaults.
2. Re-run the whole suite and the whole-line audit for the new head.
3. Update `docs/content-restoration.md` and the head promotion record.
4. Keep `demo11-fix-batch-p` and its captures intact for rollback.

## Rollback

The head change is one commit. Revert it and the previous head keeps its
captures and recipes.
