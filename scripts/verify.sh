#!/usr/bin/env bash
# =============================================================================
# SWEWorld verification — Phase 1 acceptance check.
# =============================================================================
# Asserts every service is up, routed, and reachable. Exits non-zero if
# anything fails, so this is usable in CI later.
#
#   ./scripts/verify.sh
#
# Requests use curl --resolve against 127.0.0.1 so TLS SNI and certificate
# validation see the real hostname, and --cacert so we validate against the
# world's own CA rather than skipping verification. The DNS section at the end
# separately confirms a browser on this host would reach the same places.
# =============================================================================
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
# shellcheck disable=SC1091
[[ -f .env ]] && { set -a; source .env; set +a; }

DOMAIN="${WORLD_DOMAIN:-world.local}"
HTTP_PORT="${HTTP_PORT:-80}"
HTTPS_PORT="${HTTPS_PORT:-443}"
IMAP_PORT="${IMAP_PORT:-143}"
SUBMISSION_PORT="${SUBMISSION_PORT:-587}"
CA_CERT="$REPO_ROOT/config/tls/world-ca.crt"

PASS=0; FAIL=0
ok()   { printf '\033[32m  PASS\033[0m  %s\n' "$*"; PASS=$((PASS+1)); }
bad()  { printf '\033[31m  FAIL\033[0m  %s\n' "$*"; FAIL=$((FAIL+1)); }
note() { printf '\033[90m        %s\033[0m\n' "$*"; }
head_() { printf '\n\033[1;36m%s\033[0m\n' "$*"; }

wcurl() {
    local host="$1" path="$2"; shift 2
    curl -s --max-time 20 --cacert "$CA_CERT" \
        --resolve "${host}:${HTTPS_PORT}:127.0.0.1" \
        "https://${host}:${HTTPS_PORT}${path}" "$@"
}

# check_http <label> <host> <path> [expected-substring]
check_http() {
    local label="$1" host="$2" path="$3" expect="${4:-}"
    local body code
    body="$(wcurl "$host" "$path" -w '\n%{http_code}' 2>/dev/null)"
    code="$(printf '%s' "$body" | tail -1)"
    body="$(printf '%s' "$body" | sed '$d')"
    if [[ "$code" != 200 ]]; then bad "$label — HTTP $code"; return 1; fi
    if [[ -n "$expect" ]] && ! printf '%s' "$body" | grep -qi -- "$expect"; then
        bad "$label — 200 but body missing '$expect'"; return 1
    fi
    ok "$label"
}

head_ "Containers"
EXPECTED_UP=(traefik gitea gitea-db outline outline-db outline-redis minio mattermost mattermost-db maddy roundcube)
RUNNING="$(docker compose ps --services --filter status=running 2>/dev/null)"
for svc in "${EXPECTED_UP[@]}"; do
    if printf '%s\n' "$RUNNING" | grep -qx "$svc"; then ok "container up: $svc"; else bad "container not running: $svc"; fi
done

# Traefik will not create a router for an unhealthy container, so a failure here
# is the cause of any 404 reported below, not a separate problem.
OH="$(docker inspect sweworld-outline-1 --format '{{.State.Health.Status}}' 2>/dev/null)"
if [[ "$OH" == "healthy" ]]; then ok "outline reports healthy (required for Traefik routing)"
else bad "outline health=$OH — Traefik will not route to it until healthy"; fi

head_ "TLS"
if [[ -f "$CA_CERT" ]]; then
    ok "local CA present at config/tls/world-ca.crt"
    SANS="$(openssl x509 -in "$REPO_ROOT/config/tls/world.crt" -noout -ext subjectAltName 2>/dev/null | tail -1 | sed 's/^ *//')"
    note "leaf SANs: ${SANS}"
    if openssl verify -CAfile "$CA_CERT" "$REPO_ROOT/config/tls/world.crt" >/dev/null 2>&1; then
        ok "leaf certificate verifies against the local CA"
    else
        bad "leaf certificate does not verify against the local CA"
    fi
else
    bad "no CA at config/tls/world-ca.crt — run ./scripts/gen-certs.sh"
fi

# http://:80 must redirect to https, not serve content.
REDIR="$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 10 \
    --resolve "git.${DOMAIN}:${HTTP_PORT}:127.0.0.1" "http://git.${DOMAIN}:${HTTP_PORT}/" 2>/dev/null)"
if printf '%s' "$REDIR" | grep -q "^30. https://"; then
    ok "HTTP :${HTTP_PORT} redirects to HTTPS"
    note "$REDIR"
else
    bad "HTTP :${HTTP_PORT} did not redirect to HTTPS (got: $REDIR)"
fi

