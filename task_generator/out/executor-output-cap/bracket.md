# Bracket — g2 (executor-output-cap)

- `pristine`: {'failed': 10} rc=1
- `naive`: {'failed': 9, 'passed': 1} rc=1
- `oracle`: {'passed': 10} rc=0

| fact | `pristine` | `naive` | `oracle` | verdict |
|---|---|---|---|---|
| `g2.open_feature` | fail | pass | pass | open_feature |
| `g2.r1.rule` | fail | fail | pass | hidden |
| `g2.r1.scope` | fail | fail | pass | hidden |
| `g2.r1.exclusions_or_crossover` | fail | fail | pass | hidden |
| `g2.r1.failure_behavior` | fail | fail | pass | hidden |
| `g2.r1.observability` | fail | fail | pass | hidden |
| `g2.r2.rule` | fail | fail | pass | hidden |
| `g2.r2.scope` | fail | fail | pass | hidden |
| `g2.r2.exclusions_or_crossover` | fail | fail | pass | hidden |
| `g2.r2.observability` | fail | fail | pass | hidden |

**Ships:** yes
