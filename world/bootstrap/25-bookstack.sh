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
# Set the admin password. There is no `bookstack:reset-password` artisan
# command, so this goes through the model — and ADMIN_PASS must be EXPORTED,
# because php reads it with getenv() and a plain shell variable is invisible
# there. Getting that wrong hashes the empty string, and BookStack then rejects
# every login with "These credentials do not match our records" while looking
# perfectly configured.
export ADMIN_PASS
php -r '
  require "/opt/bookstack/vendor/autoload.php";
  $app = require "/opt/bookstack/bootstrap/app.php";
  $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
  $pass = getenv("ADMIN_PASS");
  if ($pass === false || $pass === "") {
      fwrite(STDERR, "25-bookstack: ADMIN_PASS is empty in the php environment\n");
      exit(1);
  }
  $u = \BookStack\Users\Models\User::find(1);
  $u->password = Illuminate\Support\Facades\Hash::make($pass);
  $u->save();
  // Assert rather than assume: verify the stored hash accepts the password.
  if (!Illuminate\Support\Facades\Hash::check($pass, $u->fresh()->password)) {
      fwrite(STDERR, "25-bookstack: admin password did not take\n");
      exit(1);
  }
  echo "admin password set\n";
'

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
