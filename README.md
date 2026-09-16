# SWEWorld

> **Start here: [`docs/how-sweworld-works.html`](docs/how-sweworld-works.html)** — the whole
> repository explained end to end, with diagrams: the container world, the generated corpus, how a
> requirement gets hidden, and how the task arms are authored, graded and measured. Open it in a
> browser. This README covers the container half only.
>
> Also published at
> <https://claude.ai/code/artifact/663b480e-8703-4129-ac23-633a36e7f179>.
>
> **Building tasks: [`docs/task-generator-guide.html`](docs/task-generator-guide.html)**, a
> walkthrough of `task_generator/` for someone new to it: how a hidden-requirement task is
> designed whole, cut into a ticket and hidden facts, bracketed, planted and measured.
> `task_generator/README.md` opens with the same overview in text, then the full manual.

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
make verify           # acceptance checks (33 at last count, incl. corpus content)
make shell            # a shell as the agent (ubuntu, no sudo)
make stop             # tear it down
```

**`make run` boots the newest baked image** (`sweworld:latest`), falling back to
the empty `sweworld:dev` when nothing has been baked. Name another with
`make run RUN_IMAGE=sweworld:0.2.0`.

**A world with no bake is an empty world** — services up, no content. That is
the base image by design, and it is the single thing most likely to confuse
someone opening BookStack for the first time and finding nothing there.

## From a phase-4 run to a populated world

Three commands, no image rebuild:

```bash
python3 data_gen/install_corpus.py     # newest phase-4 run -> data/
make bake-image TAG=0.4.0              # ingest, gate, commit; moves :latest
make run                               # boot it
```

`install_corpus.py` **replaces** what it owns in `data/` — `docs/`, `emails/`,
`messages.jsonl`, `comments.jsonl` — so a regenerated corpus, or one changed
page, overwrites cleanly with nothing stale left beside it. It never touches
`identities.yaml` or `channels.yaml` (phase 1 writes those), `commits.jsonl`,
`history/` (host-only `make history`) or `schemas/`. It validates the shape
before you spend twenty minutes on a bake: frontmatter keys, every `.eml`
indexed and every indexed path present, comments resolving to real pages and to
parents that exist. Use `--dry-run` to see what it would do, `--run NAME` for a
run other than the newest.

Then `bake-image` boots `sweworld:dev`, copies `data/` and `scripts/` in, runs
the seven ingests in order, and refuses to commit unless `world-verify` passes —
including the content checks, so an image that lost the corpus cannot ship.
Each bake keeps its own immutable tag; `:latest` moves to the newest.

Things worth knowing before you do it:

- **Always bake from `sweworld:dev`.** Baking a baked image ingests everything
  twice *and* nests `scripts/` inside itself, so the run silently executes the
  previous bake's code. The guard in the recipe stops you; heed it rather than
  working around it.
- **Each bake is about 7GB.** Check `df -h /` first. Old tags are worth keeping
  for rollback, but they add up.
- **Nothing lives in a volume.** The data is in the image, which is exactly why
  every container started from that tag has it, and equally why replacing the
  corpus means a new bake rather than editing a running world.
- **Tasks do not follow `:latest`.** See below.

### Making task images use the new world

`harbor_tasks/_env/Dockerfile` pins its base **inline**, and today that is
`sweworld:0.3.1-forge` — repository and history, deliberately no corpus. A new
bake does not reach it. To build tasks on the corpus, edit that `FROM` line to
the tag you baked.

Spell the tag out literally. Do not reintroduce `ARG WORLD_IMAGE` +
`FROM ${WORLD_IMAGE}`: Horizon rewrites `FROM` lines through a pull-through
cache with a textual pass that cannot resolve an ARG, and the hosted build then
dies resolving a literal `${WORLD_IMAGE}`.

### Populating a container you already have running

Only for a world you are experimenting with — the ingests are **not**
idempotent (`ingest_docs.py` and `ingest_mail.py` will happily import
everything a second time), so this is a one-shot on a fresh container:

```bash
docker cp data sweworld:/opt/world-state/data
docker cp scripts sweworld:/opt/world-state/scripts
docker exec sweworld bash -c 'cd /opt/world-state && \
  python3 scripts/ingest_git.py      --data-dir data && \
  python3 scripts/ingest_docs.py     --data-dir data && \
  python3 scripts/ingest_comments.py --data-dir data && \
  python3 scripts/ingest_chat.py     --data-dir data && \
  python3 scripts/ingest_mail.py     --data-dir data'
