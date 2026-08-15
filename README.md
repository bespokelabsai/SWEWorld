# SWEWorld

A self-hosted company "world" for agent tasks: a git server, a chat workspace, a
docs wiki, and a mail server, running as **one container image** with
supervisord as PID 1 — the same shape as AlphaShop, so both run under the same
harness.

The agent works inside this world as an ordinary engineer: it has no sudo, and
the only way its code reaches a running service is through CI.

| Role | Service | URL (in-world) | Store |
|---|---|---|---|
| github | Gitea | `http://git.world.local` | SQLite |
| slack | Mattermost | `http://chat.world.local` | PostgreSQL |
| notion | BookStack | `http://docs.world.local` | MariaDB |
| email | Roundcube over Maddy | `http://mail.world.local` | SQLite |
| credentials | passstore | `http://pass.world.local` | static |
| the deployable service | curator | `http://curator.world.local` | — |

Everything is plain HTTP behind one nginx vhost ingress on port 80.

## Quick start

```bash
make build-image      # build sweworld:dev
make run              # boot it and publish every service
make verify           # 24 acceptance checks
make shell            # a shell as the agent (ubuntu, no sudo)
```

## Viewing the world

`make run` publishes every service on its own port and sets `PUBLIC_HOST`, so
the sites are browsable immediately:

| Service | URL | Sign in with |
|---|---|---|
| Gitea | http://localhost:3300 | `worldadmin` / `worldadmin` |
| Mattermost | http://localhost:8065 | `worldadmin` / `worldadmin` |
| BookStack | http://localhost:7090 | `worldadmin@world.local` / `worldadmin` |
| Roundcube | http://localhost:7080 | `worldadmin@world.local` / `worldadmin` |
| Credentials | http://localhost:7250 | — |

Ports are overridable if any clash on your machine:
`make run BOOKSTACK_PORT=9090 ROUNDCUBE_PORT=9080`.

**On a remote machine** VS Code Remote-SSH forwards these automatically; other
clients need `ssh -L 3300:localhost:3300 -L 7090:localhost:7090 …`. Everything
still works because `PUBLIC_HOST=localhost` is what the apps advertise.

**The published port and the container-internal port are deliberately the
same.** BookStack redirects to its `APP_URL`, so if it is published on 7090 but
serves on 8090 internally, that redirect resolves outside the container and
dead-ends inside it — the site half-works, which is worse than failing. The two
numbers move together for that reason. 8080/8090 are avoided entirely because
they collide on most dev machines, and a forwarded port that collides gets
silently remapped to a different local port.

If you would rather use the in-world hostnames, run with `PUBLIC_HOST=` unset
and point `*.world.local` at the host running docker:

```bash
make run PUBLIC_HOST=          # keep the world.local base URLs
sudo ./scripts/hosts.sh add    # 127.0.0.1 git.world.local, chat…, docs…, mail…
# then browse http://git.world.local:8081
```

Why the two modes exist: nginx routes by `Host` header, so reaching the world
from another machine means either resolving `*.world.local` there or hitting
each service on its own port. The second needs no DNS — but Gitea, Mattermost
and BookStack all build absolute links from a configured base URL, so those
have to be repointed or every link and redirect breaks. `PUBLIC_HOST` does
exactly that at boot; see `world/bin/init-runtime.sh`.

## Credentials

One identity is admin on every service:

```
worldadmin / worldadmin          (worldadmin@world.local)
```

The live list is served inside the world at `http://pass.world.local`. The Gitea
API token is at `/etc/sweworld/gitea-token`, readable by the agent.

## Deploying code

This is the point of the privilege model. The agent (`ubuntu`) has no sudo and
cannot reach the supervisord socket, so it cannot restart or install anything.
Code reaches a running service only through CI:

```
git push  →  Gitea Actions (act_runner, host mode, as user `deploy`)
          →  build + test
          →  request-deploy <svc> <build-dir>     # submits to the spool dir
          →  root deploy-daemon
          →  install release, flip `current`, restart under supervisord,
             health-check, roll back to `last-good` on failure
```

`request-deploy` is not setuid and uses no sudo — it writes a request into a
spool directory that only root and `deploy` can touch, and blocks on the result.
gVisor ignores the setuid bit, so this indirection is what makes privilege
separation work at all.

