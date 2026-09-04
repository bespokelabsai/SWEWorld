# Bracket — g8 (attachment-payload)

- `pristine`: {'failed': 10} rc=1
- `naive`: {'failed': 8, 'passed': 2} rc=1
- `oracle`: {'passed': 10} rc=0
- `spec`: {'passed': 10} rc=0

| fact | `pristine` | `naive` | `oracle` | `spec` | verdict |
|---|---|---|---|---|---|
| `g8.open_feature` | fail | pass | pass | pass | open_feature |
| `g8.r1.rule` | fail | fail | pass | pass | hidden |
| `g8.r1.scope` | fail | fail | pass | pass | hidden |
| `g8.r1.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g8.r1.failure_behavior` | fail | fail | pass | pass | hidden |
| `g8.r1.observability` | fail | fail | pass | pass | hidden |
| `g8.r2.rule` | fail | fail | pass | pass | hidden |
| `g8.r2.scope` | fail | fail | pass | pass | hidden |
| `g8.r2.failure_behavior` | fail | pass | pass | pass | **coincidence** |
| `g8.r2.observability` | fail | fail | pass | pass | hidden |

**Ships:** no
- g8.r2.failure_behavior: coincidence
