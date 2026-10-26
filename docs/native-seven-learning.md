# Native Seven hurt learning and attack resistance

The user confirmed that learning a defensive skill when hit, including immunity
to a particular attack, is intended behavior. Preserve that behavior. Different
unseeded learning outcomes are not sufficient evidence of an integration defect.
This does not establish the cause of every historical capture divergence.

## Verified handler

`tests/test_seven_learning.py` executes the official Boss hurt handler at
`$22:9BEB` and its native mapped copy at `$A2:9BEB`, using the real 65816
interpreter and the current five immutable packs. The target is
`demo11-native-seven-child-fight-music`; no game code, pack or ROM changes are
needed for this check.

The handler calls `$9C73` for attack-specific resistance. The attack index is
`$7FFEBF`; the learned flags start at `$7FFEC0`. An existing flag returns carry
set without calling the RNG. Otherwise it calls `$01ACF9`, adds Mario's low X
coordinate, and compares the result with `$20` (`$40` for attack index 8).
Success sets the corresponding flag and pauses for the learning message.

If that check fails, the handler can learn defensive skills through `$9CBE`
(`$7FFF15`) and `$9DAC` (`$7FFF17`). If all learning checks fail, small Mario
reaches the ordinary hurt/death path. These checks verify the actual guest
instructions, rather than a separate implementation of the probability rules.

## Reproducible boundary test

```
python3 -m unittest discover -s tests -p test_seven_learning.py -v
```

Inputs are hash-checked before execution:

| Input | SHA-256 |
| --- | --- |
| Official Boss ROM, 4 MiB | `337fe036f943dafb0df70bdb556e588b785c58ff019b1b00c08f77743e2b3ccd` |
| Native fight-music ROM, 4 MiB | `14622c254c562dcfdd5d3c8b422acec9534588bf17dbcf0e0294afed018dec63` |
| Donor `seven-opening-v1-donor/attack1200.wram.bin`, 128 KiB | `74fb4823ead68901af132ef89ce9d5a9508b93a47f3eea780b593e01ca8a2b06` |

The test explicitly resets damage gates, action and learned flags, and seeds
the RNG. This is an isolated CPU fixture, not ordinary gameplay. For attack
index 10, all 256 seed cases agree between source and mapped code:

| Outcome | Cases |
| --- | ---: |
| Attack-specific resistance learned | 32 |
| Defensive skill `$7FFF15` learned | 56 |
| Defensive skill `$7FFF17` learned | 63 |
| No learning; small-Mario death | 105 |

Two additional paired cases establish that an existing attack-10 resistance
blocks attack 10 without consuming RNG, while unlearned attack 11 with the
same seed still reaches death. This is 258 paired cases in total.

The comparison checks WRAM, recorded MMIO and returned CPU state. Explicit
normalizations are limited to discarded stack bytes, queued JSL bank bytes
`22 -> A2`, the scheduler's saved inline-pointer bank at `$0E`, and the
recipient's retained death timer `30 -> 2E` in A, `$9D` and `$1496`. These
differences are asserted before normalization. The isolated bus records MMIO;
it does not emulate PPU rendering or audio.

The test skips when the pinned local target or capture fixture is absent.
Full fight traversal, later phases, ending, map return and saved completion
remain separate acceptance requirements.
