"""Read what a step wrote and say whether the task may advance.

Every check here already exists somewhere in `tg/`. What did not exist is a
caller: `tasks/lessons.md` records the same failure four separate times -- a
detector computed and read by nothing (`stock_phrasing`, `unstated`), a gate
wired to one command nobody runs on the happy path (`unreversed` to `reverse`,
`out_of_order` to `reorder`, `horizon.unsolvable` to `--arms clues`), and a
metric reported but never gated (`open_feature`). This module is the reader.

Two rules it follows, both from that file:

  * **Judge the artifact, not the exit code.** `cli.py split` and `cli.py
    bracket` both exit non-zero on a heuristic; `horizon tasks push` exits 0
    having done nothing. An exit code is an input to a verdict here, never the
    verdict.
  * **A new detector is measured against the brackets on disk before it is
    trusted.** `healthy_naive` below is the only rule this module adds to
    `bracket.ships()`, and `orchestrate.py --verify` runs it over every
    bracket.json in `out/` to show it agrees with what a person decided.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tg import bracket as tg_bracket                           # noqa: E402
from tg import clues as tg_clues                               # noqa: E402
from tg import emit as tg_emit                                 # noqa: E402
from tg import leak as tg_leak                                 # noqa: E402
from tg.model import Task                                      # noqa: E402


@dataclasses.dataclass
class Verdict:
    """What a gate found. `hard` stops the task; `soft` is recorded and passed on."""
    step: str
    ok: bool
    hard: list[str] = dataclasses.field(default_factory=list)
    soft: list[str] = dataclasses.field(default_factory=list)
    detail: str = ""
    # What the judge is shown. The artifact itself, never this module's summary
    # of it -- a judge handed a summary answers about the summary.
    evidence: str = ""

    def render(self) -> str:
        rows = [f"  ! {p}" for p in self.hard] + [f"  ~ {p}" for p in self.soft]
        head = f"{self.step}: {'ok' if self.ok else 'BLOCKED'}"
        return "\n".join([head] + rows) if rows else head


def _read(path: pathlib.Path, limit: int = 12000) -> str:
    return path.read_text()[:limit] if path.is_file() else f"(no {path.name})"


# --------------------------------------------------------------------------- A

def healthy_naive(task: Task, measured: dict) -> list[str]:
    """The one rule this module adds to `bracket.ships()`.

    `ships()` already refuses when `open_feature` fails on naive. It does not
    refuse when a HIDDEN fact passes on naive, because that is a `coincidence`
    and already covered -- so in practice the shape it permits is exactly the
    one wanted. What it cannot see is the arithmetic stated as a shape, and the
    shape is what a person reads:

        naive must pass `open_feature` and nothing else.

    From tasks/lessons.md: "The healthy shape is `naive: {'failed': 8,
    'passed': 1}` with the one pass being `open_feature`. `failed: 9` is not a
    better result; it is a suite no blind agent can reach."

    Computed over FACT KEYS out of `rewards`, not over pytest's pass/fail
    counts, because one test can grade one fact and the counts drift from the
    keys the moment a suite has a helper test.
    """
    naive = (measured.get("trees", {}).get("naive") or {}).get("rewards")
    if not naive:
        return ["naive tree was never measured, so the blind shape is unknown"]
    problems = []
    for key, reward in sorted(naive.items()):
        wanted = 1.0 if key.endswith("open_feature") else 0.0
        if reward == wanted:
            continue
        if key.endswith("open_feature"):
            problems.append(
                f"{key}: naive scores {reward} — a build given only the ticket "
                "cannot produce the open feature, so a blind 0.00 cannot be told "
                "apart from an agent that built nothing")
        else:
            problems.append(f"{key}: naive scores {reward} — not hidden from a ticket-only build")
    return problems


def bracket_gate(task: Task) -> Verdict:
    path = task.dir / "bracket.json"
    if not path.is_file():
        return Verdict("bracket", False, ["bracket.json was never written"])
    measured = json.loads(path.read_text())
    ok, problems = tg_bracket.ships(measured)
    shape = healthy_naive(task, measured)
    hard = list(problems) + [p for p in shape if p not in problems]
    return Verdict("bracket", ok and not shape, hard,
                   detail=f"verdicts: {measured.get('verdicts')}",
                   evidence=_read(task.dir / "bracket.md"))


def split_gate(task: Task, rc: int) -> Verdict:
    """`split` exits 1 when any fact rests on no invented name.

    That is a PREDICTOR, not a verdict -- it called four of five correctly on
    g2, and g1 shipped with five of ten facts unanchored because a fact can
    rest on a chosen value or on a policy the code is silent about instead of
    on a name. So the exit code is soft here and the judge decides, which is
    the one place the README says a person has to.
    """
    rows = tg_leak.audit(task)
    unanchored = [r for r in rows if not r.get("has_anchor")]
    leaked = [r for r in rows if r.get("leaked_by_ticket")]
    present = [r for r in rows if r.get("already_in_source")]
    soft = ([f"{len(unanchored)}/{len(rows)} facts rest on no invented name"] if unanchored else []) \
        + ([f"{len(leaked)} facts quote an identifier the ticket already prints"] if leaked else []) \
        + ([f"{len(present)} facts quote an identifier already in curator/src"] if present else [])
    return Verdict("split", True, [], soft,
                   detail=f"exit {rc}", evidence=tg_leak.render(task, rows))


def emit_gate(task: Task) -> Verdict:
    """Every declared fact has a test and every test a fact."""
    problems = tg_emit.check_bijection(task)
    return Verdict("emit", not problems, list(problems))


# --------------------------------------------------------------------------- B

def _subscores(rollout: dict) -> dict:
    """The per-fact scores out of one rollout.

    `grade_result` arrives as a JSON STRING on some rollouts and as an object on
    others -- both shapes are on disk in the same directory. Reading it as an
    object crashed the verdict gate on g7 after the evaluation had been paid
    for, which is the second time in this run that assuming a field's type
    without looking at the artifact has cost a step.
    """
    raw = rollout.get("grade_result")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return (raw or {}).get("subscores") or {}


def read_rollouts(arm_dir: pathlib.Path, *, model: str | None = None) -> list[dict]:
    """Rollout jsons under `<arm>/.rollouts/v*/`, newest version that has any.

    `model` filters, because two evaluations of the SAME task version -- the
    cipher-omni run that clears the model gate and the biggie-max run that is
    the actual verdict -- land their files side by side in one `v<N>` directory.
    Averaging them together would mix a weak model's ceiling with a strong
    one's and produce a number that describes neither.

    Rollouts with a null `score` are dropped: those are errored runs, not runs
    that scored zero, and counting them as zeros is how an exhausted account
    budget reads as a broken task.
    """
    root = arm_dir / ".rollouts"
    if not root.is_dir():
        return []
    versions = sorted(root.glob("v*"), key=lambda d: int(d.name[1:] or 0), reverse=True)
    for version in versions:
        rows = []
        for path in sorted(version.glob("*.json")):
            try:
                row = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict) or row.get("score") is None:
                continue
            if model and row.get("model") != model:
                continue
            rows.append(row)
        if rows:
            return rows
    return []


def read_validation(arm_dir: pathlib.Path) -> dict:
    """`{agent: score}` out of `<arm>/.validation/*/result.json`, newest per agent.

    The directory name carries the agent: `val-<prefix>-<epoch_ms>` for oracle,
    `noop-val-<prefix>-<epoch_ms>` for noop. Newest wins, because a re-validation
    after a fix must not be outvoted by the run that failed.
    """
    root = arm_dir / ".validation"
    if not root.is_dir():
        return {}
    best: dict[str, tuple[int, float | None]] = {}
    for run in root.glob("*/result.json"):
        agent = "noop" if run.parent.name.startswith("noop-") else "oracle"
        try:
            stamp = int(run.parent.name.rsplit("-", 1)[-1])
        except ValueError:
            stamp = 0
        score = json.loads(run.read_text()).get("score")
        if agent not in best or stamp > best[agent][0]:
            best[agent] = (stamp, score)
    return {agent: score for agent, (_, score) in best.items()}


