#!/bin/bash
# Reference solution for the smoke task, run by `harbor run -a oracle`.
#
# Unlike the four real tasks, this one has a real implementation — and that is
# the point of the task existing. It walks every step an agent has to walk
# (clone from Gitea, edit, commit, push to main, wait for CI, wait for the
# deploy to flip `current`), so a green oracle run proves the environment, the
# push path, the runner, the deploy daemon, the verifier venv and the
# junit-to-rewards mapping all work — before a single token is spent on Opus.
#
# Runs as `ubuntu`: no sudo, no supervisorctl, nothing under /opt writable. If
# this script needs a privilege the agent does not have, the task is wrong.
set -uo pipefail

GITEA=http://127.0.0.1:3300
REPO=worldadmin/curator
WORK=$(mktemp -d)

echo "== waiting for the world =="
wait-for-service --quiet gitea || true

echo "== cloning =="
TOKEN=$(cat /etc/sweworld/gitea-token 2>/dev/null || echo worldadmin)
git clone --quiet "http://worldadmin:${TOKEN}@127.0.0.1:3300/${REPO}.git" "$WORK/curator" || {
  echo "clone failed"; exit 1; }
cd "$WORK/curator" || exit 1

git config user.email worldadmin@world.local
git config user.name  "World Admin"

echo "== the change =="
INIT=src/bespokelabs/curator/__init__.py
cat >> "$INIT" <<'PY'


def world_check() -> str:
    """Smoke check for the world's tooling. Returns a fixed string."""
    return "sweworld ok"
PY

# Re-export only if __all__ exists; appending to a package's __init__ already
# puts the name on the package root, and editing an __all__ that is not there
# would break the import this is meant to prove.
if grep -q "^__all__" "$INIT"; then
  python3 - "$INIT" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
s = re.sub(r"(__all__\s*=\s*\[)", r'\1"world_check", ', s, count=1)
open(p, "w").write(s)
PY
fi

git add -A
git commit --quiet -m "Add world_check() smoke helper" || { echo "nothing to commit"; exit 1; }

echo "== pushing to main =="
git push --quiet origin HEAD:main || { echo "push failed"; exit 1; }
SHA=$(git rev-parse HEAD)
# deploy-service names a release <timestamp>-<sha> using the SHORT sha CI
# handed it, so polling for the full one never matches and this loop would
# burn its whole budget on a deploy that had already landed.
SHORT=$(git rev-parse --short HEAD)
echo "pushed $SHA ($SHORT)"

echo "== waiting for the deploy to pick it up =="
# request-deploy is the last CI step and blocks until the daemon answers, so the
# release usually flips within ~30s of the push. Poll rather than sleep: a fixed
# wait is either too short on a loaded host or wasted time on an idle one.
for _ in $(seq 1 40); do
  CUR=$(readlink -f /opt/sweworld/curator/current 2>/dev/null || echo "")
  case "$CUR" in
    *"$SHORT") echo "deployed: $CUR"; exit 0 ;;
  esac
  sleep 5
done

echo "warning: current still $(readlink -f /opt/sweworld/curator/current 2>/dev/null)"
echo "the code is pushed; provenance.deployed will say whether CI got there"
exit 0
