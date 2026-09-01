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

touch "$MARK"
exit 0
