#!/bin/bash
# Reference solution, run by `harbor run -a oracle` and by Horizon's validation
# gate — which is why it has to be real. Horizon refuses to schedule any
# evaluation against a task whose oracle does not score ~1.0:
#
#     409 Conflict: One or more tasks are blocked by the evaluation validation gate.
#
# And a real one here means more than applying a patch. `run_suites.py` clones
# and grades **the pushed `main`**, not the working tree, so an oracle that edits
# files and stops scores exactly zero with every test reporting "does not
# import". Pushing IS the solution in this world.
#
# `oracle.patch` beside this script IS the reference implementation: the whole
# change as a diff — the new `retry_policy` module, the base processor's except
# block rewritten on top of it, the three provider blocks that stop counting, and
# the two hidden requirements — maintained with the task so it cannot drift from
# the suite that grades it. It used to be a heredoc
# of a thousand-odd lines, embedded because on the apex arms the sibling file was
# unreadable from the solution's own directory; Harbor copies all of solution/
# and runs this as root, so that reason does not apply here, and a patch buried
# in a shell script is one nobody reviews.
#
# Applying it is not the whole job. The patch is verified against the repository's
# own tests for the modules it touches before anything is published: a reference
# solution that has drifted from the library has to stop here, not land on `main`
# and turn up as a grader reading zero with no clue why.
set -uo pipefail

PATCH="$(dirname "$(readlink -f "$0")")/oracle.patch"
[ -r "$PATCH" ] || { echo "oracle: $PATCH is missing or unreadable"; exit 1; }


REPO_URL="http://worldadmin:worldadmin@git.world.local/worldadmin/curator.git"
WORK="$(mktemp -d)"

# The healthcheck should already have waited for gitea, but the oracle also runs
# in contexts that do not go through it. Cheap when it is already up.
wait-for-service --quiet gitea 2>/dev/null || true

git clone --quiet "$REPO_URL" "$WORK/curator" || { echo "oracle: clone failed"; exit 1; }
cd "$WORK/curator" || exit 1


git apply --whitespace=nowarn "$PATCH" || { echo "oracle: patch did not apply"; exit 1; }

# Prove the patched tree before publishing it: curator's own unit tests for the
# four modules this change touches — the base online processor, the status
# tracker that gains the cooldown horizon, and the openai/litellm processors
# whose rate-limit blocks it deletes. Offline and about eight seconds.
#
# `--noconftest`: tests/conftest.py imports `vcr`, which is not in the world
# venv, and a collection error there reads like the patch broke the library.
# None of the four files below uses a fixture from it. And no
# CURATOR_DISABLE_RICH_DISPLAY: test_online_status_tracker asserts on the
# rendered panel, so suppressing the display fails two tests that have nothing
# to do with this change.
VENV="${CURATOR_VENV:-/opt/curator-dev/venv}"
TESTS="tests/unittests/test_base_online_request_processor.py
tests/unittests/test_online_status_tracker.py
tests/unittests/test_openai_online_request_processor.py
tests/unittests/test_litellm_online_request_processor.py"
# Both of these fail closed with their own message. Letting a missing
# interpreter or a missing test file fall through to the pytest call below would
# report "curator's tests FAIL on the patched tree", which is a different and
# much more alarming thing than "this world does not have them".
[ -x "$VENV/bin/python" ] || { echo "oracle: no interpreter at $VENV/bin/python; cannot verify the patch"; exit 1; }
for t in $TESTS; do
  [ -f "$t" ] || { echo "oracle: $t is not in this checkout; cannot verify the patch"; exit 1; }
done
echo "oracle: running curator's own tests for the touched modules"
if PYTHONPATH="$WORK/curator/src" \
   TELEMETRY_ENABLED=false CURATOR_VIEWER=false \
   HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 COLUMNS=220 \
   OPENAI_API_KEY=sk-oracle ANTHROPIC_API_KEY=sk-oracle \
   "$VENV/bin/python" -m pytest -q -p no:cacheprovider --noconftest $TESTS; then
  echo "oracle: curator's tests pass on the patched tree"
else
  echo "oracle: curator's own tests FAIL on the patched tree; refusing to push"
  exit 1
fi

git config user.email "worldadmin@world.local"
git config user.name  "worldadmin"
git add -A
git commit --quiet -m "Failure-class retry policy for online request processors" || { echo "oracle: nothing to commit"; exit 1; }

# Straight to main when the branch is unprotected; a branch plus an immediately
# merged PR when it is not. The agents that scored provenance 1.0 took the second
# path, so it is known to work in this world — but the first is one round trip and
# the grader only cares that `main` moved.
if git push --quiet origin HEAD:main 2>/dev/null; then
  echo "oracle: pushed straight to main"
else
  BRANCH="oracle/retry-backoff-policy"
  git push --quiet --force origin "HEAD:$BRANCH" || { echo "oracle: push failed"; exit 1; }
  TOKEN="$(cat /etc/sweworld/gitea-token 2>/dev/null)"
  API="http://git.world.local/api/v1/repos/worldadmin/curator"
  NUM=$(curl -sS -X POST -H "Authorization: token $TOKEN" \
        -H 'Content-Type: application/json' "$API/pulls" \
        -d "{\"head\":\"$BRANCH\",\"base\":\"main\",\"title\":\"oracle: retry-backoff-policy\"}" \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("number",""))' 2>/dev/null)
  [ -n "$NUM" ] || { echo "oracle: could not open a PR"; exit 1; }
  curl -sS -X POST -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \
    "$API/pulls/$NUM/merge" -d '{"Do":"merge"}' >/dev/null \
    || { echo "oracle: merge failed"; exit 1; }
  echo "oracle: merged PR #$NUM into main"
fi

# Not required by the score — `score.py` gates the reward on the open feature and
# the nine hidden facts, and leaves provenance ungated (this ticket protects no
# whole file, so there is no protected-file term) — but the deploy takes about
# half a minute here, and
# letting it land means the oracle run also demonstrates ci_green and deployed
# rather than leaving two checks reading zero for no reason.
sleep 45
echo "oracle: done"
exit 0
