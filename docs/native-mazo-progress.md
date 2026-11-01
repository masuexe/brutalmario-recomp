# Playable Mazo progress milestone

Target `demo11-native-mazo-progress-v1` descends from the qualified
`demo11-native-mazo-primary-entry-v3`. It keeps the actual Mazo node30 and
prevents its ending actor from clearing the recipient's unrelated course00D.
The accepted r14 release package remains separate.

## Play

From the repository root, start the native game with its own save directory:

```sh
python3 tools/play_native_target.py --target demo11-native-mazo-progress-v1
```

This opens a normal game window with all 61 content packs. Its default session
directory is `local/play/demo11-native-mazo-progress-v1`. The actual launcher
has passed its ROM, executable and pack checks using `--print-env`; the native
runner also boots and plays the qualification routes below.

For an isolated position-assisted shortcut to the actual Mazo map node:

```sh
python3 tools/play_native_cheats.py --target demo11-native-mazo-progress-v1 --map 0 --x 0x100 --y 0xF0 --play-dir local/play/mazo-progress-entry
```

Press A at that node to enter room190. The shortcut changes map position and
uses a separate profile. It does not mark courses complete. Ordinary traversal
through190 remains open; the automated fight route explicitly skips it.

## Why the progress marker changes

The official Mazo course00D has a 21-byte bounded foreground allocation and
two B0 actors. That
corridor was moved to native room183 to preserve the recipient's different
412-byte course00D. The retained recipient course has its own normal actors
and map node. Their full bounded layout and sprite fingerprints are pinned
in `config/native-content/mazo-progress-v1.json`.

In room192, the copied B0 program still executed `STA $1EAF`, setting the
course00D completion bit. The parent actually saves this unearned bit at both
SRAM offsets000D/01BA after a real Mazo goal. Mazo's own completion belongs to
course30 (`1ED2`, SRAM0030/01DD). Its existing completion records the retained
Mazo goal; recipient00D needs to retain its independent progress.

The candidate keeps the same 419-byte immutable B0 program at `A1:8989` and
changes only three bytes at `A1:89AE`: `STA $1EAF` becomes `BIT #$FF; NOP`.
The preceding `ORA #$80` guarantees nonzero 8-bit A, so this replacement
preserves A and P. The next message request, actor counter and removal retain
their exact original addresses. The interpreted CPU-cycle count is also equal;
bus-master-cycle identity is not claimed. No room, sprite record, event table,
save layout or other program changes.

The real-interpreter unit harness exercises the complete native actor across
24,576 initial flag, pause, counter and CPU-status cases. All registers, flags,
stack bytes, messages and actor removal match the original, and only the
foreign flag write disappears. It covers already-cleared course00D states as
well. Existing saved bits remain intact.

## Verified boundaries

`mazo-progress-boundary-v1` follows actual node30 into190, uses a declared pipe
fixture to192, closes the message, touches the ordinary sphere and reloads
File A. Course30 and its two save copies become80. Course00D and both of its
copies remain0F. A further map-coordinate fixture selects its existing D72D
node; ordinary Y enters retained room00D in live mode14 through 120 more frames.
The Mazo flag remains saved.

`mazo-progress-integrated-ending-v2` exercises the longer chain:

- Actual node30 to190, then a declared pipe fixture into191.
- A contact-position fixture bypasses two entry obstacles. The guest requests
  message2 and makes its own191-to151 transition.
- Three contact-placement cycles produce the first boss's normal reflected-hit
  and scripted-marker progression through F400 values 0 to 6. Placements stop
  during its death dialogue. F400 is not treated as a simple health field.
- Normal B input dodges the second boss's ground check, followed by 160 normal
  ground-triggered jumps. No boss health, phase or completion fields are written.
- The game reaches F413=3 and its actual cutscene. Observations span 88 distinct
  timer values, real room192/message1, ordinary B dismissal and sphere contact.
- Actual goal/map return and console-reset File A reload preserve course30 at80
  and recipient00D at0F. Damage immunity and the position/pipe fixtures remain
  explicit assistance; this is not an unassisted or earned-fight acceptance.

Both current191/192 message tilemaps and text pixels match the pinned official
Mazo captures. Japanese font loading and English restoration pass. The complete
4096-byte GFX0282 upload matches the official source across 77 highhop samples
(`highhop084..160`). The observed airborne ground-check dodge reaches Y282.

The earlier integrated v1 input reused 240 jumps from the old practice entry.
Here transformation starts at highhop076, so the later B presses close the
ending message before its planned observation. Its real goal/save result is
retained as diagnostic evidence. The v2 route reduces contact placements and
jumps, asserts the actual cutscene without writing it, and observes the ending
message before closing it. `--legacy-probe` reproduces the unchanged v1 input.

Three fresh inherited regressions (`mazo-progress-reg-v1-{126,child,purchase}`)
match the qualified primary-entry parent exactly at 49 paired samples: 196 full
WRAM/SRAM/VRAM/framebuffer comparisons. All 45 recipes, 61 packs, 67 ROM patches
and native hooks reconcile; one B0 pack override is recorded explicitly.
The full unit suite passes 420 tests (`local/reports/unit-tests-mazo-progress-v1.log`).
A DSH recheck reruns `tools/qualify_mazo_progress.py` and passes the actual-node
assisted fight and ending, the Mazo30 save, and the intact recipient00D
(`local/reports/mazo-progress-recheck-v1.json`).

## Identities and reproduction

| Item | SHA-256 |
| --- | --- |
| ROM, unchanged from primary-entry V3 | `28da206c0bfeb7c7ed9a9c10a3eadb6377e128edb132b6984e725fb1de497ff5` |
| Native executable | `866e3ee587782f22f1a67c0249258dc896a3fe4f6e3b08522bcdc3ba03bb4c39` |
| Adapted B0 pack | `4e1640cbc64d2f8fb31065db79d24cca9755e1e31ab446196a109502d43c64ed` |

