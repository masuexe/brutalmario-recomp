# Rollback: reverting a content migration

Date 2026-10-23. Written before replacing World 1-1's layout with Demo 1-1's newer
version, so the current state can be recovered two independent ways.

## Two independent rollback routes

1. **Rebuild from pinned inputs.** Every restoration is a reviewed recipe whose base,
   donor and output are hash-pinned. Re-running the chain reproduces the exact bytes
   without any backup:

       python3 -c "import sys; sys.path.insert(0,'tools'); import restore_star_world_1 as R; R.prepare('<target>')"

   Targets form a chain via `base_restoration`, so rebuilding the head rebuilds each
   ancestor it depends on.
2. **Restore the file snapshot.** `tools/backup_state.py --label <name>` copies every
   recipe-backed ROM, the native build receipts and binaries, and the practice-save
   tree into `local/backups/<label>-<timestamp>/`, with a `manifest.json` of SHA-256
   identities and the git HEAD at snapshot time.

## Snapshot taken before the 1-1 migration

| Item | Value |
| --- | --- |
| Backup | `local/backups/pre-room105-migration-20261023-051544/` |
| Manifest SHA-256 | `1ce4f05fd66c19c35ae2f34cc40935c8ff538f0d02fc09624c64c3dd5bfe186d` |
| ROMs / binaries / save files | 17 / 17 / 860 |
| Git HEAD | `b08067bfd37ac2176d95be041ca10c1f5a0dd182` |
| Head target | `demo11-extra-graphics` |
| Head binary SHA-256 (prefix) | `3520b3a1622fbcc2` |

Backups live under gitignored `local/`, so they are machine-local: the durable
guarantee is route 1, and the snapshot is the convenient one.

## To revert after a migration

1. Identify the pre-migration head target from this table.
2. Either rebuild it (route 1) or copy its `roms/<target>.sfc` back to
   `local/restoration/<target>/rom.sfc` and its binary back to
   `local/build/<target>/` (route 2).
3. Verify the restored ROM against the manifest entry.
4. Re-run the target's qualifier (`tools/qualify_*.py`) and the unit suite.
5. Play the restored build: `python3 tools/play_demo_only1.py --restoration <target> --show-location`.

A migration is only ever appended as a **descendant** target, so reverting is
choosing the ancestor; no committed recipe or pinned input is destroyed by it.