Verified end to end: an agent push reaches a healthy deployed release in ~25s,
and a release that fails its health check is rolled back automatically.

## Architecture notes

Things that are non-obvious and cost real debugging time.

### Two databases, and only two

Each is the sole option for exactly one service:

- **PostgreSQL** — Mattermost. MySQL was removed from the Mattermost codebase in
  v11; there is no SQLite option.
- **MariaDB** — BookStack. It supports MySQL/MariaDB only, no SQLite, no Postgres.

Gitea, Maddy and Roundcube all use SQLite and need no server. There is **no
Redis and no object storage** — BookStack keeps cache, sessions and uploads on
local disk by default, and Mattermost stores files on disk.

### `maddy creds create` exits 0 when it fails

It could not create its `runtime_dir`, printed an error, and returned success —
so `set -e` sailed straight past and the image shipped a mail server with zero
accounts while logging `15-mail: OK`. `world/bootstrap/15-mail.sh` now creates
the directory *and* asserts the account exists afterwards. Do not trust that
exit code.

### Offline CI needs two things

`DEFAULT_ACTIONS_URL = self` makes Gitea resolve actions from its own instance,
so `actions/checkout` is mirrored into a local `actions` org at image build.
Mirror it with explicit refspecs — a `--mirror` push also carries GitHub's
`refs/pull/*`, which Gitea rejects outright and fails the whole push.

Actions are JavaScript, executed as `node dist/index.js`, so the image ships
Node. Without it every workflow dies with `Cannot find: node in PATH` *after*
successfully resolving the action, which reads like a mirror problem and is not.

### `run.sh` belongs to the world, not the repo

A CI build ships whatever the agent wrote, which will not include a service
entrypoint. `deploy-service` installs `/usr/local/lib/sweworld/run-<svc>.sh`
into every release. Without it the new release has nothing to exec, the health
check fails, and every deploy rolls back — correct behaviour, baffling cause.

### Service users and IDs

IDs are assigned by the system, never pinned: the apt install gives gid 999 to
`systemd-journal`, so a hardcoded `groupadd -g 999 deploy` fails. Gitea also
rewrites `~/.ssh` on every start even with SSH disabled, so it needs a home
directory it actually owns (`/var/lib/world/gitea`).

## The curator repository

`bespokelabs/curator` is imported at image build as a standalone copy with every
tie to GitHub severed — `--depth 1` (no upstream history), `rm -rf .git`
(detached), then a fresh `git init` and a single `Initial import` commit.

- working copy: `/opt/world-state/input/curator` (root-only)
- in Gitea: `worldadmin/curator`, default branch `main`
- deployed: `/opt/sweworld/curator/current`, serving on port 9100

That single commit is the baseline. When generated history is ready,
`scripts/ingest_git.py` force-pushes a rewritten history over the same branch.

## Layout

```
world/
  Dockerfile              the world image
  supervisord/            PID 1 config + priority tiers (05/10/20/30)
  nginx/sweworld.conf     vhost ingress: map $host -> backend port
  bootstrap/              build-time seeding, numbered in dependency order
  bin/                    deploy-daemon, request-deploy, deploy-service,
                          wait-for-service, world-verify, init-runtime
  config/                 per-service configuration
  ci-templates/           .gitea/workflows/ci.yml seeded into repos
  passstore/              the credentials page
scripts/                  ingestion: git, docs, chat, mail (+ worldlib)
data/schemas/             the data contracts a generation step must satisfy
data/                     placeholder content matching those contracts
Makefile                  build-image · run · verify · bake-image · push-image
```

## Publishing

Build, populate and publish are deliberately separate steps, so you never push
something you did not intend to.

```bash
make build-image           # base image: services installed, world empty
make bake-image TAG=0.1.0  # boot, ingest data/, gate on world-verify, commit
make push-image TAG=0.1.0  # tag into the registry and push
```

`bake-image` refuses to commit unless `world-verify` passes.

## Status

- Image builds clean; `world-verify` passes 24/24 from a fresh build.
- Agent push → CI → deploy → health check → live, verified end to end.
- `data/schemas/` defines the contracts; `data/` holds placeholder content.
