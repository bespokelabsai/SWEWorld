# Bracket — g6 (model-price-lookup)

- `pristine`: {'failed': 8} rc=1
- `naive`: {'failed': 7, 'passed': 1} rc=1
- `oracle`: {'passed': 8} rc=0
- `clues`: {'passed': 8} rc=0
- `spec`: {'passed': 8} rc=0

| fact | `pristine` | `naive` | `oracle` | `clues` | `spec` | verdict |
|---|---|---|---|---|---|---|
| `g6.open_feature` | fail | pass | pass | pass | pass | open_feature |
| `g6.r1.rule` | fail | fail | pass | pass | pass | hidden |
| `g6.r1.exclusions_or_crossover` | fail | fail | pass | pass | pass | hidden |
| `g6.r1.observability` | fail | fail | pass | pass | pass | hidden |
| `g6.r2.rule` | fail | fail | pass | pass | pass | hidden |
| `g6.r2.scope` | fail | fail | pass | pass | pass | hidden |
| `g6.r2.exclusions_or_crossover` | fail | fail | pass | pass | pass | hidden |
| `g6.r2.observability` | fail | fail | pass | pass | pass | hidden |

**Ships:** yes
