# Bracket — g9 (example-encoding)

- `pristine`: {'failed': 8} rc=1
- `naive`: {'failed': 7, 'passed': 1} rc=1
- `oracle`: {'passed': 8} rc=0
- `spec`: {'passed': 8} rc=0

| fact | `pristine` | `naive` | `oracle` | `spec` | verdict |
|---|---|---|---|---|---|
| `g9.open_feature` | fail | pass | pass | pass | open_feature |
| `g9.r1.rule` | fail | fail | pass | pass | hidden |
| `g9.r1.scope` | fail | fail | pass | pass | hidden |
| `g9.r1.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g9.r1.failure_behavior` | fail | fail | pass | pass | hidden |
| `g9.r2.rule` | fail | fail | pass | pass | hidden |
| `g9.r2.scope` | fail | fail | pass | pass | hidden |
| `g9.r2.failure_behavior` | fail | fail | pass | pass | hidden |

**Ships:** yes
