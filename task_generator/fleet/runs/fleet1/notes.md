# Notes fed back into every judge call

Appended by `orchestrate.py note "..."`. Re-read before each
decision, so a lesson learned mid-run reaches the tasks still
running without restarting anything.

## 2026-09-03T18:29:41Z

BASE RATE for the `audit` stage — read this before acting on an audit finding.

`cli.py audit` had never been run on any task before this run. Its Catalog A/B
verdicts are an adversarial PREDICTION, not a measurement, and it has no
calibration behind it. A measured bracket outranks it.

Measured base rates over every task on disk, so a finding can be judged against
what shipped rather than against an ideal:

  * SHARED require_feature GATES ARE NORMAL. g3 SHIPPED with four r1 facts all
    gated on `waivers_are_implemented()` and three r2 facts on
    `horizon_is_implemented()`. g1 has two r2 facts on `swept(tmp_path)` and
    measured spec 1.00 / blind 0.00 with a full world arm. Two facts behind one
    gate is the mild end of the distribution, not a defect.
  * OVERLAPPING ASSERTIONS BETWEEN FACT TESTS ARE NORMAL. g1 shipped with four
    test pairs sharing >30% of their asserted lines; g6 with two pairs at ~37%.

So: do NOT stop on 'the facts are not independent' or 'the audit clears no fact'
alone. Those describe every task in this repo that has shipped. Stop on what the
BRACKET measures — `broken`, `unreachable`, a coincidence, or an unhealthy
naive shape — and let the hosted blind arm at three rollouts settle anything the
free predictors merely disagree about. Reserve `stop` for a defect you can name
in the measurement, not in a prediction.