head_ "HTTPS routing through Traefik"
check_http "git.${DOMAIN} serves Gitea"        "git.${DOMAIN}"  "/"  "gitea"
check_http "docs.${DOMAIN} serves Outline"     "docs.${DOMAIN}" "/"  "outline"
check_http "chat.${DOMAIN} serves Mattermost"  "chat.${DOMAIN}" "/"  "mattermost"
check_http "mail.${DOMAIN} serves Roundcube"   "mail.${DOMAIN}" "/"  "roundcube"

head_ "Service APIs answer empty"
check_http "Gitea API /version"                "git.${DOMAIN}"  "/api/v1/version"     "version"
check_http "Mattermost API /system/ping"       "chat.${DOMAIN}" "/api/v4/system/ping" "OK"

head_ "Gitea is a working OIDC provider for Outline"
DISCO="$(wcurl "git.${DOMAIN}" "/.well-known/openid-configuration" 2>/dev/null)"
if printf '%s' "$DISCO" | python3 -c '
import sys, json
d = json.load(sys.stdin)
for k in ("issuer", "authorization_endpoint", "token_endpoint", "userinfo_endpoint"):
    assert d.get(k), f"missing {k}"
' >/dev/null 2>&1; then
    ok "OIDC discovery document is valid"
    note "issuer: $(printf '%s' "$DISCO" | python3 -c 'import sys,json;print(json.load(sys.stdin)["issuer"])' 2>/dev/null)"
else
    bad "OIDC discovery document missing or malformed"
fi

# The real functional test of the whole Gitea-as-IdP design: hitting Outline's
# OIDC entry point must 302 to Gitea's authorize endpoint. A 500 here means the
# Secure-cookie-over-HTTP problem is back; a 404 means OIDC is not configured.
OIDC_START="$(wcurl "docs.${DOMAIN}" "/auth/oidc" -o /dev/null -w '%{http_code} %{redirect_url}' 2>/dev/null)"
if printf '%s' "$OIDC_START" | grep -qE "^30. https://git\.${DOMAIN}"; then
    ok "Outline /auth/oidc redirects to Gitea's authorize endpoint"
    note "$OIDC_START"
else
    bad "Outline /auth/oidc did not redirect to Gitea (got: $OIDC_START)"
    note "500 => secure-cookie-over-HTTP; 404 => OUTLINE_OIDC_* unset in .env"
fi

# Phase 3's ingest_docs.py authenticates with this token, so prove it works now
# rather than discovering it is missing mid-ingest.
if [[ -n "${OUTLINE_API_TOKEN:-}" ]]; then
    COLS="$(wcurl "docs.${DOMAIN}" "/api/collections.list" \
        -X POST -H "Authorization: Bearer ${OUTLINE_API_TOKEN}" \
        -H "Content-Type: application/json" -d '{}' 2>/dev/null)"
    if printf '%s' "$COLS" | python3 -c 'import sys,json; sys.exit(0 if json.load(sys.stdin).get("ok") else 1)' 2>/dev/null; then
        ok "OUTLINE_API_TOKEN authenticates against the Outline API"
        note "collections: $(printf '%s' "$COLS" | python3 -c 'import sys,json;print([c["name"] for c in json.load(sys.stdin).get("data",[])])' 2>/dev/null)"
    else
        bad "OUTLINE_API_TOKEN present but rejected by the Outline API"
    fi
else
    bad "OUTLINE_API_TOKEN unset — run: python3 scripts/mint_outline_token.py"
fi

head_ "Admin / agent credentials (one identity, every service)"
ADMIN_USER="${WORLD_ADMIN_USER:-${GITEA_ADMIN_USER:-}}"
ADMIN_PASS="${WORLD_ADMIN_PASSWORD:-${GITEA_ADMIN_PASSWORD:-}}"
ADMIN_MAIL="${WORLD_ADMIN_EMAIL:-${MAIL_ADMIN_USER:-}}"

# Gitea: HTTP basic auth against an endpoint that requires a real session.
GITEA_ME="$(wcurl "git.${DOMAIN}" "/api/v1/user" -u "${ADMIN_USER}:${ADMIN_PASS}" 2>/dev/null)"
if printf '%s' "$GITEA_ME" | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get("login") else 1)' 2>/dev/null; then
    ok "Gitea login as '${ADMIN_USER}' (admin=$(printf '%s' "$GITEA_ME" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("is_admin"))' 2>/dev/null))"
else
    bad "Gitea login as '${ADMIN_USER}' failed — password out of sync with WORLD_ADMIN_PASSWORD?"
fi

