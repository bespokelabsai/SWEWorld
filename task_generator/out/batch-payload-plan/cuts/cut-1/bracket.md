# Bracket — g1 (batch-payload-plan)

- `pristine`: {'failed': 11} rc=1
- `naive`: {'failed': 1, 'passed': 10} rc=1
- `oracle`: {'passed': 11} rc=0

| fact | `pristine` | `naive` | `oracle` | verdict |
|---|---|---|---|---|
| `g1.open_feature` | fail | pass | pass | open_feature |
| `g1.r1.rule` | fail | pass | pass | **coincidence** |
| `g1.r1.scope` | fail | pass | pass | **coincidence** |
| `g1.r1.exclusions_or_crossover` | fail | pass | pass | **coincidence** |
| `g1.r1.failure_behavior` | fail | pass | pass | **coincidence** |
| `g1.r1.observability` | fail | pass | pass | **coincidence** |
| `g1.r2.rule` | fail | pass | pass | **coincidence** |
| `g1.r2.scope` | fail | pass | pass | **coincidence** |
| `g1.r2.exclusions_or_crossover` | fail | pass | pass | **coincidence** |
| `g1.r2.failure_behavior` | fail | fail | pass | hidden |
| `g1.r2.observability` | fail | pass | pass | **coincidence** |

**Ships:** no
- g1.r1.rule: coincidence
- g1.r1.scope: coincidence
- g1.r1.exclusions_or_crossover: coincidence
- g1.r1.failure_behavior: coincidence
- g1.r1.observability: coincidence
- g1.r2.rule: coincidence
- g1.r2.scope: coincidence
- g1.r2.exclusions_or_crossover: coincidence
- g1.r2.observability: coincidence
