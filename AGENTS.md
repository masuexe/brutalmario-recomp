# Repository working agreement

## Resume and scope

- Read the latest user instructions, `docs/content-restoration.md`, and the
  relevant restoration documents before continuing. Inspect `git status` and
  recent commits; session summaries can lag behind the worktree.
- If present, read `.agents/current-star-world-handoff.md` for local evidence
  locations and unfinished work. Resolve conflicting historical notes using
  the latest user decisions and verified capture identities.
- Markdown documents use English. User-facing conversation may use Chinese.
- Continue the authorized restoration work autonomously. Do not spawn
  subagents unless the user or applicable instructions explicitly request it.

## Preserve reproducibility

- Keep input ROMs, accepted baselines, user saves, and existing captures intact.
  Use isolated descendant targets and fresh capture directories for changes.
  Do not terminate user game processes to run checks.
- Record the exact ROM, build, input-script, and reference identities behind
  each result. Reuse historical evidence only when its identities match the
  claim; never overwrite a receipt to make an old capture appear current.
- Express content recovery in reviewed recipes with pinned source assets,
  bounded allocations, and explicit patches. Do not silently replace recipient
  layouts, map events, or engine behavior with donor behavior.
- Numeric music, graphics, sprite, and room IDs are version-local. Matching an
  ID alone does not establish that the underlying content matches.

## Verification and acceptance

- Run checks appropriate to the change. Compare source and recipient behavior
  where needed, then compare the native build with the reference host.
- Check completion logs, assertions, dump sizes, and receipts. A process exit
  code alone does not prove that the route reached its intended state.
- Label teleportation, invulnerability, forced movement, and pipe-action
  fixtures explicitly. They qualify the exercised boundary, not ordinary
  unassisted traversal. Never write completion flags to prove a real exit.
- Keep claims bounded: entry is not a complete course pass; a music-selection
  byte is not an audible match. Record deferred issues and user acceptance
  separately from automated results.
- The user authorizes reduced manual checkpoints. Ask for playtesting only
  when an essential unresolved question cannot reasonably be answered by
  automation or existing evidence. Do not ask again about accepted behavior.

## Checkpoints and handoff

- The user authorizes automatic commit and push of successful, appropriately
  verified checkpoints. Review the diff, include only relevant changes, and
  push normally; do not force-push or discard unrelated work.
- Track durable findings, recipes, tools, and reusable regression inputs.
  Keep ROMs, generated builds, captures, private session exports, and temporary
  probe scripts under ignored local storage.
- Update the relevant tracked documents when behavior or acceptance changes.
  Refresh the ignored local handoff at meaningful checkpoints and before
  handing work to another agent; supersede stale instructions clearly.
- A handoff should state the current target and identities, accepted scope,
  deferred issues, commands and evidence paths, and the next concrete action.
  Put stable workflow rules here rather than copying session transcripts.
- Report what changed, what was verified, remaining limitations, and the
  commit/push result. Keep the broader restoration goal open while work remains.
