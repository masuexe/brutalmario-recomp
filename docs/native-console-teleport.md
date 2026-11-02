# Console room transfer table correction

## Defect and repair (2026-11-02)

The user reported `teleport 0x00f` entering room 10F on Windows. The built-in
console wrote a two-byte room buffer to $19B8/$19B9. The two bytes actually belong
to separate tables: $19B8 holds the room low byte and $19D8 holds 4 plus its high
bit. Consequently the prior high bit could survive and the next screen's
low-byte exit record was overwritten. The Python practice launcher already
used the correct separate tables. This defect affects both native platforms.

Runtime patch 0011 now queues two one-byte writes, preserving the transfer ordering and existing wait constants. The extra
queued write adds two host script frames before the pipe action under the
current scheduler; it does not change normal movement physics or combat timing. Command syntax and numeric parsing are
unchanged. A separate patch extends the pinned console chain, preserving its
prior identities. Runtime materialization now recognizes verified intermediate
chain results, so adding this patch to an existing checkout can resume safely;
unknown override bytes still fail. A test checks the upgrade and repeat path.

## Evidence

`tests/test_console_teleport.py` applies the pinned runtime patches in a fresh
directory, compiles the actual `CheatQueueRoom` function, and checks transfers
00F, 10F, 000, 100, 1FF, 00F in succession. Both high-bit values are checked, and all
neighboring table records retain sentinel bytes. The compiled queue also emits
script sequences, checked against the tracked fixtures:

- `recomp/inputs/console-teleport-00f.script`
- `recomp/inputs/console-teleport-10f.script`

Fresh Linux and Windows runs execute these queue-emitted map/pipe-action
sequences. Room 00F is in Mario Start mode 13 at the first sample and gameplay
mode 14 thirty frames later. Room 10F is in mode 14 at both samples. Each host
completes both scripts with the requested room ID and full 128 KiB WRAM dumps.
This qualifies the command's queue encoding and actual transfer boundary;
it is not a keyboard-input automation or an ordinary course traversal/clear.
The first exploratory assertion incorrectly required mode 14 at the earlier
sample. Those captures remain separate; the final r2 runs check both samples.

`local/diagnostics/teleport-fix-v1/` holds source materialization, compile/link
commands, original/repaired host inputs, queue fixtures, logs, binary/ROM/script
receipts and product verification. Existing build objects and the previously
qualified cached-setting resolver object are retained; only the host object is
replaced. The unchanged r14 ROM is
`393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b`.

| Platform | Candidate SHA-256 | Startup guest mean |
| --- | --- | ---: |
| Linux | `bf7daa0ccfa269d66a0e2c2890f64f6a7c1ebfcb8423f8da00514d30f662ba3a` | 3.085 ms |
| Windows | `b4411bce166958cac01934684ee67c8f892f7814eed6c62543aeff269d8fb0e0` | 3.488 ms |

Both candidates pass the shared product verifier, including console lifecycle,
state/dump sizes and performance. Bundles are produced by `tools/product.py`:

- `local/release/product-r14-teleport-fix-linux-v1.zip`, SHA-256
  `d6c6321834ffcb5d0e487582ec731e1a121f5e42d3e3b5c5840f89fa8b8e3c03`.
- `local/release/product-r14-teleport-fix-windows-v1.zip`, SHA-256
  `7f40f0c07db0364e0ca7c07d367f6b87f44a9c3485b1bb02c60aada8ce123775`.

Earlier packages and user saves remain intact. These are still r14 bundles
without the separate map-music repair. Prior user acceptance of the earlier
console does not qualify its incorrect transfer behavior; the corrected
boundary is automatically qualified here. Whole-game restoration remains open.

The full suite ran 446 tests: 438 passed and eight rejected stale demoOnly1
host inputs before execution. The six audio-startup tests, device-stall test
and Windows-audio test require an exact current runtime-patch receipt; their
preserved local binary still records the preceding chain. This is not a passing
full-suite result. No receipt was rewritten and that older binary was not
replaced. The two new queue/materialization tests, direct room captures and
both current product verifications pass independently. Rerunning those eight
checks requires an isolated rebuilt demoOnly1 test host.
