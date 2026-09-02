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
  # The services the ingest actually talks to. The healthcheck only waits for
  # gitea -- that is all the baseline setup needed, to read main's SHA -- and
  # ingesting into Mattermost, BookStack and maddy before they answer fails,
  # returns non-zero, and fails the healthcheck. Twenty times, then the trial is
  # dead with "Healthcheck failed after 20 consecutive retries" and nothing saying
  # which of the four services was the problem.
  # These exact names. `wait-for-service` takes the world's own service list
  # and exits 1 on anything else -- `php-fpm` is a supervisord program but not
  # a name it knows, so naming it made this line fail every time, setup.sh
  # exit 1, and the healthcheck burn all 20 retries against a world that was
  # healthy throughout. The failing guard reported as the thing it guarded.
  WAIT_TIMEOUT=240 wait-for-service --quiet mattermost mariadb bookstack maddy     || { echo "task-plant: services not up" >&2; exit 1; }
  # The roster comes from the WORLD, not the plant. The ingest scripts resolve
  # every author and channel through channels.yaml and identities.yaml in the
  # --data-dir they are given, and a delta that ships its own copy is a second
  # source of truth that drifts the moment the corpus is rebuilt. Without them
  # every row fails with "unknown channel 'releases' -- declared channels: (none)".
  for roster in channels.yaml identities.yaml; do
    cp -f "/opt/world-state/data/$roster" "/opt/task-plant/$roster" 2>/dev/null || {
      echo "task-plant: no /opt/world-state/data/$roster" >&2; exit 1; }
  done
  # Comments attach to pages, and `ingest_comments` resolves each one against the
  # docs/ tree in its --data-dir; without it the run dies on "/opt/task-plant/docs
  # does not exist" even though every page it needs is already in the world. A
  # delta that adds no new pages therefore borrows the world's, read-only. If the
  # plant brought its own pages, those win and this does nothing.
  if [[ -e /opt/task-plant/docs ]]; then
    # The plant brought its own pages, so it needs the book list that says which
    # directories are real: "directory 'engineering' has no entry in
    # collections.yaml -- unlisted directories are an error, not an implicit book".
    # Same principle as the roster above -- structure comes from the world.
    cp -f /opt/world-state/data/docs/collections.yaml /opt/task-plant/docs/ 2>/dev/null
    # And the existing pages, because a comment resolves against the whole tree
    # and most of this plant's comments hang off pages the world already has.
    cp -rn /opt/world-state/data/docs/. /opt/task-plant/docs/ 2>/dev/null
  else
    ln -s /opt/world-state/data/docs /opt/task-plant/docs
  fi
  S=/opt/world-state/scripts
  # Each step only when the plant has something for it. A delta rarely touches all
  # four surfaces -- g2 has chat, mail and page comments and no new wiki pages at
  # all -- and `ingest_docs` against a missing docs/ does not no-op, it fails with
  # "524 validation error(s)" and takes the healthcheck down with it.
  for step in ingest_chat ingest_docs ingest_comments ingest_mail; do
    [[ -f "$S/$step.py" ]] || continue
    case "$step" in
      ingest_chat)     [[ -s /opt/task-plant/messages.jsonl ]] || continue ;;
      ingest_docs)     [[ -d /opt/task-plant/docs ]]           || continue ;;
      ingest_comments) [[ -s /opt/task-plant/comments.jsonl ]] || continue ;;
      ingest_mail)     [[ -d /opt/task-plant/emails ]]         || continue ;;
    esac
    python3 "$S/$step.py" --data-dir /opt/task-plant >>/var/log/task-plant.log 2>&1       || { echo "task-plant: $step failed, see /var/log/task-plant.log" >&2; exit 1; }
  done
  # Mattermost search is MEMBER-SCOPED, and the admin is created by bootstrap
  # rather than by the import, so it lands in Mattermost's defaults --
  # town-square and off-topic, both empty. An agent handed those credentials
  # searches a 9,800-message corpus and gets zero hits for every term in it,
  # then reasonably concludes there is no chat to read. Both g2 hosted world
  # rollouts did exactly that: five terms certainly present, nothing back, and
  # every hidden fact scored 0 in a world that physically contained them.
  #
  # `ingest_chat.join_admin_to_channels()` fixes this at the source, but the
  # script that runs here is the one baked into the IMAGE
  # (/opt/world-state/scripts), not the one this task was built against, so a
  # base image published before that fix ingests the new plant with the old
  # script and silently undoes it. This is the guard that does not care how old
  # the image is. It is idempotent -- adding an existing member is a no-op --
  # so it costs nothing on a world that already got it right.
  python3 - <<'PLANT_JOIN' >>/var/log/task-plant.log 2>&1 ||     echo "task-plant: admin channel-join guard failed, chat search may be blind" >&2
import json, urllib.request

BASE = "http://localhost:8065/api/v4"

def call(path, data=None, token=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    resp = urllib.request.urlopen(req, timeout=30)
    return resp, json.loads(resp.read() or b"null")

# The session token comes back as a HEADER, not in the body -- four calls of one
# hosted rollout went on parsing `.token` out of the JSON and getting "".
resp, me = call("/users/login", {"login_id": "worldadmin", "password": "worldadmin"})
token = resp.headers.get("Token")
if not token:
    raise SystemExit("no Token header from /users/login")

joined = 0
_, teams = call("/users/me/teams", token=token)
for team in teams:
    page = 0
    while True:
        _, chans = call(f"/teams/{team['id']}/channels?per_page=200&page={page}",
                        token=token)
        if not chans:
            break
        for chan in chans:
            # Open channels only. A private channel the admin was never in is not
            # something to force an entry into, and DMs have no team.
            if chan.get("type") != "O":
                continue
            try:
                call(f"/channels/{chan['id']}/members", {"user_id": me["id"]},
                     token=token)
                joined += 1
            except Exception:
                pass          # already a member, which is the common case
        page += 1
print(f"task-plant: admin in {joined} channel(s)")
PLANT_JOIN
  echo "task-plant: ingested" >> /var/log/task-plant.log
fi

touch "$MARK"
exit 0
