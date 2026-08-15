#!/usr/bin/env bash
# Boot one-shot (supervisord priority 1). Idempotent.
#
# /etc/hosts is bind-mounted by docker at run time, so the vhost names cannot be
# baked at image build. Write them here, before anything resolves them.
set -euo pipefail
DOMAIN="${WORLD_DOMAIN:-world.local}"

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

echo "init-runtime: hosts written, runtime dirs ready"
