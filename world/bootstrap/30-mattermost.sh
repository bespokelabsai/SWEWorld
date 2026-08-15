#!/usr/bin/env bash
# Build-time: mattermost config, admin user, team. Local mode is enabled so
# mmctl (and ingest_chat.py's bulk import) work over a unix socket, no token.
set -euo pipefail
DOMAIN="${WORLD_DOMAIN:-world.local}"
ADMIN_USER="${WORLD_ADMIN_USER:-worldadmin}"
ADMIN_PASS="${WORLD_ADMIN_PASSWORD:-worldadmin}"
ADMIN_MAIL="${WORLD_ADMIN_EMAIL:-worldadmin@${DOMAIN}}"
PG_BIN=/usr/lib/postgresql/16/bin
PGDATA=/var/lib/world/postgres

install -d -m 755 -o worldsvc -g worldsvc /var/lib/world/mattermost \
  /opt/mattermost/data /opt/mattermost/logs /opt/mattermost/config \
  /opt/mattermost/plugins /opt/mattermost/client/plugins
sed -e "s|@@DOMAIN@@|${DOMAIN}|g" /world-src/config/mattermost/config.json \
  > /opt/mattermost/config/config.json
chown -R worldsvc:worldsvc /opt/mattermost

su -s /bin/bash postgres -c "$PG_BIN/pg_ctl -D $PGDATA -o '-c unix_socket_directories=/tmp' -w start" >/dev/null

cd /opt/mattermost
su -s /bin/bash worldsvc -c "HOME=/var/lib/world/mattermost /opt/mattermost/bin/mattermost" &
mm_pid=$!
for i in $(seq 1 120); do
  curl -sf http://127.0.0.1:8065/api/v4/system/ping >/dev/null 2>&1 && break
  sleep 2
done

mmctl() { su -s /bin/bash worldsvc -c "HOME=/var/lib/world/mattermost /opt/mattermost/bin/mmctl --local $*"; }
mmctl "user create --email '${ADMIN_MAIL}' --username '${ADMIN_USER}' --password '${ADMIN_PASS}' --system-admin" || true
mmctl "team create --name world --display-name World --email '${ADMIN_MAIL}'" || true
mmctl "team users add world '${ADMIN_MAIL}'" || true

kill "$mm_pid" 2>/dev/null || true; wait "$mm_pid" 2>/dev/null || true
su -s /bin/bash postgres -c "$PG_BIN/pg_ctl -D $PGDATA -w stop" >/dev/null
chown -R worldsvc:worldsvc /opt/mattermost /var/lib/world/mattermost

echo "30-mattermost: OK"