ROM equality alone does not identify this candidate: its native pack and binary
differ from the parent. Original ROMs, accepted builds, saves and captures remain
intact. Recipes, the bounded override, build identities, executed scripts and
official-source references are checked by `tools/qualify_mazo_progress.py`.

```sh
python3 tools/prepare_mazo_progress.py
python3 -c "import sys; sys.path.insert(0,'tools'); import native_sprite_gap; native_sprite_gap.prepare('demo11-native-mazo-progress-v1')"
python3 tools/m1.py --target demo11-native-mazo-progress-v1 scaffold
python3 tools/m1.py --target demo11-native-mazo-progress-v1 generate
python3 tools/m1.py --target demo11-native-mazo-progress-v1 build
python3 tools/mazo_integrated_ending_route.py --output FRESH.script
python3 tools/qualify_mazo_progress.py --output local/reports/FRESH.json
```

## Remaining scope

A direct table comparison narrows the event gap. The recipient event table at
`$05D608 + 0x30` holds `FF`. The official Mazo image holds `30` at the same
index. The `04EA1E` completion routine also differs by one byte in the sampled
window. The next candidate test changes only the event-table byte and checks
whether the Mazo event and exit count become valid. This note does not apply the
change.

Event value `30` already appears in the recipient table at translevels `0D`,
`129`, `131`, `192`, `1D2`, `1EB` and `1F9`. The Mazo value would join that set.
The candidate must compare the affected map tiles and paths before it claims a
correct unlock.

A reference-host test confirms the table wiring. Entry to translevel `30`
reaches room `10C` with `13BF=30`. The unpatched product holds `1DEA=FF`. A
one-byte patch at `05:D638` changes `1DEA` to `30` in the same entry, and the
`1F02..1F10` event bytes stay zero. The patch changes the selection, not yet a
map unlock or exit count. Native candidate integration remains the next step.

A native runtime switch `BM_MAZO_EVENT30` now applies the same byte in the
loaded ROM. The full assisted route `mazo-progress-event30-v1` then reports a
real event path:

| Sample | `1DEA` | `1F08` | `1F2E` | `1ED2` | `1EAF` |
| --- | --- | --- | --- | --- | --- |
| Baseline ending v2, after goal | `FF` | `00` | `0` | `80` | `0F` |
| Event30 ending, after goal | `30` | `80` | `1` | `88` | `0F` |
| Event30 File A reload | `FF` | `80` | `1` | `88` | `0F` |

The event bit, exit count and Mazo completion persist over File A reload. The
unrelated course00D stays `0F`. This is strong event/save evidence, but the map
tile and path change still need review before the switch becomes a product
default.

The `after_goal` and `file_reload` framebuffers are byte-identical to the
baseline route in both captures (229,376 bytes each, zero differences). The
event bit changes, but this sample shows no visible map tile or path change.
Event30 alone is therefore not proof of the correct route unlock. The map Layer
1 tilemap at `7EC800` and its high-byte range at `7FC800` also stay byte-equal.

A later static check corrects the “missing tile” reading. The Layer 1 event
tables at `04D85D`, `04D93D`, `04DA1D` and `04DA33` are byte-identical between
product and Mazo at event index `30`: position `2A`, VRAM `28`, before tile `29`
and after tile `F0`. Event30 has the same definition in both images. The zero
map difference may mean the recipient already shows that target tile. The next
check compares the tile at that position and the affected route before the team
rejects or accepts the event value.

The product and Mazo ROM also hold the same Layer 1 map bytes at the event
position: index `4A` is `000c000000000000`, and index `44A` is
`45ff04ff04ff04ff` on both images. The target tile is already present in the
recipient map. A zero visual difference is therefore expected, and event30 is
not obviously wrong. The remaining question is whether the event path unlocks
the intended route elsewhere.

A direct memory diff is not clean. `after_goal` differs from the baseline in 39
WRAM bytes and 9 SRAM bytes. `file_reload` differs in 10 WRAM bytes and 9 SRAM
bytes. Some entries are timing, stack or route artefacts, such as low WRAM and
`1C3..1D9`. File reload shows the expected `1ED2`, `1F08`, `1F2E` and `1F79`
changes plus `1DEB/1DED=16`. SRAM also changes at `8C/8D` and `81C`; the event
or path meaning of those bytes stays open. A same-input baseline rerun or a
save-field audit is the next check.

A fresh same-input baseline (`mazo-progress-baseline-v3`) reproduces the same
difference set. The SRAM pairs now resolve as save fields: `66/213` is the event
bitmap (`80`), `8C/239` is the exit count (`1`) and `8D/23A` is the file checksum
(`CE` to `45`). `81C` changes from `24` to `27`, consistent with a checksum.
The differences are expected event, count and checksum updates, not unrelated
course progress. Event30 is therefore a consistent event/save candidate; the
map route still needs a field check.

The recipient's Mazo event is stillFF and the exit count remains0. Its existing
world events and paths are preserved. Full map/event integration, ordinary190
traversal, unassisted fights and audible music acceptance remain open. This is
a playable experimental checkpoint, not whole-game acceptance. The user asked
to stop autonomous goal work at this playable milestone.


Final report: `local/reports/mazo-progress-qualified-v3.json`, SHA-256
`75528a9a4f392be972d82c2ca23986144269f049b8da35ae02034f99cee75cd7`. Negative probes reject a foreign WRAM or SRAM completion,
a missing Mazo backup save and a missing actual goal. The regression checker
also verifies equal sampled CPU registers and frame numbers at all 49 points.
