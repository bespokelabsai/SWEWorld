# SWEWorld

A self-hosted "world": a git server, a docs wiki, a chat workspace, and a mail
server, all running locally behind one reverse proxy with a shared identity.

This repository is **plumbing only**. It stands the services up and defines how
content gets in. It does not generate any content — commits, documents,
messages, and emails are produced by a separate process and dropped into
`data/`.

| Service | Role | URL |
|---|---|---|
| Gitea | git server + OIDC identity provider | https://git.world.local |
| Outline | Notion-style docs | https://docs.world.local |
| Mattermost | Slack-style chat | https://chat.world.local |
| Roundcube | webmail (over Maddy) | https://mail.world.local |
| Maddy | SMTP + IMAP | `localhost:587` / `localhost:143` |
| Traefik | reverse proxy | dashboard on `:8080` |

Backing stores: a dedicated Postgres per service, Redis and MinIO for Outline.

## Quick start

```bash
sudo ./scripts/hosts.sh add     # point *.world.local at 127.0.0.1
pip install -r scripts/requirements.txt
./scripts/bootstrap.sh          # certs, stack, accounts, tokens — idempotent
./scripts/verify.sh             # 37 assertions; exits non-zero on failure
```

`bootstrap.sh` leaves `.env` fully populated. There is no manual browser step.

## Credentials

One identity is admin on every service — the same username and password an
agent working in this world signs in with. It is defined once in `.env`:

```
WORLD_ADMIN_USER=worldadmin
WORLD_ADMIN_PASSWORD=worldadmin-dev-password
WORLD_ADMIN_EMAIL=worldadmin@world.local
```

| Service | Sign in with |
|---|---|
| Gitea | `worldadmin` / `WORLD_ADMIN_PASSWORD` |
| Mattermost | `worldadmin` / `WORLD_ADMIN_PASSWORD` |
| Outline | the **Sign in with Gitea** button — same credentials, no password of its own |
| Roundcube | `worldadmin@world.local` / `WORLD_ADMIN_PASSWORD` |

Change `WORLD_ADMIN_PASSWORD` and re-run `./scripts/bootstrap.sh`. It propagates
the value into the per-service keys **and resets the password on accounts that
already exist**, so the change takes effect on a running world. `verify.sh`
proves the login works on each service rather than assuming it.

MinIO and the Traefik dashboard are internal plumbing and keep their own
settings; neither is part of the agent's identity.

To browse without certificate warnings, trust the generated CA once:

```bash
sudo cp config/tls/world-ca.crt /usr/local/share/ca-certificates/sweworld.crt
sudo update-ca-certificates
```

Firefox and Chrome keep their own trust stores — import the same file there.

Tear everything down with `docker compose down -v` (destroys all data) and
`sudo ./scripts/hosts.sh remove`.

## Four decisions worth knowing

These are the non-obvious constraints. Each one cost real debugging time, and
each will bite anyone who changes the setup without knowing about it.

### 1. Gitea is the identity provider

Outline ships **no password login at all**. It delegates authentication
entirely to an external provider, and its email magic-link sign-in only works
for users who already exist — so it cannot bootstrap its own first account.
Most guides solve this by adding Keycloak, Authelia, or Authentik.

Instead, Gitea acts as the OIDC provider. It has been an OAuth2/OIDC provider
since 1.8 and serves a discovery document at
`https://git.world.local/.well-known/openid-configuration`. `bootstrap.sh`
registers Outline as an OAuth2 client through Gitea's API.

The payoff beyond one fewer container: the world gets a single identity source,
which is what `data/schemas/identities.md` builds on.

**A user's first successful OIDC login is what provisions their Outline account
and workspace.** They cannot be pre-created.

### 2. Everything is HTTPS, and that is not a preference

Outline hardcodes `secure: env.isProduction` on its OAuth CSRF cookie
(`build/server/utils/passport.js`). With `NODE_ENV=production`, signing in over
plain HTTP fails with:

```
Error: Cannot send secure cookie over unencrypted connection
```

There is no environment variable to turn this off. HTTPS is mandatory.

`scripts/gen-certs.sh` therefore generates a local CA and one leaf covering
`*.world.local` plus the internal service names. The CA — rather than a bare
self-signed cert — matters because Outline's OIDC token exchange calls Gitea
*server-side*, and Node rejects self-signed certificates. Outline gets
`NODE_EXTRA_CA_CERTS`, so verification stays on everywhere instead of being
disabled with `NODE_TLS_REJECT_UNAUTHORIZED=0`.

Traefik redirects `:80` to `:443`.

### 3. Traefik will not route to an unhealthy container

Traefik's Docker provider skips containers whose health status is not
`healthy`. The Outline image's built-in healthcheck runs on a **60-second
interval with no `start_period`**, so a freshly started container sits in
`health: starting` for up to a minute — during which `docs.world.local` returns
a bare Traefik `404 page not found` that looks exactly like a misconfigured
router.

`docker-compose.yml` overrides that healthcheck with a 10s interval and a 20s
start period, and `bootstrap.sh` explicitly waits for `healthy`. The override
also passes `X-Forwarded-Proto: https`, because `FORCE_HTTPS` would otherwise
turn the probe into a 301 and the container would never report healthy at all.

