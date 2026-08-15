#!/usr/bin/env bash
# Boot one-shot (supervisord priority 1). Idempotent.
#
# Two jobs:
#
#   1. Write the *.world.local vhost entries into /etc/hosts. This cannot be
#      baked at image build because docker bind-mounts /etc/hosts at run time.
#
#   2. If PUBLIC_HOST is set, re-point each app's public base URL at
#      http://$PUBLIC_HOST:<port> so the world is browsable from outside the
#      container.
#
# Why (2) is needed: nginx routes by Host header, so reaching the world from
# another machine means either resolving *.world.local there, or hitting each
# service on its own published port. The second needs no DNS or hosts file, but
# Gitea, Mattermost and BookStack all generate absolute links from a configured
# base URL — leave those pointing at world.local and every link, redirect and
# asset breaks the moment you browse via localhost.
set -euo pipefail
DOMAIN="${WORLD_DOMAIN:-world.local}"

# Per-service ports, published by `make run`.
GITEA_PORT=3300
MATTERMOST_PORT=8065
BOOKSTACK_PORT=8090
ROUNDCUBE_PORT=8080
PASSSTORE_PORT=8250

if ! grep -q "sweworld vhosts" /etc/hosts 2>/dev/null; then
  {
    echo "# sweworld vhosts"
    echo "127.0.0.1 ${DOMAIN} git.${DOMAIN} chat.${DOMAIN} docs.${DOMAIN} mail.${DOMAIN} pass.${DOMAIN} curator.${DOMAIN} mx.${DOMAIN}"
  } >> /etc/hosts
fi

install -d -m 755 /run/php /run/mysqld /run/maddy
chown worldsvc:worldsvc /run/maddy 2>/dev/null || true
chown mysql:mysql /run/mysqld 2>/dev/null || true
install -d -m 755 /var/log/supervisor

if [[ -n "${PUBLIC_HOST:-}" ]]; then
  echo "init-runtime: PUBLIC_HOST=${PUBLIC_HOST} — repointing public base URLs"

  # Gitea: ROOT_URL drives every generated link and the clone URL.
  sed -i "s|^ROOT_URL = .*|ROOT_URL = http://${PUBLIC_HOST}:${GITEA_PORT}/|" /etc/gitea/app.ini
  sed -i "s|^DOMAIN = .*|DOMAIN = ${PUBLIC_HOST}|"                          /etc/gitea/app.ini

  # Mattermost: a SiteURL that does not match what the browser used breaks
  # websockets and permalinks.
  python3 - "$MATTERMOST_PORT" "$PUBLIC_HOST" <<'PY'
import json, sys
port, host = sys.argv[1], sys.argv[2]
path = "/opt/mattermost/config/config.json"
with open(path) as f:
    cfg = json.load(f)
cfg["ServiceSettings"]["SiteURL"] = f"http://{host}:{port}"
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PY
  chown worldsvc:worldsvc /opt/mattermost/config/config.json

  # BookStack: APP_URL. Laravel caches config, so clear it or the old URL wins.
  sed -i "s|^APP_URL=.*|APP_URL=http://${PUBLIC_HOST}:${BOOKSTACK_PORT}|" /opt/bookstack/.env
  (cd /opt/bookstack && php artisan config:clear >/dev/null 2>&1) || true

  # The credentials page is static, so rewrite the URLs it advertises.
  if [[ -f /opt/world/passstore/index.html ]]; then
    sed -i \
      -e "s|http://git\.${DOMAIN}|http://${PUBLIC_HOST}:${GITEA_PORT}|g" \
      -e "s|http://chat\.${DOMAIN}|http://${PUBLIC_HOST}:${MATTERMOST_PORT}|g" \
      -e "s|http://docs\.${DOMAIN}|http://${PUBLIC_HOST}:${BOOKSTACK_PORT}|g" \
      -e "s|http://mail\.${DOMAIN}|http://${PUBLIC_HOST}:${ROUNDCUBE_PORT}|g" \
      /opt/world/passstore/index.html
  fi

  cat <<EOF
init-runtime: the world is reachable at
    Gitea       http://${PUBLIC_HOST}:${GITEA_PORT}
    Mattermost  http://${PUBLIC_HOST}:${MATTERMOST_PORT}
    BookStack   http://${PUBLIC_HOST}:${BOOKSTACK_PORT}
    Roundcube   http://${PUBLIC_HOST}:${ROUNDCUBE_PORT}
    Credentials http://${PUBLIC_HOST}:${PASSSTORE_PORT}
EOF
fi

echo "init-runtime: ready"
