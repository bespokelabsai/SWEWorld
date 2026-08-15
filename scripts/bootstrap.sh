#!/usr/bin/env bash
# =============================================================================
# SWEWorld bootstrap — takes a fresh clone to a stack you can ingest into.
# =============================================================================
# Idempotent: safe to re-run. Each step checks for its own prior work.
#
#   ./scripts/bootstrap.sh
#
# What it does, in order:
#   1. Creates .env from .env.example if absent, and fills every generatable
#      secret (Outline's two hex keys) so you never hand-edit a random value.
#   2. Generates the local CA + leaf certificate (scripts/gen-certs.sh). Must
#      happen before anything starts: Traefik needs the leaf to serve HTTPS and
#      maddy exits immediately if its cert is missing.
#   3. Brings the stack up and waits for each service to answer.
#   4. Creates the Gitea admin account and its API token.
#   5. Registers Outline's OAuth2 client inside Gitea and writes the resulting
#      client id/secret back into .env, then restarts Outline to pick them up.
#   6. Creates the admin account in Mattermost and Maddy.
#   7. Mints OUTLINE_API_TOKEN by driving the OIDC login headlessly
#      (scripts/mint_outline_token.py), which also provisions the Outline user.
#
# After this runs, .env is fully populated and every Phase 3 ingestion script
# has the credentials it needs. No manual browser step is required.
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="$REPO_ROOT/.env"
CA_CERT="$REPO_ROOT/config/tls/world-ca.crt"
COMPOSE=(docker compose)

# --- output helpers ----------------------------------------------------------
c_ok()   { printf '\033[32m  ok\033[0m  %s\n' "$*"; }
c_step() { printf '\n\033[1;36m==>\033[0m \033[1m%s\033[0m\n' "$*"; }
c_warn() { printf '\033[33mwarn\033[0m  %s\n' "$*"; }
c_skip() { printf '\033[90mskip\033[0m  %s\n' "$*"; }
die()    { printf '\033[31mfail\033[0m  %s\n' "$*" >&2; exit 1; }

