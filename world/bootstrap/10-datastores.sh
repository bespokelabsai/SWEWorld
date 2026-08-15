#!/usr/bin/env bash
# Build-time: initialise the Postgres cluster (mattermost) and MariaDB
# (bookstack), and create each service's database and role.
set -euo pipefail

PG_BIN=/usr/lib/postgresql/16/bin
PGDATA=/var/lib/world/postgres

# --- postgres ----------------------------------------------------------------
su -s /bin/bash postgres -c "$PG_BIN/initdb -D $PGDATA -E UTF8 --locale=C" >/dev/null
{
  echo "listen_addresses = '127.0.0.1'"
  echo "port = 5432"
  echo "unix_socket_directories = '/tmp'"
  echo "fsync = off"              # disposable world; halves boot and seed time
  echo "full_page_writes = off"
  echo "synchronous_commit = off"
} >> "$PGDATA/postgresql.conf"
echo "host all all 127.0.0.1/32 md5" >> "$PGDATA/pg_hba.conf"

su -s /bin/bash postgres -c "$PG_BIN/pg_ctl -D $PGDATA -o '-c unix_socket_directories=/tmp' -w start" >/dev/null
su -s /bin/bash postgres -c "$PG_BIN/psql -h /tmp -q -c \"CREATE ROLE mattermost LOGIN PASSWORD 'mattermost';\""
su -s /bin/bash postgres -c "$PG_BIN/createdb -h /tmp -O mattermost mattermost"
su -s /bin/bash postgres -c "$PG_BIN/pg_ctl -D $PGDATA -w stop" >/dev/null

# --- mariadb -----------------------------------------------------------------
install -d -m 755 -o mysql -g mysql /var/lib/world/mysql /run/mysqld
mariadb-install-db --user=mysql --datadir=/var/lib/world/mysql --auth-root-authentication-method=normal >/dev/null

/usr/sbin/mariadbd --user=mysql --datadir=/var/lib/world/mysql \
  --socket=/run/mysqld/mysqld.sock --bind-address=127.0.0.1 --skip-networking=0 &
mysql_pid=$!
for i in $(seq 1 60); do
  mariadb-admin --protocol=socket --socket=/run/mysqld/mysqld.sock ping >/dev/null 2>&1 && break
  sleep 1
done
mariadb --protocol=socket --socket=/run/mysqld/mysqld.sock <<'SQL'
CREATE DATABASE bookstack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'bookstack'@'localhost' IDENTIFIED BY 'bookstack';
GRANT ALL PRIVILEGES ON bookstack.* TO 'bookstack'@'localhost';
FLUSH PRIVILEGES;
SQL
mariadb-admin --protocol=socket --socket=/run/mysqld/mysqld.sock shutdown
wait $mysql_pid 2>/dev/null || true

echo "10-datastores: OK"
