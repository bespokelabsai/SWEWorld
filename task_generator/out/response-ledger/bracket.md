# Bracket — g5 (response-ledger)

- `pristine`: {'failed': 9} rc=1
- `naive`: {'failed': 1, 'passed': 8} rc=1
- `oracle`: {'passed': 9} rc=0
- `spec`: {'passed': 9} rc=0

| fact | `pristine` | `naive` | `oracle` | `spec` | verdict |
|---|---|---|---|---|---|
| `g5.open_feature` | fail | pass | pass | pass | open_feature |
| `g5.r1.rule` | fail | pass | pass | pass | **coincidence** |
| `g5.r1.scope` | fail | pass | pass | pass | **coincidence** |
| `g5.r1.exclusions_or_crossover` | fail | pass | pass | pass | **coincidence** |
| `g5.r1.observability` | fail | fail | pass | pass | hidden |
| `g5.r2.rule` | fail | pass | pass | pass | **coincidence** |
| `g5.r2.scope` | fail | pass | pass | pass | **coincidence** |
| `g5.r2.exclusions_or_crossover` | fail | pass | pass | pass | **coincidence** |
| `g5.r2.observability` | fail | pass | pass | pass | **coincidence** |

**Ships:** no
- g5.r1.rule: coincidence
- g5.r1.scope: coincidence
- g5.r1.exclusions_or_crossover: coincidence
- g5.r2.rule: coincidence
- g5.r2.scope: coincidence
- g5.r2.exclusions_or_crossover: coincidence
- g5.r2.observability: coincidence
