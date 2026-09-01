"""What a generated task IS, and where its fact keys come from.

`out/<slug>/task.json` is deliberately not a new format. It is exactly one entry
of `data_gen/input/tasks.json` — `title`, `description`, `hidden_requirements` —
plus the three things a hand-written entry gets for free from its position in
that file and a generated one has to carry itself:

    id      `t1`..`t60` are POSITIONAL in tasks.json; a generated task is not in
            it, so it names itself (`g1`, `g2`, ...).
    slug    the harbor group/leaf directory name. Harbor reports a trial under
            its task-directory name, so this string is what appears in every
            result table.
    suite   the `_suites/<dir>` the graders live in, which `build_tasks.py`
            copies wholesale into each arm's `tests/`.

Storing it in that shape means `emit.py` copies the entry through untouched and
there is no second schema to keep in step.

Fact keys are NOT computed here. They come from `harbor_tasks/_suites/score.py`,
the same module the paid verifier runs, because a free bracket that disagreed
with the paid trial about what `g1.r1.rule` means would make the whole comparison
unreadable. `score.py` is imported for `expected_keys`, `junit_outcomes` and
`fold`; its module-level `/tests` and `/logs` constants are never touched, since
all three take their inputs as arguments.
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SUITES = REPO / "harbor_tasks" / "_suites"
OUT = REPO / "task_generator" / "out"


def score_module():
    """`harbor_tasks/_suites/score.py`, loaded by path.

    By path rather than by `sys.path` insertion: `_suites/` also holds a
    `conftest.py` that sets provider environment variables at import time, and a
    plain path insertion invites something else in there to be picked up by
    accident later.
    """
    name = "_tg_score"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SUITES / "score.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


FACT_FIELDS = score_module().FACT_FIELDS


@dataclasses.dataclass
class Task:
    """One generated task, as it sits on disk."""

    id: str
    slug: str
    suite: str
    title: str
    description: str
    hidden_requirements: list[dict]
    brief: str = ""

    @property
    def dir(self) -> pathlib.Path:
        return OUT / self.slug

    @property
    def group(self) -> str:
        """The harbor group directory: `g1-batch-payload-plan`."""
        return f"{self.id}-{self.slug}"

    def entry(self) -> dict:
        """The `--extra-tasks` record `build_tasks.py` consumes."""
        return {"id": self.id, "slug": self.slug, "suite": self.suite,
                "title": self.title, "description": self.description,
                "hidden_requirements": self.hidden_requirements}

    def meta(self) -> dict:
        """The shape `score.py` expects to derive keys from."""
        return {"task_id": self.id, "hidden_requirements": self.hidden_requirements}

    def fact_keys(self) -> list[str]:
        """Every reward key this task declares, `open_feature` first."""
        return score_module().expected_keys(self.meta())

    def hidden_keys(self) -> list[str]:
        return [k for k in self.fact_keys() if not k.endswith("open_feature")]

    def save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "task.json").write_text(json.dumps(dataclasses.asdict(self), indent=1) + "\n")


def load(slug: str) -> Task:
    path = OUT / slug / "task.json"
    if not path.is_file():
        raise SystemExit(f"no task at {path}; run `tg new {slug} --brief ...` first")
    return Task(**json.loads(path.read_text()))


def requirement_count(task: Task) -> int:
    return len(task.hidden_requirements)


def declared_facts(task: Task) -> list[tuple[int, str, str]]:
    """(requirement number, field, text) for every fact actually declared.

    A requirement declares only the fields it has — `score.py` divides the hidden
    mean by the number present, so an undeclared field is not a hole, it is a
    smaller denominator.
    """
    rows = []
    for number, req in enumerate(task.hidden_requirements, 1):
        for field in FACT_FIELDS:
            text = (req.get("requirement") or {}).get(field)
            if text:
                rows.append((number, field, text))
    return rows
