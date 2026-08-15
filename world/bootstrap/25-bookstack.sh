#!/usr/bin/env bash
# Build-time: bookstack .env, app key, schema, admin user.
set -euo pipefail
DOMAIN="${WORLD_DOMAIN:-world.local}"
ADMIN_PASS="${WORLD_ADMIN_PASSWORD:-worldadmin}"
ADMIN_MAIL="${WORLD_ADMIN_EMAIL:-worldadmin@${DOMAIN}}"

cd /opt/bookstack
sed -e "s|@@DOMAIN@@|${DOMAIN}|g" /world-src/config/bookstack/env > .env

# Start mariadb for the migration, then put it back down.
install -d -m 755 -o mysql -g mysql /run/mysqld
/usr/sbin/mariadbd --user=mysql --datadir=/var/lib/world/mysql \
  --socket=/run/mysqld/mysqld.sock --bind-address=127.0.0.1 &
for i in $(seq 1 60); do
  mariadb-admin --protocol=socket --socket=/run/mysqld/mysqld.sock ping >/dev/null 2>&1 && break
  sleep 1
done

php artisan key:generate --force --no-interaction
php artisan migrate --force --no-interaction

# BookStack seeds an admin@admin.com / password account on first migrate.
# Rename it to the world admin so one credential set works everywhere.
mariadb --protocol=socket --socket=/run/mysqld/mysqld.sock bookstack <<SQL
UPDATE users SET email='${ADMIN_MAIL}', name='World Admin' WHERE id=1;
SQL
php artisan bookstack:reset-password 1 "${ADMIN_PASS}" --no-interaction 2>/dev/null \
  || php -r '
    require "/opt/bookstack/vendor/autoload.php";
    $app = require "/opt/bookstack/bootstrap/app.php";
    $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
    $u = \BookStack\Users\Models\User::find(1);
    $u->password = Illuminate\Support\Facades\Hash::make(getenv("ADMIN_PASS"));
    $u->save();
    echo "password set\n";
  ' 2>/dev/null || echo "warn: could not reset bookstack admin password"

# --- API token for ingest_docs.py ------------------------------------------
# BookStack stores the secret hashed, so it can only be created through the
# app: generate it here and write the plaintext half where ingestion can read
# it. The world is disposable and this token never leaves the container.
TOKEN_LINE="$(php artisan tinker --execute='
  $t = new \BookStack\Api\ApiToken();
  $t->name = "ingest";
  $t->token_id = \Illuminate\Support\Str::random(32);
  $secret = \Illuminate\Support\Str::random(32);
  $t->secret = \Illuminate\Support\Facades\Hash::make($secret);
  $t->user_id = 1;
  $t->expires_at = "2099-01-01";
  $t->save();
  echo $t->token_id . ":" . $secret . PHP_EOL;
' 2>/dev/null | tail -1 | tr -d "\r\n ")"
install -d -m 755 /etc/sweworld
printf '%s\n' "$TOKEN_LINE" > /etc/sweworld/bookstack-token
chmod 644 /etc/sweworld/bookstack-token
# Assert: a silently empty token surfaces much later as 401s during ingestion.
grep -q ':' /etc/sweworld/bookstack-token \
  || { echo "25-bookstack: API token was not generated" >&2; exit 1; }

mariadb-admin --protocol=socket --socket=/run/mysqld/mysqld.sock shutdown
sleep 2

chown -R www-data:www-data /opt/bookstack/storage /opt/bookstack/bootstrap/cache /opt/bookstack/public/uploads
echo "25-bookstack: OK"