def validation_gate(task: Task, arms: dict[str, pathlib.Path]) -> Verdict:
    """Hosted oracle must be 1.00 and hosted noop 0.00, on every arm pushed.

    This is the package's own bracket in Horizon's idiom and the only way to
    run it -- `apex_arena:base` lives in Horizon's project, so the Dockerfile
    these arms emit cannot be built here.
    """
    hard = []
    detail = {}
    for arm, path in arms.items():
        scores = read_validation(path)
        detail[arm] = scores
        if scores.get("oracle") != 1:
            hard.append(f"{arm}: hosted oracle validation is {scores.get('oracle')!r}, must be 1.00")
        if scores.get("noop") not in (0, 0.0):
            hard.append(f"{arm}: hosted noop validation is {scores.get('noop')!r}, must be 0.00")
    return Verdict("validate", not hard, hard, detail=json.dumps(detail))


# The bands v1's whole verdict is read against, and the model they are read on.
#
# THE SPEC FLOOR ONLY MEANS ANYTHING ON A STRONG MODEL. Measured on g6, one task,
# one version, two models: biggie-max scored the spec arm 1.00 and the blind arm
# 0.00; cipher-omni scored the SAME spec arm 0.514 over ten rollouts
# (0.57, 1, 0, 0.86, 1, 0, 0, 0.86, 0, 0.86) and the same blind arm 0.00. So a
# spec arm below the floor on cipher-omni is evidence about the model, not about
# whether the requirements are sufficient -- and a gate that refused on it would
# have parked g6, which is known good.
#
# The blind ceiling is the other way round: both models scored g6's blind arm a
# flat 0.00, so a blind number is readable on either.
VERDICT_MODEL = "biggie-max"     # the only model the spec floor is applied to
GATING_MODEL = "cipher-omni"     # what a new task must run first; informational
SPEC_FLOOR = 0.95
BLIND_CEILING = 0.10


