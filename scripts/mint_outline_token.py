#!/usr/bin/env python3
"""Mint an Outline API token by driving the Gitea OIDC login flow headlessly.

Outline exposes no way to create an API token without an authenticated browser
session, which normally makes OUTLINE_API_TOKEN a manual copy-paste step. This
script performs the same flow a browser would:

    1. log into Gitea with the admin credentials from .env
    2. hit Outline's /auth/oidc, which redirects to Gitea's authorize endpoint
    3. submit the consent grant (only needed the first time)
    4. land back on Outline with a session cookie
    5. POST /api/apiKeys.create, passing the `csrfToken` cookie back as the
       x-csrf-token header (Outline rejects mutations without it)

The resulting token is written into .env as OUTLINE_API_TOKEN.

Signing in this way also *creates* the Outline user and workspace on first run —
Outline provisions accounts on first successful OIDC login, so there is no way
to pre-create them.

Usage:
    python3 scripts/mint_outline_token.py [--name NAME] [--force] [--print-only]
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("requests is required: pip install -r scripts/requirements.txt")

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"
CA_CERT = REPO_ROOT / "config" / "tls" / "world-ca.crt"

# Outline returns the secret under different keys across versions; check in order.
TOKEN_FIELDS = ("value", "secret", "key")


def read_env() -> dict[str, str]:
    """Parse .env into a dict, ignoring comments and blank lines."""
    if not ENV_FILE.exists():
        sys.exit(f"{ENV_FILE} not found — run scripts/bootstrap.sh first")
    env: dict[str, str] = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            env[key.strip()] = val.strip()
    return env


def write_env(key: str, value: str) -> None:
    """Set key=value in .env, preserving comments and ordering."""
    lines = ENV_FILE.read_text().splitlines(keepends=True)
    pattern = re.compile(rf"^{re.escape(key)}=")
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{key}={value}\n"
            break
    else:
        lines.append(f"{key}={value}\n")
    ENV_FILE.write_text("".join(lines))


def find_csrf(html: str) -> str | None:
    """Extract Gitea's _csrf value from a form or meta tag."""
    for pattern in (
        r'name="_csrf"\s+value="([^"]+)"',
        r'content="([^"]+)"\s+name="csrf-token"',
        r'name="csrf-token"\s+content="([^"]+)"',
    ):
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    return None


def login_to_outline(env: dict[str, str]) -> requests.Session:
    """Return a session authenticated against Outline via Gitea OIDC."""
    domain = env.get("WORLD_DOMAIN", "world.local")
    git_url = f"https://git.{domain}"
    docs_url = f"https://docs.{domain}"

    session = requests.Session()
    session.verify = str(CA_CERT) if CA_CERT.exists() else True

    # 1. Gitea login
    resp = session.get(f"{git_url}/user/login", timeout=30)
    resp.raise_for_status()
    resp = session.post(
        f"{git_url}/user/login",
        data={
            "_csrf": find_csrf(resp.text),
            "user_name": env["GITEA_ADMIN_USER"],
            "password": env["GITEA_ADMIN_PASSWORD"],
        },
        timeout=30,
    )
    if "/user/login" in resp.url:
        sys.exit("Gitea login failed — check GITEA_ADMIN_USER / GITEA_ADMIN_PASSWORD")

    # 2. Outline -> Gitea authorize
    resp = session.get(f"{docs_url}/auth/oidc", allow_redirects=True, timeout=30)

    # 3. Consent grant, only presented on first authorization
    if "/login/oauth/authorize" in resp.url:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(resp.url).query)
        resp = session.post(
            f"{git_url}/login/oauth/grant",
            data={
                "_csrf": find_csrf(resp.text),
                "client_id": query.get("client_id", [""])[0],
                "state": query.get("state", [""])[0],
                "redirect_uri": query.get("redirect_uri", [""])[0],
                "response_type": "code",
                "scope": query.get("scope", [""])[0],
                "granted": "true",
            },
            allow_redirects=True,
            timeout=30,
        )

    # 4. Confirm we actually hold an Outline session
    info = session.post(f"{docs_url}/api/auth.info", json={}, timeout=30)
    if info.status_code != 200:
        sys.exit(
            f"OIDC login did not produce an Outline session (auth.info -> "
            f"{info.status_code}). Landed at: {resp.url}"
        )
    user = info.json().get("data", {}).get("user", {})
    print(f"  signed in to Outline as {user.get('name')} <{user.get('email')}>")
    return session


def mint_token(session: requests.Session, domain: str, name: str) -> str:
    """Create an API key and return its secret value."""
    docs_url = f"https://docs.{domain}"
    # Outline requires the csrfToken cookie echoed back as a header on mutations.
    csrf_token = session.cookies.get("csrfToken")
    if not csrf_token:
        sys.exit("no csrfToken cookie on the Outline session — cannot create a key")

    resp = session.post(
        f"{docs_url}/api/apiKeys.create",
        json={"name": name},
        headers={"x-csrf-token": csrf_token},
        timeout=30,
    )
    if resp.status_code != 200:
        sys.exit(f"apiKeys.create failed ({resp.status_code}): {resp.text[:300]}")

    data = resp.json().get("data", {})
    for field in TOKEN_FIELDS:
        if data.get(field):
            return str(data[field])
    sys.exit(
        f"apiKeys.create succeeded but no token field found. "
        f"Keys present: {sorted(data)}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="ingest", help="label for the API key")
    parser.add_argument(
        "--force", action="store_true",
        help="mint a new token even if OUTLINE_API_TOKEN is already set",
    )
    parser.add_argument(
        "--print-only", action="store_true",
        help="print the token instead of writing it to .env",
    )
    args = parser.parse_args()

    env = read_env()
    if env.get("OUTLINE_API_TOKEN") and not args.force:
        print("  OUTLINE_API_TOKEN already set in .env (use --force to replace)")
        return 0

    for required in ("GITEA_ADMIN_USER", "GITEA_ADMIN_PASSWORD"):
        if not env.get(required):
            sys.exit(f"{required} is not set in .env")

    session = login_to_outline(env)
    token = mint_token(session, env.get("WORLD_DOMAIN", "world.local"), args.name)

    if args.print_only:
        print(token)
    else:
        write_env("OUTLINE_API_TOKEN", token)
        print(f"  wrote OUTLINE_API_TOKEN to .env ({len(token)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
