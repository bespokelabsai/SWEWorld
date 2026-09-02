#!/bin/bash
# Task setup. Runs as root from the healthcheck, repeatedly, before the agent
# starts — so it must be idempotent and must return fast once it has run.
set -uo pipefail
MARK=/opt/world-state/task-setup.done
[[ -f "$MARK" ]] && exit 0

install -d -m 0700 /opt/world-state

# Record the commit main sat at before the agent touched anything. The grader
# needs it to tell "pushed something" from "pushed nothing": comparing against a
# hardcoded SHA would break the moment the world image is rebaked.
TOKEN=$(cat /etc/sweworld/gitea-token 2>/dev/null || echo "")
BASE=$(curl -fsS -H "Authorization: token $TOKEN" \
  "http://127.0.0.1:3300/api/v1/repos/worldadmin/curator/branches/main" 2>/dev/null \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["commit"]["id"])' 2>/dev/null || echo "")
[[ -n "$BASE" ]] || exit 1        # try again on the next probe

{
  echo "BASE_SHA=$BASE"
  echo "BASE_RELEASE=$(readlink -f /opt/sweworld/curator/current 2>/dev/null || echo none)"
} > /opt/world-state/baseline.env
chmod 0600 /opt/world-state/baseline.env

# The plant, ingested into the RUNNING world rather than baked into the image.
#
# /opt/task-plant holds only what this task adds -- a few dozen messages, a
# handful of comments, some mail and pages -- in the same layout data/ uses. Every
# ingest script takes --data-dir, and Mattermost's bulk import, BookStack's API
# and maddy's delivery are all additive, so this appends to the corpus already
# there instead of replacing it.
#
# Doing it here rather than in a bake is what lets ONE world image serve every
# task. The alternative was `install_corpus.py --apply` plus `make bake-image` per
# task: half an hour, a 7.8GB image, and a tag that then has to be threaded back
# into build_tasks.py so the answer key names the right world.
#
# Order matters and is the same order the bake used: comments need their pages to
# exist first.
if [[ -d /opt/task-plant ]]; then
  S=/opt/world-state/scripts
  for step in ingest_chat ingest_docs ingest_comments ingest_mail; do
    [[ -f "$S/$step.py" ]] || continue
    python3 "$S/$step.py" --data-dir /opt/task-plant >>/var/log/task-plant.log 2>&1       || { echo "task-plant: $step failed, see /var/log/task-plant.log" >&2; exit 1; }
  done
  echo "task-plant: ingested" >> /var/log/task-plant.log
fi

touch "$MARK"
exit 0
