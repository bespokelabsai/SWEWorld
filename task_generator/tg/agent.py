"""One `claude -p` call, on the subscription, with its transcript kept.

Every step of the pipeline is one call through `run()`. Nothing here knows what
a task is about; the caller supplies the prompt, the directory the agent may
touch, and optionally a JSON schema the answer must satisfy.

Three flags are load-bearing and the reasons are not obvious:

`--safe-mode`. CLAUDE.md discovery walks UP from the working directory, so an
agent started anywhere under this repo is handed SWEWorld's own description of
the hidden-requirement machinery — including the sentence explaining that tasks
hide requirements a reader must infer. For the `naive` role, whose entire value
is not knowing, that is contamination straight into the arm being measured. Safe
mode also drops skills, hooks and plugins, which is what makes two runs of the
same step comparable. Auth is unaffected by it.

NOT `--bare`, ever. Its own help text: "Anthropic auth is strictly
ANTHROPIC_API_KEY or apiKeyHelper via --settings (OAuth and keychain are never
read)". It would move every call in this package onto the API key silently, which
is the exact failure `auth.py` exists to prevent.

`--max-budget-usd`. A per-call ceiling. An authoring agent that misunderstands
its instructions does not fail, it explores, and the bill is the only thing that
notices.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import subprocess
import time

from . import auth

CLI = "claude"

# Read/write/search plus a shell. The shell is not optional: an authoring agent
# has to run the suite to know whether it is done, and `tg suite` is the only way
# to do that (curator is importable nowhere on this host).
DEFAULT_TOOLS = "Bash,Read,Write,Edit,Glob,Grep"


@dataclasses.dataclass
class Result:
    """What a call produced, plus what it cost to produce it."""

    label: str
    text: str
    data: dict | list | None      # set only when a schema was required
    cost_usd: float
    turns: int
    seconds: float
    session_id: str
    raw: dict

    @property
    def ok(self) -> bool:
        return bool(self.text) or self.data is not None


def _parse(stdout: str, label: str, seconds: float, schema: dict | None) -> Result:
    """`--output-format json` gives one object; anything else is a broken run."""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label}: claude did not return JSON ({exc}). First 400 chars:\n{stdout[:400]}")
    if isinstance(payload, list):          # defensive: some versions wrap
        payload = payload[-1]
    text = (payload.get("result") or "").strip()
    if payload.get("is_error") or payload.get("subtype") not in (None, "success"):
        raise SystemExit(f"{label}: claude reported an error run: {payload.get('subtype')}\n{text[:800]}")

    data = None
    if schema is not None:
        # With --json-schema the answer is still delivered as the result string.
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{label}: schema was required but the result is not JSON ({exc}):\n{text[:800]}")

    usage = payload.get("usage") or {}
    return Result(
        label=label,
        text=text,
        data=data,
        cost_usd=float(payload.get("total_cost_usd") or 0.0),
        turns=int(payload.get("num_turns") or 0),
        seconds=seconds,
        session_id=payload.get("session_id") or "",
        raw={"usage": usage, "duration_ms": payload.get("duration_ms"),
             "model": payload.get("modelUsage") or payload.get("model")},
    )


def run(
    prompt: str,
    *,
    repo: pathlib.Path,
    label: str,
    cwd: pathlib.Path,
    add_dirs: list[pathlib.Path] | None = None,
    tools: str = DEFAULT_TOOLS,
    schema: dict | None = None,
    budget_usd: float = 8.0,
    model: str = "opus",
    effort: str = "high",
    system: str | None = None,
    timeout_s: int = 5400,
    log_dir: pathlib.Path | None = None,
) -> Result:
    """Run one step and return its answer.

    `cwd` is the only directory the agent writes to; `add_dirs` are extra trees it
    may read (the real curator checkout, the rubric). Both are passed explicitly
    rather than inherited, so a step's reachable context is a reviewable fact.
    """
    cwd.mkdir(parents=True, exist_ok=True)
    argv = [
        CLI, "-p", prompt,
        "--output-format", "json",
        "--safe-mode",
        "--permission-mode", "bypassPermissions",
        "--model", model,
        "--effort", effort,
        "--tools", tools,
        "--max-budget-usd", f"{budget_usd}",
    ]
    for extra in add_dirs or []:
        argv += ["--add-dir", str(extra)]
    if schema is not None:
        argv += ["--json-schema", json.dumps(schema)]
    if system:
        argv += ["--append-system-prompt", system]

    env = auth.oauth_env(repo)
    auth.assert_no_key_leak(env)

    started = time.time()
    done = subprocess.run(argv, cwd=str(cwd), env=env, capture_output=True,
                          text=True, timeout=timeout_s)
    seconds = time.time() - started

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{label}.stdout.json").write_text(done.stdout)
        if done.stderr.strip():
            (log_dir / f"{label}.stderr.txt").write_text(done.stderr)
        # The exact argv, minus the prompt, so a step can be re-run by hand. The
        # prompt is long and lives in prompts/ anyway.
        (log_dir / f"{label}.argv.json").write_text(json.dumps(
            [a for a in argv if a is not prompt], indent=1))

    if done.returncode != 0 and not done.stdout.strip():
        raise SystemExit(f"{label}: claude exited {done.returncode}\n{done.stderr[-1200:]}")

    result = _parse(done.stdout, label, seconds, schema)
    # The line auth.py exists to prevent. If it ever appears the run is void, not
    # merely suspect: it was billed on the key.
    if "using the API key" in done.stderr:
        raise SystemExit(f"{label}: ran on ANTHROPIC_API_KEY, not the subscription. "
                         "Void. Check tg/auth.py and the .env files.")
    return result
