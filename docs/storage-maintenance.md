# Local storage maintenance, 2026-10-30

The user requested removal of obsolete project files. Initial allocated usage
was approximately 137 GiB, including 130 GiB of captures and 1.1 GiB of builds.
Captures contain qualification evidence and were preserved.

## Completed cleanup

| Operation | Result | Allocated bytes reclaimed |
| --- | --- | ---: |
| Remove old compiler intermediates | 3,332 `.o` / `.o.d` files under `local/build`, older than seven days | 104,333,312 |
| Make zero blocks sparse in WRAM/VRAM/SRAM snapshots | 127,578 files | 2,127,048,704 |
| Make zero blocks sparse in framebuffer/audio files | 32,495 files | 19,265,478,656 |
| Total | 20.0205 GiB / 21.4969 GB | 21,496,860,672 |

The compiler cleanup retained binaries, source files, ROMs, configurations and
receipts. Deleted intermediates can be rebuilt. No user game process was stopped.

Sparse conversion removes physical allocation for aligned 4096-byte all-zero
blocks. Reads still return exactly the original bytes. It retained all capture
paths, lengths and contents; each changed file passed a full SHA256 comparison
before and after conversion. Original access/modification timestamps were
restored. Files newer than one hour, symlinks and current native highhop v3/v4
captures were excluded as applicable. Source ROMs, accepted baselines and user
save files outside captures were untouched. Existing capture receipts were
not rewritten.

The conversion scanned 276,855 memory snapshots and 130,672 media files.
The resulting manifests reconcile exactly with the reclaimed-byte totals and
changed-file counts. A temporary-copy test first verified filesystem support
and byte identity. The subsequent Mazo second-boss checker passed against the
preserved controls and source capture after conversion.

## Local evidence and repeat policy

Reports and per-file compressed manifests remain ignored:

- `local/reports/storage-old-object-plan-v1.json`
- `local/reports/storage-old-object-result-v1.json`
- `local/reports/storage-compact-plan-v1.json`
- `local/reports/storage-compact-result-v1.json` and `.files.jsonl.gz`
- `local/reports/storage-media-compact-result-v1.json` and `.files.jsonl.gz`

The exact maintenance scripts remain under
`local/probes/storage-maintenance/compact.py` and `compact-media.py`.
Their apply reports use actual before/after allocated block counts, not the
dry-run upper bound. Total directory usage can grow concurrently as fresh
qualification captures are generated.

For future cleanup, inventory allocated size first. Delete only identified
rebuildable intermediates after checking current references and file identity.
Preserve capture contents and receipts, including failed runs that explain an
investigation. Sparse conversion is a storage optimization, not permission to
delete evidence. Ordinary copies or archive extraction may allocate the zero
blocks again; use tools that retain sparse files when moving this directory.
