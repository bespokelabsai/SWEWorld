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

# curator lands here too, while gitea is still up.
WORLD_GITEA_TOKEN="$TOKEN" /world-src/bootstrap/22-curator.sh

kill "$gitea_pid" 2>/dev/null || true
wait "$gitea_pid" 2>/dev/null || true
chown -R gitea:gitea /var/lib/world/gitea

echo "20-gitea: OK"
