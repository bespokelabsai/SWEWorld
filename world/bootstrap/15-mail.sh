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

# maddy needs runtime_dir to exist and be writable by worldsvc. At build time
# /run is root-owned so worldsvc cannot create it — and `maddy creds create`
# exits 0 even when it fails that way, which makes `set -e` useless and leaves
# the world with no mail accounts while still printing success.
install -d -m 755 -o worldsvc -g worldsvc /run/maddy

# Credentials and the IMAP account are separate objects in maddy: creating only
# the first yields an account that authenticates but has nowhere to deliver.
cd /var/lib/world/maddy
su -s /bin/bash worldsvc -c "MADDY_HOSTNAME=mx.${DOMAIN} MADDY_DOMAIN=${DOMAIN} \
  maddy --config /etc/maddy/maddy.conf creds create --password '${ADMIN_PASS}' worldadmin@${DOMAIN}"
su -s /bin/bash worldsvc -c "MADDY_HOSTNAME=mx.${DOMAIN} MADDY_DOMAIN=${DOMAIN} \
  maddy --config /etc/maddy/maddy.conf imap-acct create worldadmin@${DOMAIN}"

# Assert rather than trust the exit code: see the note above.
if ! su -s /bin/bash worldsvc -c "MADDY_HOSTNAME=mx.${DOMAIN} MADDY_DOMAIN=${DOMAIN} \
     maddy --config /etc/maddy/maddy.conf creds list" 2>/dev/null \
     | grep -qx "worldadmin@${DOMAIN}"; then
  echo "15-mail: credentials for worldadmin@${DOMAIN} were NOT created" >&2
  exit 1
fi

# --- roundcube ---------------------------------------------------------------
install -m 644 /world-src/config/roundcube-config.inc.php /opt/roundcube/config/config.inc.php
install -d -m 755 /var/lib/world/roundcube
sqlite3 /var/lib/world/roundcube/roundcube.db < /opt/roundcube/SQL/sqlite.initial.sql

# Roundcube runs under php-fpm as www-data, NOT as worldsvc like the rest of the
# world's services. Its sqlite database, temp and log directories must be
# writable by www-data or every login returns 401 with nothing in the log --
# because it cannot write the log either.
install -d -m 755 /var/lib/world/roundcube/temp /var/lib/world/roundcube/logs
chown -R www-data:www-data /var/lib/world/roundcube /opt/roundcube/temp /opt/roundcube/logs

# Assert: a 401 with an empty log is a miserable thing to debug later.
su -s /bin/bash www-data -c 'test -w /var/lib/world/roundcube/roundcube.db' \
  || { echo "15-mail: roundcube db is not writable by www-data" >&2; exit 1; }

echo "15-mail: OK"
