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
import re
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
# One rollout at 1.00 proves the remarks carry the requirement. See verdict_clues.
CLUES_FLOOR = 1.00


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


def _spoken(entry: dict) -> str:
    """Every word anybody actually says: remarks, woven turns, page and mail bodies.

    `missing_identifiers` and `unstated` are both computed against the remark
    TEXTS. After `reknit` that is not the corpus a reader sees -- the exchange
    written around a remark is, and it is usually where a name gets typed. So a
    finding out of those fields is checked against this before it is called hard.
    """
    out = []
    for req in entry.get("requirements", []):
        for clue in req.get("clues", []):
            out.append(clue.get("text") or "")
            invented = clue.get("invented") or {}
            out.append(str(invented.get("body") or ""))
            out.append(str(invented.get("subject") or ""))
            for msg in invented.get("messages") or []:
                out.append(str(msg.get("text") or ""))
    return " ".join(out).lower()


def named_clues(rows) -> set[str]:
    """The clue ids a `fact_conflicts` list points at."""
    return {m for row in rows or ()
            for m in re.findall(r"\b([A-Za-z0-9]+\.r\d+\.[A-Za-z0-9_.-]+)\s+says", str(row))}


def unreachable_names(task: Task, entry: dict) -> list[str]:
    """Names the SUITE requires that an agent can learn from nowhere.

    `missing_identifiers` reads `required_names`, which `surface.required()` parses
    out of the requirement prose -- and it misses things. g7's list held `A`, `No`
    and `exists` but not `verify_sidecar`, which `test_r1.py` demands by name
    through `sym()`. Nothing else looked, so the plant passed every gate and then
    `prove` returned 0/3 on `r1.rule` with "no module exports 'verify_sidecar'",
    taking the three status assertions down with it -- one defect, four correlated
    failures.

    A name is only OWED to the corpus when the ticket does not print it. g11's suite
    names 18 symbols and 11 are absent from its corpus; every one of those 11 is in
    the ticket, and g11 proved 10/10. So the set that matters is
    `suite - ticket - corpus`, and for g7 that is exactly one name.
    """
    suite = (pathlib.Path(__file__).resolve().parents[2]
             / "harbor_tasks" / "_suites" / task.suite)
    if not suite.is_dir():
        return []
    want: set[str] = set()
    for path in suite.glob("test_*.py"):
        want |= set(re.findall(r"sym\(\s*[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']", path.read_text()))
    ticket = task.description or ""
    said = _spoken(entry)
    return sorted(n for n in want
                  if n not in ticket and n.lower() not in said)


