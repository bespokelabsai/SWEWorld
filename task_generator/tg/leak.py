"""Two of the rubric's Catalog A patterns, checked mechanically at split time.

Both were violated in the first cut of the first task, and both were checkable
without spending anything:

**"Ticket gives it away."** An identifier a fact requires, printed in the visible
ticket. The blind build then writes the helper by name and its body follows.

**"Codebase already does it."** An identifier a fact requires that already exists
in the pristine source. The blind engineer does not invent it — they find it, and
the fact comes free with the reading.

Prompts are advice and gates are enforcement. The prompt now says both things; this
file is what makes saying them optional-proof. It **reports** rather than refuses,
because a fact can be hidden on a chosen value or a silent policy with no
identifier at all — the bracket is the gate that refuses. What this catches is the
whole class of giveaway that the bracket only finds after a naive build has been
paid for.

Anchors are read from backticked spans: the fact text is written for a grader, so
anything the grader can require is quoted in it.
"""
from __future__ import annotations

import re
import subprocess

from .model import REPO, Task, declared_facts

SOURCE = REPO / "curator" / "src"

BACKTICKED = re.compile(r"`([^`]+)`")
# An identifier worth checking: a name, a dotted path, or a call. Bare English and
# literals are not anchors — `2`, `<=` and `bytes` tell a grader nothing to require.
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


# Members of the test tooling and the stdlib. They turn up in a fact's quoted
# example without being anything the agent has to invent, and they were the whole
# of the noise the first run of this check produced.
BORROWED = {
    "call_count", "side_effect", "return_value", "PropertyMock", "MagicMock",
    "from_dict", "assert_called", "monkeypatch", "tmp_path", "pytest", "raises",
    "dumps", "loads", "encode", "decode", "basename", "dirname", "join", "glob",
    "isinstance", "issubclass", "getattr", "TypeError", "ValueError", "KeyError",
    "AttributeError", "NotImplementedError", "dataclass", "frozen", "Sequence",
}


def anchors(text: str) -> set[str]:
    """The identifiers a fact quotes, which is what a test can require."""
    found: set[str] = set()
    for span in BACKTICKED.findall(text):
        for name in IDENT.findall(span):
            if len(name) > 3 and not name.isupper() and name not in BORROWED:
                found.add(name)
    return found


def strong(name: str) -> bool:
    """Whether this anchor is a name somebody would have had to invent.

    The distinction earns its place. The first run of this check reported an
    "arbitrary anchor" for eight of ten facts, and seven of those were fragments —
    `mini` out of `gpt-4o-mini`, `_000_000` out of a limit literal, `api_request`
    out of a local variable in an example. Every one of those facts measured as a
    coincidence. The one that measured `hidden` had `SingleRequestTooLargeError`.

    So a strong anchor is a compound name: CamelCase with at least two humps, or
    snake_case with at least two substantial parts. A fragment is not a name a
    grader can require, and treating it as one turns this check back into noise.
    """
    if len(name) < 6:
        return False
    humps = sum(1 for i, c in enumerate(name) if c.isupper() and i > 0)
    if humps >= 1 and name[0].isupper():
        return True
    # Parts must contain letters. `_000_000`, out of a limit literal like
    # `1_000_000`, otherwise reads as a two-part snake_case name and reintroduces
    # exactly the noise this function exists to remove.
    parts = [p for p in name.split("_") if len(p) >= 3 and any(c.isalpha() for c in p)]
    return len(parts) >= 2


def in_source(names: set[str]) -> set[str]:
    """Which of these already exist in the pristine source tree.

    One grep for all of them: a per-name search over a tree this size is slow
    enough that it would discourage running the check.
    """
    if not names or not SOURCE.is_dir():
        return set()
    pattern = r"\b(" + "|".join(re.escape(n) for n in sorted(names)) + r")\b"
    done = subprocess.run(["grep", "-rhoE", pattern, str(SOURCE), "--include=*.py"],
                          capture_output=True, text=True)
    return {line.strip() for line in done.stdout.splitlines() if line.strip()}


def audit(task: Task) -> list[dict]:
    """Per fact: which anchors leak through the ticket, and which the repo supplies."""
    ticket_words = set(IDENT.findall(task.description or ""))
    rows = []
    every = set()
    for _, _, text in declared_facts(task):
        every |= anchors(text)
    existing = in_source(every)

    for number, field, text in declared_facts(task):
        names = anchors(text)
        leaked = sorted(names & ticket_words)
        present = sorted(names & existing)
        arbitrary = sorted(names - ticket_words - existing)
        invented = [n for n in arbitrary if strong(n)]
        rows.append({
            "key": f"{task.id}.r{number}.{field}",
            "leaked_by_ticket": leaked,
            "already_in_source": present,
            "arbitrary_anchors": arbitrary,
            "invented_names": invented,
            "has_anchor": bool(invented),
        })
    return rows


def render(task: Task, rows: list[dict]) -> str:
    lines = ["| fact | named in the ticket | already in curator | a name somebody invented |",
             "|---|---|---|---|"]
    for row in rows:
        mark = ", ".join(f"`{n}`" for n in row["invented_names"][:4]) or "**none**"
        lines.append(
            f"| `{row['key']}` | {', '.join(row['leaked_by_ticket'][:4]) or '—'} "
            f"| {', '.join(row['already_in_source'][:4]) or '—'} | {mark} |")
    weak = [r["key"] for r in rows if not r["has_anchor"]]
    lines += ["", f"{len(rows) - len(weak)} of {len(rows)} facts rest on a name the "
              "ticket does not print and curator does not already contain."]
    for key in weak:
        lines.append(f"- `{key}` has none — expect `coincidence` unless it rests on a "
                     "chosen value or a policy the code is silent about")
    return "\n".join(lines) + "\n"
