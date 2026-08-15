#!/usr/bin/env bash
# =============================================================================
# Generate a local CA and one leaf certificate covering every world hostname.
# =============================================================================
# Why a real CA instead of a bare self-signed cert:
#
#   Outline hardcodes `secure: env.isProduction` on its OAuth CSRF cookie
#   (build/server/utils/passport.js), so signing in over http:// fails with
#   "Cannot send secure cookie over unencrypted connection". HTTPS is not
#   optional for this stack. And once we are on HTTPS, Outline's *server-side*
#   OIDC token exchange against Gitea has to trust that certificate — Node
#   rejects self-signed by default. A CA we control solves both: the browser
#   trusts one CA, and containers get it via NODE_EXTRA_CA_CERTS / a mounted
#   bundle rather than disabling verification everywhere.
#
# Idempotent: existing certs are left alone unless --force is passed.
#
#   ./scripts/gen-certs.sh [--force]
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck disable=SC1091
[[ -f .env ]] && { set -a; source .env; set +a; }

DOMAIN="${WORLD_DOMAIN:-world.local}"
MAIL_HOSTNAME="${MAIL_HOSTNAME:-mx.${DOMAIN}}"
TLS_DIR="$REPO_ROOT/config/tls"
MADDY_TLS_DIR="$REPO_ROOT/config/maddy/tls"
FORCE="${1:-}"

if [[ -f "$TLS_DIR/world.crt" && "$FORCE" != "--force" ]]; then
    echo "certificates already present in config/tls/ (use --force to regenerate)"
    exit 0
fi

mkdir -p "$TLS_DIR" "$MADDY_TLS_DIR"

# --- 1. Certificate authority -------------------------------------------------
openssl req -x509 -newkey rsa:4096 -nodes -sha256 -days 3650 \
    -keyout "$TLS_DIR/world-ca.key" \
    -out    "$TLS_DIR/world-ca.crt" \
    -subj "/O=SWEWorld/CN=SWEWorld Local CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    2>/dev/null

# --- 2. Leaf covering every name anything in the world resolves by ------------
# Includes the docker service names (minio, maddy) so container-to-container
# TLS works with the same certificate.
SANS="DNS:${DOMAIN},DNS:*.${DOMAIN},DNS:${MAIL_HOSTNAME},DNS:maddy,DNS:minio,DNS:localhost,IP:127.0.0.1"

openssl req -newkey rsa:2048 -nodes -sha256 \
    -keyout "$TLS_DIR/world.key" \
    -out    "$TLS_DIR/world.csr" \
    -subj "/O=SWEWorld/CN=*.${DOMAIN}" \
    2>/dev/null

openssl x509 -req -in "$TLS_DIR/world.csr" \
    -CA "$TLS_DIR/world-ca.crt" -CAkey "$TLS_DIR/world-ca.key" -CAcreateserial \
    -out "$TLS_DIR/world.crt" -days 3650 -sha256 \
    -extfile <(printf 'subjectAltName=%s\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n' "$SANS") \
    2>/dev/null

rm -f "$TLS_DIR/world.csr"

# --- 3. Maddy wants fullchain.pem / privkey.pem -------------------------------
cat "$TLS_DIR/world.crt" "$TLS_DIR/world-ca.crt" > "$MADDY_TLS_DIR/fullchain.pem"
cp "$TLS_DIR/world.key" "$MADDY_TLS_DIR/privkey.pem"

# Containers run unprivileged and only ever read these. This is a disposable
# local CA whose key never leaves the repo directory.
chmod 644 "$TLS_DIR"/*.crt "$TLS_DIR"/*.key "$MADDY_TLS_DIR"/*.pem

echo "generated:"
echo "  config/tls/world-ca.crt   <- trust this one (browser / system store)"
echo "  config/tls/world.crt      <- leaf: *.${DOMAIN}, ${MAIL_HOSTNAME}, maddy, minio"
echo "  config/maddy/tls/         <- same leaf, named for maddy"
echo
echo "SANs: ${SANS}"
