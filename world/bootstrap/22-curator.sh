#!/usr/bin/env bash
# Build-time: import the vendored curator snapshot into Gitea.
#
# The tie to GitHub was severed once, when the snapshot was made — the tarball
# holds no .git, no origin and no upstream history. Nothing here reaches the
# network, and the same tarball produces the same tree on every build. See
# vendor/README.md for the pinned commit and how to refresh it.
#
# `git init` then gives it a fresh repository with one "Initial import" commit.
# That commit is the baseline; when the generated history is ready,
# scripts/ingest_git.py force-pushes a rewritten history over this branch.
set -euo pipefail
DOMAIN="${WORLD_DOMAIN:-world.local}"
ADMIN_USER="${WORLD_ADMIN_USER:-worldadmin}"
TOKEN="${WORLD_GITEA_TOKEN:?WORLD_GITEA_TOKEN is required}"
GITEA_URL="http://127.0.0.1:3300"
SRC=/opt/world-state/input/curator
SNAPSHOT="/vendor/${CURATOR_SNAPSHOT:?CURATOR_SNAPSHOT is required}"

[ -f "$SNAPSHOT" ] || {
  echo "22-curator: $SNAPSHOT not found — the CURATOR_SNAPSHOT arg in" \
       "world/Dockerfile must name a file that exists in vendor/" >&2
  exit 1
}

install -d -m 755 "$SRC"
tar -xzf "$SNAPSHOT" -C "$SRC"

curl -sf -X POST "$GITEA_URL/api/v1/user/repos" \
  -H "Authorization: token ${TOKEN}" -H "Content-Type: application/json" \
  -d '{"name":"curator","private":false,"auto_init":false,"default_branch":"main"}' >/dev/null

cd "$SRC"
git init -q -b main
git config user.name  "World Admin"
git config user.email "${ADMIN_USER}@${DOMAIN}"
git add -A
git commit -q -m "Initial import"
git remote add origin "http://${ADMIN_USER}:${TOKEN}@127.0.0.1:3300/${ADMIN_USER}/curator.git"
git push -q -u origin main

# Seed the CI workflow so a push builds, tests and deploys through the
# root deploy-daemon — the only path code has into a running service.
install -d .gitea/workflows
cp /world-src/ci-templates/python.yml .gitea/workflows/ci.yml
git add .gitea && git commit -q -m "Add CI workflow"
git push -q origin main

# Assert: gitea clears a repository's `is_empty` flag *after* the push returns,
# and only reconsiders it when a push creates the default branch. So if the
# build tears gitea down before that lands, the repo is "empty" forever — and an
# empty repo is never scanned for workflows, so CI silently never fires on any
# future push. Everything else still looks right: the commits are there, the
# clone works, world-verify passes.
#
# This is the last push before gitea is stopped, which makes it the one exposed.
# The two network clones this script used to do gave gitea seconds of incidental
# slack; vendoring removed them and the race surfaced immediately. Waiting on the
# observable state is the fix — the old margin was luck, not design.
for _ in $(seq 1 30); do
  empty=$(curl -sf -H "Authorization: token ${TOKEN}" \
            "$GITEA_URL/api/v1/repos/${ADMIN_USER}/curator" \
          | python3 -c 'import json,sys; print(json.load(sys.stdin)["empty"])' 2>/dev/null || echo "?")
  [ "$empty" = "False" ] && break
  sleep 1
done
[ "$empty" = "False" ] || {
  echo "22-curator: gitea still reports curator as empty after 30s — workflow" \
       "detection would never run and CI would never fire" >&2
  exit 1
}

# The first release: deploy-service expects /opt/sweworld/curator/current to
# exist so the service has something to run before any CI deploy happens.
rel=/opt/sweworld/curator/releases/00000000000000-initial
install -d -m 755 "$rel"
rsync -a --exclude '.git' "$SRC"/ "$rel"/
install -m 755 /world-src/config/curator-run.sh "$rel/run.sh"
ln -sfn "$rel" /opt/sweworld/curator/current
ln -sfn "$rel" /opt/sweworld/curator/last-good
chown -R svc:svc /opt/sweworld/curator

echo "22-curator: OK (${CURATOR_SNAPSHOT} -> $(git -C "$SRC" rev-parse --short HEAD))"
