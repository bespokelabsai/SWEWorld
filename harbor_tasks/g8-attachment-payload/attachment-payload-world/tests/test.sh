#!/usr/bin/env bash
# Harbor verifier entrypoint. Executed directly rather than through `bash`, as
# root, from the image's own WORKDIR — so the shebang, the execute bit and the
# absolute paths below all matter.
set -uo pipefail

mkdir -p /logs/verifier
# 0700: score.py treats junit.xml and provenance.json found here as
# authoritative, and run_suites.py drops privileges to import agent code. The
# directory the verdict is assembled in must not be reachable by the uid that
# runs the submission. mkdir's default 0755 was.
chmod 0700 /logs/verifier

# Open /tests to the grading group, read-only, and only now -- the agent's
# phase is over, so nothing it runs can still read the answer key. run_suites.py
# runs pytest as nobody:nogroup and that child must import this directory
# without being able to write it; at Harbor's root-owned 0700 it could do
# neither. `o-rwx` keeps uid 1000 out either way.
# How visible /tests is to the grading child depends on HOW this task grades.
#
# A worker/judge SPLIT suite (this task's suite ships probe.py+judge.py) runs its
# worker from a root-staged JAIL (run_suites.run_split) and never reads /tests. So
# keep /tests ROOT-ONLY: the worker -- the one process that runs agent code --
# then cannot open() ANY answer file by absolute path. That is the whole fix.
# Locking individual files (judge.py, test_r*.py) did NOT work, because the
# answers also live in files the worker reaches: /tests/task.json states every
# expected value in prose, and test_open.py's source carries the answer literals.
# Root-only /tests removes the entire class at once. provenance.py / run_suites.py
# / score.py / judge.py all run as root and read /tests fine.
#
# A NON-split suite runs pytest as nobody FROM /tests and must keep it
# group-readable (that path's in-process forgery is the separate,
# provenance-mitigated case run_suites documents).
#
# Both halves FAIL CLOSED. A lock that did not take, or a task.json nobody could
# read, used to print a warning and carry on -- and the second fell into the
# branch below, opening every answer file to the grading group. No reward is
# better than a reward the submission could have read the answers for.
SUITE=$(python3 -c 'import json;print(json.load(open("/tests/task.json"))["suite"])' 2>/dev/null || echo "")
if [ -z "$SUITE" ] || [ ! -d "/tests/$SUITE" ]; then
  echo "FATAL: cannot tell which suite grades this task from /tests/task.json; not grading" >&2
  exit 1
fi
if [ -f "/tests/$SUITE/probe.py" ] && [ -f "/tests/$SUITE/judge.py" ]; then
  if ! { chown -R root:root /tests && chmod -R go-rwx /tests; }; then
    echo "FATAL: could not lock /tests to root-only; not grading" >&2
    exit 1
  fi
else
  chgrp -R nogroup /tests 2>/dev/null && chmod -R g+rX,o-rwx /tests 2>/dev/null     || echo "WARNING: could not open /tests to the grading group" >&2
fi

# provenance.py FIRST, and it must stay first. /etc/sweworld/gitea-token is
# 0644 by design, so the unprivileged pytest child can also push to Gitea and
# start a CI run; provenance is only unforgeable because it has already been
# measured and written somewhere that child cannot reach by the time the
# submission is imported.
# Both halves run whatever happened, and neither gates the other. That split is
# the point: "wrote it right but never deployed" and "deployed something that
# misses the hidden requirement" are different failures, and a single reward
# would report them identically.
python3 /tests/provenance.py
"${CURATOR_VENV:-/opt/curator-dev/venv}/bin/python" /tests/run_suites.py

# score.py is the only thing that writes rewards.json, so a crash in either of
# the two above still leaves every key present and zero.
python3 /tests/score.py

# Always exit 0: the reward file is the verdict. A non-zero exit here reads as a
# broken harness rather than a failed task.
exit 0