def clue_gate(task: Task, previous: set[str] | None = None) -> Verdict:
    """Everything the plant says about itself, read after EVERY pass that writes it.

    `settle`, `reverse`, `reorder`, `reknit` and `consistency` all mutate
    `clues/plant.json` through `clues.finish()`, which recomputes every derived
    field. `cli.py audit_plant` reads it for the commands that end there, but
    `settle` is not one of them -- `cmd_settle` returns 0 unconditionally on the
    apply path -- so a $10 pass that rewrites remarks reported success no matter
    what it did. This is the fleet's reader, and the worker calls it after all of
    them.
    """
    ledger = task.dir / "clues" / "plant.json"
    if not ledger.is_file():
        return Verdict("clues", False, ["clues/plant.json was never written"])
    entry = json.loads(ledger.read_text())["tasks"][0]
    hard, soft = tg_clues.problems(entry)
    hard, soft = list(hard), list(soft)
    owed = []

    # `consistency` IS A SAMPLE, NOT A MEASUREMENT.
    #
    # Measured over 26 rounds across these five tasks: an exchange NOTHING
    # touched between two runs is routinely clean in one and a hard conflict in
    # the next. g10's `s3_l1`, `s3_l2` and `s3_l3` were rewritten once, came back
    # clean, were not touched again, and all three were flagged on the next pass.
    # g11's `l14` and `r2.l1` did the same, and so did g9's `l-scope-2`. Over the
    # last three rounds per task there are 11 conflicts that repeat and 15 that
    # appear once and never again -- so more than half of what the fleet was
    # paying to repair was resampling, and the counts never converged:
    # g7 9->9->14->12->11->11, g10 8->10->8->9->8.
    #
    # So a conflict earns `hard` by SURVIVING a re-read. The first run has
    # nothing to compare against and every row stands; after that a row is hard
    # only if the previous run named the same clue. A real defect is still there
    # next pass -- the aimed redo is what fixes it -- and noise costs a soft row
    # instead of a $3.25 round.
    if previous is not None:
        kept, unconfirmed = [], []
        for row in hard:
            if not row.startswith("fact_conflicts"):
                kept.append(row)
            elif named_clues([row]) & previous:
                kept.append(row)
            else:
                unconfirmed.append(row)
        hard = kept
        for row in unconfirmed:
            soft.append("first sighting, not yet confirmed by a second read — " + row[:200])

    # A FRESH PLANT IS NOT A BROKEN ONE.
    #
    # `finish()` appends "never run — cli.py consistency <slug> …" to
    # `fact_conflicts`, which is HARD, so a perfectly good first plant always
    # exits non-zero. Parking on that would stop all five tasks on the stage that
    # costs the most and works. What it means is that a later stage is owed, and
    # the plan already runs it.
    kept = []
    for row in hard:
        if row.startswith("fact_conflicts") and ("never run" in row or "stale" in row):
            owed.append(row.split(":", 1)[-1].strip()[:150])
        else:
            kept.append(row)
    hard = kept

    for name in PROMOTED:
        rows = entry.get(name) or []
        if rows:
            hard.append(f"{name}: {len(rows)} finding(s) — promoted from advisory by the fleet")

    # `unstated` IS THE REMARKS, AND A READER SEES THE EXCHANGES.
    #
    # It comes out of `claims.json`, the settle judge's reading of each remark
    # TEXT. `reknit` then writes the conversation around every remark, and that is
    # where a name usually gets typed -- so after reknit the finding is evidence
    # about a corpus nobody reads. Measured on all five plants here: every term an
    # `absent` row says appears "nowhere in the corpus in any spelling" is in the
    # exchanges, `dataset_signature` 4 times, `AttachmentError` 7, `CheckpointInfo`
    # 7, `ValueError` 5. Promoting it was handing the judge a false hard finding
    # every round, on every task, and the judge overrode it every time.
    #
    # Before reknit it is the only reader of settle's per-assertion verdicts and
    # stays hard, which is the pass where it can still be acted on cheaply.
    absent = [r for r in (entry.get("unstated") or [])
              if isinstance(r, str) and r.split(": ", 1)[-1].startswith("absent")]
    woven = bool(json.loads(ledger.read_text()).get("reknit_at"))
    spoken = _spoken(entry) if woven else ""
    if absent and not woven:
        hard.append(f"unstated: {len(absent)} graded assertion(s) nothing in the corpus bears on")
    elif absent:
        soft.append(f"unstated: {len(absent)} assertion(s) absent from the REMARKS — "
                    "read against claims.json, which predates the exchanges")

    # HARD, and the only reader of it: a name in the suite, absent from the ticket
    # and absent from the corpus, cannot be reached by any amount of reading.
    for name in unreachable_names(task, entry):
        hard.append(f"unreachable: the suite requires `{name}` by name, the ticket never "
                    f"prints it and no remark says it — that fact cannot pass")

    for req in entry.get("requirements", []):
        rid = req.get("req_id", "?")
        # A NAME CANNOT BE INFERRED. The tests read these by position -- an
        # attribute, a keyword, a dict key -- so a fact whose name no remark
        # types scores zero however well the corpus reads, and no amount of
        # reasoning recovers it. Printed by `cmd_clues` today and in neither
        # HARD nor SOFT, which is why it is hard here.
        # ... and read against the exchanges, not only the remarks: g8 was held
        # hard on the word `calls`, which four of its woven turns type.
        missing = [n for n in (req.get("missing_identifiers") or [])
                   if not woven or n.split()[0].strip("`,.").lower() not in spoken]
        if missing:
            hard.append(f"{rid}: no remark says {', '.join(missing)} — the tests reach "
                        "for those by name, so those facts cannot pass")
        if req.get("gaps"):
            hard.append(f"{rid}: nothing carries {', '.join(req['gaps'])}")
        # Diversity across slack / notion / email, and across weeks and rooms.
        # `finish()` recomputes this on every pass, so it is current here even
        # after `settle` has added remarks -- but `cmd_clues` is the only thing
        # that ever prints it, and only at plant time.
        for row in req.get("spread") or []:
            soft.append(f"{rid}: {row}")
        for row in req.get("unprinted_values") or []:
            soft.append(f"{rid}: nothing prints {row}")

    detail = {"owed": owed,
              "remarks": sum(len(r.get("clues") or []) for r in entry.get("requirements", []))}
    return Verdict("clues", not hard, hard, soft,
                   detail=json.dumps(detail),
                   evidence=_read(task.dir / "clues" / "README.md", 20000))


def verdict_clues(task: Task, clues_dir: pathlib.Path) -> Verdict:
    """Are the planted remarks enough to solve the task?

    Read as an EXISTENCE claim, exactly like the spec ceiling: one rollout at
    1.00 says the scattered evidence is sufficient. A mean would be answering a
    different question -- how reliably a given model finds and uses it -- which
    is what the world arm is for, and which no shipped clue arm has ever been
    held to (g1's never cleared 0.70 against a spec arm at 1.00).
    """
    rows = read_rollouts(clues_dir, model=VERDICT_MODEL) or read_rollouts(clues_dir)
    if not rows:
        return Verdict("verdict.clues", False,
                       ["clues: no rollouts on disk — nothing was measured"])
    scores = [float(r.get("score") or 0) for r in rows]
    best = max(scores)
    opens = [v for r in rows for k, v in _subscores(r).items()
             if k.endswith("open_feature")]
    report = {"n": len(scores), "best": round(best, 4),
              "mean": round(sum(scores) / len(scores), 4),
              "open_feature": round(sum(opens) / len(opens), 3) if opens else None}
    hard, soft = [], []
    if best < CLUES_FLOOR:
        hard.append(f"clues: best rollout {best:.3f} over {len(scores)} — no run has "
                    f"reached {CLUES_FLOOR:.2f}, so nothing has shown the planted "
                    "remarks are sufficient to solve the task")
    if len(scores) > 1 and sum(scores) / len(scores) < best:
        soft.append(f"clues: {len(scores)} rollouts range {min(scores):.2f}-{best:.2f} — "
                    "a clue arm splits between engaging a requirement and skipping it")
    return Verdict("verdict.clues", not hard, hard, soft, detail=json.dumps(report, indent=1))
