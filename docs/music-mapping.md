# Brutal Mario Cross-Version Music ID Mapping Reference

This document defines the custom music ID mapping between Carol's **Legacy Demo Family**
(`cheap_demo`, `7hero`, `mazo`, `ow`, `demo7`, `demo8`) and the **New Demo Family**
(`demoOnly1` and `demo 1-1`).

> [!IMPORTANT]
> Numeric music IDs in Brutal Mario are version-local. Level headers (`$3A:B524`),
> sprite music triggers, and `$1DFB` commands in legacy donor ROMs use legacy indices.
> When porting levels or repairing music on the modern line (`demo 1-1`), **never copy
> donor music IDs verbatim**; consult this table to map them to the recipient target.

## Version Chronology and Engine Architecture

| Family | ROM Releases | Release Date | Music Engine Architecture |
| :--- | :--- | :--- | :--- |
| **Legacy Family (Old)** | `demo7`, `demo8`, `cheap_demo`, `7hero`, `mazo`, `ow` | ~2008–2011 | Shared 110-entry pointer table at `$0FE000` + multi-song bank group uploads (`$3F:8008`, etc. into ARAM `$6800`). |
| **New Family (Modern)** | `demoOnly1` (2012), `demo 1-1` (2015) | 2012, 2015 | Overhauled global pointer table at `$0FE000` uploading individual custom songs directly to ARAM `$5400`. `demo 1-1` re-adds several unreleased tracks. |

## Core Cross-Version Mapping Table

| Legacy ID (`cheap_demo` family) | `demoOnly1` ID | `demo 1-1` ID | Track Title | Origin Game | Verified In-Game Usages | Status |
| :---: | :---: | :---: | :--- | :--- | :--- | :--- |
| **`$24`** | `$51` | **`$51`** | **Fear Factory** | Donkey Kong Country | Cave Star, Castle Crush, Skull Coaster | verified graph match |
| **`$27`** | `$8E` | **`$8E`** | **Castle Pandemonium** | Final Fantasy II | Finish! Bowser Keep (Crash/Burn) | verified graph match |
| **`$28`** | `$49` | **`$49`** | **Podol / Boundaries** | Romancing SaGa 3 | Bay Star, Frozen Cave (pre-clear), Deep Sea Research (+1 more) | verified graph match |
| **`$29`** | *(none)* | **`$B0`** | **Megalomania** | Live A Live | Lemmy Koopa Boss (Room 6E / Lemmy the Hikikomori) | verified graph match |
| **`$2E`** | `$58` | **`$58`** | **Grape Garden** | Kirby's Adventure | Sky Star, Athletic Special (part 3), Battleship Halberd (+3 more) | verified graph match |
| **`$30`** | `$7A` | **`$7A`** | **Slide** | Super Mario 64 | End of Special Zone, Special Warp Star | verified graph match |
| **`$33`** | `$AC` | **`$AC`** | **Last Battle** | Romancing SaGa 2 | Seven Koopalings Boss, Wily's Revenge | verified graph match |
| **`$36`** | `$61` | **`$61`** | **Rainbow Resort** | Kirby's Adventure | Mario's Attack, Athletic Special (parts 1-2), Ludwig's Castle | verified graph match |
| **`$38`** | `$A4` | **`$A4`** | **The Decisive Battle** | Final Fantasy VI | Naval Piranha Boss, Ocean Palace Boss, Finish! Bowser Keep (Naval Piranha) | verified graph match |
| **`$39`** | `$98` | **`$98`** | **Go! Go! Kids!** | Treasure Hunter G | Twinbee Special (Dangling Ghost Boss), Morton the NEET Boss, Special Warp Star Boss (+1 more) | verified graph match |
| **`$3A`** | `$A2` | **`$A2`** | **The Flame and the Arrow** | Treasure of the Rudras | Two-Face Moon Boss, Wendy the Gal Boss, Finish! Bowser Keep (Two-Face Moon) | verified graph match |
| **`$3B`** | `$9C` | **`$9C`** | **Irwin on Reflection** | Legend of Mana | Baby Bowser Boss, Toad Boss (End of Special Zone), Mirror Fort | verified graph match |
| **`$3E`** | *(none)* | **`$8D`** | **Koopa's Road** | Super Mario 64 | Finish! Bowser Keep (SMB3 Castle) | verified graph match |
| **`$40`** | `$60` | **`$60`** | **Iceberg Ocean** | Kirby's Dream Course | Valley Star, Athletic Special (part 4), What Matches a Key? (+2 more) | verified graph match |
| **`$41`** | `$79` | **`$79`** | **Cap Theme** | Super Mario 64 | Valley Star (Cap item power-up) | verified byte identical |
| **`$42`** | `$71` | **`$71`** | **A Child's Fantasy Realm** | Pop'n Twinbee: Rainbow Bell Adventures | Twinbee Special, Gachapoko Land | verified graph match |
| **`$43`** | `$59` | **`$59`** | **Aboard the Hilda Garde** | Final Fantasy IX | Milky Way Wishes, Night Galaxy Train, Really Big Jump | verified graph match |
| **`$47`** | *(none)* | **`$6B`** | **Leonid's Castle** | Romancing SaGa 3 | Gourmet Boo, Koindozer Forest, A Remote Shack (+4 more) | verified graph match |
| **`$4A`** | `$38` | **`$38`** | **Town Where the West Wind Blows** | Wild Arms 2 | Baby Yoshi Hill, Grassland Star | verified graph match |
| **`$4B`** | `$B9` | **`$B9`** | **To Far Away Times** | Chrono Trigger | Unused / Ending sequences | verified graph match |
| **`$58`** | `$A0` | **`$A0`** | **Boss Theme** | Super Nazo Puyo: Rulue's Roux | Finish! Bowser Keep (Section 1), Fort of Gravity | verified graph match |
| **`$59`** | `$39` | **`$39`** | **Hometown Domina** | Legend of Mana | Unused in cheap_demo, present in demoOnly line | verified graph match |
| **`$5D`** | `$32` | **`$32`** | **Freiluftmusik** | SaGa Frontier 2 | Plains Star, Chomp Chomp Panic 1, Fishing Spree | verified graph match |
| **`$61`** | `$A5` | **`$A5`** | **The Fierce Battle** | Final Fantasy VI | Athletic Special (Part 5 / Final section) | verified graph match |

