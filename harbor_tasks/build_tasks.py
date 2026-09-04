#!/usr/bin/env python3
"""Turn `data_gen/input/tasks.json` into Harbor tasks.

Each task is emitted twice:

  <id>-<slug>/<slug>        the real task — the agent gets `title` and
                            `description` and nothing else, exactly what phase 3
                            calls "stated openly"
  <id>-<slug>/<slug>-spec   the positive control — the same task with both
                            hidden requirements written into the ticket

Both live in one folder per task, alongside that task's `fixtures/`. Harbor
reads a directory of tasks with a single non-recursive `iterdir()`
(`models/job/config.py:_get_local_task_configs`), so a group directory is
exactly one `-p` target and gives `harbor run -p harbor_tasks/t1-cache-stats`
the whole bracket for one task. The leaf names stay globally unique because a
trial directory is named after its task directory — two tasks both called
`blind` would land as two `blind__<hash>` rows nobody can tell apart.

The control is what makes a failure readable. A task that fails without its
corpus has told you either that the hidden requirement bit or that the tests are
over-constrained, and those look identical from the outside; the control
separates them for the cost of one extra `instruction.md`. Only `instruction.md`
and `[task].name` may differ between a pair — anything else and the pair stops
being a control.

    python3 harbor_tasks/build_tasks.py --limit 4
    python3 harbor_tasks/build_tasks.py --pick t7,t12

Rebuilding is idempotent: generated files are overwritten, `_suites/` is copied
into each task's `tests/` (Harbor copies `tests/` to /tests at verify time, and
only whole directories travel).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import clue_digest

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
TASKS_JSON = REPO / "data_gen" / "input" / "tasks.json"
SUITES = ROOT / "_suites"

# The base every task builds one thin layer on. Verified to be repository +
# history with nothing else: see harbor_tasks/_env/Dockerfile.
BASE_IMAGE = "sweworld:repo-only-dev"
# The same world with the corpus in it — nine months of chat, the wiki and the
# mailboxes. Only the `world` arm boots this; every other arm has to see an empty
# Mattermost, or the corpus stops being the one variable between them.
WORLD_IMAGE = "sweworld:0.4.4"
# The same world, published to Horizon's registry and pinned by digest. Horizon
# cannot resolve a local tag, so the hosted world arm builds FROM this instead.
#
# One entry, shared by every task, and that is the point of ingesting the plant at
# container start: the image holds the company and nothing task-specific, so a
# second task needs no second publish. Pinned by digest because the corpus is the
# independent variable -- a moved tag would change what a task measures without
# changing the task.
WORLD_REGISTRY = ("us-central1-docker.pkg.dev/apex-485220/horizon/environments/"
                  "sweworld-batch-payload-plan"
                  "@sha256:f34db48366a6603074553d14986d5a58fb55abe8a71231321f838d90c1e6347f")

# Task ids whose emitted directories must not be regenerated.
#
# This began as protection against `emit()` overwriting g1's hand-written oracle
# with a stub -- a 1.0 reference solution replaced by a 0.0 one, with the same
# success line printed either way. `solve()` generates the real oracle now, so
# that specific danger is gone: regenerating g1 would produce the same script
# bar the commit message and branch name.
#
# g1 stays frozen anyway, for a different and better reason. It is the one task
# measured across all four arms, and those numbers are only comparable to each
# other while the artifact that produced them does not move. Everything here is
# validated against the NEW task instead.
FROZEN = {"g1"}

# Slugs for the tasks phase 3 currently plants. A generated slug from the title
# would do, but these are the names that will appear in every result table and
# in `jobs/`, so the four in use are named by hand.
# t1, t12, t23 and t40 are the four the plant covers — phase 3 was run
# `--pick t1,t12,t23,t40` and then renumbered them t1..t4 in clues.json, which
# is why the ids there do not match these. t2, t3 and t4 have suites but no
# plant, so they get spec and blind arms and no clues arm.
SLUGS = {
    1: "cache-stats",
    2: "batch-cost-estimate",
    3: "shared-limiter",
    4: "deepseek-empty-retry",
    12: "schema-validation",
    23: "batch-status-resume",
    40: "executor-image-pin",
}

# Which suite directory under _suites/ grades which task.
SUITE_DIR = {
    1: "t1_cache_stats",
    2: "t2_batch_cost",
    3: "t3_shared_limiter",
    4: "t4_deepseek_empty",
    12: "t12_schema_validation",
    23: "t23_batch_status_resume",
    40: "t40_executor_image_pin",
}

FACT_FIELDS = ("rule", "scope", "exclusions_or_crossover", "failure_behavior",
               "observability")


def toml_str(text: str) -> str:
    """A TOML basic-string body: backslashes and double quotes escaped.

    None of the 60 hand-written titles in tasks.json contains a double quote, so
    interpolating one raw was safe for years. A generated title is not bound by
    that: `Batch payload planner for `batch_size="auto"`` closed the TOML string
    mid-value, and harbor died with `TOMLDecodeError: Expected newline or end of
    document` — which reads like a corrupt template rather than an unescaped
    title.
    """
    return text.replace("\\", "\\\\").replace('"', '\\"')


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


# =============================================================================
# The files
# =============================================================================
# Four, everywhere, and measured rather than assumed. Docker REFUSES a `cpus`
# above the host's count rather than capping it -- "range of CPUs is from 0.01 to
# 4.00, as there are only 4 CPUs available" -- so too high a value does not make a
# run slower, it makes it impossible: the container never starts, the trial
# reports `RuntimeError` with a bare {"mean": 0.0} and no per-fact keys, and that
# reads exactly like a score of zero. Asking for 8 failed on this box AND on
# Horizon's validation runner, which has four too. g1's world-hosted has always
# said 4 and has always validated.
#
# TWO, and the two runners are not the same size -- which is why this looked for
# hours like an agent-type problem. Measured on 2026-09-03:
#
#   validation runner:  "range of CPUs is from 0.01 to 4.00, as there are only 4"
#   evaluation runner:  "range of CPUs is from 0.01 to 2.00, as there are only 2"
#
# Docker REFUSES a `cpus` above the host count rather than capping it, so 4 passes
# `tasks validate` with a clean Final Score: 1.0 and then errors EVERY rollout at
# `docker compose up --detach --wait`, buried under a screen of BuildKit progress
# lines. A green validation is therefore no evidence that the eval will start.
# Set this to the SMALLER runner.
#
# Raising it is only safe in company with `evaluations submit --machine-type`, which
# is what actually gives the eval runner more cores -- and `tasks validate` has no
# such flag, so a task.toml above 4 cannot be validated at all any more. g6's
# world-hosted arm is hand-set to 8 for a run submitted with `--machine-type
# e2-standard-8`; rebuilding it from here puts it back to 2, which is correct for a
# default-machine submit and wrong for that one.
HOSTED_CPUS = 2
LOCAL_CPUS = 4


def task_toml(name: str, task: dict, variant: str) -> str:
    """Per-task Harbor config, following AlphaShop's validated shape.

    `[agent] user = "ubuntu"` and `[verifier] user = "root"` become
    `docker compose exec -u`, which is what maps Harbor onto the world's own
    privilege split: the agent is an ordinary engineer with no sudo, and the
    grader needs root to read the pristine tree at /opt/world-state and the
    release symlinks under /opt/sweworld.
    """
    kind = {
        "spec": "The two requirements that decide correctness are stated in "
                "the ticket.",
        "clues": "The requirements that decide correctness are not stated, but "
                 "every remark the team made about them is quoted in the "
                 "ticket.",
        "blind": "The requirements that decide correctness are not written "
                 "down anywhere the agent is pointed at.",
        "world-hosted": "The requirements that decide correctness are not "
                 "stated. The remarks they were inferred from are in the "
                 "company's chat, wiki and mail, and the agent has to find them.",
        "world": "The requirements that decide correctness are not stated. The "
                 "remarks they were inferred from are in the company's chat, "
                 "wiki and mail, and the agent has to find them.",
    }[variant]
    cpus = HOSTED_CPUS if variant == "world-hosted" else LOCAL_CPUS
    return f'''schema_version = "1.4"

[task]
name = "bespokelabs/{name}"
version = "1.0.0"
description = "{toml_str(task['title'])}. {kind}"
authors = [{{ name = "SWEWorld" }}]
keywords = ["sweworld", "curator", "python", "hidden-requirements"{'' if variant == 'blind' else f', "{variant}"'}]

[metadata]
category = "implementation"
difficulty = "{'hard' if variant == 'blind' else 'medium'}"
source_task = "{task['_id']}"
variant = "{variant}"
# Kept beside `variant`: a reader that predates the extra arms falls back to
# this. `spec` and `clues` are controls — they hand over what the task hides.
# `world` is not: it is the blind ticket against a corpus that has the answers
# in it somewhere, so a reader falling back should read it as blind.
control = {str(variant in ('spec', 'clues')).lower()}

[agent]
# The world's engineer: uid 1000, no sudo, cannot reach supervisord, cannot read
# /opt/world-state or the deploy queue.
user = "ubuntu"
timeout_sec = 3600.0

[verifier]
# Root, because grading reads the pristine tree at /opt/world-state/input/curator
# (to tell an agent's new identifiers from curator's own) and the release
# symlinks under /opt/sweworld/curator, neither of which the agent can touch —
# so the state being graded cannot be forged.
user = "root"
# 2400, not 1800. Horizon's own lint rejects anything under 2000s, and the reason
# is worth keeping: a grader that overruns is KILLED, and a killed grader scores
# zero — so a perfect solution and a broken one produce the same result and
# nothing in the output says which happened.
timeout_sec = 2400.0

[environment]
# NO docker_image and NO docker-compose.yaml. One thin layer on the world image,
# booting supervisord through ENTRYPOINT (environment/task-entrypoint.sh).
# Harbor's compose template appends `command: ["sh","-c","sleep infinity"]`, and
# Compose's `command:` overrides CMD rather than ENTRYPOINT, so with a compose
# file those args reach supervisord as argv and the world never boots.
build_timeout_sec = 3600.0
# claude-code installs itself from downloads.claude.ai and calls the API.
network_mode = "public"
cpus = {cpus}
memory_mb = 13000

[environment.healthcheck]
# Each probe must be FAST: Harbor caps one probe at timeout_sec and does the
# waiting itself through start_period_sec + retries, so wait-for-service's own
# 600s default has to be capped or every probe blows the cap and counts failed.
#
# Gitea by name, not `--all`. These tasks need the repository and the CI
# runner; Mattermost and BookStack are empty here and waiting on them only
# adds minutes. (`--core` is AlphaShop's flag and does not exist in this
# world: `wait-for-service` here takes [--all] [--quiet] [service...], and an
# unknown name exits 1, which fails every probe.)
#
# This also carries task setup, because the healthcheck is the only hook that
# runs as root before the agent starts. task-setup.sh is idempotent.
command = "WAIT_TIMEOUT=15 wait-for-service --quiet gitea && /usr/local/bin/task-setup.sh"
start_period_sec = 600.0
start_interval_sec = 10.0
interval_sec = 15.0
# 900, not 120. Harbor caps ONE probe at this, and the probe now carries the
# plant ingestion -- a Mattermost bulk import plus BookStack pages plus mail.
# At 120 the probe is killed mid-import, the next one starts over, and the trial
# dies having never finished a single pass.
timeout_sec = 900.0
retries = 20
'''


def instruction(task: dict, variant: str) -> str:
    """What the agent is told.

    The openly-stated half is `title` + `description` verbatim — the same two
    fields phase 3 hands the planter under "THE FEATURE (stated openly, an agent
    will be told this)". Nothing else from tasks.json may appear here unless
    this is the control.

    The orientation section is deliberately identical in both worlds, corpus or
    no corpus. It names chat, the wiki and mail even though this world's are
    empty: when the same instruction is run against the populated world, the
    corpus is then the only variable, and the difference between the two runs is
    attributable to it rather than to a reworded ticket.
    """
    body = [
        "You are an engineer at this company, working on `curator` — the "
        "Python library for bulk LLM inference and dataset curation that the "
        "company ships. You have an ordinary engineer's access and nothing "
        "more: no sudo, and no way to put code on a running service except "
        "through CI.",
        "",
        "## The ticket",
        "",
        f"**{task['title']}**",
        "",
        task["description"],
        "",
    ]

    if variant == "spec":
        body += [
            "## Requirements settled earlier",
            "",
            "These were agreed before the ticket was written. They are not "
            "obvious from the code, so they are repeated here in full:",
            "",
        ]
        for i, req in enumerate(task["hidden_requirements"], 1):
            body.append(f"{i}.")
            for field in FACT_FIELDS:
                if req["requirement"].get(field):
                    label = field.replace("_", " ")
                    body.append(f"   - *{label}*: {req['requirement'][field]}")
            body.append("")

    if variant == "clues":
        # Not the requirement — the remarks it was inferred from. What is and
        # is not quoted here is clue_digest's decision; see its docstring.
        # Matched by TITLE: the plant renumbers whatever `--pick` selected, so
        # an id match pairs a task with another feature's remarks.
        body += [clue_digest.render(task["_id"], task["title"]), ""]

    body += [
        "## Getting around",
        "",
        "- The repository is in Gitea at "
        "<http://git.world.local/worldadmin/curator.git>. Your account is "
        "`worldadmin`, password `worldadmin`; a token is readable at "
        "`/etc/sweworld/gitea-token` if you prefer.",
        "- Nothing is checked out for you. Clone it.",
        "- `curator` and its dependencies are installed in the virtualenv at "
        "`$CURATOR_VENV` (`/opt/curator-dev/venv`), so "
        "`$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the "
        "library and its tests. The library itself is NOT installed there — put "
        "your checkout's `src/` on `PYTHONPATH`.",
        "- Complete this ticket to the best of your ability using every source "
        "of information you can reach: the repository's own history and issues, "
        "the company chat, the wiki, internal mail. Any of them may carry "
        "something the ticket does not say.",
        # Three world-arm rollouts out of three FOUND the second requirement and
        # then refused it, in as many words: "all of it is tagged 'when we get to
        # it' and none of it is in the ticket's API, so I built neither", "separate
        # work, shapes still moving". The corpus was not wrong -- real teams settle
        # a design and then do not get to it, which is the reason a ticket exists
        # now -- and rewording the corpus to sound more urgent would only make it
        # read like a specification. What was missing was this sentence.
        "- Some of what this company decided, it never got round to doing. The "
        "history holds designs that were agreed and then parked — \"that's its "
        "own ticket\", \"when we get to it\" — and parked is not cancelled. Where "
        "a decision was settled and the code does not reflect it yet, carrying it "
        "out is part of this ticket, not a reason to leave it alone.",
        # The bullet above shut the "parked means cancelled" door and two hosted
        # rollouts walked straight through the one next to it, independently and
        # in almost the same words: "the ticket is the current authoritative spec
        # and supersedes those", "the ticket is my assignment and is more
        # recent/specific". Both had READ the requirement -- one quoted the field
        # name and its exact semantics out of a page comment -- and then filed it
        # as an older draft. Nothing had told them the ticket is a summary rather
        # than the latest revision of one.
        "- The ticket is where the work starts, not a complete specification of "
        "it, and it is not the newest word on anything. It was written short. "
        "Where the record settles something the ticket leaves out, or names a "
        "field, a value or a behaviour the ticket does not, that is an addition "
        "to what you owe — not an earlier draft the ticket has replaced. "
        # First version ended "the record is not the stale side of it", and two
        # rollouts read that as licence to DELETE something the ticket states --
        # both dropped `truncated_streams` from `CodeExecutionResult` on the
        # strength of a wiki line about a different field, and lost the open
        # feature for it. The record adds; it does not subtract. Nothing is
        # hidden by saying so: `split` refuses to ship a fact the ticket prints,
        # so every hidden requirement here is something the ticket is SILENT
        # about, and an apparent contradiction is always a misreading.
        "So the record adds to the ticket. Where the ticket states something "
        "outright, that stands — a page that looks like it contradicts the "
        "ticket is nearly always about a neighbouring question, and the move is "
        "to find what it actually names rather than overrule the ticket with it.",
        "- Chat is at <http://chat.world.local>, the wiki at "
        "<http://docs.world.local>, webmail at <http://mail.world.local>, and "
        "the service list at <http://pass.world.local>. Gitea and Mattermost "
        "want the username `worldadmin`; BookStack and Roundcube want the email "
        "`worldadmin@world.local`.",
        # A trial spent four calls scraping BookStack's search HTML, stripped
        # the tags, saw only the page header and concluded the wiki was empty.
        # The token was sitting in /etc/sweworld the whole time and the same
        # search over the API answers in JSON.
        "- The wiki has a REST API — `Authorization: Token $(cat "
        "/etc/sweworld/bookstack-token)` — and "
        "`/api/search?query=...`, `/api/pages/{id}` return JSON, which is "
        "easier to read than the HTML.",
        # BookStack's search index is keyed by ENTITY (`entity_type`/`entity_id`)
        # and `Comment extends Model`, not `Entity` — so a page comment is not
        # indexed and cannot be made so by configuration. A world-arm trial
        # searched the wiki seven times, opened no page, and lost two facts to a
        # constant whose only mention is in a comment. The capability was always
        # there; nothing said so.
        "- Wiki pages carry **comments**, and BookStack's search does not index "
        "them — a term that exists only in a comment returns nothing from "
        "`/api/search`. `/api/pages/{id}` returns that page's `comments` "
        "alongside its body, so a page worth reading is worth fetching whole.",
        "- `wait-for-service <name>` blocks until a service answers.",
        "",
        "## Done means",
        "",
        "The change is merged to `main` in Gitea, CI is green for that commit, "
        "and the running release has picked it up — pushing is what deploys "
        "here, and it takes about half a minute.",
    ]
    return "\n".join(body) + "\n"


DOCKERFILE = f'''# One thin layer on the world image.
#
# The base ref is spelled out INLINE. Do not reintroduce `ARG WORLD_IMAGE` +
# `FROM ${{WORLD_IMAGE}}`: Horizon rewrites FROM lines through its Docker Hub
# pull-through cache with a textual pass that cannot resolve an ARG, and the
# hosted build then dies trying to resolve a literal "${{WORLD_IMAGE}}".
#
# {BASE_IMAGE} is the world with the repository and its full history and
# nothing else — Mattermost, BookStack and mail are empty — plus the virtualenv
# an engineer needs to actually run curator. See harbor_tasks/_env/Dockerfile.
FROM {BASE_IMAGE}

# The terminal recorder. Harbor records the agent's session through tmux and
# asciinema, and neither is in the world image — so without this the trial still
# runs, still grades, and simply produces no transcript. That is the worst shape
# a missing dependency can take: every diagnosis of WHY an arm scored what it did
# has come from reading those recordings back. Unpinned deliberately; an exact
# version pin rots faster than the recorder's interface.
RUN apt-get update \\
 && apt-get install -y --no-install-recommends tmux asciinema \\
 && rm -rf /var/lib/apt/lists/*

# The world's services can boot slowly on a cold, shared host.
ENV WAIT_TIMEOUT=600

COPY setup.sh /usr/local/bin/task-setup.sh
RUN chmod 0755 /usr/local/bin/task-setup.sh

# This task's plant, ingested by task-setup.sh once the world is up, instead of
# being baked into a per-task world image. `plant/` always exists and holds a
# README when there is nothing to plant: Harbor drops zero-byte files, and
# BuildKit then fails a COPY of a missing directory with "failed to calculate
# checksum of ref", which names no path and reads like a platform fault.
COPY plant /opt/task-plant

COPY --chmod=0755 task-entrypoint.sh /usr/local/bin/task-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/task-entrypoint.sh"]
'''

# The populated world is a RELEASE bake and carries no dev virtualenv, while the
# verifier runs pytest with `$CURATOR_VENV/bin/python`. Without the copy the suite
# never runs at all: every fact scores zero and `suite_error` fires, which reads
# exactly like an agent that failed everything rather than a broken image.
HOSTED_DOCKERFILE = DOCKERFILE.replace(
    f"FROM {BASE_IMAGE}",
    f"FROM {WORLD_REGISTRY}\n\n"
    "# No `COPY --from=sweworld:repo-only-dev` — Horizon cannot resolve a second\n"
    "# local tag either, so /opt/curator-dev is already inside the published image.\n"
    "\n"
    "# tmux and asciinema are the terminal recording, not the trial: without them\n"
    "# the run still grades and the only record of what the agent typed is gone.\n"
    "RUN apt-get update \\\n"
    " && apt-get install -y --no-install-recommends tmux asciinema \\\n"
    " && rm -rf /var/lib/apt/lists/*")

WORLD_DOCKERFILE = DOCKERFILE.replace(
    f"FROM {BASE_IMAGE}",
    f"FROM {WORLD_IMAGE}\n\nCOPY --from={BASE_IMAGE} /opt/curator-dev /opt/curator-dev"
).replace(
    f"# {BASE_IMAGE} is the world with the repository and its full history and\n"
    "# nothing else — Mattermost, BookStack and mail are empty — plus the virtualenv\n"
    "# an engineer needs to actually run curator. See harbor_tasks/_env/Dockerfile.",
    f"# {WORLD_IMAGE} is the same world with the corpus baked in: the repository and\n"
    "# its history, and nine months of chat, wiki and mail. The remarks this task's\n"
    "# requirements are hidden in are somewhere in there.")

ENTRYPOINT = '''#!/bin/bash
# Boot the world as PID 1.
#
# Harbor appends `command: ["sh","-c","sleep infinity"]` to keep a plain image
# alive and exec the agent into it. This image's real init is supervisord, and
# Compose's `command:` overrides CMD rather than ENTRYPOINT — so those args
# would be handed to supervisord as positional arguments and the world would
# never boot. Ignore them and run supervisord in the foreground: it stays PID 1,
# reaping zombies and keeping the container alive, while the harness execs the
# agent and then the verifier in over `docker exec`.
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
'''

SETUP = '''#!/bin/bash
# Task setup. Runs as root from the healthcheck, repeatedly, before the agent
# starts — so it must be idempotent and must return fast once it has run.
set -uo pipefail
MARK=/opt/world-state/task-setup.done
[[ -f "$MARK" ]] && exit 0

install -d -m 0700 /opt/world-state

# Record the commit main sat at before the agent touched anything. The grader
# needs it to tell "pushed something" from "pushed nothing": comparing against a
# hardcoded SHA would break the moment the world image is rebaked.
TOKEN=$(cat /etc/sweworld/gitea-token 2>/dev/null || echo "")
BASE=$(curl -fsS -H "Authorization: token $TOKEN" \\
  "http://127.0.0.1:3300/api/v1/repos/worldadmin/curator/branches/main" 2>/dev/null \\
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["commit"]["id"])' 2>/dev/null || echo "")
[[ -n "$BASE" ]] || exit 1        # try again on the next probe

{
  echo "BASE_SHA=$BASE"
  echo "BASE_RELEASE=$(readlink -f /opt/sweworld/curator/current 2>/dev/null || echo none)"
} > /opt/world-state/baseline.env
chmod 0600 /opt/world-state/baseline.env

# The plant, ingested into the RUNNING world rather than baked into the image.
#
# /opt/task-plant holds only what this task adds -- a few dozen messages, a
# handful of comments, some mail and pages -- in the same layout data/ uses. Every
# ingest script takes --data-dir, and Mattermost's bulk import, BookStack's API
# and maddy's delivery are all additive, so this appends to the corpus already
# there instead of replacing it.
#
# Doing it here rather than in a bake is what lets ONE world image serve every
# task. The alternative was `install_corpus.py --apply` plus `make bake-image` per
# task: half an hour, a 7.8GB image, and a tag that then has to be threaded back
# into build_tasks.py so the answer key names the right world.
#
# Order matters and is the same order the bake used: comments need their pages to
# exist first.
if [[ -d /opt/task-plant ]]; then
  # The services the ingest actually talks to. The healthcheck only waits for
  # gitea -- that is all the baseline setup needed, to read main's SHA -- and
  # ingesting into Mattermost, BookStack and maddy before they answer fails,
  # returns non-zero, and fails the healthcheck. Twenty times, then the trial is
  # dead with "Healthcheck failed after 20 consecutive retries" and nothing saying
  # which of the four services was the problem.
  # These exact names. `wait-for-service` takes the world's own service list
  # and exits 1 on anything else -- `php-fpm` is a supervisord program but not
  # a name it knows, so naming it made this line fail every time, setup.sh
  # exit 1, and the healthcheck burn all 20 retries against a world that was
  # healthy throughout. The failing guard reported as the thing it guarded.
  WAIT_TIMEOUT=240 wait-for-service --quiet mattermost mariadb bookstack maddy \
    || { echo "task-plant: services not up" >&2; exit 1; }
  # The roster comes from the WORLD, not the plant. The ingest scripts resolve
  # every author and channel through channels.yaml and identities.yaml in the
  # --data-dir they are given, and a delta that ships its own copy is a second
  # source of truth that drifts the moment the corpus is rebuilt. Without them
  # every row fails with "unknown channel 'releases' -- declared channels: (none)".
  for roster in channels.yaml identities.yaml; do
    cp -f "/opt/world-state/data/$roster" "/opt/task-plant/$roster" 2>/dev/null || {
      echo "task-plant: no /opt/world-state/data/$roster" >&2; exit 1; }
  done
  # Comments attach to pages, and `ingest_comments` resolves each one against the
  # docs/ tree in its --data-dir; without it the run dies on "/opt/task-plant/docs
  # does not exist" even though every page it needs is already in the world. A
  # delta that adds no new pages therefore borrows the world's, read-only. If the
  # plant brought its own pages, those win and this does nothing.
  if [[ -e /opt/task-plant/docs ]]; then
    # The plant brought its own pages, so it needs the book list that says which
    # directories are real: "directory 'engineering' has no entry in
    # collections.yaml -- unlisted directories are an error, not an implicit book".
    # Same principle as the roster above -- structure comes from the world.
    cp -f /opt/world-state/data/docs/collections.yaml /opt/task-plant/docs/ 2>/dev/null
    # And the existing pages, because a comment resolves against the whole tree
    # and most of this plant's comments hang off pages the world already has.
    cp -rn /opt/world-state/data/docs/. /opt/task-plant/docs/ 2>/dev/null
  else
    ln -s /opt/world-state/data/docs /opt/task-plant/docs
  fi
  S=/opt/world-state/scripts
  # Each step only when the plant has something for it. A delta rarely touches all
  # four surfaces -- g2 has chat, mail and page comments and no new wiki pages at
  # all -- and `ingest_docs` against a missing docs/ does not no-op, it fails with
  # "524 validation error(s)" and takes the healthcheck down with it.
  for step in ingest_chat ingest_docs ingest_comments ingest_mail; do
    [[ -f "$S/$step.py" ]] || continue
    case "$step" in
      ingest_chat)     [[ -s /opt/task-plant/messages.jsonl ]] || continue ;;
      ingest_docs)     [[ -d /opt/task-plant/docs ]]           || continue ;;
      ingest_comments) [[ -s /opt/task-plant/comments.jsonl ]] || continue ;;
      ingest_mail)     [[ -d /opt/task-plant/emails ]]         || continue ;;
    esac
    python3 "$S/$step.py" --data-dir /opt/task-plant >>/var/log/task-plant.log 2>&1 \
      || { echo "task-plant: $step failed, see /var/log/task-plant.log" >&2; exit 1; }
  done
  # Mattermost search is MEMBER-SCOPED, and the admin is created by bootstrap
  # rather than by the import, so it lands in Mattermost's defaults --
  # town-square and off-topic, both empty. An agent handed those credentials
  # searches a 9,800-message corpus and gets zero hits for every term in it,
  # then reasonably concludes there is no chat to read. Both g2 hosted world
  # rollouts did exactly that: five terms certainly present, nothing back, and
  # every hidden fact scored 0 in a world that physically contained them.
  #
  # `ingest_chat.join_admin_to_channels()` fixes this at the source, but the
  # script that runs here is the one baked into the IMAGE
  # (/opt/world-state/scripts), not the one this task was built against, so a
  # base image published before that fix ingests the new plant with the old
  # script and silently undoes it. This is the guard that does not care how old
  # the image is. It is idempotent -- adding an existing member is a no-op --
  # so it costs nothing on a world that already got it right.
  python3 - <<'PLANT_JOIN' >>/var/log/task-plant.log 2>&1 || \
    echo "task-plant: admin channel-join guard failed, chat search may be blind" >&2
import json, urllib.request

BASE = "http://localhost:8065/api/v4"

def call(path, data=None, token=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    resp = urllib.request.urlopen(req, timeout=30)
    return resp, json.loads(resp.read() or b"null")

# The session token comes back as a HEADER, not in the body -- four calls of one
# hosted rollout went on parsing `.token` out of the JSON and getting "".
resp, me = call("/users/login", {"login_id": "worldadmin", "password": "worldadmin"})
token = resp.headers.get("Token")
if not token:
    raise SystemExit("no Token header from /users/login")

joined = 0
_, teams = call("/users/me/teams", token=token)
for team in teams:
    page = 0
    while True:
        _, chans = call(f"/teams/{team['id']}/channels?per_page=200&page={page}",
                        token=token)
        if not chans:
            break
        for chan in chans:
            # Open channels only. A private channel the admin was never in is not
            # something to force an entry into, and DMs have no team.
            if chan.get("type") != "O":
                continue
            try:
                call(f"/channels/{chan['id']}/members", {"user_id": me["id"]},
                     token=token)
                joined += 1
            except Exception:
                pass          # already a member, which is the common case
        page += 1
print(f"task-plant: admin in {joined} channel(s)")
PLANT_JOIN
  echo "task-plant: ingested" >> /var/log/task-plant.log
fi

touch "$MARK"
exit 0
'''

STUB_SOLVE = '''#!/bin/bash
# Reference solution, run by `harbor run -a oracle`.
#
# A no-op, because this task has no `fixtures/oracle.patch` to apply — the
# hand-written tasks in data_gen/input/tasks.json carry an `oracle.py` fixture
# used by the bracket instead, and there is no generated diff to push. What the
# `-spec` control proves for those is that the suite can be passed at all.
#
# Running it is still worth something: it proves the image builds, the world
# boots, the verifier runs and the reward file lands. Expect a score of zero.
#
# NOTE this scores 0, and Horizon refuses to schedule an evaluation against a
# task whose oracle does not score ~1.0 ("409 ... evaluation validation gate").
# A task built from task_generator gets the real oracle below and passes; one
# built from tasks.json does not, and cannot be run hosted until it has a patch.
set -uo pipefail
echo "oracle: no reference implementation; this run checks the plumbing only"
exit 0
'''

# The real one. Everything above the patch, then the patch, then everything below.
REAL_SOLVE_HEAD = '''#!/bin/bash
# Reference solution, run by `harbor run -a oracle` and by Horizon's validation
# gate — which is why it has to be real. Horizon refuses to schedule any
# evaluation against a task whose oracle does not score ~1.0:
#
#     409 Conflict: One or more tasks are blocked by the evaluation validation gate.
#
# And a real one here means more than applying a patch. `run_suites.py` clones
# and grades **the pushed `main`**, not the working tree, so an oracle that edits
# files and stops scores exactly zero with every test reporting "does not
# import". Pushing IS the solution in this world.
#
# The patch is embedded rather than read from a file beside this script: on the
# apex arms the sibling file was unreadable from the solution's own directory
# (/tests is root-owned 0700), and a heredoc has no permissions of its own. It is
# generated from fixtures/oracle.patch at build time, so it cannot drift from the
# suite that grades it.
set -uo pipefail

REPO_URL="http://worldadmin:worldadmin@git.world.local/worldadmin/curator.git"
WORK="$(mktemp -d)"

# The healthcheck should already have waited for gitea, but the oracle also runs
# in contexts that do not go through it. Cheap when it is already up.
wait-for-service --quiet gitea 2>/dev/null || true

git clone --quiet "$REPO_URL" "$WORK/curator" || { echo "oracle: clone failed"; exit 1; }
cd "$WORK/curator" || exit 1

cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
'''

REAL_SOLVE_TAIL = '''
CURATOR_ORACLE_PATCH_EOF

git apply --whitespace=nowarn /tmp/oracle.patch || {{ echo "oracle: patch did not apply"; exit 1; }}
rm -f /tmp/oracle.patch

git config user.email "worldadmin@world.local"
git config user.name  "worldadmin"
git add -A
git commit --quiet -m "{title}" || {{ echo "oracle: nothing to commit"; exit 1; }}

# Straight to main when the branch is unprotected; a branch plus an immediately
# merged PR when it is not. The agents that scored provenance 1.0 took the second
# path, so it is known to work in this world — but the first is one round trip and
# the grader only cares that `main` moved.
if git push --quiet origin HEAD:main 2>/dev/null; then
  echo "oracle: pushed straight to main"
else
  BRANCH="oracle/{slug}"
  git push --quiet --force origin "HEAD:$BRANCH" || {{ echo "oracle: push failed"; exit 1; }}
  TOKEN="$(cat /etc/sweworld/gitea-token 2>/dev/null)"
  API="http://git.world.local/api/v1/repos/worldadmin/curator"
  NUM=$(curl -sS -X POST -H "Authorization: token $TOKEN" \\
        -H 'Content-Type: application/json' "$API/pulls" \\
        -d "{{\\"head\\":\\"$BRANCH\\",\\"base\\":\\"main\\",\\"title\\":\\"oracle: {slug}\\"}}" \\
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("number",""))' 2>/dev/null)
  [ -n "$NUM" ] || {{ echo "oracle: could not open a PR"; exit 1; }}
  curl -sS -X POST -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \\
    "$API/pulls/$NUM/merge" -d '{{"Do":"merge"}}' >/dev/null \\
    || {{ echo "oracle: merge failed"; exit 1; }}
  echo "oracle: merged PR #$NUM into main"
fi

# Not required by the score — `score.py` sets reward = hidden_mean and leaves
# provenance unweighted — but the deploy takes about half a minute here, and
# letting it land means the oracle run also demonstrates ci_green and deployed
# rather than leaving two checks reading zero for no reason.
sleep 45
echo "oracle: done"
exit 0
'''


def sh_dq(text: str) -> str:
    """Escape text for interpolation into a bash DOUBLE-quoted string.

    Backslash first, or it re-escapes the escapes. Then the three characters
    double quotes do not protect: `"` ends the string, and both `` ` `` and `$`
    still substitute inside one.

    Escaping only the quote is the obvious half-fix and it is wrong here: the
    first generated title was `Batch payload planner for `batch_size="auto"``,
    whose backticks would have made bash run `batch_size="auto"` as a command in
    the middle of `git commit -m`. Titles come from a model now, so anything a
    shell reads as syntax will eventually appear in one.
    """
    for char in ("\\", '"', "`", "$"):
        text = text.replace(char, "\\" + char)
    return text


