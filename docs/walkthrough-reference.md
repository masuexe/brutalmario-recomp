# Brutal Mario Community Walkthrough & Route Reference

This reference document compiles community walkthrough resources and course route
mechanics for use by automated testing agents and restoration contributors.

Community walkthrough wikis:
- **Brutal Mario Wiki (English Fandom)**: [https://brutalmario.fandom.com/](https://brutalmario.fandom.com/)
- **Super Kitiku Mario Wiki (Japanese WikiWiki)**: [https://wikiwiki.jp/kitikumario/](https://wikiwiki.jp/kitikumario/)

---

## 1. Role in Automated Testing & Restoration

When constructing automated verification scripts (`recomp/inputs/*.script`) and
evaluating course playthroughs, agents must distinguish between:
1. **Author-intended level design puzzles and gimmicks** (e.g. strict fuel budgets,
   inverted key/keyhole dynamics, Mario 64 cap abilities, water-switch sequences).
2. **True restoration defects** (e.g. broken sprite pointers, missing graphics/ExGFX,
   audio engine stalls, corrupt Map16 buffers).

Consulting these walkthroughs helps agents:
- **Formulate realistic input scripts**: Target genuine clear mechanics (goal tapes,
  keyholes, switch triggers, coin collections) rather than brute-forcing empty coordinates.
- **Identify secret exits**: Know the prerequisite actions (e.g. 100 coins, secret
  suicide pits, water level manipulations, 1st place cart rank).
- **Verify custom boss patterns**: Understand boss phase triggers, attack sequences,
  and vulnerability states for Carol's custom boss encounters.
- **Cross-reference version differences**: Match course names and concepts between
  legacy demo releases (`cheap_demo`, `7hero`, etc.) and the recipient baseline
  (`demoOnly1`, `demo 1-1`).

---

## 2. Guidelines for Route Design in Agent Test Suites

1. **Check Walkthroughs Before Writing Routes**:
   Before attempting to generate an automated pass or test script for a new level, read
   both the Fandom and WikiWiki pages for that course to understand its mechanics, layout,
   and exit criteria.
2. **Explicitly Label Fixtures**:
   If an input script uses coordinate pokes, temporary damage immunity, or stage warps,
   label them clearly as fixtures. Real guest actions (pressing switches, carrying keys,
   touching goal tapes, collecting coins, passing screen pipes) must be verified.
3. **Check for Inverted or Unconventional Mechanics**:
   Carol frequently inverted standard Super Mario World conventions (e.g. carrying a
   moving keyhole into a static key, jumping into a suicide pit to reach a warp,
   hitting 3 Bob-ombs on a roulette slot machine, or searching for an animated brick
   containing a P-Switch). Do not assume a level is impossible or buggy without checking
   the community walkthrough first.
4. **Fuel and Time Budget Calculations**:
   In vertical or flight levels (such as Sky Star), the fuel/time budget is often tightly
   tuned. Verify mathematical feasibility (e.g. climb speed vs fuel consumption) before
   running exhaustive input searches.
5. **Collectibles Terminology (Dragon Coins vs. DK Coins)**:
   - **Dragon Coins (ドラゴンコイン / Yoshi Coins)**: The standard collectible coins inherited
     from *Super Mario World*. Exactly **5 Dragon Coins** are placed throughout a course.
     Collecting all 5 awards an extra life and sets the course's completion bit in SRAM (`$1F2F`).
   - **DK Coins (DKコイン / Cranky's Video Game Hero Coins)**: Large collectible coins originating
     from *Donkey Kong Country*. At most **1 DK Coin** exists per stage in games that feature them.
   - *Note*: Historical project documentation occasionally conflated the 5 Dragon Coins as
     "5 DK coins" or referred to the `$1F2F` flag as the "DK bit". Always use the correct term:
     courses contain **5 Dragon Coins**.

---

## 3. Comprehensive Stage Name & Cross-Reference Table

Stage names often differ between the Japanese community wiki (`wikiwiki.jp/kitikumario`)
and the English Fandom wiki (`brutalmario.fandom.com`). Stages marked with `*` contain
secret exits.

### World 1: Grassland (草原)

| Map / Room | Japanese Wiki Name (`wikiwiki`) | English Fandom Name | Type / Notes |
| :---: | :--- | :--- | :--- |
| `$104` | ヨッシーの家 | Yoshi's House / Hey, I am Mario! | Intro / starting area |
| `$105` | 旅の始まり | Journey's Beginning / A Beautiful Journey | Introductory stage |
| `$106` | ヨッシーを追え！ | Chase After Yoshi! | Scrolling chase sequence |
| `$010` / `$105` | 息を止め続けろ * | Keep Holding Your Breath * | Room 105; secret exit to Star World / Blue Switch |
| `$120` | 無敵のバリア | Invincible Barrier | Room 120 cave sequence |
| `$138` | 旅の終わり (没) / 砦 | World 1 Castle / Fort | Room 138; custom sample dependency |
| `$06E` | 引きこもりレミー * | Lemmy the Hikikomori * | Lemmy Boss (Megalomania BGM, ID `$B0`) |
| `$014` | 青スイッチ宮殿 | Blue Switch Palace | Hidden Palace |

### World 2: Forest (森林)

| Map / Room | Japanese Wiki Name (`wikiwiki`) | English Fandom Name | Type / Notes |
| :---: | :--- | :--- | :--- |
| `$00F` | 釣りまくり * | Fishing Spree * | Secret exit available |
| `$124` | お水の世界 | World of Water | Hidden map |
| `$121` | この橋渡るべからず | Thou Shalt Not Cross This Bridge | Bridge hazard stage |
| `$122` | 僻地のボロ屋 | A Remote Shack | Cabin / house stage |
| `$123` | ウロの中はカビはだらけ | It's Moldy Within The Hollow | Tree hollow stage |
| `$125` | お化けの森 * | Ghost Forest * | Secret exit available |
| `$126` | 放火魔マリオ * | Mario the Pyromaniac * | Hidden map; fire mechanics |
| `$06F` | ニートのモートン | Morton the NEET | Morton Boss (Go! Go! Kids! BGM) |
| `$00D` | 姉歯物件 | Aneha Estate | Scrapped / hidden map |

### World 3: Bay (入江)

| Map / Room | Japanese Wiki Name (`wikiwiki`) | English Fandom Name | Type / Notes |
| :---: | :--- | :--- | :--- |
| `$00B` | イルカの丸焼き | Dolphin Barbecue | Dolphin mechanics |
| `$11C` | 深海調査 | Deep Sea Research | Underwater exploration |
| `$11D` | 海底神殿 | Ocean Palace | Underwater palace |
| `$11E` | タイタニック * | Titanic * | Shipwreck stage; secret exit available |
| `$070` | ギャルのウェンディ | Wendy the Gal | Wendy Boss (The Flame and the Arrow BGM) |

### World 4: Cave (洞窟)

| Map / Room | Japanese Wiki Name (`wikiwiki`) | English Fandom Name | Type / Notes |
| :---: | :--- | :--- | :--- |
| `$11F` | どくろコースター * | Skull Coaster * | Coaster track; secret exit available |
| `$127` | ザ・ワールド 時よ止まれ | The World! Stop Time! | Time freeze gimmick |
| `$113` | お馬鹿屋敷 * | Haunt-idiot Mansion * | Ghost house; secret exit available |
| `$114` | 鏡の砦 * | Mirror Fort * | Hidden fortress; mirror reflection mechanics |
| `$015` | 赤スイッチ宮殿 | Red Switch Palace | Hidden Palace |
| `$115` | スクーコスライド | Squawks Ride | Donkey Kong Country Squawks riding |
| `$116` | 迷路洞窟1 * | Maze Cave 1 * | Maze cave; secret exit unlocks Cave Star |
| `$12A` | 迷路洞窟2 | Maze Cave 2 | Hidden maze branch |
| `$071` | 痴呆症イギー | Iggy the Demented | Iggy Boss |

### World 5: Plateau / Mountain (高原)

| Map / Room | Japanese Wiki Name (`wikiwiki`) | English Fandom Name | Type / Notes |
| :---: | :--- | :--- | :--- |
| `$00E` | ホーミングキラーの恐怖 | Fear of Homing Bills | Custom homing bullet bills |
| `$102` | 重力の砦 * | Fort of Gravity * | Gravity inversion; secret exit available |
| `$103` | 恐怖の月曜日 | Fear of Monday | Hidden map |
| `$016` | 緑スイッチ宮殿 | Green Switch Palace | Hidden Palace |
| `$10C` | ワンワンパニック1 * | Chomp Chomp Panic 1 * | Chain Chomp hazards; secret exit available |
| `$10D` | いつかどこかで / ガチャポコランド | Gachapoko Land / Where is This? | Custom minigame theme |
| `$10E` | クラッシュエレベーター * | Castle Crush / Crush Elevator * | Elevator ascent; secret exit unlocks Plains Star |
| `$10F` | リフトでGO！1 | Lift Go! 1 | Platform ride |
| `$072` | ホームレスのラリー | Larry's Castle / Homeless Larry | Larry Boss |

### World 6: Sky (天空)

| Map / Room | Japanese Wiki Name (`wikiwiki`) | English Fandom Name | Type / Notes |
| :---: | :--- | :--- | :--- |
| `$131` | 銀河鉄道の夜 | Night Galaxy Train | Train ride stage |
| `$01E` | ワンワンパニック2 | Chomp Chomp Panic 2 | Chain Chomp hazard sequel |
| `$101` | そこにシビれる！憧れるゥ！ * | Careful! Lightning! * | Lightning / electrical hazards; secret exit available |
| `$132` | トカゲもおだてりゃ空を飛ぶ * | Really Big Jump * | Hidden map; Yoshi flight |
| `$130` | コインドーザーの森 | Koindozer Forest | Coin bulldozer stage |
| `$006` | 双子リフト * | Twin Lifts * | Hidden map; dual lift platforms |
| `$022` | UFO襲来 * | The Future of UFOs / UFO Invasion * | UFO abduction gimmick; secret exit available |
| `$020` | 風雲 デデデ城 | Dedede's Sky Castle | Kirby King Dedede theme & boss |
| `$013` | 黄色スイッチ宮殿 | Yellow Switch Palace | Hidden Palace |
| `$01F` | アートネイチャーロイ | Roy's Castle / Art Nature Roy | Roy Boss |

### World 7: Snowfield (雪原)

| Map / Room | Japanese Wiki Name (`wikiwiki`) | English Fandom Name | Type / Notes |
| :---: | :--- | :--- | :--- |
| `$01C` | 北の国から | Northern Resort | Snow / ice field intro |
| `$12F` | 氷の洞窟 | Frozen Cave | Slippery ice cave |
| `$01B` | 4色の砦 | Four-Color Fort | Multi-colored switch block fortress |
| `$021` | 食いしん坊のテレサ * | Gourmet Boo * | Big Boo stage; secret exit available |
| `$01D` | クリスマス中止のお知らせ (没) | Warning - Christmas | Scrapped holiday stage |
| `$10A` | 鍵はどこにある * | What Matches a Key? * | **Inverted mechanic**: carry moving keyhole to static key! |
| `$133` | マリオの窃盗物保管所 | Mario's Item Theft | Hidden storage stage |
| `$118` | マリオ襲来 | Mario's Attack | Shadow / clone Mario chase |
| `$01A` | ホモのルドウィッグ * | Ludwig's Castle * | Ludwig Boss; secret exit unlocks Snow Star |

### World 8: Bowser's Valley (クッパの谷)

| Map / Room | Japanese Wiki Name (`wikiwiki`) | English Fandom Name | Type / Notes |
| :---: | :--- | :--- | :--- |
| `$016` | 戦艦ハルバード | Battleship Halberd | Meta Knight's Halberd airship stage |
| `$018` | 飛空艇の墓場 | Airborne Cemetery | Airship wreckage stage |
| `$019` | ダークキャッスル * | Dark Castle * | Dark castle; secret exit unlocks Valley Star |
| `$128` | ドラゴンズホール | Hall of Dragons | Dragon hazard stage |
| `$13B` | ミラージュパレス / TO BE CONTINUED | Mirage Palace / To Be Continued | Seiken Densetsu 3 / Mana mirage stage |
| `$108` | 決戦！クッパ城 | Finish! Bowser Keep | Multi-section climax castle (WIP across demos) |

---

## 4. Star World Course & Secret Exit Details

Star World (スターロード) consists of 9 courses connected in an outer ring and center hub.
Each course features unique custom sprites, ASM mechanics, and secret exit requirements.

| Star Course | Room | Custom Theme / Gimmick | Normal Exit | Secret Exit Route |
| :--- | :---: | :--- | :--- | :--- |
| **Grassland Star**<br>*(草原のスター)* | `$001` / `$002` | Intro demo stage; Koopa graphics replacement in 2nd half. | Standard goal tape. | Jump into the pit marked with the **"SUICIDE"** signpost; warps to hidden descent room where key and keyhole await at the bottom. |
| **Forest Star**<br>*(森林のスター)* | `$003` | Forest labyrinth; replaced by Lively Water in Demo 7.5. | Standard exit. | Hidden pipe / alternate branch. |
| **Bay Star**<br>*(入江のスター)* | `$004` | SM64 water-level switches (`$7E:FFD0`) and water currents. | Screen-8 pipe to goal room `$048`. | Hit top water switch, let water rise to max level, lower it 2 levels, grab key and reach keyhole. Unlocks Warp Star. |
| **Cave Star**<br>*(洞窟のスター)* | `$002` / `$007` | DKC2 roller coaster track with Skull Cart; racing position counter against Koopas. | Reach end of roller coaster track. | Defeat **all Koopas** along the coaster; the block in front of the goal turns off and reveals the secret goal (the race counter ends at 1). |
| **Plains Star**<br>*(高原のスター)* | `$002` / `$005` | Entire level enclosed in breakable SMB3-style brick blocks. | Break out and reach goal tape. | Locate the single brick with a **distinctly different animation/flashing effect** near the upper-right (past the 4th Dragon Coin and 3 Koopas); hit it to reveal a **P-Switch**, then press it to turn the bricks into coins and access the secret key and keyhole below. |
| **Sky Star**<br>*(天空のスター)* | `$006` / `$007` | Vertical rocket climb; tight fuel budget (89-pixel slack). Right page has no fuel blocks. | Standard rocket ceiling finish (`Y in 0x400..0x44F`, `X high 0`). | Near-clean right-page ascent (`X high 1`) with remaining fuel; key and keyhole sit directly above to unlock Warp Star. |
| **Snow Star**<br>*(雪原のスター)* | `$008` | Winter cavern with seals, icicles, and a final 3-block roulette / slot machine. | Match regular items / goal points on the final roulette blocks. | Hit **3 Bob-ombs (`ボム兵`)** on the final 3-block roulette / slot machine to trigger the secret exit. |
| **Valley Star**<br>*(クッパの谷のスター)* | `$117` | Super Mario 64 Cap power-ups (Wing, Metal, Vanish) & Kirby Dream Course aesthetics. | Standard exit. | Collect all **100 coins** in the level (SM64 100-coin star mechanic) to spawn/unlock the secret key exit. |
| **Special Warp Star**<br>*(スペシャルスター)* | `$00A` / `$079` | Central hub course; custom boss encounter (sprite `$24`). | **Unfinished** by author Carol. | **Route unknown / Unfinished.** The boss program in donor ROMs implements phases 0, 1, and 2 without a terminal victory state or exit destination (accepted donor exception; see `star-world-center-restoration.md`). |

### Japanese wiki walkthrough details (fetched 2026-10-25)

Source: [WikiWiki Kitiku Mario map guide](https://wikiwiki.jp/kitikumario/) pages
`マップ攻略/入江のスター` and `マップ攻略/洞窟のスター`. These details explain
the intended mechanics behind the table rows above.

**Bay Star secret route.** The water-level switches (crystal-like sprites)
raise or lower the water surface to the switch height. The full route is:

1. Touch the switch on page `0B`, then return to the start point.
2. Hit the block at the upper right to get the key.
3. Carry the key to the pipe on page `06`. A vine grows from the block above
   that pipe. Before using it, hit the rotating block (`クルクルブロック`)
   above the vine.
4. Climb the vine with the key and touch the switch near the ceiling. The water
   rises to near the ceiling.
5. Go back down to the pipe and place the key at the coin row at the pipe's
   upper right.
6. Return to page `08` and touch the switch to the right of the spring while
   Super Mario or higher. The water starts to drop.
7. Hurry back, take the placed key, and go to the lower right.
8. At the keyhole, wait for the water to drop, then break the blocks to reach
   the secret goal.

**Cave Star secret route.** Beat every Koopa on the coaster course. The block
in front of the goal then turns off and the secret goal becomes reachable.

---

## 5. Notable Custom Bosses & Special Gimmicks

- **Lemmy the Hikikomori** (Room `$06E`):
  Uses custom Live A Live *Megalomania* music (slot `$B0` on modern line). Lemmy hides behind
  bullet-proof barriers and computer monitors while shooting projectile waves.
- **Morton the NEET** (Room `$06F`):
  Uses Treasure Hunter G *Go! Go! Kids!* music (slot `$98`). Morton sits at a desk throwing
  junk and summoning minions.
- **Wendy the Gal** (Room `$070`):
  Uses Treasure of the Rudras *The Flame and the Arrow* (slot `$A2`). Wendy uses fashion/shopping
  accessories and high-speed dash attacks.
- **Ludwig Castle** (Room `$01A`):
  Uses Romancing SaGa 2 *Last Battle* (slot `$AC`). Custom multi-phase fight requiring
  coordinated jumps and evasion of custom flame pillars.
- **What Matches a Key?** (Room `$10A`):
  Features an inverted mechanic: Mario must lift and carry a floating keyhole actor across
  hazards and insert it into a giant stationary key anchored to the ground.

---

## 6. External Community Links

- Fandom Level Hub: [https://brutalmario.fandom.com/wiki/Levels](https://brutalmario.fandom.com/wiki/Levels)
- Fandom Star Road Guide: [https://brutalmario.fandom.com/wiki/Star_Road](https://brutalmario.fandom.com/wiki/Star_Road)
- Fandom Secret Exits Guide: [https://brutalmario.fandom.com/wiki/Secret_exits](https://brutalmario.fandom.com/wiki/Secret_exits)
- WikiWiki Map Walkthrough: [https://wikiwiki.jp/kitikumario/マップ攻略](https://wikiwiki.jp/kitikumario/%E3%83%9E%E3%83%83%E3%83%97%E6%94%BB%E7%95%A5)
- WikiWiki Stage Name Directory: [https://wikiwiki.jp/kitikumario/ステージ名一覧](https://wikiwiki.jp/kitikumario/%E3%82%B9%E3%83%86%E3%83%BC%E3%82%B8%E5%90%8D%E4%B8%80%E8%A6%A7)
- WikiWiki Star Road Directory: [https://wikiwiki.jp/kitikumario/マップ攻略/スターロード](https://wikiwiki.jp/kitikumario/%E3%83%9E%E3%83%83%E3%83%97%E6%94%BB%E7%95%A5/%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%AD%E3%83%BC%E3%83%89)
