#!/usr/bin/env bash
# Build-time: import bespokelabs/curator into Gitea as a clean, standalone copy.
#
# Every tie to GitHub is severed on purpose:
#   --depth 1     never fetch upstream history (we don't want it)
#   rm -rf .git   detach completely — it becomes a plain folder of files
#   git init      fresh repository, one "Initial import" commit, no remote
#
# That single commit is the baseline. When the generated history is ready,
# scripts/ingest_git.py force-pushes a rewritten history over this branch.
set -euo pipefail
DOMAIN="${WORLD_DOMAIN:-world.local}"
ADMIN_USER="${WORLD_ADMIN_USER:-worldadmin}"
TOKEN="${WORLD_GITEA_TOKEN:?WORLD_GITEA_TOKEN is required}"
GITEA_URL="http://127.0.0.1:3300"
SRC=/opt/world-state/input/curator

install -d -m 755 /opt/world-state/input

git clone --depth 1 https://github.com/bespokelabsai/curator.git "$SRC"
rm -rf "$SRC/.git"          # severed: no origin, no upstream history

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

# The first release: deploy-service expects /opt/sweworld/curator/current to
# exist so the service has something to run before any CI deploy happens.
rel=/opt/sweworld/curator/releases/00000000000000-initial
install -d -m 755 "$rel"
rsync -a --exclude '.git' "$SRC"/ "$rel"/
install -m 755 /world-src/config/curator-run.sh "$rel/run.sh"
ln -sfn "$rel" /opt/sweworld/curator/current
ln -sfn "$rel" /opt/sweworld/curator/last-good
chown -R svc:svc /opt/sweworld/curator

echo "22-curator: OK ($(git -C "$SRC" rev-parse --short HEAD))"
