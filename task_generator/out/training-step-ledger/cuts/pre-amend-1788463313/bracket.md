# Bracket — g11 (training-step-ledger)

- `pristine`: {'failed': 10} rc=1
- `naive`: {'failed': 10} rc=1
- `oracle`: {'passed': 10} rc=0
- `spec`: {'failed': 1, 'passed': 9} rc=1

| fact | `pristine` | `naive` | `oracle` | `spec` | verdict |
|---|---|---|---|---|---|
| `g11.open_feature` | fail | fail | pass | fail | open_feature |
| `g11.r1.rule` | fail | fail | pass | pass | hidden |
| `g11.r1.scope` | fail | fail | pass | pass | hidden |
| `g11.r1.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g11.r1.failure_behavior` | fail | fail | pass | pass | hidden |
| `g11.r1.observability` | fail | fail | pass | pass | hidden |
| `g11.r2.rule` | fail | fail | pass | pass | hidden |
| `g11.r2.exclusions_or_crossover` | fail | fail | pass | pass | hidden |
| `g11.r2.failure_behavior` | fail | fail | pass | pass | hidden |
| `g11.r2.observability` | fail | fail | pass | pass | hidden |

**Ships:** no
- g11.open_feature: the open feature does not pass on naive — a build given only the ticket cannot produce it, so it grades something the ticket does not state and no blind score can be read against it
- g11.open_feature: unreachable — a build given the ticket and the hidden requirements still fails it, so the requirement does not say what the suite grades