env_get() { grep -E "^${1}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- || true; }

# Done in python rather than sed: generated secrets routinely contain '/' and
# '&', which sed would mangle as delimiters and backreferences.
env_set() {
    python3 - "$ENV_FILE" "$1" "$2" <<'PY'
import sys, re
path, key, val = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    lines = f.readlines()
pat = re.compile(rf"^{re.escape(key)}=")
found = False
for i, line in enumerate(lines):
    if pat.match(line):
        lines[i] = f"{key}={val}\n"
        found = True
        break
if not found:
    lines.append(f"{key}={val}\n")
with open(path, "w") as f:
    f.writelines(lines)
PY
}

# Reach a service through Traefik. --resolve (rather than a Host header) so that
# TLS SNI and certificate validation both see the real hostname; --cacert so we
# validate against our own CA instead of disabling verification.
#   world_curl git.world.local /api/v1/version [extra curl args...]
world_curl() {
    local host="$1" path="$2"; shift 2
    curl -s --max-time 15 \
        --cacert "$CA_CERT" \
        --resolve "${host}:${HTTPS_PORT}:127.0.0.1" \
        "https://${host}:${HTTPS_PORT}${path}" "$@"
}

wait_for() {
    local label="$1" tries="$2"; shift 2
    printf '      waiting for %s' "$label"
    for ((i = 1; i <= tries; i++)); do
        if "$@" >/dev/null 2>&1; then printf ' ready\n'; return 0; fi
        printf '.'; sleep 2
    done
    printf ' TIMEOUT\n'
    return 1
}

container_healthy() {
    [[ "$(docker inspect "$1" --format '{{.State.Health.Status}}' 2>/dev/null)" == "healthy" ]]
}

# =============================================================================
c_step "1/7  .env and generated secrets"
# =============================================================================
if [[ ! -f "$ENV_FILE" ]]; then
    cp "$REPO_ROOT/.env.example" "$ENV_FILE"
    c_ok "created .env from .env.example"
else
    c_skip ".env already exists — leaving your values alone"
fi

set -a; source "$ENV_FILE"; set +a

# Outline validates these are 32 hex-encoded bytes and refuses to boot otherwise.
for key in OUTLINE_SECRET_KEY OUTLINE_UTILS_SECRET; do
    if [[ -z "$(env_get "$key")" ]]; then
        env_set "$key" "$(openssl rand -hex 32)"
        c_ok "generated $key"
    else
        c_skip "$key already set"
    fi
done

# Propagate the single admin identity into the per-service keys. docker compose
# cannot expand one .env value inside another, so the derived keys have to be
# written out literally. Editing WORLD_ADMIN_* and re-running is the supported
# way to change the agent's credentials everywhere.
WA_USER="$(env_get WORLD_ADMIN_USER)"
WA_PASS="$(env_get WORLD_ADMIN_PASSWORD)"
WA_MAIL="$(env_get WORLD_ADMIN_EMAIL)"
if [[ -n "$WA_USER" && -n "$WA_PASS" && -n "$WA_MAIL" ]]; then
    env_set GITEA_ADMIN_USER      "$WA_USER"
    env_set GITEA_ADMIN_PASSWORD  "$WA_PASS"
    env_set GITEA_ADMIN_EMAIL     "$WA_MAIL"
    env_set MM_ADMIN_USER         "$WA_USER"
    env_set MM_ADMIN_PASSWORD     "$WA_PASS"
    env_set MM_ADMIN_EMAIL        "$WA_MAIL"
    env_set MAIL_ADMIN_USER       "$WA_MAIL"
    env_set MAIL_ADMIN_PASSWORD   "$WA_PASS"
    c_ok "propagated WORLD_ADMIN_* to gitea/mattermost/mail admin keys"
else
    c_warn "WORLD_ADMIN_* not fully set; leaving per-service admin keys as-is"
fi

# Re-source so the freshly generated values are exported. docker compose ranks
# real environment variables ABOVE .env file entries, so a stale empty export
# here would silently win over the correct value on disk.
set -a; source "$ENV_FILE"; set +a
HTTPS_PORT="${HTTPS_PORT:-443}"
DOMAIN="${WORLD_DOMAIN:-world.local}"

# =============================================================================
c_step "2/7  TLS certificate authority"
# =============================================================================
"$REPO_ROOT/scripts/gen-certs.sh" | sed 's/^/      /'

# =============================================================================
c_step "3/7  starting the stack"
# =============================================================================
"${COMPOSE[@]}" up -d
c_ok "docker compose up -d issued"

wait_for "gitea"      60 world_curl "git.${DOMAIN}"  "/api/v1/version" -f \
    || die "gitea never became ready — check: docker compose logs gitea"
# Traefik refuses to route to a container that is not yet `healthy`, so this
# wait is what stops docs.$DOMAIN from 404ing right after bootstrap finishes.
wait_for "outline (healthy)" 60 container_healthy sweworld-outline-1 \
    || c_warn "outline slow to become healthy; docs.${DOMAIN} may 404 briefly"
wait_for "mattermost" 90 world_curl "chat.${DOMAIN}" "/api/v4/system/ping" -f \
    || c_warn "mattermost slow to start (check: docker compose logs mattermost)"
wait_for "roundcube"  60 world_curl "mail.${DOMAIN}" "/" -f \
    || c_warn "roundcube slow to start"

# =============================================================================
c_step "4/7  Gitea admin user and API token"
# =============================================================================
gitea_exec() { "${COMPOSE[@]}" exec -T -u git gitea "$@"; }

if gitea_exec gitea admin user list 2>/dev/null | awk '{print $2}' | grep -qx "$GITEA_ADMIN_USER"; then
    # Re-sync rather than skip: the whole point of WORLD_ADMIN_PASSWORD is that
    # changing it and re-running bootstrap updates the live account.
    gitea_exec gitea admin user change-password \
        -u "$GITEA_ADMIN_USER" -p "$GITEA_ADMIN_PASSWORD" --must-change-password=false >/dev/null 2>&1 \
        && c_ok "gitea user '$GITEA_ADMIN_USER' exists — password synced to WORLD_ADMIN_PASSWORD" \
        || c_warn "gitea user '$GITEA_ADMIN_USER' exists but password sync failed"
else
    gitea_exec gitea admin user create \
        --username "$GITEA_ADMIN_USER" \
        --password "$GITEA_ADMIN_PASSWORD" \
        --email "$GITEA_ADMIN_EMAIL" \
        --admin --must-change-password=false >/dev/null
    c_ok "created gitea admin '$GITEA_ADMIN_USER'"
fi

if [[ -z "$(env_get GITEA_API_TOKEN)" ]]; then
    TOKEN="$(gitea_exec gitea admin user generate-access-token \
        -u "$GITEA_ADMIN_USER" --scopes all --token-name "ingest-$(date +%s)" --raw \
        2>/dev/null | tr -d '\r\n ')"
    [[ -n "$TOKEN" ]] || die "could not generate a Gitea access token"
    env_set GITEA_API_TOKEN "$TOKEN"
    export GITEA_API_TOKEN="$TOKEN"
    c_ok "generated GITEA_API_TOKEN -> .env"
else
    export GITEA_API_TOKEN="$(env_get GITEA_API_TOKEN)"
    c_skip "GITEA_API_TOKEN already in .env"
fi

# =============================================================================
c_step "5/7  Outline OAuth2 client (registered inside Gitea)"
# =============================================================================
REDIRECT_URI="https://docs.${DOMAIN}/auth/oidc.callback"

if [[ -n "$(env_get OUTLINE_OIDC_CLIENT_ID)" && -n "$(env_get OUTLINE_OIDC_CLIENT_SECRET)" ]]; then
    c_skip "OUTLINE_OIDC_* already in .env"
else
    RESP="$(world_curl "git.${DOMAIN}" "/api/v1/user/applications/oauth2" \
        -X POST \
        -H "Authorization: token ${GITEA_API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"Outline\",\"redirect_uris\":[\"${REDIRECT_URI}\"],\"confidential_client\":true}")"

    CLIENT_ID="$(printf '%s' "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("client_id",""))' 2>/dev/null || true)"
    CLIENT_SECRET="$(printf '%s' "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("client_secret",""))' 2>/dev/null || true)"

    if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
        c_warn "could not register the OAuth app automatically. Response was:"
        printf '      %s\n' "$RESP"
        c_warn "Register it by hand: Gitea -> Settings -> Applications -> OAuth2,"
        c_warn "redirect URI ${REDIRECT_URI}, then put the values in .env."
    else
        env_set OUTLINE_OIDC_CLIENT_ID "$CLIENT_ID"
        env_set OUTLINE_OIDC_CLIENT_SECRET "$CLIENT_SECRET"
        # Writing .env is not enough: this script exported these as empty
        # strings when it sourced .env above, and docker compose ranks real
        # environment variables ABOVE .env entries. Without re-exporting, the
        # recreate below injects "" and Outline renders no login button at all.
        export OUTLINE_OIDC_CLIENT_ID="$CLIENT_ID"
        export OUTLINE_OIDC_CLIENT_SECRET="$CLIENT_SECRET"
        c_ok "registered OAuth2 client ${CLIENT_ID}"

        "${COMPOSE[@]}" up -d --force-recreate outline >/dev/null 2>&1
        c_ok "recreated outline with OIDC credentials"
        wait_for "outline (healthy)" 60 container_healthy sweworld-outline-1 \
            || c_warn "outline slow to become healthy"
    fi
