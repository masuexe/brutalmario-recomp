# Room 126 course clear and save ownership

Date: 2026-10-31. Room126 is outside the verified Forest World2 list.
The historical capture below uses a node-assignment override, not ordinary map
travel. After entry, the route uses only ordinary right and A inputs.

Room `126` (translevel `04A`) starts at player `(80,320)` with four lives.
Twenty cycles of right and A move the player to `(588,320)`. At sample `j10`
the goal byte `$1493` is `9B` and lives rise from four to five. At sample
`j15` `$1493` is `03`. Sample `j20` returns to the overworld (mode `0E`,
room `126`) with five lives.

Capture: `w2-126-run-v1`. Script: `recomp/inputs/world2-room126-run.script`.
The run does not write completion flags, events or saves. The SRAM hash changes
from `38e21fcf...` at entry to `8b77ee69...` after the map return, so the clear
updates the save through the game routine. It qualifies the course traversal
from the entry fixture, not the full map route or correct completion ownership.
The changed SRAM hash alone does not establish which course was saved.


## Ownership correction and actual-node route

The historical override changes `D7E2` to `4A` at a node whose ordinary
assignment is `05`. Its real goal changes `$1EA7` from `09` to `89`, not the
room126/translevel04A flag at `$1EEC`. A fresh reset control,
`room126-clear-save-reload-v1`, confirms that node05's flag survives in WRAM
and both SRAM copies at `0005` and `01B2`. This is a fixture limitation, not
proof of a product save defect.

The replacement input is `recomp/inputs/room126-node-clear-save-reload.script`.
It places Mario on map6 at `(0178,0128)` and uses the existing `D727=4A`
assignment. It does not edit the node table. Ordinary Y enters room126; after
entry only ordinary right+A input reaches the real goal. Map placement remains
a fixture, so no walking route to the node is claimed.


Capture `room126-node-clear-save-reload-v1` passes the ownership qualifier.
At `j10` the real goal timer is `9C` (the override control samples `9B`);
it decreases to `04` before the map return. Lives rise from four to five.
The actual-node route changes only completion byte `$1EEC`, from `0F` to
`8F`. Both SRAM copies, `004A` and `01F7`, contain `8F` after clear and
console reset/File A reload. The exit count rises from zero to one and stays
one after reload. Node05 remains `09`. Reload restores four lives; the extra
life is not claimed to persist.

Verification checks the exact ROM, native binary, build/module/runtime
identities, executed scripts, clean completion logs and full WRAM/SRAM sizes.
Three negative probes reject a missing reloaded WRAM flag, a missing backup
save flag and an absent goal timer. No game code or resource changed.

```sh
python3 tools/qualify_room126_save.py --output local/reports/FRESH.json
```

- Target: `demo11-native-product-r14`.
- ROM SHA-256: `393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b`.
- Binary SHA-256: `b854560490132a35343a8150a3e12cb746da50474f29544f70dc582e1ec09eed`.
- Report: `local/reports/room126-save-qualified-v1.json`.
- Report SHA-256: `63f3abc57a323079d10ef657147ce1fdc495d894863438d56f211df16cc34522`.

The version-specific [community name list](https://wikiwiki.jp/kitikumario/ステージ名一覧),
rechecked on 2026-10-31, calls room126 Baby Yoshi Hill. The Fandom course page
could not be fetched. The corrected Forest inventory excludes room126; the
historical filename does not establish World2 membership. Other worlds,
ordinary map travel, Seven earned victory and Mazo world/save assignment
remain open.