```

Order matters: comments need the pages to exist, and `ingest_docs.py` hands over
the page ids in `.docs-manifest.json`.

### Checking the corpus before you bake it

```bash
make check-corpus                          # both of the below
python3 scripts/check_corpus.py            # does the corpus agree with itself?
python3 scripts/check_corpus.py --fix      # retime pages and mail to agree with chat
python3 scripts/check_corpus.py --plants   # has an edit broken a planted task?
```

`bake-image` runs the first two before it starts a container, because a bake is
twenty minutes and ~3GB and none of what they catch is visible to `world-verify`,
which counts rows. `CORPUS_CHECK=0` bypasses it for a corpus you know is
mid-repair.

The ingest scripts validate each file against its schema and `world-verify`
counts rows in the populated world; neither reads two files together. That is
where the findings a reader actually notices live — a wiki page announced in
chat before it exists, a PR discussed a month before it was opened, a `.post1`
hotfix announced before the release it patches. `check_corpus.py` cross-checks
chat against the wiki, the mail and `data/history/forge.json`, which is the only
clock in the world that never drifts.

`--fix` repairs the half that is repairable without touching prose: it moves each
page's `created_at`, and each announcement mail's `Date`, to the value that
contradicts the fewest remarks. **Artifacts move and chat does not** — a page
carries one timestamp and no anchor, while 287 planted clues anchor to a chat
message by `"HH:MM author"`, so retiming a message detaches a clue silently and
rewording one cannot. On the corpus as generated, `--fix` takes 173 findings to
55; the 55 that remain each need a wording change and are reported line by line.

`--plants` is the separate question of whether an edit has desynchronised a
planted task, and it is the one to run after touching `data/` by hand:
`inject.located()` substring-searches the corpus for the plant's own words, and
`harbor_tasks/.located-corpora/` caches the old bodies, so a broken plant still
builds a healthy-looking artifact.

### Why the corpus drifts in the first place

Three things decided when something happened and none of them agreed.
`artifacts.json` gives a page a *date* with no time; `worldapps.Clock` stamped
the file from a private counter that added seven minutes per call from the day's
start; and the chat announcing the page ran on the engine's own per-turn cursor,
in a channel-day simulated separately. Same wall clock, three unjoined
authorities — which is why all 108 pages landed between 09:14 and 10:38 on
thirteen distinct values, and why a 09:00 opener could announce a 09:14 file.

`Clock.set_now()` and `data_gen/patches/sim_engine-pin-app-clock.patch` join the
first two: a tool call is now stamped inside the turn that made it. That removes
the arbitrary drift but cannot make a persona write a page before announcing it,
which is what `--fix` reconciles and `check_corpus.py` gates.

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

Not browser-facing, but published so you can point a client at them:

| Purpose | Port | Notes |
|---|---|---|
| nginx vhost ingress | 8081 → 80 | routes `*.world.local` by `Host` header |
| SMTP | 2525 → 25 | inbound mail |
| IMAP | 1143 → 143 | plaintext; what `ingest_mail.py` uses |
| SMTP submission | 1587 → 587 | authenticated send |

Ports are overridable if any clash on your machine:
`make run BOOKSTACK_PORT=9090 ROUNDCUBE_PORT=9080`. The overridable ones are
`GITEA_PORT`, `MM_PORT`, `BOOKSTACK_PORT`, `ROUNDCUBE_PORT`, `PASS_PORT` and
`HTTP_PORT`.

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

| | |
|---|---|
| Username | `worldadmin` |
| Password | `worldadmin` |
| Email | `worldadmin@world.local` |

Gitea and Mattermost want the **username**; BookStack and Roundcube want the
**email**. That difference is the usual reason a login "does not work".

The personas exist as accounts too, but only for mail — they never sign in to
anything else, and their BookStack users carry no password at all, because they
exist purely so authorship has something to point at:

| Persona | Mailbox | Password |
|---|---|---|
| alice | `alice@world.local` | `persona` |
| bob | `bob@world.local` | `persona` |
| carol | `carol@world.local` | `persona` |

The persona password comes from `MAIL_PERSONA_PASSWORD` in `.env` and defaults to
`persona`; the admin's comes from `WORLD_ADMIN_PASSWORD`. Change either there,
not here.

**The admin mailbox receives a copy of every message in the world**, so signing
in to Roundcube as `worldadmin` shows the whole corpus rather than an empty
inbox. One copy per message, not per file — a message already exists twice on
disk, in the sender's Sent and the recipient's INBOX. Turn it off with
`ingest_mail.py --no-admin-copy`.

Tokens, readable by the agent inside the world:

| Service | Path |
|---|---|
| Gitea | `/etc/sweworld/gitea-token` |
| BookStack | `/etc/sweworld/bookstack-token` (`<id>:<secret>`) |

The live list is also served inside the world at `http://pass.world.local`
(published on http://localhost:7250).

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
so `actions/checkout` is seeded into a local `actions` org at image build, from
`vendor/` — only the `v4` tree, since that is the ref the CI template names. A
workflow naming any other ref fails at resolution; add it to `vendor/` if the
world should support it.

This used to be a `git clone --mirror` from GitHub, which needed one non-obvious
trick: push with explicit refspecs, because a `--mirror` push also carries
GitHub's `refs/pull/*`, which Gitea rejects outright and fails the whole push.
Vendoring removes the trap along with the network call — a tree committed fresh
has no pull refs to carry.

Actions are JavaScript, executed as `node dist/index.js`, so the image ships
Node. Without it every workflow dies with `Cannot find: node in PATH` *after*
successfully resolving the action, which reads like a resolution problem and is
not.

### Backdating BookStack means four tables, not one

The API stamps `now` and attributes everything to the token owner, so ingestion
creates through the API and then corrects the database. The trap is how many
places authorship is stored:

| Table | Surfaces as |
|---|---|
| `entities` | the Created/Updated byline on a page, chapter or book |
| `comments` | the author and date on each comment |
| `page_revisions` | "Revision #1 … by …", and the revision history |
| `activities` | **the Recent Activity feed** |

Correcting only the first two leaves a wiki whose pages read correctly but whose
dashboard says "World Admin created page X, 3 minutes ago" for every item in the
world. That feed is the dashboard's main content and appears on every book page,
so it is the first thing anyone sees — not an audit log tucked away in an admin
screen, which is what it looks like from the schema.

Comment activities are the awkward ones: `comment_create` carries no
`loggable_id` at all and names its comment only in a `detail` string, and the
`commented_on` row that follows it points at the *page*. Neither can be joined to
an author directly. See `resettle_history()` in `scripts/ingest_docs.py`.

Books need attention for a different reason: they come from `collections.yaml`,
which has no author or date, so they were never backdated at all. Each one now
takes the author and date of its earliest document — a book existed when someone
wrote its first page.

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

`bespokelabs/curator` is **vendored, not cloned**. `vendor/curator-<sha>.tar.gz`
is a frozen snapshot with no `.git` in it — the tie to GitHub was severed once,
when the snapshot was made. At image build it is unpacked and given a fresh
`git init` and a single `Initial import` commit.

- working copy: `/opt/world-state/input/curator` (root-only)
- in Gitea: `worldadmin/curator`, default branch `main`
- deployed: `/opt/sweworld/curator/current`, serving on port 9100

That single commit is the baseline. When generated history is ready,
`scripts/ingest_git.py` force-pushes a rewritten history over the same branch.

The build reaches no network for it, and the tree is identical every time. That
second property is the important one: generated history has to land exactly on
this tree, and a `git clone` of `main` moved underneath it. The snapshot is
pinned by `CURATOR_SNAPSHOT` in `world/Dockerfile`; `vendor/README.md` records
the upstream commit and how to refresh it.

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
vendor/                   frozen third-party source (curator), never cloned
scripts/                  ingestion: git, docs, comments, chat, mail
                          (+ worldlib, check_corpus)
data/schemas/             the data contracts a generation step must satisfy
data/                     the corpus those contracts describe — 9.6k chat
                          messages, 108 wiki pages, 613 mails, and the
                          rewritten curator history under history/
Makefile                  build-image · run · verify · bake-image · push-image

data_gen/                 generates the corpus: stages 0-2 read the real
                          curator repository, phases 1-4 build the company,
                          its people and months of chat, docs and mail
                          (guide: docs/data-gen-guide.html)
task_generator/           authors one hidden-requirement task at a time, and
                          emits its arms into harbor_tasks/ (guide:
                          docs/task-generator-guide.html)
docs/                     the three standalone HTML guides: the whole repo,
                          task_generator, and data_gen
harbor_tasks/             the emitted arms, plus _suites/ (the graders that
                          run inside the container) and _env/ (their bases)
failed_tasks/             the first hand-written batch, kept for the record
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
