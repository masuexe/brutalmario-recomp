# Seven move table and unlock probe

Date: 2026-10-31. Source: the user supplied
`/home/harp/projects/sfc/patches/cheap_demo/7hero.xls`. That workbook holds the
move list, the conditions and the boss health table. The project keeps the
workbook outside the repository.

## Move list

The workbook names these moves: Super Jump, Super Spin, 逆風の太刀,
ジョルトカウンター, オーラ, フェザーシール, 無双三段, ミリオンダラー,
高速ナブラ, アストラルゲート, アビスゲート and シャドウサーバント.

The conditions include:

- `B` during Super Jump.
- `Select` when the stock is empty.
- A chance on a normal jump, a spin jump or a death.
- The Aura state changes the chance to one quarter.
- アストラルゲート removes one learned move. The same move can flash again,
  and the maximum WP can grow to 99.

The workbook gives the boss health per body: 2000, 4000, 5000, 6000, 7000,
8000 and 64000 for the final form. It also states that Wendy is always first.
Ludwig, Iggy and Lemmy appear after Roy. Morton appears after Ludwig. The other
order is random.

## RAM candidate

The fight captures hold a 17-byte 0/1 flag block at `7FFF10..7FFF20`. The
block grows during a fight: `seven-fight-pursue-v1-native/p010` has six set
bytes, and `seven-fight-mixed-v1-native/mixed0400` has more. This matches a
learned-move table.

A labeled probe wrote `01` to all 17 bytes. The probe is inconclusive: the
current opening fixture lands in map mode `0E` at room `0FF`, so no fight
starts. The historical `seven-fight-mixed-v1-native` capture entered room
`0FF` in mode `14` with a different binary and patch identity. The next step
is to restore a working fight entry before the unlock probe can prove the block.

## Next work

1. Find why the current opening fixture returns to map mode at room `0FF`.
2. Re-run the all-ones write with a working entry.
3. Compare the HUD and the attack set with a normal fight capture.
4. Then use the real moves against the final form and check the health table.

Do not claim an unlocked move set or an earned victory yet.
