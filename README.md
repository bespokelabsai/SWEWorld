# SWEWorld

A self-hosted company "world" for agent tasks: a git server, a chat workspace, a
docs wiki and a mail server, running as **one container image**. An agent works
inside it as an ordinary engineer, with no sudo, and its code reaches a running
service only through CI.

**New here? Read [`docs/how-sweworld-works.html`](docs/how-sweworld-works.html)**
(open it in a browser). It explains the whole repository end to end.

| Role | Service | In-world URL |
|---|---|---|
| github | Gitea | `http://git.world.local` |
| slack | Mattermost | `http://chat.world.local` |
| notion | BookStack | `http://docs.world.local` |
| email | Roundcube over Maddy | `http://mail.world.local` |
| credentials | passstore | `http://pass.world.local` |
| the deployable service | curator | `http://curator.world.local` |

## Quick start

Needs Docker.

```bash
make build-image      # build the base image, sweworld:dev
make run              # boot the world and publish every service
make verify           # acceptance checks against the running world
make shell            # a shell as the agent (ubuntu, no sudo)
make stop             # tear it down
```

`make run` boots the newest baked image (`sweworld:latest`). If nothing has
been baked it boots the empty base, where the services run but hold no
content. To pick another image: `make run RUN_IMAGE=sweworld:0.4.9`.

## Populating the world

Copy a generated corpus into `data/`, check it, and bake it into an image:

```bash
python3 data_gen/install_corpus.py     # newest phase-4 run -> data/
make check-corpus                      # does the corpus agree with itself?
make bake-image TAG=0.4.12             # ingest data/, gate on verify, commit
make run                               # boot it
```

Each bake is about 7 GB on disk. Always bake from `sweworld:dev`. Publishing a
bake is a separate step: `make push-image TAG=… REGISTRY=…`.

## Viewing the world

| Service | URL | Sign in with |
|---|---|---|
| Gitea | http://localhost:3300 | `worldadmin` / `worldadmin` |
| Mattermost | http://localhost:8065 | `worldadmin` / `worldadmin` |
| BookStack | http://localhost:7090 | `worldadmin@world.local` / `worldadmin` |
| Roundcube | http://localhost:7080 | `worldadmin@world.local` / `worldadmin` |
| Credentials | http://localhost:7250 | — |

Gitea and Mattermost want the **username**; BookStack and Roundcube want the
**email**. Persona accounts (for example `dario`, `dario@world.local`) use the
password `persona-world`.

If a port clashes, override it:
`make run BOOKSTACK_PORT=9090 ROUNDCUBE_PORT=9080` (also `GITEA_PORT`,
`MM_PORT`, `PASS_PORT`, `HTTP_PORT`). On a remote machine, forward the ports
over SSH (VS Code Remote-SSH does this automatically).

## Where things are

```
world/            the container image: Dockerfile, supervisord, nginx,
                  bootstrap scripts, deploy tooling, world-verify
scripts/          ingestion of data/ into a running world, and check_corpus
data/             the generated corpus (chat, wiki, mail, repo history)
data/schemas/     the contracts that corpus must satisfy
vendor/           frozen third-party source (curator, actions/checkout)
data_gen/         generates the corpus: the company, its people, months of
                  chat, docs and mail
task_generator/   authors hidden-requirement tasks and emits their arms
harbor_tasks/     the emitted task arms, plus the graders (_suites/)
docs/             standalone HTML guides
failed_tasks/     the first hand-written batch, kept for the record
Makefile          build-image, run, verify, shell, logs, stop,
                  check-corpus, history, bake-image, push-image, clean
```

## Next steps

| To… | Read |
|---|---|
| understand the whole system | [`docs/how-sweworld-works.html`](docs/how-sweworld-works.html) |
| generate or change the corpus | [`data_gen/README.md`](data_gen/README.md), [`docs/data-gen-guide.html`](docs/data-gen-guide.html) |
| build a new task | [`task_generator/README.md`](task_generator/README.md), [`docs/task-generator-guide.html`](docs/task-generator-guide.html) |
| run or inspect task arms | [`harbor_tasks/README.md`](harbor_tasks/README.md) |
| work on the container itself | [`world/README.md`](world/README.md) |
| work in this repo with Claude Code | [`CLAUDE.md`](CLAUDE.md) |