fi

# =============================================================================
c_step "6/7  Mattermost and Maddy accounts"
# =============================================================================
mm_exec() { "${COMPOSE[@]}" exec -T mattermost mmctl --local "$@"; }

if mm_exec user search "$MM_ADMIN_EMAIL" 2>/dev/null | grep -qi "username"; then
    mm_exec user change-password "$MM_ADMIN_EMAIL" --password "$MM_ADMIN_PASSWORD" >/dev/null 2>&1 \
        && c_ok "mattermost user '$MM_ADMIN_USER' exists — password synced" \
        || c_warn "mattermost user '$MM_ADMIN_USER' exists but password sync failed"
else
    mm_exec user create --email "$MM_ADMIN_EMAIL" --username "$MM_ADMIN_USER" \
        --password "$MM_ADMIN_PASSWORD" --system-admin >/dev/null 2>&1 \
        && c_ok "created mattermost admin '$MM_ADMIN_USER'" \
        || c_warn "mattermost user create failed (is the server up? check logs)"
fi

if mm_exec team list 2>/dev/null | grep -qx "$MM_TEAM_NAME"; then
    c_skip "mattermost team '$MM_TEAM_NAME' already exists"
else
    mm_exec team create --name "$MM_TEAM_NAME" --display-name "$MM_TEAM_DISPLAY_NAME" \
        --email "$MM_ADMIN_EMAIL" >/dev/null 2>&1 \
        && c_ok "created mattermost team '$MM_TEAM_NAME'" \
        || c_warn "mattermost team create failed"
