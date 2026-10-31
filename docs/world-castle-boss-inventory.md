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
