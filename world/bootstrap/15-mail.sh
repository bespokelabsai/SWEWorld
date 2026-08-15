#!/usr/bin/env bash
# Build-time: maddy config, TLS material, and the admin mailbox.
#
# Closed-world config: no DMARC/DKIM/SPF/MX checks (they need public DNS) and no
# outbound delivery. Maddy still refuses to start without a certificate on disk,
# so a self-signed pair is generated here — nothing verifies it, plaintext auth
# is permitted on 143/587, and no traffic ever leaves the container.
set -euo pipefail
DOMAIN="${WORLD_DOMAIN:-world.local}"
ADMIN_PASS="${WORLD_ADMIN_PASSWORD:-worldadmin}"

install -d -m 755 /etc/maddy
install -m 644 /world-src/config/maddy.conf /etc/maddy/maddy.conf

install -d -m 755 -o worldsvc -g worldsvc /var/lib/world/maddy/tls
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout /var/lib/world/maddy/tls/privkey.pem \
  -out    /var/lib/world/maddy/tls/fullchain.pem \
  -subj "/CN=mx.${DOMAIN}" -addext "subjectAltName=DNS:mx.${DOMAIN},DNS:localhost" >/dev/null 2>&1
chown -R worldsvc:worldsvc /var/lib/world/maddy
chmod 644 /var/lib/world/maddy/tls/*.pem

# Credentials and the IMAP account are separate objects in maddy: creating only
# the first yields an account that authenticates but has nowhere to deliver.
cd /var/lib/world/maddy
su -s /bin/bash worldsvc -c "MADDY_HOSTNAME=mx.${DOMAIN} MADDY_DOMAIN=${DOMAIN} \
  maddy --config /etc/maddy/maddy.conf creds create --password '${ADMIN_PASS}' worldadmin@${DOMAIN}"
su -s /bin/bash worldsvc -c "MADDY_HOSTNAME=mx.${DOMAIN} MADDY_DOMAIN=${DOMAIN} \
  maddy --config /etc/maddy/maddy.conf imap-acct create worldadmin@${DOMAIN}"

# --- roundcube ---------------------------------------------------------------
install -m 644 /world-src/config/roundcube-config.inc.php /opt/roundcube/config/config.inc.php
install -d -m 755 -o worldsvc -g worldsvc /var/lib/world/roundcube
sqlite3 /var/lib/world/roundcube/roundcube.db < /opt/roundcube/SQL/sqlite.initial.sql
chown -R worldsvc:worldsvc /var/lib/world/roundcube
chown -R www-data:www-data /opt/roundcube/temp /opt/roundcube/logs 2>/dev/null || true

echo "15-mail: OK"
