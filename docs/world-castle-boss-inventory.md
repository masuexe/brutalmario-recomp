# World castle boss room inventory

Date: 2026-10-31. Static product parse for rooms `06E` to `072`. This note
does not qualify entry, phase behavior or a save.

| Room | Screens | Size | Screen exits |
| --- | ---: | ---: | --- |
| `06E` | 1 | 631 | screen 0 to `143` |
| `06F` | 1 | 209 | screen 0 to `135` |
| `070` | 2 | 3360 | screen 1 to `104` secondary, screen 0 to `267` |
| `071` | 6 | 3608 | screen 5 to `122` |
| `072` | 3 | 4646 | screen 0 to `114` secondary |

Each room also holds the usual screen jump sentinel. The next checks need live
entry, phase and exit captures for each room.

Live entry check for room `06F`: capture `room06f-entry-v1` reaches mode `14`,
room `06F`, player `(16,352)` and four lives. Phase and exit checks stay open.

Live entry check for room `06E`: capture `room06e-entry-v1` reaches mode `14`,
room `06E`, player `(48,176)` and four lives.

Live entry check for room `070`: capture `room070-entry-v1` reaches mode `14`,
room `070`, player `(128,352)` and four lives.

Live entry check for room `071`: capture `room071-entry-v1` reaches mode `14`,
room `071`, player `(32,336)` and four lives.

Live entry check for room `072`: capture `room072-entry-v1` reaches mode `14`,
room `072`, player `(32,352)` and four lives. All five castle boss rooms now
have a live entry on the product. Phase, exit and save checks stay open.

A room `06F` idle watch (`room06f-idle-v1`) stays in mode `14`, room `06F`,
with four lives for the first 400 frames. No phase or exit starts without
input.

Entry actor samples record these custom slots:

| Room | Live custom actors |
| --- | --- |
| `06E` | slot 7 custom `06`, slots 8 and 9 custom `37` |
| `06F` | slot 9 custom `A2` at `(224,368)` |
| `070` | none in the first samples |
| `071` | none in the first samples |
| `072` | none in the first samples |
