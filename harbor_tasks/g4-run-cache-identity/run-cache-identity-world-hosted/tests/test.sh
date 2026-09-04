#!/usr/bin/env bash
# Harbor verifier entrypoint. Executed directly rather than through `bash`, as
# root, from the image's own WORKDIR — so the shebang, the execute bit and the
# absolute paths below all matter.
set -uo pipefail

mkdir -p /logs/verifier

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
