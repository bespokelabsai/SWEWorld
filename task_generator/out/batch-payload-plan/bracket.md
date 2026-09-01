# Bracket — g1 (batch-payload-plan)

- `pristine`: {'failed': 11} rc=1
- `naive`: {'failed': 10, 'passed': 1} rc=1
- `oracle`: {'passed': 11} rc=0
- `clues`: {'passed': 11} rc=0

| fact | `pristine` | `naive` | `oracle` | `clues` | verdict |
|---|---|---|---|---|---|
| `g1.open_feature` | fail | pass | pass | pass | open_feature |
| `g1.r1.rule` | fail | fail | pass | pass | hidden |
| `g1.r1.scope` | fail | fail | pass | pass | hidden |
| `g1.r1.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g1.r1.failure_behavior` | fail | fail | pass | pass | hidden |
| `g1.r1.observability` | fail | fail | pass | pass | hidden |
| `g1.r2.rule` | fail | fail | pass | pass | hidden |
| `g1.r2.scope` | fail | fail | pass | pass | hidden |
| `g1.r2.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g1.r2.failure_behavior` | fail | fail | pass | pass | hidden |
| `g1.r2.observability` | fail | fail | pass | pass | hidden |

**Ships:** yes
