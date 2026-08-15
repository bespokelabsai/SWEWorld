#!/usr/bin/env bash
# Add (or remove) the world's subdomains to /etc/hosts.
#
#   sudo ./scripts/hosts.sh add
#   sudo ./scripts/hosts.sh remove
#
# Traefik routes by Host header, so the browser has to resolve these names.
# Inside the docker network the same names resolve via network aliases on the
# traefik service (see docker-compose.yml) — this script is only for the host.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
[[ -f "$REPO_ROOT/.env" ]] && set -a && source "$REPO_ROOT/.env" && set +a

DOMAIN="${WORLD_DOMAIN:-world.local}"
MARKER="# >>> sweworld >>>"
END_MARKER="# <<< sweworld <<<"
HOSTS_FILE="${HOSTS_FILE:-/etc/hosts}"

usage() { echo "usage: $0 {add|remove|status}" >&2; exit 2; }

remove_block() {
    if grep -qF "$MARKER" "$HOSTS_FILE"; then
        sed -i "/$(printf '%s' "$MARKER" | sed 's/[][\.*^$/]/\\&/g')/,/$(printf '%s' "$END_MARKER" | sed 's/[][\.*^$/]/\\&/g')/d" "$HOSTS_FILE"
        echo "removed sweworld block from $HOSTS_FILE"
    else
        echo "no sweworld block present in $HOSTS_FILE"
    fi
}

case "${1:-}" in
    add)
        [[ $EUID -eq 0 ]] || { echo "must run as root (use sudo)" >&2; exit 1; }
        remove_block
        {
            echo "$MARKER"
            echo "127.0.0.1 git.$DOMAIN docs.$DOMAIN chat.$DOMAIN mail.$DOMAIN"
            echo "$END_MARKER"
        } >> "$HOSTS_FILE"
        echo "added: git.$DOMAIN docs.$DOMAIN chat.$DOMAIN mail.$DOMAIN -> 127.0.0.1"
        ;;
    remove)
        [[ $EUID -eq 0 ]] || { echo "must run as root (use sudo)" >&2; exit 1; }
        remove_block
        ;;
    status)
        grep -F -A1 "$MARKER" "$HOSTS_FILE" || echo "not configured"
        ;;
    *) usage ;;
esac