# Mattermost: a real login call, not just a ping.
MM_LOGIN="$(wcurl "chat.${DOMAIN}" "/api/v4/users/login" -X POST -H "Content-Type: application/json" \
    -d "{\"login_id\":\"${ADMIN_USER}\",\"password\":\"${ADMIN_PASS}\"}" 2>/dev/null)"
if printf '%s' "$MM_LOGIN" | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get("id") else 1)' 2>/dev/null; then
    ok "Mattermost login as '${ADMIN_USER}' (roles: $(printf '%s' "$MM_LOGIN" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("roles"))' 2>/dev/null))"
else
    bad "Mattermost login as '${ADMIN_USER}' failed"
fi

# Outline has no password of its own — the agent signs in through Gitea. The
# OIDC redirect and API-token checks above already prove that path works.
ok "Outline: no separate password by design (signs in via Gitea OIDC)"

head_ "Storage backends"
for pair in "outline-db:${OUTLINE_DB_USER:-outline}" "gitea-db:${GITEA_DB_USER:-gitea}" "mattermost-db:${MM_DB_USER:-mattermost}"; do
    svc="${pair%%:*}"; usr="${pair##*:}"
    if docker compose exec -T "$svc" pg_isready -U "$usr" >/dev/null 2>&1; then
        ok "$svc accepting connections"; else bad "$svc not ready"; fi
done
if docker compose exec -T outline-redis redis-cli ping 2>/dev/null | grep -q PONG; then
    ok "Outline Redis responding"; else bad "Outline Redis not responding"; fi

# --entrypoint sh is required: the minio/mc image's entrypoint is `mc` itself,
# so without it the shell command is passed as arguments to mc.
BUCKET_LS="$(docker run --rm --network sweworld --entrypoint sh minio/mc:latest -c \
    "mc alias set w http://minio:9000 '${MINIO_ROOT_USER}' '${MINIO_ROOT_PASSWORD}' >/dev/null 2>&1 && mc ls w/" 2>/dev/null)"
if printf '%s' "$BUCKET_LS" | grep -q "${MINIO_BUCKET:-outline}"; then
    ok "MinIO bucket '${MINIO_BUCKET:-outline}' exists"; else bad "MinIO bucket '${MINIO_BUCKET:-outline}' missing"; fi

head_ "Mail (bypasses Traefik — raw ports on localhost)"
python3 - "$IMAP_PORT" "$SUBMISSION_PORT" "${MAIL_ADMIN_USER:-}" "${MAIL_ADMIN_PASSWORD:-}" <<'PY'
import sys, imaplib, smtplib

imap_port, smtp_port, user, password = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
GREEN, RED, GREY, RESET = "\033[32m", "\033[31m", "\033[90m", "\033[0m"
def ok(m):  print(f"{GREEN}  PASS{RESET}  {m}")
def bad(m): print(f"{RED}  FAIL{RESET}  {m}")

failed = 0
try:
    M = imaplib.IMAP4("127.0.0.1", imap_port)
    ok(f"IMAP :{imap_port} greeting received")
    if user and password:
        try:
            M.login(user, password)
            ok(f"IMAP login as {user}")
            _, data = M.list()
            ok(f"IMAP LIST returned {len(data)} folder(s) for this account")
            M.logout()
        except Exception as e:
            bad(f"IMAP login as {user}: {e}"); failed += 1
    else:
        print(f"{GREY}        MAIL_ADMIN_USER unset; skipped login check{RESET}")
except Exception as e:
    bad(f"IMAP :{imap_port}: {e}"); failed += 1

try:
    S = smtplib.SMTP("127.0.0.1", smtp_port, timeout=10)
    S.ehlo()
    ok(f"SMTP submission :{smtp_port} greeting received")
    if user and password:
        try:
            S.login(user, password)
            ok(f"SMTP AUTH as {user}")
        except Exception as e:
            bad(f"SMTP AUTH as {user}: {e}"); failed += 1
    S.quit()
except Exception as e:
    bad(f"SMTP :{smtp_port}: {e}"); failed += 1

sys.exit(1 if failed else 0)
PY
if [[ $? -eq 0 ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

head_ "Host DNS (browser reachability)"
for sub in git docs chat mail; do
    if getent hosts "${sub}.${DOMAIN}" >/dev/null 2>&1; then
        ok "${sub}.${DOMAIN} resolves on this host"
    else
        bad "${sub}.${DOMAIN} does not resolve — run: sudo ./scripts/hosts.sh add"
    fi
done

head_ "Summary"
printf '  %d passed, %d failed\n\n' "$PASS" "$FAIL"
[[ $FAIL -eq 0 ]] || exit 1
printf '\033[1;32mAll checks passed — every service is up and reachable.\033[0m\n'
