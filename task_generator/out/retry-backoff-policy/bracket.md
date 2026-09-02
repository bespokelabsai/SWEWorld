# Bracket — g3 (retry-backoff-policy)

- `pristine`: {'failed': 10} rc=1
- `naive`: {'failed': 9, 'passed': 1} rc=1
- `oracle`: {'passed': 10} rc=0
- `spec`: {'passed': 10} rc=0

| fact | `pristine` | `naive` | `oracle` | `spec` | verdict |
|---|---|---|---|---|---|
| `g3.open_feature` | fail | pass | pass | pass | open_feature |
| `g3.r1.rule` | fail | fail | pass | pass | hidden |
| `g3.r1.scope` | fail | fail | pass | pass | hidden |
| `g3.r1.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g3.r1.failure_behavior` | fail | fail | pass | pass | hidden |
| `g3.r1.observability` | fail | fail | pass | pass | hidden |
| `g3.r2.rule` | fail | fail | pass | pass | hidden |
| `g3.r2.scope` | fail | fail | pass | pass | hidden |
| `g3.r2.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g3.r2.observability` | fail | fail | pass | pass | hidden |

**Ships:** yes