## Modern Family Additions (`demoOnly1` and `demo 1-1`)

These tracks were ported and introduced in Carol's new engine line (`demoOnly1` and `demo 1-1`), and do not exist in the legacy family under these slots:

| New Slot ID | Track Title | Origin Game | Introduced In | Notes |
| :---: | :--- | :--- | :---: | :--- |
| **`$2A`** | **Prophecy** | Secret of Mana | demoOnly1 | Added in demoOnly1 custom music list. |
| **`$52`** | **Stickerbrush Symphony** | Donkey Kong Country 2 | demoOnly1 | Bramble theme ported by Carol. |
| **`$5A`** | **The Moon** | DuckTales | demoOnly1 | Famous 8-bit arrangement. |
| **`$62`** | **Cold Man's Stage** | Mega Man & Bass | demoOnly1 | Rockman & Forte icy stage theme. |
| **`$68`** | **Last Dungeon** | Romancing SaGa 2 | demoOnly1 | Used in Bowser's Keep Yoshi coins room and Mammon Machine. |
| **`$69`** | **Ghost House** | New Super Mario Bros. | demo 1-1 | Used in Horror House / Ghost Forest (1,009 bytes). |
| **`$6A`** | **Krook's March** | Donkey Kong Country 2 | demo 1-1 | DKC2 castle / march theme (4,172 bytes). |
| **`$6B`** | **Leonid's Castle** | Romancing SaGa 3 | demo 1-1 | Re-added in demo 1-1 replacing legacy $47 (604 bytes). |
| **`$72`** | **Taking Over the Halberd** | Kirby Super Star | demoOnly1 | Revenge of Meta Knight airship theme. |
| **`$73`** | **Magic Man's Stage** | Mega Man & Bass | demoOnly1 | Rockman & Forte theme. |
| **`$86`** | **Boss / Action Track** | Custom Port | demo 1-1 | New slot allocated in demo 1-1 table. |
| **`$88`** | **Save Hut** | Kirby Super Star | demoOnly1 | Used in Lemmy's Castle orb room. |
| **`$8D`** | **Koopa's Road** | Super Mario 64 | demo 1-1 | Replaces demoOnly1 NSMB Castle; restores SM64 Koopa Road (2,280 bytes). |
| **`$8F`** | **Thema** | SaGa Frontier 2 | demoOnly1 | Main theme arrangement. |
| **`$90`** | **Sad Freedom** | Treasure Hunter G | demoOnly1 | Sad emotional melody. |
| **`$91`** | **The Galaxy Reactor** | Super Mario Galaxy | demoOnly1 | SMG Bowser final galaxy arrangement. |
| **`$92`** | **Undersea Palace** | Chrono Trigger | demoOnly1 | Ocean Palace theme. |
| **`$93`** | **One of Them Is Hope** | Secret of Mana | demoOnly1 | Sanctuary theme. |
| **`$94`** | **The Savior of Those on Earth** | Lufia II | demoOnly1 | Estpolis II boss battle. |
| **`$99`** | **Final Fight** | SNK vs. Capcom: Chaos | demoOnly1 | Fighting game boss theme. |
| **`$9A`** | **Gangplank Galleon** | Donkey Kong Country | demoOnly1 | King K. Rool boss battle. |
| **`$9D`** | **Masked Dedede's Theme** | Kirby Super Star Ultra | demoOnly1 | Revenge of the King arena. |
| **`$A6`** | **Maybe I'm a Lion** | Final Fantasy VIII | demoOnly1 | Griever / Ultimecia battle. |
| **`$A7`** | **High Tension Wire** | Trials of Mana (Seiken Densetsu 3) | demoOnly1 | Fast battle theme. |
| **`$A8`** | **Nuclear Fusion** | Trials of Mana (Seiken Densetsu 3) | demoOnly1 | God-beast battle. |
| **`$AB`** | **Bowser Battle** | Super Mario RPG | demoOnly1 | Chandelier battle theme. |
| **`$AE`** | **Battle With Magus** | Chrono Trigger | demoOnly1 | Decisive Magus duel. |
| **`$AF`** | **The Sun Rises** | Okami | demoOnly1 | Okami climax battle. |
| **`$B0`** | **Megalomania** | Live A Live | demo 1-1 | Re-added in demo 1-1 for Lemmy's Castle boss duel, restoring cheap_demo legacy BGM $29 (2,067 bytes). |
| **`$B8`** | **The Credits Concerto** | Donkey Kong Country | demoOnly1 | DKC end credits medley. |