The hostnames also resolve *inside* the Docker network, via network aliases on
the Traefik service. Outline performs its OIDC token exchange against
`https://git.world.local` server-side, so the container and the browser must
agree on one URL.

### 4. docker compose ranks the environment above `.env`

An exported shell variable beats the same key in the `.env` file. Because
`bootstrap.sh` sources `.env` early, it holds empty exports for values it is
about to generate — so after writing a new secret to the file it must also
re-`export` it. Otherwise `docker compose up` silently injects the stale empty
value, and Outline renders a login page with no sign-in button.

## Mail

Maddy is configured for a closed world in `config/maddy/maddy.conf`, which
differs from its stock config in four ways: no DMARC/DKIM/SPF/MX checks (they
need public DNS), no outbound delivery (non-local recipients are rejected
immediately rather than queued against MX records that never resolve), no DKIM
signing, and `insecure_auth` on submission and IMAP so ingestion scripts can
log in over plaintext `:143`.

Mail ports publish directly to the host, bypassing Traefik, which proxies HTTP
only.

Credentials and mailboxes are separate objects in Maddy — creating a user needs
both `maddy creds create` and `maddy imap-acct create`.

## Layout

```
docker-compose.yml          the stack
.env.example                every secret, with where each comes from
config/maddy/maddy.conf     closed-world mail config
config/traefik/dynamic.yml  TLS certificate wiring
scripts/
  hosts.sh                  /etc/hosts entries (add|remove|status)
  gen-certs.sh              local CA + leaf
  bootstrap.sh              one-shot setup, idempotent
  mint_outline_token.py     headless OIDC login to mint an API token
  verify.sh                 acceptance checks
  worldlib.py               shared: .env, personas, timestamps, validation
  ingest_git.py             commits.jsonl  -> Gitea
  ingest_docs.py            data/docs/     -> Outline
  ingest_chat.py            messages.jsonl -> Mattermost
  ingest_mail.py            data/emails/   -> Maddy over IMAP
data/
  schemas/                  the data contracts
    identities.md           shared persona list + conventions for all schemas
    commits.md              git history as JSONL
    docs.md                 Outline collections and documents
    messages.md             Mattermost chat history
    emails.md               mailbox contents as .eml + index
  identities.yaml           placeholder personas
  commits.jsonl             placeholder history
  channels.yaml             placeholder channels
  messages.jsonl            placeholder chat
  docs/                     placeholder documents
  emails/                   placeholder mailboxes
```

## Ingestion

```bash
python3 scripts/ingest_git.py  --dry-run     # validate + replay, push nothing
python3 scripts/ingest_docs.py --dry-run
python3 scripts/ingest_chat.py --dry-run
python3 scripts/ingest_mail.py --dry-run
```

Drop `--dry-run` to write to the running world. Common flags: `--data-dir`,
`--env-file`, `--fail-fast`, `-v`.

`--dry-run` is not a no-op. It does the full parse and validation and builds
the real artifacts: `ingest_git.py` replays the entire history into a temp repo
you can `git log`, and `ingest_chat.py` writes the complete Mattermost import
archive. Only the writes to a live service are skipped.

Validation collects **every** error before reporting, each with `file:line`, so
one run tells you everything wrong with a generated dataset:

```
data/commits.jsonl:6: unknown field 'authr' (did you mean 'author'?)
data/commits.jsonl:2: unknown persona 'dave' in author — known ids: alice, bob, carol
data/messages.jsonl:9: thread_id 'does-not-exist' does not match any message id
```

To replace the placeholder content with real generated data, overwrite the
files under `data/` and re-run. To wipe the world first:
`docker compose down -v && ./scripts/bootstrap.sh`.

Out of scope, raising `NotImplementedError` rather than failing quietly: merge
commits, git LFS, submodules, signed commits, and Mattermost custom emoji.

## Data contracts

`data/schemas/` specifies exactly what a data-generation step must produce for
each service. Start with `identities.md` — it defines the persona list every
other schema references, plus the conventions (ISO-8601 timestamps, persona
`id` references, strict unknown-key rejection) that apply across all of them.

The guiding principle: **authored formats stay simple and human-writable; the
ingestion scripts absorb each service's awkwardness.** The one place that is
deliberately not a 1:1 mapping is Mattermost, whose importer demands nested
objects in a fixed order with millisecond epochs — `messages.md` explains why
authoring stays flat there.

Nothing in `data/` is generated yet. The world is expected to be reset with real
generated content later; `docker compose down -v` destroys everything and
`bootstrap.sh` rebuilds it empty.

## Status

- **Phase 1 — infrastructure: complete.** `verify.sh` passes 37/37.
- **Phase 2 — data contracts in `data/schemas/`: complete.**
- **Phase 3 — ingestion scripts: complete.** All four run end to end.
- **Phase 4 — placeholder data and dry runs: complete.** All four validate
  clean data, and reject malformed data with `file:line` errors and exit 1.

The placeholder content in `data/` has been ingested into the running world as
a live end-to-end test. Replace it with generated content when ready.
