# Bracket — g2 (executor-output-cap)

- `pristine`: {'failed': 10} rc=1
- `naive`: {'failed': 5, 'passed': 5} rc=1
- `oracle`: {'passed': 10} rc=0

| fact | `pristine` | `naive` | `oracle` | verdict |
|---|---|---|---|---|
| `g2.open_feature` | fail | pass | pass | open_feature |
| `g2.r1.rule` | fail | fail | pass | hidden |
| `g2.r1.scope` | fail | fail | pass | hidden |
| `g2.r1.exclusions_or_crossover` | fail | pass | pass | **coincidence** |
| `g2.r1.failure_behavior` | fail | fail | pass | hidden |
| `g2.r1.observability` | fail | fail | pass | hidden |
| `g2.r2.rule` | fail | pass | pass | **coincidence** |
| `g2.r2.scope` | fail | pass | pass | **coincidence** |
| `g2.r2.exclusions_or_crossover` | fail | pass | pass | **coincidence** |
| `g2.r2.observability` | fail | fail | pass | hidden |

**Ships:** no
- g2.r1.exclusions_or_crossover: coincidence
- g2.r2.rule: coincidence
- g2.r2.scope: coincidence
- g2.r2.exclusions_or_crossover: coincidence