## Legacy Family Exclusive / Unported Tracks

These tracks exist in the legacy family (`cheap_demo`, etc.) but were either unported or replaced in the new demo line:

| Legacy ID | Track Title | Origin Game | Known Level Usages | Notes |
| :---: | :--- | :--- | :--- | :--- |
| **`$31`** | **Go Red Team! Go White Team! Rah Rah Rah!** | Treasure Hunter G | Switch Palaces (Blue, Green, Red, Yellow) | Standard palace track in legacy family; in demoOnly family, standard SMW palace track is used. |
| **`$53`** | **Haunted Chase** | Donkey Kong Country 2 | Airborne Cemetery, Ghost Special, Abode of Larry | Ghost rope climbing theme from DKC2; present in cheap_demo bank. |
| **`$54`** | **Jingle Bells** | James Lord Pierpont | Snow Star | Holiday theme used in Snow Star. Does not exist in demoOnly1. |
| **`$57`** | **KingBonbie VS MechaBonbie** | Super Momotarou Dentetsu DX | Rescue Yoshi | Mecha Bonbie battle theme; legacy family only. |
| **`$5A`** | **Akuma's Theme** | Street Fighter Alpha 2 | Unused in cheap_demo | Present in cheap_demo bank; omitted in demoOnly1. |
| **`$5C`** | **Mißgestalt** | SaGa Frontier 2 | Unused in cheap_demo | Present in cheap_demo bank; omitted in demoOnly1. |

## Agent Restoration Workflow

When an agent restores a level or repairs music on the modern line (`demo 1-1`):

1. **Identify the Donor Cue**: Check the donor ROM's room header byte (at `$3A:B524` or similar), sprite controller immediates (such as cap expiry), or `$1DFB` writes in execution captures.
2. **Look Up the Recipient Slot**: Consult the core table above. For example, if donor requests `$28` (Podol), map to recipient `$49`. If donor requests `$40` (Iceberg Ocean), map to recipient `$60` (header byte `$61`).
3. **Special Bank Dependencies**: If donor requested a bank-internal selection (such as cap requests `$21/$22` inside bank `$3F:8008`), translate to recipient global custom song slots (cap pickup `$79`, cap expiry resume `$60`).
4. **Re-added in Demo 1-1**: For tracks like *Koopa's Road* (`$8D`), *Leonid's Castle* (`$6B`), or *Megalomania* (`$B0`), use the `demo 1-1` ID even though `demoOnly1` lacked them.
5. **Unmapped Tracks**: If the donor track has no recipient slot, do not invent arbitrary IDs. Follow the protocol in [`docs/world1-room106-music-investigation.md`](world1-room106-music-investigation.md) to audition candidate library tracks or consult the user.