fi
mm_exec team users add "$MM_TEAM_NAME" "$MM_ADMIN_EMAIL" >/dev/null 2>&1 || true

# --- maddy: credentials and the IMAP account are two separate objects --------
maddy_exec() { "${COMPOSE[@]}" exec -T maddy "$@"; }

if maddy_exec maddy creds list 2>/dev/null | grep -qx "$MAIL_ADMIN_USER"; then
    maddy_exec maddy creds password --password "$MAIL_ADMIN_PASSWORD" "$MAIL_ADMIN_USER" >/dev/null 2>&1 \
        && c_ok "maddy credentials for '$MAIL_ADMIN_USER' exist — password synced" \
        || c_warn "maddy credentials exist but password sync failed"
else
    maddy_exec maddy creds create --password "$MAIL_ADMIN_PASSWORD" "$MAIL_ADMIN_USER" >/dev/null 2>&1 \
        && c_ok "created maddy credentials for '$MAIL_ADMIN_USER'" \
        || c_warn "maddy creds create failed (check: docker compose logs maddy)"
fi

if maddy_exec maddy imap-acct list 2>/dev/null | grep -qx "$MAIL_ADMIN_USER"; then
    c_skip "maddy mailbox for '$MAIL_ADMIN_USER' already exists"
else
    maddy_exec maddy imap-acct create "$MAIL_ADMIN_USER" >/dev/null 2>&1 \
        && c_ok "created maddy mailbox for '$MAIL_ADMIN_USER'" \
        || c_warn "maddy imap-acct create failed"
fi

# =============================================================================
c_step "7/7  Outline API token"
# =============================================================================
# Outline has no endpoint to mint a token without a browser session, so this
# drives the OIDC login headlessly. Side effect: the first successful login is
# what provisions the Outline user and workspace — they cannot be pre-created.
if python3 "$REPO_ROOT/scripts/mint_outline_token.py" 2>&1 | sed 's/^/    /'; then
    :
else
    c_warn "could not mint OUTLINE_API_TOKEN automatically."
    c_warn "Sign in at https://docs.${DOMAIN} and create one under Settings -> API Tokens."
fi

# =============================================================================
printf '\n\033[1;32mBootstrap complete.\033[0m\n\n'
cat <<EOF
  Next:
    sudo ./scripts/hosts.sh add     # if you have not already
    ./scripts/verify.sh             # confirm all four services answer

  To browse without certificate warnings, trust the local CA once:
    sudo cp config/tls/world-ca.crt /usr/local/share/ca-certificates/sweworld.crt
    sudo update-ca-certificates
  (Firefox and Chrome keep their own stores — import the same file there.)

  Sign in at https://docs.${DOMAIN} / https://git.${DOMAIN} as
  ${GITEA_ADMIN_USER}. Mail is at https://mail.${DOMAIN}
  (${MAIL_ADMIN_USER}).
EOF
