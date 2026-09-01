#!/bin/bash
# Reference solution, run by `harbor run -a oracle`.
#
# Deliberately a no-op that exercises the plumbing rather than an implementation.
# A real reference solution here is four curator features and eight hidden
# requirements — days of work — and it is not what proves the tests are
# satisfiable. The `-spec` control does that: it is the same task with the
# requirements written into the ticket, so a real agent passing it is evidence
# the suite can be passed, and a real agent failing the uncontrolled twin is
# then evidence about the requirement rather than about the test.
#
# Running the oracle is still worth it: it proves the image builds, the world
# boots, the verifier runs and the reward file lands. Expect a score of zero.
set -uo pipefail
echo "oracle: no reference implementation; this run checks the plumbing only"
exit 0
