# Can the clues alone build g6?

**7 of 8** facts score against a tree built from the ticket and the planted remarks and nothing else, on every one of 3 build(s).

Read the grid, not the total. Facts that fail *together*, on the same runs, are one defect in one remark — not variance, and not one problem each. Find it before sampling again.

| fact | #1 | #2 | #3 | why not |
|---|---|---|---|---|
| `g6.open_feature` | ok | ok | ok |  |
| `g6.r1.exclusions_or_crossover` | ok | ok | ok |  |
| `g6.r1.observability` | ok | ok | ok |  |
| `g6.r1.rule` | ok | ok | ok |  |
| `g6.r2.exclusions_or_crossover` | ok | ok | ok |  |
| `g6.r2.observability` | ok | **FAIL** | ok | assert 0.0 == 4.0 ± 4.0e-06 |
| `g6.r2.rule` | ok | ok | ok |  |
| `g6.r2.scope` | ok | ok | ok |  |

A failure here is a defect in the plant, not in the agent: the same suite scores 11 of 11 against the oracle, which was built from the specification these remarks are supposed to carry.
