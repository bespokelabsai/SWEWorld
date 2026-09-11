#!/usr/bin/env python3
"""Turn measured bracket runs into `BRACKET.md` and each task's `README.md`.

The measurement is the expensive part and it is NOT done here: `_suites/
bracket_matrix.txt` is the record of running every suite against all three
implementations, one `<task> <tree> <suite> <field> <VERDICT>` row per test.
This script only reads it, so regenerating the prose costs nothing and cannot
quietly change a number.

Refresh the matrix by re-running the suites (see "Reproducing this" in the
generated document), then:

    python3 failed_tasks/make_bracket.py
"""
from __future__ import annotations

import collections
import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent          # failed_tasks/
MATRIX = ROOT / "_suites" / "bracket_matrix.txt"
TASKS_JSON = ROOT.parent / "data_gen" / "input" / "tasks.json"

# The groups, the suites that measured them and this script all sit here now.
# It used to live in harbor_tasks/ and reach across for the groups, which meant
# every path was a different number of levels up from a different root.
GROUPS_ROOT = ROOT

GROUP = {"t1": "t1-cache-stats", "t2": "t2-batch-cost-estimate",
         "t3": "t3-shared-limiter", "t4": "t4-deepseek-empty-retry"}
SLUG = {"t1": "cache-stats", "t2": "batch-cost-estimate",
        "t3": "shared-limiter", "t4": "deepseek-empty-retry"}
SUITE = {"t1": "t1_cache_stats", "t2": "t2_batch_cost",
         "t3": "t3_shared_limiter", "t4": "t4_deepseek_empty"}

# Facts whose suite skips them: no implementation can be told from any other,
# so a pass or a fail here would be an arbitrary verdict. See "Measurable vs
# unmeasurable" in the generated document.
UNMEASURABLE = {("t2", "r1", "exclusions_or_crossover"),
                ("t2", "r2", "failure_behavior")}

VERDICT = {"PASSED": "PASS", "FAILED": "fail", "SKIPPED": "skip"}


def read_matrix() -> dict:
    rows: dict = {}
    for line in MATRIX.read_text().splitlines():
        parts = line.split()
        if len(parts) != 5 or parts[3] == "-":
            continue
        task, tree, suite, field, result = parts
        rows.setdefault((task, suite.replace("test_", ""), field), {})[tree] = \
            VERDICT[result]
    for key in UNMEASURABLE:
        rows[key] = dict.fromkeys(("pristine", "naive", "oracle"), "skip")
    return rows


def classify(req: str, cells: dict) -> str:
    if req == "open":
        return "open"
    if "skip" in cells.values():
        return "unmeasurable"
    # A fact the obvious implementation already satisfies is not hidden.
    return "coincidence" if cells.get("naive") == "PASS" else "hidden"


def titles() -> dict:
    data = json.loads(TASKS_JSON.read_text())
    return {f"t{i}": t for i, t in enumerate(data["tasks"], 1)}


def task_table(rows: dict, task: str) -> tuple[list[str], collections.Counter]:
    out = ["| requirement | field | pristine | naive | oracle | verdict |",
           "|---|---|---|---|---|---|"]
    tally: collections.Counter = collections.Counter()
    mine = {k: v for k, v in rows.items() if k[0] == task}
    for (_, req, field), cells in sorted(mine.items(), key=lambda kv: kv[0][1:]):
        kind = classify(req, cells)
        mark = {"open": "_the ticket_", "hidden": "**hidden**",
                "coincidence": "coincidence",
                "unmeasurable": "unmeasurable"}[kind]
        if kind != "open":
            tally[kind] += 1
        out.append(f"| {req} | `{field}` | {cells.get('pristine', '-')} | "
                   f"{cells.get('naive', '-')} | {cells.get('oracle', '-')} "
                   f"| {mark} |")
    return out, tally


def write_readmes(rows: dict, meta: dict) -> None:
    """One README per task folder: what it asks, and whether it is measurable."""
    for task, group in GROUP.items():
        info = meta[task]
        table, tally = task_table(rows, task)
        body = [f"# {task} — {info['title']}", "",
                info["description"].strip(), "",
                "## Hidden requirements", ""]
        # One row per fact field, because that is the unit the suites grade:
        # a field with no decisive test makes the requirement unscoreable.
        for i, req in enumerate(info["hidden_requirements"], 1):
            body += [f"**r{i}**", "", "| field | what it asks |", "|---|---|"]
            for field, text in req["requirement"].items():
                body.append(f"| `{field}` | {' '.join(text.split())} |")
            body.append("")
        body += ["## Versions", "",
                 "| version | what it is |", "|---|---|",
                 f"| `{SLUG[task]}/` | the ticket only — the hidden "
                 "requirements are recoverable from the corpus and nowhere "
                 "else |",
                 f"| `{SLUG[task]}-spec/` | the control — both hidden "
                 "requirements written into `instruction.md` |",
                 f"| `{SLUG[task]}-clues/` | the remarks phase 3 planted, "
                 "quoted in date order, herrings included — the requirement "
                 "itself is never stated |",
                 f"| `fixtures/oracle.py` | the informed implementation; must "
                 "pass every row below |",
                 f"| `fixtures/naive.py` | the obvious implementation; must "
                 "pass the ticket and fail the hidden rows |", "",
                 "```bash",
                 f"harbor run -p failed_tasks/{group} -a oracle",
                 "```", "",
                 "## Measured", ""] + table + [
                 "", f"{tally['hidden']} genuinely hidden, "
                 f"{tally['coincidence']} coincidence, "
                 f"{tally['unmeasurable']} unmeasurable. "
                 "See [BRACKET.md](../BRACKET.md) for what those "
                 "mean.", ""]
        (GROUPS_ROOT / group / "README.md").write_text("\n".join(body))


def write_bracket(rows: dict, meta: dict, head: str, tail: str) -> None:
    parts = [head.replace("@DATE@", datetime.date.today().isoformat())]
    total: collections.Counter = collections.Counter()
    per_task = {}
    for task, group in GROUP.items():
        table, tally = task_table(rows, task)
        per_task[task] = tally
        total.update(tally)
        parts.append(f"## {task} — {meta[task]['title']}\n"
                     f"`failed_tasks/{group}/` — "
                     f"[README]({group}/README.md)\n\n"
                     + "\n".join(table) + "\n")
    totals = ["## Totals", "",
              "| task | genuinely hidden | coincidence | unmeasurable |",
              "|---|---|---|---|"]
    for task in GROUP:
        t = per_task[task]
        totals.append(f"| {task} | {t['hidden']} | {t['coincidence']} "
                      f"| {t['unmeasurable']} |")
    totals += [f"| **all** | **{total['hidden']}** | **{total['coincidence']}** "
               f"| **{total['unmeasurable']}** |", ""]
    parts.append("\n".join(totals))
    parts.append(tail)
    (ROOT / "BRACKET.md").write_text("\n".join(parts))


HEAD = """# Are the hidden requirements real?

Every grading test, run against three implementations of the same task.
Regenerated from measured runs on @DATE@ by `make_bracket.py`.
"""

if __name__ == "__main__":
    rows = read_matrix()
    meta = titles()
    prose = (ROOT / "_suites" / "bracket_prose.md").read_text().split("@SPLIT@")
    write_bracket(rows, meta, HEAD + prose[0], prose[1])
    write_readmes(rows, meta)
    print(f"BRACKET.md + {len(GROUP)} README(s)")