def solve(task: dict, slug: str) -> str:
    """The oracle script for this task: real when there is a patch, stub otherwise."""
    patch = group_dir(task, slug) / "fixtures" / "oracle.patch"
    if not patch.is_file():
        return STUB_SOLVE
    body = patch.read_text().rstrip("\n")
    if "CURATOR_ORACLE_PATCH_EOF" in body:
        raise SystemExit(f"{task['_id']}: the oracle patch contains the heredoc "
                         "delimiter; pick another")
    return REAL_SOLVE_HEAD + body + REAL_SOLVE_TAIL.format(
        title=sh_dq(task["title"]), slug=slug)

TEST_SH = '''#!/usr/bin/env bash
# Harbor verifier entrypoint. Executed directly rather than through `bash`, as
# root, from the image's own WORKDIR — so the shebang, the execute bit and the
# absolute paths below all matter.
set -uo pipefail

mkdir -p /logs/verifier

# Both halves run whatever happened, and neither gates the other. That split is
# the point: "wrote it right but never deployed" and "deployed something that
# misses the hidden requirement" are different failures, and a single reward
# would report them identically.
python3 /tests/provenance.py
"${CURATOR_VENV:-/opt/curator-dev/venv}/bin/python" /tests/run_suites.py

# score.py is the only thing that writes rewards.json, so a crash in either of
# the two above still leaves every key present and zero.
python3 /tests/score.py

# Always exit 0: the reward file is the verdict. A non-zero exit here reads as a
# broken harness rather than a failed task.
exit 0
'''