def verdict_ab(task: Task, spec_dir: pathlib.Path, blind_dir: pathlib.Path) -> Verdict:
    """spec is satisfiable; blind recovers nothing while still building the feature.

    Both halves are stated as the claim they actually make, which is not what an
    average measures.

    SPEC IS AN EXISTENCE CLAIM. "Are these requirements sufficient to solve the
    task?" is answered yes by ONE agent solving it. A mean answers a different
    question -- how reliably this particular model solves it -- and on a weak
    model that conflation condemns good tasks: g11's spec arm scored 1.000 on
    six of ten cipher-omni rollouts, which proves sufficiency, while its mean of
    0.689 sat under any sensible floor.

    BLIND IS A CONDITIONAL CLAIM. A zero only means "the requirements are
    hidden" for a rollout that BUILT the feature; for one that did not, it means
    "the agent built nothing" and carries no information about hiding. So the
    test runs over the feature-building subset only. Measured: on g7, g9, g10
    and g11 alike, every blind rollout that built the feature scored exactly
    0.000 -- including g7, where only one of ten managed it.
    """
    hard, soft = [], []
    report = {}

    def rollouts(path):
        """Verdict-model rollouts if any, else the gating model's, labelled."""
        strong = read_rollouts(path, model=VERDICT_MODEL)
        weak = read_rollouts(path, model=GATING_MODEL)
        return strong, weak

    # --- spec: does ANY rollout reach the floor? ----------------------------
    strong, weak = rollouts(spec_dir)
    every = strong + weak
    if not every:
        hard.append("spec: no rollouts on disk — nothing was measured")
    else:
        best = max(float(r.get("score") or 0) for r in every)
        source = VERDICT_MODEL if strong and max(
            float(r.get("score") or 0) for r in strong) >= SPEC_FLOOR else GATING_MODEL
        report["spec"] = {"n": len(every), "best": round(best, 4),
                          "mean": round(sum(float(r.get("score") or 0) for r in every) / len(every), 4),
                          "proved_on": source if best >= SPEC_FLOOR else None}
        if best < SPEC_FLOOR:
            hard.append(
                f"spec: no rollout reached {SPEC_FLOOR:.2f} (best {best:.3f} over "
                f"{len(every)}) — nothing has yet shown the requirements as written "
                "are sufficient to solve the task")

    # --- blind: among rollouts that built the feature, is the score ~0? -----
    strong, weak = rollouts(blind_dir)
    every = strong + weak
    built = []
    for row in every:
        opens = [v for k, v in _subscores(row).items() if k.endswith("open_feature")]
        if opens and opens[0] == 1.0:
            built.append(float(row.get("score") or 0))
    report["blind"] = {"n": len(every), "built_the_feature": len(built),
                       "mean_when_built": round(sum(built) / len(built), 4) if built else None}
    if not every:
        hard.append("blind: no rollouts on disk — nothing was measured")
    elif not built:
        hard.append(
            f"blind: not one of {len(every)} rollouts built the open feature, so every "
            "score is 'the agent built nothing' rather than 'the requirements were "
            "hidden' — the arm carries no information until a stronger model runs it")
    else:
        mean = sum(built) / len(built)
        if mean > BLIND_CEILING:
            hard.append(f"blind: rollouts that built the feature still scored "
                        f"{mean:.3f} (ceiling {BLIND_CEILING:.2f}) — the requirements "
                        "are not hidden")
        if len(built) < 3:
            soft.append(f"blind: only {len(built)} rollout(s) built the feature, so the "
                        "zero rests on a small sample")

    return Verdict("verdict", not hard, hard, soft, detail=json.dumps(report, indent=1))


