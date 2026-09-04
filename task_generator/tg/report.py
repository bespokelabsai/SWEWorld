"""One page: what each condition of the rubric's protocol actually returned.

Deliberately renders and never measures. `harbor_tasks/make_bracket.py` is built
the same way and for the same reason — regenerating the prose must not be able to
quietly change a number.
"""
from __future__ import annotations

import json
import pathlib

from . import bracket, trial
from .model import Task, declared_facts


def _fold(rewards) -> dict:
    """One metrics dict from `trial.rewards`, which returns one dict PER TRIAL.

    It is a list even at `n_trials == 1`, and every read site here wanted a dict.
    Two of them did `.get` on it and raised `AttributeError: 'list' object has no
    attribute 'get'`, killing `report` after both paid arms had already run — the
    one moment the command exists for. Folding once here rather than at each site
    is also what makes `--runs 3` mean something: the arm reports its mean.
    """
    rows = [r for r in (rewards if isinstance(rewards, list) else [rewards])
            if isinstance(r, dict)]
    keys = {k for r in rows for k in r}
    folded = {}
    for key in keys:
        values = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        if values:
            folded[key] = sum(values) / len(values)
    return folded


def render(task: Task) -> str:
    d = task.dir
    measured = json.loads((d / "bracket.json").read_text()) if (d / "bracket.json").is_file() else None
    findings = json.loads((d / "audit.json").read_text()) if (d / "audit.json").is_file() else []
    spend = json.loads((d / "spend.json").read_text()) if (d / "spend.json").is_file() else []
    audit_by_key = {row["key"]: row for row in findings}

    arms = {}
    for arm in ("spec", "blind"):
        for candidate in sorted((trial.JOBS).glob(f"{arm}-{task.id}-*")):
            arms[arm] = {"job": candidate.name,
                         "metrics": _fold(trial.rewards(candidate.name))}

    lines = [f"# {task.id} — {task.title}", "", f"*{task.slug}*", "",
             "## The ticket the agent sees", "", task.description, "",
             "## Validation protocol", ""]

    lines += ["| condition | how it was run | expected | got |", "|---|---|---|---|"]

    def hidden_mean(metrics: dict) -> str:
        value = metrics.get(f"{task.id}.hidden_mean")
        return "—" if value is None else f"{value:.4f}"

    if measured:
        ok, problems = bracket.ships(measured)
        counts: dict[str, int] = {}
        for verdict in measured["verdicts"].values():
            counts[verdict] = counts.get(verdict, 0) + 1
        lines.append(f"| 1 · blind | `naive` reference build, free bracket | fails every hidden fact "
                     f"| {counts.get('coincidence', 0)} coincidence(s) |")
        lines.append(f"| 2 · full spec | `oracle` reference build, free bracket | passes everything "
                     f"| {counts.get('broken', 0)} broken |")
    else:
        lines.append("| 1 · blind | — | fails every hidden fact | not measured |")
        lines.append("| 2 · full spec | — | passes everything | not measured |")

    if "spec" in arms:
        lines.append(f"| 2 · full spec (paid) | harbor `{arms['spec']['job']}` | 1.0 "
                     f"| {hidden_mean(arms['spec']['metrics'])} |")
    if "blind" in arms:
        lines.append(f"| 1 · blind (paid) | harbor `{arms['blind']['job']}` | < 1.0 "
                     f"| {hidden_mean(arms['blind']['metrics'])} |")
    # Horizon runs the same two arms hosted, and its numbers belong in the same
    # table: the subscore keys are the keys score.py produces, so a hosted result
    # and a harbor result measure the same thing.
    hz = d / "horizon" / "results.json"
    if hz.is_file():
        block = json.loads(hz.read_text())
        for arm, label, expected in (("spec", "2 · full spec (horizon)", "1.0"),
                                     ("blind", "1 · blind (horizon)", "< 1.0"),
                                     ("blind_opus", "1 · blind (horizon, opus)", "< 1.0")):
            row = (block.get("arms") or {}).get(arm) or {}
            got = row.get("avg_score")
            runs = row.get("runs")
            shown = "in flight" if got is None else f"{got:.4f} over {runs} run(s)"
            if row.get("open_feature_built"):
                shown += f", open feature built {row['open_feature_built']}"
            lines.append(f"| {label} | `{row.get('task_id', '')[:8]}` "
                         f"{block.get('agent_type', '')} | {expected} | {shown} |")
        lines.append(f"| bracket (horizon) | hosted `validate -a oracle` / `-a noop` "
                     f"| 1.0 / 0.0 | "
                     f"{block['arms']['blind']['validate_oracle']} / "
                     f"{block['arms']['blind']['validate_noop']} |")
    lines.append("| 3 · ticket + clues | needs a phase-3 plant | passes | out of scope |")
    lines.append("| 4 · clues only | needs a phase-3 plant | reconstructs | out of scope |")

    lines += ["", "## Per fact", "",
              "| fact | bracket | audit | spec arm | blind arm | requirement |",
              "|---|---|---|---|---|---|"]
    for number, field, text in declared_facts(task):
        key = f"{task.id}.r{number}.{field}"
        verdict = (measured or {}).get("verdicts", {}).get(key, "—")
        row = audit_by_key.get(key, {})
        spec_v = arms.get("spec", {}).get("metrics", {}).get(key)
        blind_v = arms.get("blind", {}).get("metrics", {}).get(key)
        lines.append(
            f"| `{key}` | {verdict} | {row.get('verdict', '—')} "
            f"| {'—' if spec_v is None else spec_v} | {'—' if blind_v is None else blind_v} "
            f"| {text[:120]} |")

    if spend:
        total = sum(r["cost_usd"] for r in spend)
        lines += ["", "## What authoring cost", "",
                  f"{len(spend)} agent call(s), ${total:.2f} of subscription usage.", "",
                  "| step | $ | turns | s |", "|---|---|---|---|"]
        lines += [f"| `{r['label']}` | {r['cost_usd']:.2f} | {r['turns']} | {r['seconds']:.0f} |"
                  for r in spend]

    return "\n".join(lines) + "\n"