# =============================================================================
# Emitting
# =============================================================================
def write(path: Path, text: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def group_dir(task: dict, slug: str) -> Path:
    """The folder holding every version of one task, plus its fixtures."""
    return ROOT / f"{task['_id']}-{slug}"


def check_clue_arm(task: dict, text: str) -> None:
    """Two ways the clues arm can be built wrong and read as a result.

    A LEAK makes it a reworded `-spec`: if a `settles` clause or a
    subconclusion reaches the instruction, the requirement is stated after all
    and a good score says nothing about whether the remarks carried it.

    A GAP makes it unpassable: a fact field no remark covers cannot be inferred
    from the remarks, so the arm fails that field for a defect in the plant.
    Caught here it reads as a broken plant; caught after a run it reads as a
    finding about the agent, which is the expensive kind of wrong.
    """
    planted = clue_digest.load(task["_id"], task["title"])["task"]

    # Ground truth, not self-consistency. `coverage()` below compares the plant
    # against the plant's OWN copy of the requirements, which stayed green while
    # the two files described different features entirely. The fields have to
    # match tasks.json or the clues arm grades something the remarks never
    # discussed.
    mine = {f for f, v in task["hidden_requirements"][0]["requirement"].items() if v}
    theirs = {f for f, v in planted["requirements"][0]["requirement"].items() if v}
    if planted.get("title") != task["title"]:
        raise SystemExit(
            f"{task['_id']}: the plant titled {planted.get('title')!r} was "
            f"matched to {task['title']!r}")
    if mine != theirs:
        raise SystemExit(
            f"{task['_id']} r1: tasks.json states {sorted(mine)} but the plant "
            f"was built against {sorted(theirs)} — the plant is stale for this "
            "task, so its clues cannot grade these requirements")
    leaks = clue_digest.leaked_fields(planted, text)
    if leaks:
        raise SystemExit(f"{task['_id']}: answer key reached the clues "
                         f"instruction: {', '.join(leaks)}")
    gaps = clue_digest.coverage(planted)
    if gaps:
        raise SystemExit(f"{task['_id']}: no planted remark carries "
                         f"{gaps} — the clues arm cannot pass those facts")


def write_plant(task: dict, slug: str, variant: str, out: Path) -> None:
    """The delta `cli.py inject` produced, or a placeholder saying why not.

    Only the world arm gets a plant: the other three carry their remarks in the
    instruction, or not at all, and a corpus in front of a `-spec` agent would
    stop it being a control.

    Always writes SOMETHING. Harbor drops zero-byte files, so an empty directory
    does not survive the trip and the Dockerfile's `COPY plant` then fails with
    BuildKit's "failed to calculate checksum of ref" -- a message that names no
    path and reads like a broken platform rather than a missing folder. The
    generated `data/README.md` exists for the same reason.
    """
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    src = (REPO / "task_generator" / "out" / slug / "clues" / "plant-data")
    if not variant.startswith("world") or not src.is_dir():
        why = ("this arm quotes its remarks in the instruction"
               if variant in ("clues", "spec") else
               "this arm hides nothing in the corpus" if variant == "blind" else
               f"no plant delta at {src} — run `cli.py inject {slug}`")
        write(out / "README.md", f"No plant for the {variant} arm: {why}.\n")
        return
    for path in sorted(src.rglob("*")):
        if path.is_file():
            rel = path.relative_to(src)
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, out / rel)


