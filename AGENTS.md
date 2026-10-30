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
- The delivery target is the native PC game. A single SFC image, emulator
  compatibility and cartridge capacity are not product requirements. Prefer
  native content packs and explicit runtime adaptations when ROM limits block
  restoration; see `docs/native-content-expansion.md`.
- SFC hardware limits are not product constraints. When the existing
  architecture obstructs restoration, compatibility or performance, the user
  authorizes changes to runtime code, resource loading and game code to use
  PC capabilities, including external resources and native implementations.
  Necessary adaptations within this scope do not require renewed permission.
- Preserve the intended gameplay, level mechanics, physics, combat timing and
  save semantics by default. Explain and verify any necessary behavior changes;
  permission to exceed hardware limits does not authorize arbitrary gameplay
  changes. Record the rationale, validation results and known limitations.
- Prioritize content restoration and introduce native adaptations as actual
  needs arise. Do not take detours solely to retain SFC or emulator compatibility,
  or perform unrelated large rewrites solely to increase PC hardware usage.

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
- Official demo chronology (from oldest to newest):
  `demo6 -> demo6.5 -> demo7 -> cheap_demo -> ow -> mazo -> 7hero -> boss -> demoonly1 -> 1-1`.
  When code or data is missing, prioritize the newest available code, and ONLY
  reference code from the official demos in this list (do not reference unofficial
  hacks or unverified edits). Note that `cheap_demo` is the last version that contains
  all custom sprite code; for missing custom sprites not present in newer versions,
  consult `cheap_demo` first.
- Numeric music, graphics, sprite, and room IDs are version-local. Matching an
  ID alone does not establish that the underlying content matches. For custom
  music mapping between the legacy donor family (cheap_demo, 7hero, etc.) and
  the recipient baseline (demo 1-1 / demoOnly1), consult `docs/music-mapping.md`.
- When investigating course layouts, clearing routes, secret exits, boss mechanics,
  and intended game gimmicks for testing scripts, consult `docs/walkthrough-reference.md`
  and the community walkthroughs (https://brutalmario.fandom.com/ and
  https://wikiwiki.jp/kitikumario/).
- Collectibles terminology: Super Mario World courses contain **5 Dragon Coins**
  (ドラゴンコイン / Yoshi Coins) that grant a life and set the saved flag at `$1F2F`,
  whereas **DK Coins** (from Donkey Kong Country) appear at most once per course.
  Do not refer to the 5 Dragon Coins as "DK coins".

## Verification and acceptance

- Run checks appropriate to the change. Compare source and recipient behavior
  where needed. Use the reference host where it can exercise the same content;
  native-only content does not need an emulator-compatible build. Retain donor
  behavior references and qualify native integration with explicit assertions
  and regressions; do not claim same-image parity when the images differ.
- Check completion logs, assertions, dump sizes, and receipts. A process exit
  code alone does not prove that the route reached its intended state.
- Match native executable mappings or adapters to the source program's
  data-bank semantics, including low WRAM and I/O accesses after `PHK/PLB`.
  Qualify motion, state changes or child generation where the program has them;
  initial actor appearance alone can hide a program that skips its main logic.
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
