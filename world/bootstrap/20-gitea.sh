#!/usr/bin/env bash
# Build-time: gitea config, admin user, API token, and act_runner registration.
set -euo pipefail
DOMAIN="${WORLD_DOMAIN:-world.local}"
ADMIN_USER="${WORLD_ADMIN_USER:-worldadmin}"
ADMIN_PASS="${WORLD_ADMIN_PASSWORD:-worldadmin}"
ADMIN_MAIL="${WORLD_ADMIN_EMAIL:-worldadmin@${DOMAIN}}"
GITEA_URL="http://127.0.0.1:3300"

install -d -m 755 /etc/gitea
sed -e "s|@@DOMAIN@@|${DOMAIN}|g" /world-src/config/gitea/app.ini > /etc/gitea/app.ini
chown -R gitea:gitea /etc/gitea /var/lib/world/gitea
chmod 640 /etc/gitea/app.ini

gitea_run() { su -s /bin/bash gitea -c "HOME=/var/lib/world/gitea GITEA_WORK_DIR=/var/lib/world/gitea $*"; }

# Start gitea just long enough to create the admin, mint a token and register
# the runner; the image ships with it stopped and supervisord owns it at boot.
gitea_run "gitea web --config /etc/gitea/app.ini" &
gitea_pid=$!
for i in $(seq 1 60); do
  curl -sf "$GITEA_URL/api/v1/version" >/dev/null 2>&1 && break
  sleep 1
done

gitea_run "gitea admin user create --config /etc/gitea/app.ini \
  --username '${ADMIN_USER}' --password '${ADMIN_PASS}' --email '${ADMIN_MAIL}' \
  --admin --must-change-password=false"

TOKEN="$(gitea_run "gitea admin user generate-access-token --config /etc/gitea/app.ini \
  -u '${ADMIN_USER}' --scopes all --token-name world --raw" | tr -d '\r\n ')"
install -d -m 755 /etc/sweworld
printf '%s\n' "$TOKEN" > /etc/sweworld/gitea-token
chmod 644 /etc/sweworld/gitea-token   # the agent legitimately uses the API

# --- act_runner (host-exec mode) ---------------------------------------------
REG_TOKEN="$(gitea_run "gitea --config /etc/gitea/app.ini actions generate-runner-token" | tail -1 | tr -d '\r\n ')"
install -d -o deploy -g deploy /etc/act_runner
install -m 644 /world-src/config/act_runner/config.yaml /etc/act_runner/config.yaml
su -s /bin/bash deploy -c "cd /var/lib/world/act-runner && \
  act_runner register --no-interactive --instance '$GITEA_URL' --token '$REG_TOKEN' \
  --name world-runner --labels host:host --config /etc/act_runner/config.yaml"

# --- mirror actions/checkout so `uses: actions/checkout@v4` resolves offline ---
# DEFAULT_ACTIONS_URL=self makes Gitea look for actions inside its own instance.
# Without this mirror every workflow fails at the checkout step, which surfaces
# only as "task N repo is ..." in the runner log and a failed run in the UI.
# Needs network, which exists at image build time and never again.
api() { curl -sf -H "Authorization: token ${TOKEN}" -H "Content-Type: application/json" "$@"; }
api -X POST -d '{"username":"actions","full_name":"actions"}' "$GITEA_URL/api/v1/orgs" >/dev/null 2>&1 || true
api -X POST -d '{"name":"checkout","private":false,"auto_init":false}' \
    "$GITEA_URL/api/v1/orgs/actions/repos" >/dev/null 2>&1 || true

# Vendored, not mirrored: no network, and the tree is the same on every build.
# Only the v4 tree ships — ci-templates/python.yml names actions/checkout@v4 and
# nothing else, and the action's upstream history is of no use inside the world.
# A workflow naming any other ref fails loudly at resolution; add the ref to
# vendor/ if that ever becomes something the world should support.
SNAPSHOT="/vendor/${ACTIONS_CHECKOUT_SNAPSHOT:?ACTIONS_CHECKOUT_SNAPSHOT is required}"
[ -f "$SNAPSHOT" ] || {
  echo "20-gitea: $SNAPSHOT not found — the ACTIONS_CHECKOUT_SNAPSHOT arg in" \
       "world/Dockerfile must name a file that exists in vendor/" >&2
  exit 1
}
work=$(mktemp -d)
tar -xzf "$SNAPSHOT" -C "$work"
git -C "$work" init -q -b main
git -C "$work" config user.name  "World Admin"
git -C "$work" config user.email "${ADMIN_USER}@${DOMAIN}"
git -C "$work" add -A
git -C "$work" commit -q -m "actions/checkout v4"
git -C "$work" tag v4
git -C "$work" push -q \
    "http://${ADMIN_USER}:${TOKEN}@127.0.0.1:3300/actions/checkout.git" \
    'refs/heads/*:refs/heads/*' 'refs/tags/*:refs/tags/*'
rm -rf "$work"

# Assert: a missing mirror only shows up much later as failed CI runs.
api "$GITEA_URL/api/v1/repos/actions/checkout" >/dev/null \
  || { echo "20-gitea: actions/checkout mirror missing" >&2; exit 1; }

# curator lands here too, while gitea is still up.
WORLD_GITEA_TOKEN="$TOKEN" /world-src/bootstrap/22-curator.sh

kill "$gitea_pid" 2>/dev/null || true
wait "$gitea_pid" 2>/dev/null || true
chown -R gitea:gitea /var/lib/world/gitea

echo "20-gitea: OK"
