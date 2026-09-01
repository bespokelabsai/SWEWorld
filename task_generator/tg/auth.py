"""The environment an authoring agent runs in, and nothing else.

One job: hand back an environment where `claude` uses the subscription. That is
not the default and it is not what naming the token achieves.

`harbor_tasks/_loop/run.sh` records what happens otherwise. Both credentials
live in the repo's `.env` — `ANTHROPIC_API_KEY` for phase-3 one-shots,
`CLAUDE_CODE_OAUTH_TOKEN` for agent turns — and when both are set the
claude-code path PREFERS the key, announcing it in one log line nobody reads:

    API key and OAuth token both set; using the API key
    (set CLAUDE_FORCE_OAUTH=1 to use the subscription)

Every harbor job from `spec-recheck-*` through `clues-t4-1` carries that line.
Those trials ran on the key while the subscription token sat unused beside them,
and `jobs/aborted-spec-t12-1-apikey/` is the one that had to be thrown away for
it. So the key is not merely deprioritised here, it is REMOVED from the
environment the agent inherits.
"""
from __future__ import annotations

import os
import pathlib
import re

# Both are read; both are candidates for removal. `ANTHROPIC_AUTH_TOKEN` is the
# other name the CLI accepts for a key, and leaving it behind reintroduces the
# bug under a different spelling.
_DROP = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
_TOKEN = "CLAUDE_CODE_OAUTH_TOKEN"

_LINE = re.compile(r"""^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$""")


def env_file_values(path: pathlib.Path) -> dict[str, str]:
    """The assignments in a dotenv file, unquoted, comments and blanks skipped.

    Deliberately not `dotenv`: this runs before anything is installed, and the
    file it reads is the one `set -a; . ./.env` in run.sh reads, so matching that
    shell's simple semantics is the whole requirement.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        found = _LINE.match(raw)
        if not found:
            continue
        name, value = found.group(1), found.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name] = value
    return values


def oauth_env(repo: pathlib.Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    """A child environment on the subscription, with the API key gone.

    Raises rather than falling back. A missing token used to mean "quietly run on
    the key", which is the failure this module exists to make impossible: it
    costs money on the wrong meter and the output looks identical.
    """
    env = dict(os.environ)
    for name in ("", "data_gen"):
        env_path = repo / name / ".env" if name else repo / ".env"
        for key, value in env_file_values(env_path).items():
            env.setdefault(key, value)

    token = (env.get(_TOKEN) or "").strip()
    if not token:
        raise SystemExit(
            f"{_TOKEN} is not in the environment or in {repo}/.env. Refusing to "
            "launch: without it the CLI would fall back to ANTHROPIC_API_KEY and "
            "bill the wrong meter while looking exactly the same.")

    for name in _DROP:
        env.pop(name, None)
    env[_TOKEN] = token
    # Belt and braces: the adapter honours this even if something downstream puts
    # a key back. run.sh sets it for the same reason.
    env["CLAUDE_FORCE_OAUTH"] = "1"
    env.update(extra or {})
    return env


def assert_no_key_leak(env: dict[str, str]) -> None:
    """Called by the agent driver on the env it is about to hand over."""
    present = [name for name in _DROP if env.get(name)]
    if present:
        raise SystemExit(f"refusing to launch: {', '.join(present)} still in the child environment")
