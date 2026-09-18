#!/bin/bash
# Task setup. Runs as root from the healthcheck, repeatedly, before the agent
# starts — so it must be idempotent and must return fast once it has run.
set -uo pipefail
MARK=/opt/world-state/task-setup.done
[[ -f "$MARK" ]] && exit 0

install -d -m 0700 /opt/world-state

# The agent's git identity. `useradd -m ubuntu` leaves a bare home, and the world
# sets user.name/user.email only inside the repos it bootstraps as root -- while
# the ticket tells the agent "Nothing is checked out for you. Clone it." So its
# FIRST commit, every run, is
#
#     Author identity unknown ... fatal: unable to auto-detect email address
#
# Three of ten rollouts in one g6 evaluation hit it. Two had turns left and set
# it themselves; the third hit it at message 389 of a 401-message cap with the
# whole change written and staged, committed nothing, and scored 0.07 against a
# median of 0.91. run_suites.py grades a clean clone of pushed `main`, so a
# commit that never happens zeroes every requirement fact as well as provenance
# -- the friction does not cost a fraction of a score, it costs the whole run.
#
# Ahead of the BASE_SHA block below on purpose: that block exits 1 to be retried
# on the next probe, and an identity written after it would not land until Gitea
# answers. core.pager because git opens `less` on a tmux terminal and an agent
# that lands in the pager spends turns getting out of it.
#
# Warn rather than fail. This is a convenience the trial grades fine without, and
# failing the healthcheck over it would burn all 20 retries on a healthy world --
# the failing guard reporting as the thing it guards. `git config --global` still
# overrides it for an agent that sets its own.
cat > /home/ubuntu/.gitconfig <<'GITCONFIG'
[user]
    name = worldadmin
    email = worldadmin@world.local
[core]
    pager = cat
GITCONFIG
chown ubuntu:ubuntu /home/ubuntu/.gitconfig 2>/dev/null
chmod 0644 /home/ubuntu/.gitconfig 2>/dev/null
grep -q 'worldadmin@world.local' /home/ubuntu/.gitconfig 2>/dev/null || \
  echo "task-setup: ubuntu has no git identity -- its first commit will fail" >&2

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
    python3 "$S/$step.py" --data-dir /opt/task-plant >>/opt/world-state/task-plant.log 2>&1       || { echo "task-plant: $step failed, see /opt/world-state/task-plant.log" >&2; exit 1; }
  done
  # ingest_chat stages its import archive in /opt/mattermost/data/import and
  # Mattermost keeps it after the job succeeds: a 0644 zip whose import.jsonl is
  # every planted message's text, in a directory the agent can read. Locking
  # /opt/task-plant does nothing about that second copy. Safe here because
  # ingest_chat blocks on the import job before returning, and the glob also
  # clears whatever the base image's own bake left behind.
  rm -f /opt/mattermost/data/import/*.zip
  # maddy stores every message body as a plain file under messages/ and indexes
  # them in a world-readable SQLite db, so `grep -r /var/lib/world/maddy` returns
  # the planted mail in full without ever opening IMAP. That is the same shortcut
  # as a readable /opt/task-plant, one directory over: with the plant locked, this
  # was the ONLY path a filesystem-wide grep as the agent still found. maddy runs
  # as worldsvc and owns all of it, so 0640/0750 costs it nothing -- login, BODY
  # search and fetch all verified after -- and Roundcube reaches mail over IMAP,
  # not the disk. Done here rather than in world/bootstrap because the base image
  # is published and old, exactly like the PLANT_JOIN guard below. SQLite gives a
  # recreated -wal/-shm the mode of the db file, so it survives a restart.
  chmod 0750 /var/lib/world/maddy/messages 2>/dev/null
  chmod 0640 /var/lib/world/maddy/*.db /var/lib/world/maddy/*.db-wal \
             /var/lib/world/maddy/*.db-shm 2>/dev/null
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
  python3 - <<'PLANT_JOIN' >>/opt/world-state/task-plant.log 2>&1 ||     echo "task-plant: admin channel-join guard failed, chat search may be blind" >&2
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
  echo "task-plant: ingested" >> /opt/world-state/task-plant.log
  # Now that every row is in the services, the plaintext plant has done its job
  # and is only an answer key left on disk. 0700 kept the `ubuntu` agent out of
  # it, but the benchmark's threat model is an agent with root, and root reads
  # a 0700 directory as easily as anything. Gone from the running container, a
  # root agent has to find the remarks where everyone else does -- in chat, the
  # wiki and mail -- among the rest of the corpus. Only after success: a failed
  # step above exits for the next probe to retry, and that retry needs the plant.
  # The image's COPY layer still holds it; nothing inside the container can read
  # a lower layer once the file is removed from the merged view.
  rm -rf /opt/task-plant
fi

touch "$MARK"
exit 0
