#!/bin/bash
# Reference solution, run by `harbor run -a oracle`.
#
# A no-op, because this task has no `fixtures/oracle.patch` to apply — the
# hand-written tasks in data_gen/input/tasks.json carry an `oracle.py` fixture
# used by the bracket instead, and there is no generated diff to push. What the
# `-spec` control proves for those is that the suite can be passed at all.
#
# Running it is still worth something: it proves the image builds, the world
# boots, the verifier runs and the reward file lands. Expect a score of zero.
#
# NOTE this scores 0, and Horizon refuses to schedule an evaluation against a
# task whose oracle does not score ~1.0 ("409 ... evaluation validation gate").
# A task built from task_generator gets the real oracle below and passes; one
# built from tasks.json does not, and cannot be run hosted until it has a patch.
set -uo pipefail
echo "oracle: no reference implementation; this run checks the plumbing only"
exit 0
