# Mazo candidate verification reruns

Date: 2026-10-31. The three existing assisted Mazo qualifiers rerun against the
current tracked recipes and existing captures. The accepted product stays r14.

| Check | Command | Result |
| --- | --- | --- |
| 9C orb | `qualify_mazo_orb_sequence.py --native mazo-orb-sequence-native-v2 --source mazo-orb-sequence-source-v3` | PASS: 98 samples per host, 15 exact pairs, expiry and respawn |
| 9C reflection | `qualify_mazo_reflection.py --native mazo-reflect-long-native-v1 --source mazo-reflect-long-source-v1` | PASS: five impacts, scripted marker, second-boss arrival, 385 samples each |
| Ending | `qualify_mazo_ending.py --native mazo-ending-cumulative-v2 --source mazo-ending-source-v2` | PASS: cutscene transfer, message dismissal, sphere goal, bounded flag persistence |

The message candidate also passes its own qualifier on the same tree.

A later check adds two default map behaviors. Captures
`new-save-yoshi-default-v2` and `map-node-default-v1` show the Yoshi House start
and the 10C node entry to room 190. The full unit suite passes 413 tests
(`local/unit-tests-round84.log`). The
reports live under `local/reports` and stay ignored. These reruns show that
the later message and room 190 work did not disturb the orb, reflection or
ending checkpoints. They do not claim boss damage, a full earned clear or
whole-game acceptance.