def emit(task: dict, slug: str, variant: str) -> Path:
    suffix = "" if variant == "blind" else f"-{variant}"
    name = f"sweworld-{slug}{suffix}"
    out = group_dir(task, slug) / (slug + suffix)
    text = instruction(task, variant)
    if variant == "clues":
        check_clue_arm(task, text)
    write(out / "task.toml", task_toml(name, task, variant))
    write(out / "instruction.md", text)
    write(out / "environment" / "Dockerfile",
          HOSTED_DOCKERFILE if variant == "world-hosted"
          else WORLD_DOCKERFILE if variant == "world" else DOCKERFILE)
    write(out / "environment" / "task-entrypoint.sh", ENTRYPOINT, True)
    write(out / "environment" / "setup.sh", SETUP, True)
    write_plant(task, slug, variant, out / "environment" / "plant")
    write(out / "solution" / "solve.sh", solve(task, slug), True)

    tests = out / "tests"
    if tests.exists():
        shutil.rmtree(tests)
    # Harbor copies the whole tests/ directory to /tests, so the shared harness
    # is copied in rather than symlinked — a symlink out of the task directory
    # does not survive the trip.
    shutil.copytree(SUITES, tests, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc"))
    write(tests / "test.sh", TEST_SH, True)
    write(tests / "task.json", json.dumps(
        {"task_id": task["_id"], "suite": task["_suite"],
         "variant": variant, "control": variant in ("spec", "clues"),
         "hidden_requirements": task["hidden_requirements"]}, indent=1))
    lint(out)
    return out


def lint(out: Path) -> None:
    """Horizon's own checks on the directory we just wrote. Fails the build.

    Both of these already existed as importable functions and neither was ever
    called, so both defects reached a hosted run and had to be fixed by hand:

      timeouts   a verifier timeout under 2000s. Horizon KILLS an overrunning
                 grader and scores it zero, so a perfect solution and a broken
                 one are indistinguishable in the result.
      prereqs    tmux and asciinema missing. Not fatal to the trial -- and that
                 is the problem, because what is lost is the terminal recording,
                 which is the only record of what the agent actually typed.

    Soft-fails if the horizon packages are not installed: this repo's local
    Harbor runs do not need them, and a missing import must not stop a build.
    """
    try:
        from apex_arena.utils import lint_harbor_timeouts
        from horizon_cli.harbor_prereq_lint import lint_harbor_agent_prereqs
    except ImportError:
        return
    findings = list(lint_harbor_timeouts(out) or []) + \
        list(lint_harbor_agent_prereqs(out) or [])
    if findings:
        raise SystemExit(f"{out.name}: " + "\n  ".join([""] + findings))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--world", action="store_true",
                    help=f"also emit the in-world arm, which boots {WORLD_IMAGE} "
                         "and hides the remarks in the corpus instead of quoting "
                         "them in the ticket")
    ap.add_argument("--limit", type=int, default=None,
                    help="take the first N tasks instead of --pick")
    ap.add_argument("--pick", default="t1,t2,t3,t4,t12,t23,t40",
                    help="comma-separated task ids (default: the four the "
                         "plant covers, plus the three that have suites but "
                         "no plant)")
    ap.add_argument("--no-control", action="store_true",
                    help="skip the -spec twins")
    ap.add_argument("--hosted", action="store_true",
                    help="also emit the world arm that builds FROM the published "
                         "registry image, for Horizon. Same task, same plant; only "
                         "the base differs, because Horizon cannot resolve a local tag.")
    ap.add_argument("--thaw", action="store_true",
                    help=f"regenerate a task listed in FROZEN ({', '.join(sorted(FROZEN))}) "
                         "anyway. Overwrites its hand-written oracle with the stub.")
    ap.add_argument("--extra-tasks", default=None,
                    help="a JSON list of generated tasks (task_generator/"
                         "tasks.generated.json) to build alongside the "
                         "hand-written ones. Each entry carries its own id, "
                         "slug and suite, because ids in tasks.json are "
                         "POSITIONAL and a generated task is not in that file.")
    args = ap.parse_args(argv)

    data = json.loads(TASKS_JSON.read_text())
    # Ids are positional and 1-based, assigned at read time, exactly as
    # phase3_plant.py does it — the file itself carries no id field.
    tasks = []
    for i, task in enumerate(data["tasks"], 1):
        tasks.append({**task, "_id": f"t{i}", "_suite": SUITE_DIR.get(i, "")})

    # Generated tasks name their own id, slug and suite. They cannot be
    # positional: they are not in tasks.json, and `g1` would index SLUGS at 1 and
    # come out as `cache-stats`.
    if args.extra_tasks:
        extra = json.loads(Path(args.extra_tasks).read_text())
        for entry in extra:
            tasks.append({**entry, "_id": entry["id"], "_suite": entry["suite"],
                          "_slug": entry["slug"]})

    if args.limit:
        chosen = tasks[:args.limit]
    else:
        want = [p.strip() for p in args.pick.split(",") if p.strip()]
        by_id = {t["_id"]: t for t in tasks}
        missing = [w for w in want if w not in by_id]
        if missing:
            print(f"no such task id(s): {missing}", file=sys.stderr)
            return 1
        chosen = [by_id[w] for w in want]

    if not SUITES.exists():
        print(f"no test suites at {SUITES}", file=sys.stderr)
        return 1

    frozen = [t["_id"] for t in chosen if t["_id"] in FROZEN]
    if frozen and not args.thaw:
        print(f"refusing to regenerate {', '.join(frozen)}: frozen (see FROZEN).\n"
              f"Emitting would overwrite a hand-written oracle with the stub and\n"
              f"turn a 1.0 reference solution into a 0.0 one. Pass --thaw if that\n"
              f"is genuinely what you want.", file=sys.stderr)
        return 1

    made = []
    for task in chosen:
        digits = task["_id"][1:]
        n = int(digits) if digits.isdigit() and task["_id"].startswith("t") else None
        slug = task.get("_slug") or SLUGS.get(n) or slugify(task["title"])
        if not task["_suite"]:
            print(f"  {task['_id']}: no grading suite yet — skipped")
            continue
        made.append(emit(task, slug, "blind"))
        # The world arm is emitted BEFORE the --no-control bail. It is not a
        # control -- it is the blind ticket against a corpus that has the answers
        # in it -- but it used to sit after the `continue` below, so
        # `--no-control --world` quietly produced no world arm and reported
        # success.
        if args.world:
            made.append(emit(task, slug, "world"))
        if args.hosted:
            made.append(emit(task, slug, "world-hosted"))
        if args.no_control:
            continue
        made.append(emit(task, slug, "spec"))
        try:
            clue_digest.load(task["_id"], task["title"])
        except clue_digest.MissingClues as exc:
            print(f"  {task['_id']}: no clues arm — {exc}")
            continue
        made.append(emit(task, slug, "clues"))

    for path in made:
        print(f"  {path.relative_to(REPO)}")
    print(f"{len(made)} task(s) written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
