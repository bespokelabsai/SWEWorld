# Bracket — g4 (run-cache-identity)

- `pristine`: {'failed': 9} rc=1
- `naive`: {'failed': 8, 'passed': 1} rc=1
- `oracle`: {'passed': 9} rc=0
- `spec`: {'passed': 9} rc=0

| fact | `pristine` | `naive` | `oracle` | `spec` | verdict |
|---|---|---|---|---|---|
| `g4.open_feature` | fail | pass | pass | pass | open_feature |
| `g4.r1.rule` | fail | fail | pass | pass | hidden |
| `g4.r1.scope` | fail | fail | pass | pass | hidden |
| `g4.r1.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g4.r1.observability` | fail | fail | pass | pass | hidden |
| `g4.r2.rule` | fail | fail | pass | pass | hidden |
| `g4.r2.scope` | fail | fail | pass | pass | hidden |
| `g4.r2.failure_behavior` | fail | fail | pass | pass | hidden |
| `g4.r2.observability` | fail | fail | pass | pass | hidden |

**Ships:** yes