# --------------------------------------------------------------------------- C

# `tg.clues.problems()` splits its findings into HARD and SOFT. Two of the SOFT
# ones are promoted here, and only here -- `clues.py` is untouched, so the
# sequential path keeps its own policy.
#
# `contradictions`  a corpus that argues with itself is not a hard task, it is
#                   an unsolvable one. g2 lost r1.rule and three more facts to
#                   one invented sentence: the agent "took the most recent",
#                   split 50/50, and behaved correctly. The corpus lied to it.
# `unstated`        settle's per-assertion verdicts. Only `absent` is promoted
#                   -- nothing in the corpus bears on a graded assertion, so no
#                   amount of reading recovers it. `implied` stays soft and goes
#                   to the judge, because `implied` is a difficulty knob and
#                   flattening every one of them turns the corpus into an
#                   answer key.
PROMOTED = ("contradictions",)


def clue_gate(task: Task) -> Verdict:
    ledger = task.dir / "clues" / "plant.json"
    if not ledger.is_file():
        return Verdict("clues", False, ["clues/plant.json was never written"])
    entry = json.loads(ledger.read_text())["tasks"][0]
    hard, soft = tg_clues.problems(entry)
    hard, soft = list(hard), list(soft)
    for name in PROMOTED:
        rows = entry.get(name) or []
        if rows:
            hard.append(f"{name}: {len(rows)} finding(s) — promoted from advisory by the fleet")
    # `clues.unstated()` writes STRINGS -- `f"{key}: {verdict} — {why}"` -- for
    # both `implied` and `absent`, not the verdict dicts. Reading it as dicts
    # crashed on every plant that had any rows at all, and passed on g6 only
    # because g6's list is empty.
    absent = [r for r in (entry.get("unstated") or [])
              if isinstance(r, str) and r.split(": ", 1)[-1].startswith("absent")]
    if absent:
        hard.append(f"unstated: {len(absent)} graded assertion(s) nothing in the corpus bears on")
    return Verdict("clues", not hard, hard, soft,
                   evidence=_read(task.dir / "clues" / "README.md", 20000))
