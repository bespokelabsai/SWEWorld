# Can the clues alone build g1?

**7 of 11** facts score against a tree built from the ticket and the planted remarks and nothing else, on every one of 3 build(s).

Read the grid, not the total. Facts that fail *together*, on the same runs, are one defect in one remark — not variance, and not one problem each. Find it before sampling again.

| fact | #1 | #2 | #3 | why not |
|---|---|---|---|---|
| `g1.open_feature` | ok | ok | ok |  |
| `g1.r1.exclusions_or_crossover` | **FAIL** | ok | **FAIL** | Failed: the batch_plan.json sidecar is not implemented, so the constraint that goes with it cannot be cre... |
| `g1.r1.failure_behavior` | ok | ok | ok |  |
| `g1.r1.observability` | **FAIL** | ok | **FAIL** | AttributeError: module 'bespokelabs.curator.request_processor.batch_payload_planner' has no attrib... |
| `g1.r1.rule` | **FAIL** | ok | **FAIL** | AssertionError: batch_payload_planner does not export PLAN_FILE_NAME; it has ['BatchLimits', 'BatchPayloadT... |
| `g1.r1.scope` | **FAIL** | ok | **FAIL** | AssertionError: the "auto" branch wrote no plan sidecar |
| `g1.r2.exclusions_or_crossover` | ok | ok | ok |  |
| `g1.r2.failure_behavior` | ok | ok | ok |  |
| `g1.r2.observability` | ok | ok | ok |  |
| `g1.r2.rule` | ok | ok | ok |  |
| `g1.r2.scope` | ok | ok | ok |  |

A failure here is a defect in the plant, not in the agent: the same suite scores 11 of 11 against the oracle, which was built from the specification these remarks are supposed to carry.
