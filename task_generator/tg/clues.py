"""Build the remarks that hide a task's requirements, and decide where each belongs.

`data_gen/phase3_plant.py` does this against day specs that phase 4 has not
simulated yet. This does it against a corpus that is finished: the conversations
happened, the pages were written. Nothing here re-simulates anything.

Two things follow from that, and they are the whole difference.

**Placement is a judgement, not a score.** Phase 3 ranks candidate slots by token
overlap against a conversation's *agenda* -- a few dozen words -- and calls a slot
"explicit" above a literal overlap of 3. Against a real channel-day of sixty
messages that threshold is met by accident. So overlap is used here only to bound
what a model is shown, and the model decides whether a remark could realistically
have been made there: whether the room is already chewing on something it answers,
whether that person would have been the one to say it, whether somebody has already
made the point. It may reject every candidate, and that is how a new conversation
comes to exist.

**Solvability is measured, not argued.** Phase 3 proves it with a closed-book
reconstruct-then-grade, best-of-three, run twice. It has to: its tasks have no
executable grader. A task_generator task does, so the proof is the real thing --
`prove.py` builds an implementation from the ticket and these remarks alone and
scores it with the suite that scores the paid arm.

Three checks, in the order they cost anything:

    free      a fact nothing covers, a remark that restates the requirement, an
              identifier claimed verbatim and absent
    free      `surface.py` -- every name the grader reads that the ticket withholds
              is said by some placed remark
    ~$2       `prove.py` -- an agent builds from the digest and the suite marks it

The first version had only the first of those, and the arm scored 0.00 over ten
hosted rollouts because nine of one requirement's ten graded names appeared nowhere
in the corpus. The second caught that class outright; the third exists because it
did not catch the rest -- a name said as a noun and built inline, a value stated by
somebody the reader had no reason to connect it to.
"""
from __future__ import annotations

import collections
import dataclasses
import datetime as dt
import json
import pathlib
import re
import shutil

from . import agent, clue_schemas as cs, steps, surface
from .corpus import Corpus, week_of
from .model import FACT_FIELDS, REPO, Task, declared_facts, load

PROMPTS = REPO / "task_generator" / "prompts"

# Phase 3's limits on a single remark, kept because they are what makes a leaf a
# remark rather than a specification.
MAX_SENTENCES, MAX_WORDS = 2, 30
CONCLUDES = re.compile(
    r"\b(which means|so we (?:need|have|should|must)|therefore|the fix is|"
    r"the answer is|so the rule|which is why we (?:need|should|must)|"
    r"meaning we|so anything that)\b", re.I)
ASKS = re.compile(r"\b(asks?|asking|wonders?|wondering|queries|querying|unsure|unclear)\b", re.I)

# A `verbatim` identifier that the remark itself hedges. The presence test below
# only asks whether the name is in the text, so "call it plan_fingerprint or
# something in that direction" passes it — and then the graded suite requires that
# exact symbol. A live world run named its function `plan_id` instead, having read
# the only corpus mention of `plan_fingerprint` and been told the name was
# provisional; three of ten facts went with it. Scarcity is the difficulty we want;
# a name the corpus disowns is not.
HEDGED_NAME = re.compile(
    r"(or something(?: (?:like that|along those lines|in that direction))?|"
    r"or some such|or similar|or whatever we call it|or thereabouts|"
    r"working name|provisional(?:ly)?|for want of a better|"
    r"name (?:is|isn'?t) (?:not )?(?:settled|final|fixed)|"
    r"call it .{0,40}? or)\b", re.I)

# Advice against acting, which a rendering may not add on its own. See the note in
# `keep_wording`: the plant may say a shape is unsettled, but only the plant gets to
# tell a reader not to build it.
DISCOURAGES = re.compile(
    r"\b(don'?t|do not|dont|wouldn'?t|shouldn'?t|no point|not worth|hold off|"
    r"leave it|wait (?:un)?til)\b[^.!?]{0,60}\b("
    r"write|writing|code|coding|build|building|implement|implementing|depend|"
    r"rely|touch|wire|bother)\b", re.I)

WORD = re.compile(r"[a-z_][a-z0-9_]{2,}")
STOP = set("the and for with that this from have has was were are but not you our its "
           "will can any all one two into out off over under about their there they "
           "when what which while would could should than then them these those".split())


def tokens(text: str) -> set[str]:
    return {w for w in WORD.findall(text.lower()) if w not in STOP}


# ---------------------------------------------------------------------------
# prompts
# ---------------------------------------------------------------------------
def prompt(name: str, **values: str) -> str:
    """`steps.prompt`, not a second copy of it.

    This used to substitute first and then flag any line holding both `{{` and
    `}}`, which is a property of the substituted CONTENT rather than of the
    template. `steps.prompt` had the same bug, fixed there and not here, and
    `settle` duly died on a real assertion out of a real suite:

        clue_claims.md: unfilled placeholders: ['assert auto.backend_params ==
        {}, f"backend_params must be {{}} when none were given, ..."']

    `{{}}` is an f-string writing a literal `{}` -- ordinary test code, mistaken
    for a template hole after $46 of plant had already been paid for. Reading the
    placeholders out of the TEMPLATE before anything is substituted is the fix,
    and importing it is what stops it being fixed once more somewhere else.
    """
    return steps.prompt(name, **values)


# What a voice is made of, and which parts of it belong to a LETTER rather than to
# the person. Mail is the one register where the typing habits genuinely drop away:
# somebody whose chat capitalization is `always lowercase` still capitalises in a
# mail to a colleague. A page comment does NOT get this treatment — people leave
# comments in their own voice, casual and lowercase included, and flattening that
# reads more artificial than the informality ever did.
VOICE_FIELDS = ("name", "cadence", "formality", "capitalization", "punctuation",
                "vocabulary", "typo_tendency", "register", "signature_words",
                "hedge_words", "affirm_words", "question_style")
LETTER_DROPS_VOICE = ("cadence", "capitalization", "punctuation", "typo_tendency")


def describe_voice(voice: dict, *, written: bool = False) -> str:
    """This person's voice. `written` is for MAIL, and drops the typing habits.

    Vocabulary, stance and hedges are the person and survive any medium. Casing,
    burst cadence and punctuation habits are how they type in a chat box, and in a
    letter they are simply not in play. Only mail sets this: a wiki comment is
    somebody talking in their own voice under a page, lowercase and all, and
    scrubbing that produced comments blander than the corpus around them.
    """
    keep = [k for k in VOICE_FIELDS if not (written and k in LETTER_DROPS_VOICE)]
    lines = [f"- **{k}**: {voice[k]}" for k in keep if voice.get(k)]
    if written:
        lines.append("- **how they write here**: carefully — capitalised, "
                     "punctuated, complete sentences. The vocabulary and stance "
                     "above are theirs; the typing habits are not in play.")
    return "\n".join(lines)


def roster_lines(corpus: Corpus, people: list[str],
                 reach: dict[str, dict[str, int]] | None = None) -> str:
    rooms = collections.defaultdict(collections.Counter)
    for m in corpus.messages:
        rooms[m.author][m.channel] += 1
    out = []
    for who in people:
        voice = corpus.voice(who)
        top = ", ".join(f"#{c}" for c, _ in rooms[who].most_common(4)) or "(no channels)"
        line = (f"- **{who}** ({voice.get('name', who)}) — writes "
                f"{voice.get('capitalization', '?')}, {voice.get('cadence', '?')}; "
                f"posts in {top}")
        if reach and who in reach:
            line += f"; can be quoted in {', '.join(sorted(reach[who]))}"
        out.append(line)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# windows
# ---------------------------------------------------------------------------
def windows(corpus: Corpus, back: float = 0.40) -> tuple[tuple[str, str], tuple[str, str]]:
    """When clues may be said, and when herrings must have been said.

    Phase 3 reserves a lead-in on a calendar it controls. Here the calendar is
    fixed, so the clue window is the back `back` of the corpus and the herring
    window is the quarter before it opens -- which makes "the reversal came first"
    a property of the dates rather than something each placement has to get lucky
    about.
    """
    # Over the days that EXIST, not over the calendar. This corpus simulates 161
    # days scattered across 456 of calendar time, and it is front-loaded: a window
    # cut as "the last 40% of the span" by date arithmetic caught 6 days and 194
    # messages, and 33 of 45 remarks then had no candidate location at all. The
    # units that matter are days somebody actually spoke.
    days = sorted({m.date for m in corpus.messages})
    if not days:
        raise SystemExit("corpus has no messages")
    opens = days[max(0, int(len(days) * (1 - back)))]
    herring_from = days[max(0, int(len(days) * (1 - back - back * 0.6)))]
    before = days[max(0, days.index(opens) - 1)]
    return ((opens, days[-1]), (herring_from, before))


# ---------------------------------------------------------------------------
# free checks
# ---------------------------------------------------------------------------
def leaf_problems(leaf: dict, requirement: dict) -> list[str]:
    """Phase 3's structural checks, none of which cost a model call."""
    out = []
    text = leaf.get("text") or ""
    if len(re.findall(r"[.!?]+", text)) > MAX_SENTENCES or len(text.split()) > MAX_WORDS:
        out.append("longer than one remark")
    if CONCLUDES.search(text):
        out.append("draws the conclusion itself, which is the reader's job")
    if ASKS.search(leaf.get("settles") or ""):
        out.append("describes asking rather than settling")
    if not (leaf.get("leaves_open") or "").strip():
        out.append("names nothing it leaves for a sibling remark")
    for name in leaf.get("verbatim") or []:
        if name.lower() not in text.lower():
            out.append(f"claims verbatim {name!r} but does not contain it")
        elif HEDGED_NAME.search(text):
            out.append(f"hedges verbatim {name!r} — the suite requires that exact "
                       f"symbol, so the remark cannot call it provisional")
    for term in leaf.get("forbidden_terms") or []:
        if term and term.lower() in text.lower():
            out.append(f"contains its own forbidden term {term!r}")
    # giveaways: a leaf that restates the requirement's own wording makes the
    # clues arm a reworded spec arm.
    for field, stated in (requirement or {}).items():
        want = tokens(stated or "")
        if len(want) >= 4 and len(want & tokens(text)) / len(want) > 0.75:
            out.append(f"restates {field} almost verbatim")
    return out


def coverage(facts: list[str], leaves: list[dict]) -> list[str]:
    """Facts no leaf CLAIMS to carry. Weak on purpose, and never the only check.

    `covers` is written by the model that wrote the leaf, so this asks the
    generator whether the generator did its job. It passed on g1's first plant,
    every fact accounted for, and the arm scored 0.00 over ten hosted rollouts
    because nine of one requirement's ten graded names appeared in no remark at
    all. Kept because before `settle` has run there is nothing else, and reported
    as `gaps_claimed` so nobody mistakes it for evidence.
    """
    carried = {f for leaf in leaves for f in (leaf.get("covers") or [])}
    return [f for f in facts if f not in carried]


def uncarried(req_id: str, facts: list[str], verdicts: dict) -> list[str] | None:
    """Facts no remark was JUDGED to state, out of the settle verdicts.

    The independent artifact `coverage` lacks. A verdict is a reading of the
    remark texts against one assertion the suite makes, so a fact is carried here
    only if somebody, somewhere, actually said the thing -- not because the leaf
    that was supposed to say it listed the fact in `covers`.

    `not_required` claims are not evidence of anything and do not count; a fact
    whose every claim is `not_required` is not graded, so there is nothing to
    carry and it is not a gap. Returns None when no settle pass has run, which is
    the caller's signal to fall back.

    Measured before being trusted, and it did not earn much: run against every
    archived plant here -- including the ones that scored 0.48 and 0.70 hosted --
    it returns empty every time. A requirement's fact is graded by several
    assertions and at least one of them is always `stated`, so fact-level
    coverage cannot see a hole. What does see it is `unstated()` below, one row
    per assertion. This stays because it costs nothing and is the honest version
    of the number, not because it has ever caught anything.
    """
    if not verdicts:
        return None
    out = []
    for field in facts:
        rows = [v for v in verdicts.values() if v.get("key") == f"{req_id}.{field}"]
        if not rows or all(r.get("verdict") == "not_required" for r in rows):
            continue
        if not any(r.get("verdict") == "stated" for r in rows):
            out.append(field)
    return out


def unstated(verdicts: dict) -> list[str]:
    """Graded assertions no remark states outright, one row each.

    The granularity `uncarried` cannot reach. `settle --dry-run` computes the same
    thing and exits non-zero on it -- and then the apply path returns 0 and the
    report goes stale against the plant it sits beside, so the next pass to touch
    the plant reports nothing. Recomputing it in `finish` means every pass says
    whether the corpus still leaves a reader to work something out.
    """
    return [f"{v['key']}: {v['verdict']} — {(v.get('why') or '')[:110]}"
            for v in verdicts.values()
            if v.get("verdict") in ("implied", "absent")]


def spread(leaves: list[dict]) -> list[str]:
    """>=2 sources, >=3 weeks, >=2 rooms, and no subconclusion twice in one room."""
    placed = [l for l in leaves if l.get("slot")]
    out = []
    weeks = {week_of(l["slot"]["date"]) for l in placed if l["slot"].get("date")}
    rooms = {l["slot"]["room"] for l in placed}
    sources = {l["source"] for l in placed}
    if len(sources) < 2:
        out.append(f"one source only ({', '.join(sources) or 'none'})")
    if len(weeks) < 3:
        out.append(f"{len(weeks)} week(s) — a reader covering 3 would have all of it")
    if len(rooms) < 2:
        out.append(f"{len(rooms)} room(s)")
    seen: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for leaf in placed:
        seen[(leaf["subconclusion"], leaf["slot"]["room"])].append(leaf["slot"]["date"])
    for (sub, room), dates in seen.items():
        days = sorted(dt.date.fromisoformat(d) for d in dates if d)
        for a, b in zip(days, days[1:]):
            if (b - a).days < 14:
                out.append(f"{sub}: two remarks in {room} within {(b - a).days} days")
    return out


# ---------------------------------------------------------------------------
# stages
# ---------------------------------------------------------------------------
def _record(task: Task, label: str, text: str, result) -> None:
    logs = task.dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / f"{label}.prompt.md").write_text(text)
    spend = task.dir / "spend.json"
    rows = json.loads(spend.read_text()) if spend.is_file() else []
    rows.append({"label": label, "cost_usd": round(result.cost_usd, 4),
                 "turns": result.turns, "seconds": round(result.seconds, 1),
                 "session": result.session_id})
    spend.write_text(json.dumps(rows, indent=1) + "\n")


def company_blurb(corpus: Corpus) -> str:
    chans = ", ".join(f"#{c} ({n})" for c, n in list(corpus.channels().items())[:8])
    return (f"A small team building `bespokelabs/curator`, a Python library for batch and "
            f"online LLM inference. Chat channels, busiest first: {chans}. "
            f"They also keep a wiki and use internal mail.")


def demanded(need: surface.Need | None, which: str) -> str:
    """The graded surface as the tree prompt shows it: fact by fact, then the whole.

    Fact by fact rather than one list, because a name asked of the requirement in
    general gets attached to whichever remark the model is writing when it reads the
    instruction, and the reader then meets `max_batches_per_plan` in a remark about
    file layout.
    """
    per_fact = (getattr(need, which, None) or {}) if need else {}
    if not per_fact:
        return ("*(none — this requirement's tests reach for nothing the ticket does "
                "not already name)*")
    return "\n".join(f"- **{field}** — " + ", ".join(f"`{n}`" for n in sorted(set(names)))
                     for field, names in per_fact.items())


def stage_tree(task: Task, corpus: Corpus, req_id: str, req: dict,
               sources: list[str], people: list[str], budget: float,
               reach: dict | None = None, need: surface.Need | None = None,
               missing: list[str] | None = None, attempt: int = 1) -> dict:
    facts = [f for f in FACT_FIELDS if (req.get("requirement") or {}).get(f)]
    requirement = "\n".join(
        f"- **{f}** — {req['requirement'][f]}" for f in facts)
    reversed_note = ""
    if req.get("earlier_reversed_version"):
        reversed_note = ("## What they had decided before, and reversed\n\n"
                         f"{req['earlier_reversed_version']}\n\n"
                         "Do not write remarks stating this. It is planted separately, "
                         "earlier, as a decision somebody believed at the time.")
    defect = ""
    if missing:
        defect = ("## Your last attempt left these unsayable\n\n"
                  "No remark you wrote contained "
                  + ", ".join(f"`{n}`" for n in missing)
                  + ". Every fact they belong to is unscoreable as it stands. Write "
                    "the tree again with each of them literally inside some remark, "
                    "spread across different people and days, and keep everything "
                    "else that worked.")
    first, last = corpus.span()
    text = prompt("clue_tree.md", brief=cs.brief(), company=company_blurb(corpus),
                  title=task.title, description=task.description, req_id=req_id,
                  requirement=requirement, reversed=reversed_note,
                  names=demanded(need, "names"), values=demanded(need, "values"),
                  defect=defect, roster=roster_lines(corpus, people, reach),
                  sources=", ".join(sources), span=f"{first} to {last}")
    label = f"clue-tree-{req_id}" + (f".attempt{attempt}" if attempt > 1 else "")
    result = agent.run(text, repo=REPO, label=label, cwd=task.dir,
                       tools="", schema=cs.tree_schema(people, facts, sources),
                       budget_usd=budget, log_dir=task.dir / "logs")
    _record(task, label, text, result)
    return normalise(result.data, req_id, req, people)


def normalise(tree: dict, req_id: str, req: dict, people: list[str]) -> dict:
    """Namespace ids, drop impossible leaves, and note the free-check problems.

    Problems are recorded rather than raised: a tree with one weak leaf is worth
    more than no tree, and the README says which leaves are weak so a reader can
    judge. The one exception is a leaf held by somebody who does not exist, which
    is dropped outright because it can never be placed.
    """
    requirement = req.get("requirement") or {}
    subs = []
    for sub in tree.get("subconclusions") or []:
        subs.append({**sub, "id": f"{req_id}.{sub['id']}"})
    leaves = []
    for leaf in tree.get("leaves") or []:
        if leaf.get("holder") not in people:
            continue
        leaf = {**leaf,
                "id": f"{req_id}.{leaf['id']}",
                "subconclusion": f"{req_id}.{leaf.get('subconclusion', '')}",
                "covers": (leaf.get("covers") or [])[:2],
                "verbatim": leaf.get("verbatim") or [],
                "forbidden_terms": leaf.get("forbidden_terms") or [],
                "kind": "clue"}
        leaf["problems"] = leaf_problems(leaf, requirement)
        leaves.append(leaf)
    known = {s["id"] for s in subs}
    for leaf in leaves:
        if leaf["subconclusion"] not in known:
            leaf["problems"] = leaf.get("problems", []) + ["names no known subconclusion"]
    for sub in subs:
        mine = [l for l in leaves if l["subconclusion"] == sub["id"]]
        if len(mine) < 2:
            for leaf in mine:
                leaf["problems"].append(
                    f"{sub['id']} rests on {len(mine)} remark(s) — one person carrying a "
                    "whole conclusion is not hidden")
    return {"subconclusions": subs, "leaves": leaves}


def stage_herrings(task: Task, corpus: Corpus, req_id: str, req: dict,
                   people: list[str], budget: float) -> list[dict]:
    if not req.get("earlier_reversed_version"):
        return []
    facts = [f for f in FACT_FIELDS if (req.get("requirement") or {}).get(f)]
    text = prompt("clue_herrings.md", company=company_blurb(corpus), title=task.title,
                  description=task.description, req_id=req_id,
                  requirement="\n".join(f"- **{f}** — {req['requirement'][f]}" for f in facts),
                  reversed=req["earlier_reversed_version"],
                  roster=roster_lines(corpus, people))
    result = agent.run(text, repo=REPO, label=f"clue-herring-{req_id}", cwd=task.dir,
                       tools="", schema=cs.herring_schema(people), budget_usd=budget,
                       log_dir=task.dir / "logs")
    _record(task, f"clue-herring-{req_id}", text, result)
    return [{**h, "id": f"{req_id}.{h['id']}", "kind": "herring", "covers": [],
             "subconclusion": "", "source": "slack", "leaves_open": "",
             "verbatim": [], "forbidden_terms": h.get("forbidden_terms") or [],
             "problems": []}
            for h in (result.data or {}).get("herrings") or []]


# ---------------------------------------------------------------------------
# placement
# ---------------------------------------------------------------------------
def shortlist(corpus: Corpus, leaf: dict, window: tuple[str, str],
              used: set[str], want: int = 8) -> list:
    """The places worth showing the model, and only those.

    Overlap is used here and nowhere else, purely to decide what goes in the
    prompt. It is normalised by the square root of the candidate's length because
    a channel-day of sixty messages would otherwise out-score every page and every
    short conversation on sheer volume -- which is the miscalibration that makes
    phase 3's raw-count threshold meaningless against real prose.

    Then one candidate per week at most, so the model is choosing between genuinely
    different moments rather than five views of the same fortnight.
    """
    source = leaf.get("source") or "slack"
    if source == "slack":
        pool = corpus.channel_days(holder=leaf["holder"], window=window)
    elif source == "notion":
        # Both ways onto the wiki: a section in a page this person wrote, and a
        # comment on anybody's. Without the second, five of seven people have two
        # pages or fewer and `notion` collapses into an invented Slack thread.
        pool = (corpus.page_candidates(holder=leaf["holder"], window=window)
                + corpus.page_candidates(holder=leaf["holder"], window=window,
                                         wrote_it=False))
    else:
        pool = corpus.mail_candidates(holder=leaf["holder"], window=window)
    pool = [c for c in pool if c.key not in used
            and f"page-full|{c.room[5:]}" not in used]
    if not pool:
        return []

    want_tokens = tokens(leaf["text"] + " " + (leaf.get("settles") or ""))
    scored = []
    for cand in pool:
        have = tokens(cand.excerpt)
        overlap = len(want_tokens & have) / (len(have) ** 0.5 or 1)
        scored.append((overlap, cand))
    scored.sort(key=lambda pair: -pair[0])

    picked, seen_weeks = [], set()
    for _, cand in scored:
        wk = week_of(cand.date) if cand.date else cand.key
        if wk in seen_weeks:
            continue
        seen_weeks.add(wk)
        picked.append(cand)
        if len(picked) >= want:
            break
    return picked


def render_candidates(cands: list) -> str:
    out = []
    for cand in cands:
        out.append(f"### `{cand.key}` — {cand.title} ({cand.date})\n\n"
                   f"People here: {', '.join(cand.who)}\n\n"
                   "```\n" + cand.excerpt.strip() + "\n```\n")
    return "\n".join(out)


def stage_place(task: Task, corpus: Corpus, leaf: dict, window: tuple[str, str],
                used: set[str], budget: float) -> dict:
    cands = shortlist(corpus, leaf, window, used)
    if not cands:
        return {"choice": "none", "why": "no candidate location in range for this person",
                "realism": 0, "adapted": leaf["text"], "invent": {}}
    verbatim = ""
    if leaf.get("verbatim"):
        verbatim = ("**These must appear literally in the wording:** "
                    + ", ".join(f"`{v}`" for v in leaf["verbatim"]))
    text = prompt("clue_place.md", holder=leaf["holder"], text=leaf["text"],
                  settles=leaf.get("settles") or "", verbatim=verbatim,
                  leaves_open=leaf.get("leaves_open") or "(nothing recorded)",
                  voice=describe_voice(corpus.voice(leaf["holder"])),
                  candidates=render_candidates(cands))
    result = agent.run(text, repo=REPO, label=f"clue-place-{leaf['id']}", cwd=task.dir,
                       tools="", schema=cs.place_schema([c.key for c in cands],
                                              sorted(corpus.channels()),
                                              leaf.get("source") or "slack"),
                       budget_usd=budget, log_dir=task.dir / "logs")
    _record(task, f"clue-place-{leaf['id']}", text, result)
    data = dict(result.data or {})
    data["candidates"] = [c.key for c in cands]
    by_key = {c.key: c for c in cands}
    if data.get("choice") in by_key:
        data["_candidate"] = by_key[data["choice"]]
    return data


def keep_wording(leaf: dict, adapted: str) -> tuple[str, str | None]:
    """Take the rewrite only if it kept what the remark had to keep.

    A rewrite that drops a `verbatim` identifier is rejected outright, the same way
    phase 3 protects a narrowed leaf: an identifier a grader will look for is not
    the model's to drop while making a sentence read better. Length is checked too,
    because the adapted line is the one that actually lands in the corpus.
    """
    adapted = (adapted or "").strip()
    if not adapted:
        return leaf["text"], "empty rewrite"
    for name in leaf.get("verbatim") or []:
        if name.lower() not in adapted.lower():
            return leaf["text"], f"rewrite lost the identifier {name!r}"
    # Keeping the identifier is not enough if the rewrite also disowns it. A
    # rendering that says "call it X or something in that direction" satisfies the
    # loop above and still tells a reader the name is up for grabs.
    if (leaf.get("verbatim") or []) and HEDGED_NAME.search(adapted) \
            and not HEDGED_NAME.search(leaf["text"]):
        return leaf["text"], "rewrite hedged an identifier the plant states plainly"
    # The plant decides what a remark discourages. A rendering that invents advice
    # against acting is not a wording change: "shape is still moving" became
    # "so id say dont write anything against it yet" in a live corpus, and six
    # consecutive world rollouts quoted that clause back as their reason to skip
    # the requirement it was carrying.
    if DISCOURAGES.search(adapted) and not DISCOURAGES.search(leaf["text"]):
        return leaf["text"], "rewrite invented advice against acting on the remark"
    if len(adapted.split()) > MAX_WORDS + 10:
        return leaf["text"], "rewrite ran long"
    return adapted, None


def stage_conversation(task: Task, corpus: Corpus, leaf: dict, invent: dict,
                       budget: float) -> dict:
    """The conversation that should have happened, when no existing one fits."""
    channel = (invent.get("channel") or "engineering").lstrip("#")
    date = invent.get("date") or ""
    nearby = []
    for (chan, day), msgs in sorted(corpus.by_channel_day.items()):
        if chan == channel and date and abs_days(day, date) <= 7:
            nearby.append(f"{day}: " + "; ".join(m.text[:90] for m in msgs[:4]))
    people = invent.get("participants") or [leaf["holder"]]
    voices = "\n\n".join(f"**{p}**\n{describe_voice(corpus.voice(p))}" for p in people)
    verbatim = ""
    if leaf.get("verbatim"):
        verbatim = ("**These must appear literally:** "
                    + ", ".join(f"`{v}`" for v in leaf["verbatim"]))
    text = prompt("clue_conversation.md", holder=leaf["holder"], text=leaf["text"],
                  settles=leaf.get("settles") or "", verbatim=verbatim,
                  why=invent.get("prompted_by") or "no existing conversation fits",
                  channel=channel, date=date, people=", ".join(people),
                  nearby="\n".join(nearby[:6]) or "(nothing that week)", voices=voices)
    result = agent.run(text, repo=REPO, label=f"clue-conv-{leaf['id']}", cwd=task.dir,
                       tools="", schema=cs.CONVERSATION, budget_usd=budget,
                       log_dir=task.dir / "logs")
    _record(task, f"clue-conv-{leaf['id']}", text, result)
    return {"channel": channel, "date": date,
            "messages": (result.data or {}).get("messages") or []}


def default_invent(corpus: Corpus, leaf: dict, window: tuple[str, str],
                   used: set[str]) -> dict:
    """Where a conversation would go when the model named no replacement.

    The holder's busiest channel, on a day inside the window that this plant has
    not already used, with the people who really posted there that week.
    """
    kind = {"slack": "chat_thread", "notion": "doc_new",
            "email": "mail_new"}.get(leaf.get("source") or "slack", "chat_thread")
    rooms = collections.Counter(m.channel for m in corpus.messages
                                if m.author == leaf["holder"])
    channel = rooms.most_common(1)[0][0] if rooms else "engineering"
    days = sorted({m.date for m in corpus.messages
                   if window[0] <= m.date <= window[1]})
    for date in days:
        if f"new|{channel}|{date}" not in used:
            people = sorted(corpus.spoke.get((channel, week_of(date)), set())
                            | {leaf["holder"]})
            return {"kind": kind, "channel": channel, "date": date,
                    "participants": people[:4], "title": "",
                    "prompted_by": "no existing conversation in range fits this remark"}
    return {"kind": kind, "channel": channel, "date": days[-1] if days else "",
            "participants": [leaf["holder"]], "title": "",
            "prompted_by": "no existing conversation in range fits this remark"}


def abs_days(a: str, b: str) -> int:
    try:
        return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days)
    except Exception:
        return 999


# ---------------------------------------------------------------------------
# the plan
# ---------------------------------------------------------------------------
def slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-") or "note"


def slot_of(leaf: dict, placed: dict, invented: dict | None) -> dict | None:
    """The carrier a remark won, in phase 3's slot shape plus what is new here."""
    cand = placed.get("_candidate")
    if cand is not None:
        channel = cand.room[1:] if cand.room.startswith("#") else ""
        kind = {"chat_day": "chat_insert", "page": "doc_edit",
                "page_comment": "doc_comment", "mail_thread": "mail_reply"}[cand.kind]
        return {"key": cand.key, "source": leaf["source"], "date": cand.date,
                "channel": channel, "room": cand.room, "index": None,
                "class": "explicit" if (placed.get("realism") or 0) >= 4 else "passing",
                "score": placed.get("realism"), "forced": False,
                "why": placed.get("why") or "", "kind": kind,
                "insert_after": placed.get("insert_after") or "",
                "anchor": placed.get("anchor") or "",
                "title": cand.title}
    if invented:
        kind = invented.get("kind") or (placed.get("invent") or {}).get("kind") or "chat_thread"
        date = invented.get("date") or ""
        channel = (invented.get("channel") or "").lstrip("#")
        # A new page is not "#pipeline on the 23rd" and neither is a new thread. The
        # first plant wrote every invented carrier as a channel and a date, which is
        # how four wiki remarks and two mail remarks ended up reading as chat.
        if kind == "doc_new":
            # Never the leaf id. `g1-r1-l-sidecar-consts.md` is a wiki page named
            # after the clue it was built to hide, which is the most visible plant
            # this generator can produce. The writer's schema requires a title, so
            # this only fires when the writer was skipped -- fall back to what the
            # remark settles, which reads like a page somebody wrote.
            title = (invented.get("title")
                     or (placed.get("invent") or {}).get("title")
                     or " ".join((leaf.get("settles") or "untitled note").split()[:9]))
            path = f"{invented.get('collection') or 'engineering'}/" + slugify(title) + ".md"
            room, channel = f"page:{path}", ""
            key = f"new|{path}"
        elif kind == "mail_new":
            title = invented.get("subject") or ""
            room, channel = f"thread:new|{leaf['id']}", ""
            key = f"new|mail|{leaf['id']}"
        else:
            room, title = f"#{channel}", (placed.get("invent") or {}).get("title") or ""
            key = f"new|{channel}|{date}"
        return {"key": key, "source": leaf["source"], "date": date,
                "channel": channel, "room": room,
                "index": None, "class": "explicit", "score": placed.get("realism"),
                "forced": False, "why": placed.get("why") or "",
                "kind": kind, "insert_after": "", "anchor": "", "title": title}
    return None


def plan(slug: str, *, sources: tuple[str, ...] = cs.SOURCES, run: str | None = None,
         budget: float = 3.0, back: float = 0.40) -> dict:
    task = load(slug)
    corpus = Corpus(pathlib.Path(run) if run else None)
    clue_window, herring_window = windows(corpus, back)
    # Only people who can actually hold a remark in this window, and only the
    # sources they can hold one in. Checked BEFORE the tree, because the tree's
    # `holder` and `source` are enums it picks from -- an unreachable pair costs a
    # paid call and produces a leaf that can never be placed.
    reach = corpus.reachable(clue_window)
    people = [p for p in corpus.people() if p in corpus.cast and p in reach]
    sources = tuple(s for s in sources
                    if any(s in reach[p] for p in people)) or ("slack",)
    out = task.dir / "clues"
    out.mkdir(parents=True, exist_ok=True)
    needs = surface.required(task)

    used: set[str] = set()
    # The same two ledgers `replace` keeps, because `place_one` needs them to
    # cap invented threads per channel and comments per page.
    per_channel: collections.Counter = collections.Counter()
    per_page: collections.Counter = collections.Counter()
    requirements = []
    for number, req in enumerate(task.hidden_requirements, 1):
        req_id = f"{task.id}.r{number}"
        facts = [f for f in FACT_FIELDS if (req.get("requirement") or {}).get(f)]
        need = needs.get(req_id)
        print(f"[{req_id}] tree over {len(facts)} fact(s), "
              f"{len(need.all_names) if need else 0} name(s) the grader reaches for")
        tree = stage_tree(task, corpus, req_id, req, list(sources), people, budget,
                          reach, need)
        # One re-ask, and only for names, because a name is the one defect no amount
        # of reading recovers from: the clues arm that cost ten rollouts died on
        # `no attribute 'plan_fingerprint'`, a word the whole plant never used. The
        # better of the two trees is kept rather than the newer, so a second attempt
        # that fixes the names and loses something else cannot make things worse.
        if need:
            short = surface.unsaid(need.all_names, [l["text"] for l in tree["leaves"]])
            if short:
                print(f"[{req_id}] re-asking: nothing says {', '.join(short)}")
                again = stage_tree(task, corpus, req_id, req, list(sources), people,
                                   budget, reach, need, missing=short, attempt=2)
                if len(surface.unsaid(need.all_names,
                                      [l["text"] for l in again["leaves"]])) < len(short):
                    tree = again
        herrings = stage_herrings(task, corpus, req_id, req, people, budget)
        print(f"[{req_id}] {len(tree['subconclusions'])} subconclusions, "
              f"{len(tree['leaves'])} leaves, {len(herrings)} herring(s)")

        # `place_one`, not a second copy of it. This loop used to call
        # `stage_conversation` for every rejected candidate whatever the remark's
        # source, so a `notion` remark whose placement asked for `doc_new` was
        # written as a chat transcript and then filed under a `page:` room -- with
        # the page's filename falling back to the CLUE ID when the conversation
        # writer returned no title. Fixing it in `place_one` alone is what made
        # `replace --mismatched` a step anybody had to run.
        # Spread BEFORE placing, not only when somebody runs `replace`. `rebalance`
        # existed and was reachable from the re-placement path alone, so the first
        # plant kept whatever source the tree picked per leaf -- and the tree picks
        # chat unless told otherwise. g1 came out 44 slack / 2 notion / 4 email and
        # g4 came out 48 slack / 0 / 0: a company whose every decision happens in
        # one channel, which is the least realistic thing here and the easiest tell
        # to read. Per requirement rather than over the whole plant, so BOTH
        # requirements are spread rather than one paying for the other.
        rebalance(tree["leaves"], reach)
        for leaf in tree["leaves"]:
            leaf = place_one(task, corpus, leaf, clue_window, used, per_channel,
                             budget, per_page)
            if leaf.get("adapted") is None:
                leaf["adapted"] = leaf["text"]
            where = leaf["slot"]["room"] if leaf["slot"] else "nowhere"
            print(f"  {leaf['id']:28} -> {where} ({leaf['slot']['date'] if leaf['slot'] else '-'})")

        # Herrings go where the leaves are not: strictly before the earliest of
        # them. A fixed corpus cannot reserve the calendar the way phase 3 does,
        # so the ordering is enforced here, against the dates that exist.
        dated = [l["slot"]["date"] for l in tree["leaves"] if l.get("slot") and l["slot"].get("date")]
        cutoff = min(dated) if dated else clue_window[0]
        for herring in herrings:
            herring = place_one(task, corpus, herring,
                                (herring_window[0], min(cutoff, herring_window[1])),
                                used, per_channel, budget, per_page)
            if herring.get("adapted") is None:
                herring["adapted"] = herring["text"]
            if herring["slot"]:
                herring["slot"]["reversed_on"] = cutoff

        # After the leaves, so the reversal can refer to what they worked out, and
        # placed in a window that OPENS at the herring rather than at the corpus
        # start -- a retraction dated before the thing it retracts reads, to anyone
        # going in date order, as a decision nobody had made yet.
        placed_h = [h for h in herrings if h.get("slot")]
        reversals = stage_reversals(task, corpus, req_id, req, placed_h,
                                    [as_row(l) for l in tree["leaves"]],
                                    people, facts, budget)
        for row in reversals:
            after = next((h["slot"]["date"] for h in placed_h
                          if h["id"] == row["reverses"]), clue_window[0])
            row = place_one(task, corpus, row,
                            (max(after, clue_window[0]), clue_window[1]),
                            used, per_channel, budget, per_page)
            if row.get("adapted") is None:
                row["adapted"] = row["text"]

        requirements.append({
            "req_id": req_id, "requirement": req.get("requirement") or {},
            "earlier_reversed_version": req.get("earlier_reversed_version"),
            "fragmentation_sources": list(sources),
            "types": req.get("hidden_requirement_types") or [],
            "subconclusions": tree["subconclusions"],
            "clues": [as_row(x) for x in tree["leaves"] + herrings + reversals],
            "gaps": coverage(facts, tree["leaves"]),
            "spread": spread(tree["leaves"]),
            "required_names": need.all_names if need else [],
            "required_values": need.all_values if need else [],
            "missing_identifiers": [],      # filled below, once everything is placed
            "unprinted_values": [],
        })

    # A name is missing only when NOBODY says it anywhere in the plant -- a reader
    # meets the whole corpus, not one requirement's slice, and r2's remarks naming
    # `BatchPlanTooFragmentedError` hand it to r1's reader just as well. Only placed
    # remarks count: `horizon.render_remarks` drops an unplaced one, so a name whose
    # only carrier never found a home is a name nobody ever reads.
    said = [clue["text"] for record in requirements
            for clue in record["clues"] if clue.get("carrier")]
    for record in requirements:
        record["missing_identifiers"] = surface.unsaid(record["required_names"], said)
        record["unprinted_values"] = surface.unsaid(record["required_values"], said)

    ledger = {"schema_version": 1,
              "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "generator": "task_generator/tg/clues.py",
              "corpus": str(corpus.root),
              "windows": {"clues": clue_window, "herrings": herring_window},
              "tasks": [{"task_id": task.id, "title": task.title,
                         "description": task.description,
                         "requirements": requirements}]}
    # Through `finish` rather than writing the three files here, which is what
    # this did. `finish` is "the one tail every pass ends at" and a FRESH plant
    # was the one thing that never went through it -- so the six checks it
    # computes existed for re-plants only, and the first plant of a new task was
    # measured by nothing. It writes the same three files.
    return finish(task, corpus, ledger, "planted_at")


def as_row(leaf: dict) -> dict:
    """One clue in phase 3's `clues.json` shape, so clue_digest reads it unchanged.

    `text` is the ADAPTED wording -- what would actually appear in the corpus --
    because that is what a reader of the clues arm sees. The tree's original
    sentence is kept beside it as `drafted` so the two can be compared.
    """
    return {"clue_id": leaf["id"], "kind": leaf.get("kind", "clue"),
            "reverses": leaf.get("reverses") or "",
            "covers": leaf.get("covers") or [],
            "subconclusion": leaf.get("subconclusion") or "",
            "holder": leaf["holder"],
            "text": leaf.get("adapted") or leaf["text"],
            "drafted": leaf["text"],
            "settles": leaf.get("settles") or "",
            "leaves_open": leaf.get("leaves_open") or "",
            "verbatim": leaf.get("verbatim") or [],
            "forbidden_terms": leaf.get("forbidden_terms") or [],
            "source": leaf.get("source") or "slack",
            "carrier": leaf.get("slot"),
            "placement": leaf.get("placement") or {},
            "invented": leaf.get("invented"),
            "problems": leaf.get("problems") or [],
            "status": "planned", "rendered_in": None, "verified": False}


def snapshot(task: Task, label: str) -> pathlib.Path | None:
    """Copy the current plant aside before a pass rewrites it.

    Eleven of these sit in `out/batch-payload-plan/` and every one was a `cp -r`
    somebody typed -- `clues.v4-hosted-0.70`, `clues.settled-63of69`,
    `clues.v7-perfect-1.00`. They are the only reason a measured plant could be
    compared against the one that replaced it, and the only reason `l6` could be
    proved to be the difference. Too useful to leave to whoever remembers.
    """
    live = task.dir / "clues"
    if not (live / "plant.json").is_file():
        return None
    into = task.dir / f"clues.{label}"
    if into.exists():
        shutil.rmtree(into)
    shutil.copytree(live, into)
    return into


def _partial(task: Task, stamp: str) -> pathlib.Path:
    return task.dir / "clues" / f".{stamp}.partial.json"


def resume(task: Task, stamp: str) -> dict:
    """The plant, or where an interrupted pass of this kind got to.

    Every pass that edits a finished plant mutates `ledger` in place and writes
    ONCE, at the end, through `finish()`. So a pass killed before that loses every
    call it has paid for. On one afternoon `repair` died four calls in and `reknit`
    fourteen exchanges in, both to a ten-minute harness timeout, $1.64 of model
    time for nothing and `plant.json` untouched on both occasions -- which also
    means the failure is invisible afterwards, because the artifact still reads
    exactly as it did before the money was spent.

    Because the ledger IS the state, a checkpoint is just the ledger and resuming
    is just reading it back.
    """
    part = _partial(task, stamp)
    if part.is_file():
        print(f"  resuming from {part.name} — an earlier pass was interrupted")
        return json.loads(part.read_text())
    return json.loads((task.dir / "clues" / "plant.json").read_text())


def checkpoint(task: Task, ledger: dict, stamp: str) -> None:
    """Record where the pass has got to, so a kill costs one call, not all of them."""
    _partial(task, stamp).write_text(json.dumps(ledger, indent=1) + "\n")


def finish(task: Task, corpus: Corpus, ledger: dict, stamp: str) -> dict:
    """Recompute every derived field over the whole plant, stamp it, write the files.

    Every pass that edits a finished plant ends the same way, and the first three
    each grew their own copy of this tail with a different hole in it: `repair`
    recomputes the surface fields and not `spread`, `reorder` recomputes
    `missing_identifiers` and nothing else, and NOBODY recomputes `gaps` or re-runs
    `leaf_problems`. So a rewrite that dropped the only remark carrying a fact, or
    that grew to fifty words, was invisible in the README the same pass then wrote.
    """
    entry = ledger["tasks"][0]
    needs = surface.required(task)
    # The settle judge's readings of the remark texts, when a settle pass has left
    # any. They are what makes `gaps` evidence rather than the generator's own
    # word for it -- see `uncarried`.
    claims = task.dir / "clues" / "claims.json"
    verdicts = (json.loads(claims.read_text()).get("verdicts") or {}
                if claims.is_file() else {})
    said = [clue["text"] for req in entry["requirements"]
            for clue in req["clues"] if clue.get("carrier")]
    for req in entry["requirements"]:
        requirement = req.get("requirement") or {}
        known = {sub["id"] for sub in req["subconclusions"]}
        need = needs.get(req["req_id"])
        # `forbidden_terms` and the graded surface disagree, and the surface wins.
        # The tree stage lists the words that would give a requirement away and it
        # regularly lists `plan_document` -- which `surface.py` then demands somebody
        # type, because the test reads that attribute by name. Fourteen remarks here
        # were flagged for carrying a term they were required to carry.
        graded = set(need.all_names if need else [])
        for clue in req["clues"]:
            clue["forbidden_terms"] = [t for t in clue.get("forbidden_terms") or []
                                       if t not in graded]
        # Against the ADAPTED text, which is what a reader sees. The plan-time check
        # ran on the drafted sentence and placement rewrites it afterwards, so a
        # remark that grew past thirty words on its way into a room said so nowhere.
        leaves = [{**c, "slot": c.get("carrier")} for c in req["clues"]
                  if c["kind"] != "herring"]
        for clue in leaves:
            # A reversal sits in no subconclusion and leaves nothing for a sibling:
            # it answers a herring, not a step of the tree. Running the leaf checks
            # over it reported four healthy remarks as broken.
            if clue["kind"] == "reversal":
                problems = [p for p in leaf_problems(clue, requirement)
                            if "sibling remark" not in p]
            else:
                problems = leaf_problems(clue, requirement)
                if clue["subconclusion"] not in known:
                    problems.append("names no known subconclusion")
            # `leaves` holds copies, so the recomputed list goes back on the row.
            next(c for c in req["clues"]
                 if c["clue_id"] == clue["clue_id"])["problems"] = problems
        fields = [f for f in FACT_FIELDS if requirement.get(f)]
        req["gaps_claimed"] = coverage(fields, leaves)
        judged = uncarried(f"{entry['task_id']}.{req['req_id']}", fields, verdicts)
        req["gaps"] = req["gaps_claimed"] if judged is None else judged
        req["gaps_from"] = "covers" if judged is None else "settle verdicts"
        req["spread"] = spread([l for l in leaves if l.get("slot")])
        req["required_names"] = need.all_names if need else []
        req["required_values"] = need.all_values if need else []
        req["missing_identifiers"] = surface.unsaid(req["required_names"], said)
        req["unprinted_values"] = surface.unsaid(req["required_values"], said)

    # Three checks that read the rendered plant rather than the constraints that
    # were supposed to produce it. Each existed already and each was wired to a
    # single command nobody runs on the happy path -- `unreversed` only to
    # `reverse`, `out_of_order` only to `reorder` -- so four herrings sat
    # unretracted through a whole measured corpus and the plant passed every gate
    # it had. Computing them here means every pass that touches a plant reports
    # them, whether or not it was the pass that could have caused them.
    entry["stock_phrasing"] = stock_phrasing(entry)
    entry["voice_problems"] = voice_problems(entry)
    entry["unclashed"] = unclash(entry, corpus)
    entry["double_booked"] = double_booked(entry, corpus)
    entry["too_wordy"] = too_wordy(entry, corpus)
    entry["contradictions"] = contradictions(entry)
    entry["finished_claims"] = finished_claims(entry)
    entry["unstated"] = unstated(verdicts)
    entry["unreversed"] = unreversed(entry)
    entry["out_of_order"] = out_of_order(entry)
    entry["unknit"] = unknit(entry, set(corpus.people()))

    ledger[stamp] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    out = task.dir / "clues"
    (out / "plant.json").write_text(json.dumps(ledger, indent=1) + "\n")
    # The pass completed; its resume point is now misleading rather than useful.
    _partial(task, stamp).unlink(missing_ok=True)
    (out / "README.md").write_text(render_readme(task, corpus, ledger))
    (out / "tree.md").write_text(render_tree(ledger))
    return ledger


# What each stored field means for the exit code. Hard findings are defects in
# the artifact a reader will see; soft ones are worth printing and not worth
# failing a paid pass over.
HARD = ("unknit", "unreversed", "out_of_order", "voice_problems",
        "double_booked")
SOFT = ("stock_phrasing", "unstated", "finished_claims", "too_wordy",
        "contradictions")


def problems(entry: dict) -> tuple[list[str], list[str]]:
    """The findings `finish` stored, as (must-fix, worth-knowing).

    `finish` computes six checks on every pass and writes them onto the entry, and
    until this existed **nothing read four of them**. `stock_phrasing` and
    `unstated` had no reader anywhere in the package; `unreversed`, `out_of_order`
    and `unknit` were each read by exactly one command -- the one that could have
    caused them. So `settle`, `replace` and `repair` could each introduce a defect
    another pass owns and exit 0, which is how four herrings sat unretracted
    through a whole measured corpus.

    That is the same disease `finish`'s own docstring describes, one level up:
    `finish` fixed the recording and left the gating alone. Every command that
    writes a plant now calls this and fails on the first tuple.
    """
    def line(name: str, row) -> str:
        # `out_of_order` yields dicts and everything else yields strings. It was
        # never printed before this function existed, so nobody had to read one.
        if isinstance(row, dict) and "not_before" in row:
            row = (f"{row['clue_id']} is dated {row['dated']} but settles "
                   f"{row['subconclusion']}, whose problem is not raised until "
                   f"{row['not_before']} — the answer arrives before the question")
        return f"{name}: {row}"

    return ([line(n, r) for n in HARD for r in entry.get(n) or []],
            [line(n, r) for n in SOFT for r in entry.get(n) or []])


# ---------------------------------------------------------------------------
# the README
# ---------------------------------------------------------------------------
def carrier_block(corpus: Corpus, clue: dict) -> list[str]:
    """The material around a remark, so its fit can be judged rather than trusted.

    The first README printed a placement's `why` and nothing else, which is exactly
    the sentence a reader cannot check: "the room is already chewing on this" is a
    claim about messages the reader was never shown. Everything below is the real
    surrounding text, pulled from the corpus at render time.
    """
    car = clue.get("carrier") or {}
    kind, out = car.get("kind"), []
    inv = clue.get("invented") or {}

    if kind == "chat_insert":
        key = car.get("key", "")
        _, _, rest = key.partition("|")
        channel, _, date = rest.partition("|")
        msgs = corpus.by_channel_day.get((channel, date), [])
        after = (car.get("insert_after") or "").strip()
        out += [f"*Goes into the real conversation in #{channel} on {date}, "
                f"after {after or 'the last message'}:*", "", "```"]
        # The anchor is a minute and a name, and people send four messages in a
        # minute -- marking every match put the same "goes here" on four lines of
        # one burst. The remark follows the LAST of them, which is also what an
        # inserter has to do with an anchor this coarse.
        matches = [i for i, m in enumerate(msgs)
                   if after and after == f"{m.created_at[11:16]} {m.author}"]
        at = matches[-1] if matches else (len(msgs) - 1 if msgs else -1)
        for i, m in enumerate(msgs):
            marker = "   <-- THE REMARK GOES HERE" if i == at else ""
            out.append(f"{m.created_at[11:16]}  {m.author}: {m.text[:150]}{marker}")
        out += ["```", ""]
    elif kind in ("doc_edit", "doc_comment"):
        path = car.get("room", "")[5:]
        page = next((p for p in corpus.pages if p.path == path), None)
        what = "a section in" if kind == "doc_edit" else "a comment on"
        out += [f"*Goes as {what} the real page `{path}`"
                + (f", at: {car['anchor']}" if car.get("anchor") else "") + ":*", ""]
        if page:
            out += ["```", page.body[:1200].strip(), "```", ""]
    elif kind == "mail_reply":
        mid = car.get("room", "")[7:]
        note = next((m for m in corpus.mail if m.message_id == mid), None)
        out += [f"*Goes as a reply into the real thread \"{car.get('title') or mid}\":*", ""]
        if note:
            out += ["```", note.body[:1200].strip(), "```", ""]
    elif kind == "doc_new":
        out += [f"*A new page — **{inv.get('title')}** in `{inv.get('collection')}`, "
                f"{inv.get('date')}:*", ""]
        for section in inv.get("sections") or []:
            mark = " **← carries the remark**" if section.get("carries_the_remark") else ""
            out += [f"> **{section.get('heading')}**{mark}", "",
                    "> " + (section.get("body") or "").replace("\n", "\n> ")[:700], ""]
    elif kind == "mail_new":
        out += [f"*A new thread — **{inv.get('subject')}**, {inv.get('date')}:*", "", "```"]
        for m in inv.get("messages") or []:
            mark = "   <-- the remark" if m.get("is_the_remark") else ""
            out += [f"From: {m.get('sender')}  To: {', '.join(m.get('to') or [])}{mark}",
                    (m.get("body") or "")[:500], ""]
        out += ["```", ""]
    elif kind == "chat_thread":
        out += [f"*A new conversation in #{inv.get('channel')} on {inv.get('date')}:*", "", "```"]
        for m in inv.get("messages") or []:
            mark = "   <-- the remark" if m.get("is_the_remark") else ""
            out.append(f"{m.get('minute', '')}  {m.get('author', '')}: {m.get('text', '')}{mark}")
        out += ["```", ""]
    return out


def render_readme(task: Task, corpus: Corpus, ledger: dict) -> str:
    entry = ledger["tasks"][0]
    rows = [(c, r) for r in entry["requirements"] for c in r["clues"]]
    dated = sorted(rows, key=lambda pair: (pair[0]["carrier"] or {}).get("date") or "")

    lines = [f"# Clues for {task.id} — {task.title}", "",
             f"{len(rows)} remarks across {len(entry['requirements'])} hidden "
             f"requirements, to be planted in `{ledger['corpus']}`.", "",
             f"Clue window `{ledger['windows']['clues'][0]}` to "
             f"`{ledger['windows']['clues'][1]}`; herrings before "
             f"`{ledger['windows']['herrings'][1]}`.", "",
             "**Nothing here has been inserted into the corpus.** This is the plan: "
             "what each person says, where it goes, and why it belongs there.", "",
             "## The task the agent is given", "", task.description, "",
             "## Every remark, in the order a reader would meet them", "",
             "| date | where | who | says | carries |", "|---|---|---|---|---|"]
    for clue, req in dated:
        car = clue["carrier"] or {}
        where = car.get("room") or "*unplaced*"
        if car.get("kind", "").startswith(("chat_thread", "doc_new", "mail_new")):
            where += " *(new)*"
        covers = ", ".join(f"`{c}`" for c in clue["covers"]) or ("*herring*" if clue["kind"] == "herring" else "—")
        said = clue["text"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {car.get('date') or '—'} | {where} | {clue['holder']} "
                     f"| {said} | {covers} |")

    for req in entry["requirements"]:
        lines += ["", f"## {req['req_id']}", "", "**The hidden requirement:**", ""]
        for field, value in (req["requirement"] or {}).items():
            lines.append(f"- **{field}** — {value}")
        if req["earlier_reversed_version"]:
            lines += ["", f"**Reversed earlier:** {req['earlier_reversed_version']}"]
        lines += ["", "**What a reader has to infer along the way:**", ""]
        for sub in req["subconclusions"]:
            lines.append(f"- *{sub['text']}*")
            lines.append(f"  - nobody says: {sub.get('commonsense', '')}")
        if req["gaps"]:
            lines += ["", f"> **No remark carries {', '.join(req['gaps'])}.** The clues arm "
                          "cannot pass those facts."]
        if req.get("required_names"):
            said = [n for n in req["required_names"] if n not in req["missing_identifiers"]]
            lines += ["", "**Names the tests reach for that the ticket withholds:**", "",
                      "- said: " + (", ".join(f"`{n}`" for n in said) or "*none*")]
            if req["missing_identifiers"]:
                lines += ["- **never said: "
                          + ", ".join(f"`{n}`" for n in req["missing_identifiers"])
                          + "** — a reader cannot produce a name nobody wrote, so every "
                            "fact needing one scores zero however well the rest is read."]
        if req.get("unprinted_values"):
            lines += ["", "> **Values nobody prints:** "
                      + ", ".join(f"`{v}`" for v in req["unprinted_values"])
                      + ". Fine if the remarks say enough to compute them; check that "
                        "they do."]
        if req["spread"]:
            lines += ["", "> **Spread:** " + "; ".join(req["spread"])]
        lines += settle_lines(task, req["req_id"])

        # Grouped by the step each remark serves, not in one flat list. The whole
        # design is that no remark closes a step alone, and a flat list is exactly
        # the shape that hides whether that is true.
        lines += ["", "### The remarks, by the step they build", ""]
        by_sub = collections.defaultdict(list)
        for clue in req["clues"]:
            by_sub[clue["subconclusion"] if clue["kind"] == "clue" else "_herrings"].append(clue)
        ordered = []
        for sub in req["subconclusions"]:
            mine = sorted(by_sub.pop(sub["id"], []),
                          key=lambda c: (c.get("carrier") or {}).get("date") or "")
            problems = sum(1 for c in mine if stance(c) == "problem")
            asked = sum(1 for c in mine if hedged(c["text"]))
            lines += [f"### {sub['id']} — {sub['text']}", "",
                      f"*Nobody says:* {sub.get('commonsense', '')}", "",
                      f"*{len(mine)} remarks — {problems} reporting the problem, "
                      f"{len(mine) - problems} settling the design"
                      + (f", {asked} still asking rather than saying" if asked else "")
                      + ".*", ""]
            ordered += mine
            for clue in mine:
                lines += clue_block(corpus, clue, req)
        for key, mine in by_sub.items():
            if key == "_herrings":
                lines += ["### Herrings — believed at the time, overturned later", ""]
            else:
                lines += [f"### {key} — *(no such subconclusion)*", ""]
            for clue in mine:
                lines += clue_block(corpus, clue, req)
        continue

    return "\n".join(lines) + "\n"


def settle_lines(task: Task, req_id: str) -> list[str]:
    """The last `settle` verdict for this requirement, if one has been taken.

    Read out of `claims.json` rather than recomputed, because the verdicts cost a
    model call each and the README is written by four passes that do not make them.
    Absent file, absent section -- an old plant simply does not carry the line.
    """
    path = task.dir / "clues" / "claims.json"
    if not path.is_file():
        return []
    rows = [row for row in json.loads(path.read_text())["verdicts"].values()
            if row["key"].startswith(req_id + ".")]
    if not rows:
        return []
    short = [r for r in rows if r["verdict"] not in ("stated", "not_required")]
    if not short:
        return ["", f"> **Said outright:** every one of the {len(rows)} assertions "
                    "grading this requirement rests on a remark that states it "
                    "(`settled.md`)."]
    counts = collections.Counter(r["verdict"] for r in short)
    return ["", f"> **{len(short)} of {len(rows)} graded assertions are not stated "
                "outright** — "
                + ", ".join(f"{n} {v}" for v, n in sorted(counts.items()))
                + ". A reader has to supply the rest themselves, and may not. "
                  "See `settled.md`."]


def clue_block(corpus: Corpus, clue: dict, req: dict) -> list[str]:
    lines = []
    if True:
        for clue in [clue]:
            car = clue["carrier"] or {}
            head = "herring" if clue["kind"] == "herring" else ", ".join(clue["covers"])
            subs = {sub["id"]: sub["text"] for sub in req["subconclusions"]}
            lines += [f"#### `{clue['clue_id']}` — {head}", "",
                      f"**{clue['holder']}**, {car.get('date') or 'unplaced'}, "
                      f"{car.get('room') or '—'}", "",
                      "> " + clue["text"].replace("\n", "\n> "), ""]
            # What the remark is FOR, which the first README never said: a reader
            # could see which fact a clue was filed under and not what they were
            # supposed to take away from it.
            if clue["kind"] == "clue":
                lines += [f"*What a reader should take from it:* {clue.get('settles') or '—'}", ""]
                if clue.get("subconclusion") in subs:
                    lines += [f"*Step it builds toward:* `{clue['subconclusion']}` — "
                              f"{subs[clue['subconclusion']]}", ""]
            else:
                lines += ["*A herring: stated as settled at the time, overturned later "
                          f"(from {car.get('reversed_on', '?')}).*", ""]
            if clue["drafted"] != clue["text"]:
                lines += [f"*Drafted as:* {clue['drafted']}", ""]
            if car.get("why"):
                lines += [f"*Why there:* {car['why']}", ""]
            if clue.get("leaves_open"):
                lines += [f"*Still leaves open:* {clue['leaves_open']}", ""]
            if clue["verbatim"]:
                lines += ["*Must appear literally:* "
                          + ", ".join(f"`{v}`" for v in clue["verbatim"]), ""]
            lines += carrier_block(corpus, clue)
            if clue["problems"]:
                lines += ["> **Problems:** " + "; ".join(clue["problems"]), ""]
    return lines


def render_tree(ledger: dict) -> str:
    lines = ["# The tree", ""]
    for req in ledger["tasks"][0]["requirements"]:
        lines += [f"## {req['req_id']}", ""]
        for sub in req["subconclusions"]:
            mine = [c for c in req["clues"] if c["subconclusion"] == sub["id"]]
            lines += [f"### {sub['id']} — {sub['text']}", "",
                      f"*The leap nobody states:* {sub.get('commonsense', '')}", ""]
            for clue in mine:
                car = clue["carrier"] or {}
                lines.append(f"- **{clue['holder']}** ({car.get('date') or '—'}, "
                             f"{car.get('room') or '—'}): {clue['text']}")
            lines.append("")
        loose = [c for c in req["clues"] if c["kind"] == "herring"]
        if loose:
            lines += ["### herrings — believed at the time, reversed later", ""]
            for clue in loose:
                car = clue["carrier"] or {}
                lines.append(f"- **{clue['holder']}** ({car.get('date') or '—'}): {clue['text']}")
            lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# repair — the plant against a measured proof
# ---------------------------------------------------------------------------
def leaves_for(entry: dict, req_id: str, field: str) -> list[dict]:
    """Every planted remark that claims to carry one fact."""
    for req in entry["requirements"]:
        if req["req_id"] == req_id:
            return [c for c in req["clues"] if field in (c.get("covers") or [])]
    return []


def describe_leaves(rows: list[dict]) -> str:
    out = []
    for clue in rows:
        car = clue.get("carrier") or {}
        out.append(f"### `{clue['clue_id']}` — **{clue['holder']}**, "
                   f"{car.get('date') or 'unplaced'}, {car.get('room') or '—'}\n\n"
                   f"> {clue['text']}\n\n"
                   f"*It is meant to leave the reader knowing:* {clue.get('settles') or '—'}\n")
    return "\n".join(out) or "*(no remark claims this fact)*"


def repair(slug: str, failures: dict[str, str], *, run: str | None = None,
           budget: float = 3.0) -> dict:
    """Rewrite the remarks a proof says do not carry their fact, in place.

    In place, and not a re-plant, for the reason phase 4 repairs a thinned clue
    rather than re-running its day: a re-plant re-rolls every remark in the tree,
    including the ones the same proof just showed are working. Here that is 32
    remarks thrown away to fix four, and the placement -- which conversation each one
    sits in, and what it is answering -- is the expensive part.
    """
    task = load(slug)
    corpus = Corpus(pathlib.Path(run) if run else None)
    plant = task.dir / "clues" / "plant.json"
    ledger = resume(task, "repaired_at")
    entry = ledger["tasks"][0]
    reach = corpus.reachable(tuple(ledger["windows"]["clues"]))
    people = [p for p in corpus.people() if p in corpus.cast and p in reach]
    used = {(c.get("carrier") or {}).get("key") for req in entry["requirements"]
            for c in req["clues"] if c.get("carrier")}
    used.discard(None)

    changed = {"rewritten": [], "added": [], "unfixed": []}
    for key, why in sorted(failures.items()):
        req_id, field = key.rsplit(".", 1)
        req = next((r for r in entry["requirements"] if r["req_id"] == req_id), None)
        if not req:
            changed["unfixed"].append(f"{key}: no such requirement in the plant")
            continue
        fact = (req["requirement"] or {}).get(field)
        rows = leaves_for(entry, req_id, field)
        mine = {c["clue_id"] for c in rows}
        # A remark claiming another fact can still be what breaks this one: the plant
        # that scored 10 of 11 failed its last fact on a remark filed under `rule`
        # saying the hash is only reached "when there's a line to feed it", dated
        # after the two remarks that had the empty case right.
        others = [c for c in req["clues"]
                  if c["clue_id"] not in mine and c.get("carrier")]
        text = prompt("clue_repair.md", req_id=req_id, field=field, fact=fact or "(undeclared)",
                      leaves=describe_leaves(rows), others=describe_leaves(others),
                      failure=why or "(no assertion recorded)",
                      roster=roster_lines(corpus, people, reach))
        result = agent.run(text, repo=REPO, label=f"clue-repair-{key}", cwd=task.dir,
                           tools="", schema=cs.repair_schema(people, FACT_FIELDS, list(cs.SOURCES)),
                           budget_usd=budget, log_dir=task.dir / "logs")
        _record(task, f"clue-repair-{key}", text, result)
        data = result.data or {}

        by_id = {c["clue_id"]: c for r in entry["requirements"] for c in r["clues"]}
        for row in data.get("rewrites") or []:
            clue = by_id.get(row.get("clue_id"))
            if not clue or not (row.get("text") or "").strip():
                continue
            # The same guard the placement stage uses: a rewrite that drops an
            # identifier the grader reads by name is not an improvement.
            kept, why_not = keep_wording({**clue, "verbatim": row.get("verbatim")
                                          or clue.get("verbatim") or []}, row["text"])
            if why_not:
                changed["unfixed"].append(f"{clue['clue_id']}: {why_not}")
                continue
            clue["repaired_from"] = clue.get("repaired_from") or clue["text"]
            clue["text"] = kept
            clue["verbatim"] = sorted(set((clue.get("verbatim") or []) + (row.get("verbatim") or [])))
            clue["repair_note"] = row.get("why", "")
            changed["rewritten"].append(f"{clue['clue_id']} ({key})")
            checkpoint(task, ledger, "repaired_at")

        extra = data.get("addition")
        if extra and (extra.get("text") or "").strip() and extra.get("holder") in people:
            leaf = {**extra, "id": f"{req_id}.fix{len(req['clues'])}",
                    "subconclusion": extra.get("subconclusion") or "",
                    "covers": [field], "kind": "clue",
                    "verbatim": extra.get("verbatim") or [],
                    "forbidden_terms": extra.get("forbidden_terms") or []}
            leaf["problems"] = leaf_problems(leaf, req["requirement"])
            placed = stage_place(task, corpus, leaf, tuple(ledger["windows"]["clues"]),
                                 used, budget)
            invented = None
            if placed.get("choice") == "none":
                inv = placed.get("invent") or default_invent(
                    corpus, leaf, tuple(ledger["windows"]["clues"]), used)
                placed["invent"] = inv
                invented = stage_conversation(task, corpus, leaf, inv, budget)
            leaf["placement"] = {k: v for k, v in placed.items() if k != "_candidate"}
            leaf["slot"] = slot_of(leaf, placed, invented)
            leaf["invented"] = invented
            leaf["adapted"] = keep_wording(leaf, placed.get("adapted"))[0]
            if leaf["slot"]:
                used.add(leaf["slot"]["key"])
                req["clues"].append(as_row(leaf))
                changed["added"].append(f"{leaf['id']} ({key}) -> {leaf['slot']['room']}")
            else:
                changed["unfixed"].append(f"{key}: the new remark could not be placed")

    # The gate is re-run over what the digest will now hold, not over what was asked
    # for: a rewrite can lose a name as easily as it can add one.
    return {"ledger": finish(task, corpus, ledger, "repaired_at"), **changed}


# ---------------------------------------------------------------------------
# the carriers that are not chat
# ---------------------------------------------------------------------------
def nearby_pages(corpus: Corpus, date: str, want: int = 3) -> str:
    """Real pages from around a date, so a new one is written in the wiki's register."""
    pages = sorted(corpus.pages, key=lambda p: abs_days(p.date, date) if p.date and date else 999)
    out = []
    for page in pages[:want]:
        out.append(f"### {page.title} — {page.author}, {page.date}\n\n"
                   "```\n" + page.body[:900].strip() + "\n```\n")
    return "\n".join(out) or "(no pages nearby)"


def nearby_mail(corpus: Corpus, date: str, want: int = 3) -> str:
    threads = sorted(corpus.mail, key=lambda m: abs_days(m.date, date) if m.date and date else 999)
    out = []
    for note in threads[:want]:
        out.append(f"### {note.subject} — {note.sender} -> {', '.join(note.to)}, {note.date}\n\n"
                   "```\n" + note.body[:700].strip() + "\n```\n")
    return "\n".join(out) or "(no mail nearby)"


def stage_document(task: Task, corpus: Corpus, leaf: dict, invent: dict,
                   budget: float) -> dict:
    """A page that should have existed, with the remark inside one of its sections.

    Written rather than reached for because `notion` used to fall through to
    `stage_conversation`: every wiki remark in the first plant was published as a
    Slack message, and the ledger's `source` column said `notion` while the corpus
    said #pipeline.
    """
    date = invent.get("date") or ""
    verbatim = ""
    if leaf.get("verbatim"):
        verbatim = ("**These must appear literally in the section that carries it:** "
                    + ", ".join(f"`{v}`" for v in leaf["verbatim"]))
    text = prompt("clue_document.md", holder=leaf["holder"], text=leaf["text"],
                  verbatim=verbatim, date=date,
                  why=invent.get("prompted_by") or "no existing page covers this ground",
                  nearby=nearby_pages(corpus, date), voice=describe_voice(corpus.voice(leaf["holder"])))
    result = agent.run(text, repo=REPO, label=f"clue-doc-{leaf['id']}", cwd=task.dir,
                       tools="", schema=cs.DOCUMENT, budget_usd=budget,
                       log_dir=task.dir / "logs")
    _record(task, f"clue-doc-{leaf['id']}", text, result)
    data = result.data or {}
    return {"kind": "doc_new", "date": date, "title": data.get("title") or "",
            "collection": data.get("collection") or "engineering",
            "sections": data.get("sections") or []}


def stage_mail(task: Task, corpus: Corpus, leaf: dict, invent: dict,
               budget: float) -> dict:
    """A mail thread that should have happened, with the remark inside one reply."""
    date = invent.get("date") or ""
    people = invent.get("participants") or [leaf["holder"]]
    verbatim = ""
    if leaf.get("verbatim"):
        verbatim = ("**These must appear literally in their message:** "
                    + ", ".join(f"`{v}`" for v in leaf["verbatim"]))
    voices = "\n\n".join(f"**{p}**\n{describe_voice(corpus.voice(p))}" for p in people)
    text = prompt("clue_mail.md", holder=leaf["holder"], text=leaf["text"],
                  verbatim=verbatim, date=date,
                  why=invent.get("prompted_by") or "no existing thread fits",
                  nearby=nearby_mail(corpus, date), people=", ".join(people), voices=voices)
    result = agent.run(text, repo=REPO, label=f"clue-mail-{leaf['id']}", cwd=task.dir,
                       tools="", schema=cs.MAIL, budget_usd=budget,
                       log_dir=task.dir / "logs")
    _record(task, f"clue-mail-{leaf['id']}", text, result)
    data = result.data or {}
    return {"kind": "mail_new", "date": date, "subject": data.get("subject") or "",
            "participants": people, "messages": data.get("messages") or []}


def write_invented(task: Task, corpus: Corpus, leaf: dict, invent: dict,
                   budget: float) -> dict:
    """Whichever writer the source calls for."""
    kind = invent.get("kind") or {"slack": "chat_thread", "notion": "doc_new",
                                  "email": "mail_new"}.get(leaf.get("source"), "chat_thread")
    invent["kind"] = kind
    if kind == "doc_new":
        return stage_document(task, corpus, leaf, invent, budget)
    if kind == "mail_new":
        return stage_mail(task, corpus, leaf, invent, budget)
    return stage_conversation(task, corpus, leaf, invent, budget)


# ---------------------------------------------------------------------------
# re-placement — same remarks, better homes
# ---------------------------------------------------------------------------
# What the mix should look like. Not because a ratio is principled, but because
# the first plant came out 29 slack / 4 notion / 3 email BY DEFAULT -- the tree
# picks a source per leaf and picks chat unless told otherwise -- and a company
# whose every decision happens in one channel is the least realistic thing here.
# Chat stays the plurality because that is where engineering argument really
# happens, but not by the margin it used to: at 0.55/0.25/0.20 the plants still
# read as a chat corpus with a few documents attached, and a reader who learns
# that the interesting remarks live in Mattermost has most of the plant for free.
# Reachability still overrides this — an unreachable source is not a place anyone
# can be quoted — so these are targets, not guarantees.
MIX = (("slack", 0.40), ("notion", 0.30), ("email", 0.30))
MAX_INVENTED_PER_CHANNEL = 5
MAX_COMMENTS_PER_PAGE = 2


def rebalance(rows: list[dict], reach: dict[str, dict[str, int]]) -> None:
    """Reassign each remark's source toward MIX, within what its holder can reach.

    Reachability wins over the quota every time: a source somebody never used is
    not a place they can be quoted, and phase 3 learned that the expensive way --
    remarks handed to people who could not make them are remarks that cannot be
    placed at all.
    """
    quota = {source: max(1, round(share * len(rows))) for source, share in MIX}
    # Two callers, two row shapes: `replace` passes placed clues, which carry
    # `clue_id`; `plan` passes tree leaves, which carry `id` and are not given a
    # `clue_id` until placement. The sort is only here to make the assignment
    # deterministic, so either identifier will do — reading one of them
    # unconditionally cost a $45 run its first tree call.
    for row in sorted(rows, key=lambda r: r.get("clue_id") or r.get("id") or ""):
        can = [s for s, _ in MIX if (reach.get(row["holder"]) or {}).get(s)]
        if not can:
            continue
        # The scarcest reachable source this remark could still fill.
        pick = max(can, key=lambda s: quota.get(s, 0))
        if quota.get(pick, 0) <= 0:
            pick = row["source"] if row["source"] in can else can[0]
        quota[pick] = quota.get(pick, 0) - 1
        row["source"] = pick


def free_invention(corpus: Corpus, leaf: dict, invent: dict, window: tuple[str, str],
                   used: set[str], per_channel: collections.Counter) -> dict:
    """Keep an invented conversation from piling into one room.

    15 of the first plant's 21 invented threads were in #pipeline, on dates chosen
    by whoever was writing that leaf. A reader scrolling one channel meets the plant
    as a run of conversations that only ever happen when there is something to hide.
    """
    if (invent.get("kind") or "chat_thread") != "chat_thread":
        return invent
    rooms = [c for c, _ in collections.Counter(
        m.channel for m in corpus.messages if m.author == leaf["holder"]).most_common()]
    days = sorted({m.date for m in corpus.messages if window[0] <= m.date <= window[1]})
    # Per channel, not global. A day the corpus covers is not the same as a day
    # THIS room was awake: #code-review posts on 94% of active days, so the few it
    # misses are exactly the days on which a thread there is the only thing that
    # happened -- which is what `inject.timing()` refuses. Picking from the room's
    # own days makes that unreachable instead of caught later.
    by_room: dict[str, list[str]] = {}
    for m in corpus.messages:
        if window[0] <= m.date <= window[1]:
            by_room.setdefault(m.channel, []).append(m.date)
    live = {room: sorted(set(dates)) for room, dates in by_room.items()}
    channel = (invent.get("channel") or (rooms[0] if rooms else "engineering")).lstrip("#")
    for option in [channel] + rooms:
        if per_channel[option] >= MAX_INVENTED_PER_CHANNEL:
            continue
        # The model's own date, but only if the corpus actually has that day.
        # It was accepted unchecked, and `days` was merely the fallback -- so a
        # thread landed in #code-review on 2026-01-29, two days after the corpus
        # ends, and another on a dead Tuesday. A channel that is the only thing
        # alive on a date is the plant announcing itself; `inject.timing()` caught
        # both, which is one gate too late to be free.
        room_days = live.get(option) or days
        date = invent.get("date") if option == channel else ""
        if date and date not in room_days:
            date = ""
        for candidate in ([date] if date else []) + room_days:
            if candidate and f"new|{option}|{candidate}" not in used:
                invent["channel"], invent["date"] = option, candidate
                per_channel[option] += 1
                return invent
    per_channel[channel] += 1
    return invent


def comment_day(corpus: Corpus, holder: str, after: str,
                window: tuple[str, str]) -> str:
    """A day this person was actually around, strictly after the page was written."""
    days = sorted({m.date for m in corpus.messages if m.author == holder
                   and window[0] <= m.date <= window[1] and m.date > after})
    return days[len(days) // 3] if days else after


def stage_reversals(task: Task, corpus: Corpus, req_id: str, req: dict,
                    herrings: list[dict], said: list[dict], people: list[str],
                    facts: list[str], budget: float) -> list[dict]:
    """One remark per herring, in which the earlier decision is dropped out loud.

    The herring prompt forbids any hint that the decision will be revisited, which
    is right -- somebody recording a decision does not know it is about to be
    overturned. But nothing then said it HAD been. A reader met a confident January
    remark and a confident May remark that disagreed, with nothing to say which one
    won, and the January one was the more specific of the two because a herring
    states a whole shape (`{"num_jobs": 2, "start_idx": 0, ...}`) where the clues
    that replace it are spread over five people and three months.

    Not a herring and not a leaf: it carries facts like a leaf, so it takes part in
    coverage, and it is paired to the herring it answers so `unreversed()` can tell
    whether every earlier decision was actually put down.
    """
    if not herrings:
        return []
    lines = []
    for clue in sorted(said, key=lambda c: (c.get("carrier") or {}).get("date") or ""):
        car = clue.get("carrier") or {}
        lines.append(f"- **{car.get('date', '?')} · {clue['holder']}** — {clue['text']}")
    text = prompt("clue_reversals.md", company=company_blurb(corpus), title=task.title,
                  description=task.description, req_id=req_id,
                  requirement="\n".join(
                      f"- **{f}** — {req['requirement'][f]}" for f in facts),
                  reversed=req.get("earlier_reversed_version") or "",
                  herrings="\n".join(f"- `{h['id']}` **{h['holder']}** — {h['text']}"
                                     for h in herrings),
                  remarks="\n".join(lines) or "(nothing yet)",
                  roster=roster_lines(corpus, people))
    result = agent.run(text, repo=REPO, label=f"clue-reversal-{req_id}", cwd=task.dir,
                       tools="", schema=cs.reversal_schema(
                           people, [h["id"] for h in herrings], facts),
                       budget_usd=budget, log_dir=task.dir / "logs")
    _record(task, f"clue-reversal-{req_id}", text, result)
    out = []
    for number, row in enumerate((result.data or {}).get("reversals") or [], 1):
        out.append({"id": f"{req_id}.rev{number}", "kind": "reversal",
                    "reverses": row["reverses"], "text": row["text"],
                    "settles": row.get("settles") or "", "holder": row["holder"],
                    "covers": row.get("covers") or [], "leaves_open": "",
                    "verbatim": row.get("verbatim") or [], "forbidden_terms": [],
                    "subconclusion": "", "source": "slack"})
    return out


def unreversed(entry: dict) -> list[str]:
    """Herrings that nothing later puts down, and reversals that arrive too early.

    Two failures with the same cause -- a plant where the reader cannot tell which
    of two contradicting remarks won. A herring with no reversal is a decision the
    corpus never retracts; a reversal dated at or before its herring is a retraction
    of something that, to a reader going in date order, has not been decided yet.
    """
    out = []
    for req in entry["requirements"]:
        answered = {}
        for clue in req["clues"]:
            if clue.get("kind") == "reversal" and clue.get("reverses"):
                answered.setdefault(clue["reverses"], []).append(clue)
        for clue in req["clues"]:
            if clue.get("kind") != "herring":
                continue
            when = (clue.get("carrier") or {}).get("date") or ""
            rows = answered.get(clue["clue_id"]) or []
            if not rows:
                out.append(f"{clue['clue_id']}: said {when} and never taken back")
                continue
            for row in rows:
                then = (row.get("carrier") or {}).get("date") or ""
                if not then:
                    out.append(f"{row['clue_id']}: reverses {clue['clue_id']} "
                               "but was never placed")
                elif then <= when:
                    out.append(f"{row['clue_id']}: dated {then}, which is not after "
                               f"{clue['clue_id']} on {when}")
    return out


def place_one(task: Task, corpus: Corpus, leaf: dict, window: tuple[str, str],
              used: set[str], per_channel: collections.Counter, budget: float,
              per_page: collections.Counter | None = None,
              write_chat: bool = False) -> dict:
    """One remark through placement and, if nothing real fits, through a writer.

    `write_chat=False` skips writing an invented CHAT conversation here, because
    `reknit` writes one from scratch and does not read this one. Not a guess:
    `stage_thread` takes `clue["text"]`, the room from `room_of()`, the voices and
    the reversal, and never touches `clue["invented"]["messages"]`. g1 paid
    `clue-conv` 155 calls / $6.01 for conversations that `clue-thread` then
    discarded -- and those were the same conversations lesson 15 records as having
    drifted from their remarks in 33 of 35 cases, precisely because they were
    written here and never revisited.

    What is still needed from the invented branch is the SLOT -- channel and date
    -- and `free_invention` computes that deterministically, with no model call.
    So the dict handed to `slot_of` carries the kind, channel and date and no
    messages; `unknit` skips a clue with no turns, and `stage_thread` reads the
    `kind` off it.

    Documents and mail still get written. `stage_thread` looks an invented page up
    in `corpus.pages` and will not find one that exists only in the plant, so those
    two writers produce an artifact reknit genuinely depends on.
    """
    placed = stage_place(task, corpus, leaf, window, used, budget)
    invented = None
    if placed.get("choice") == "none":
        invent = placed.get("invent") or default_invent(corpus, leaf, window, used)
        invent["kind"] = cs.INVENT_KIND.get(leaf.get("source") or "slack", "chat_thread")
        invent = free_invention(corpus, leaf, invent, window, used, per_channel)
        placed["invent"] = invent
        if write_chat or not str(invent["kind"]).startswith("chat"):
            invented = write_invented(task, corpus, leaf, invent, budget)
        else:
            invented = dict(invent)
    leaf["placement"] = {k: v for k, v in placed.items() if k != "_candidate"}
    leaf["slot"] = slot_of(leaf, placed, invented)
    leaf["invented"] = invented
    leaf["adapted"] = keep_wording(leaf, placed.get("adapted"))[0]
    slot = leaf["slot"]
    if slot and slot.get("kind") == "doc_comment":
        path = slot["room"][5:]
        slot["page_written"] = slot["date"]
        slot["date"] = comment_day(corpus, leaf["holder"], slot["date"], window)
        if per_page is not None:
            per_page[path] += 1
            if per_page[path] >= MAX_COMMENTS_PER_PAGE:
                used.add(f"page-full|{path}")
    if slot:
        used.add(slot["key"])
    return leaf


def occupancy(entry: dict, moving: set[str] | None = None
              ) -> tuple[set[str], collections.Counter, collections.Counter]:
    """What the calendar already holds: taken slots, threads per channel, comments per page.

    Every pass that places a remark into a plant that already has remarks in it needs
    these three, and needs them to exclude whatever it is about to move -- a remark
    does not collide with the slot it is being lifted out of.
    """
    moving = moving or set()
    rows = [c for req in entry["requirements"] for c in req["clues"]
            if c["clue_id"] not in moving and c.get("carrier")]
    used = {c["carrier"]["key"] for c in rows}
    used.discard(None)
    per_channel = collections.Counter(
        c["carrier"].get("channel") for c in rows
        if c["carrier"].get("kind") == "chat_thread")
    per_page = collections.Counter(
        c["carrier"].get("room", "")[5:] for c in rows
        if c["carrier"].get("kind") == "doc_comment")
    for path, n in per_page.items():
        if n >= MAX_COMMENTS_PER_PAGE:
            used.add(f"page-full|{path}")
    return used, per_channel, per_page


def replace(slug: str, *, run: str | None = None, budget: float = 3.0,
            only: list[str] | None = None) -> dict:
    """Re-place every remark without rewriting one.

    The wording is the expensive, proven half: this plant's remarks build the task
    from the clues alone, 11 facts out of 11, and a re-plant would re-roll all of
    it to fix where they sit. So the text is carried over verbatim and only the
    carrier is decided again -- against a source mix, against page comments and
    mail threads that the first pass could not reach, and with a cap on how many
    conversations any one channel is allowed to grow.
    """
    task = load(slug)
    corpus = Corpus(pathlib.Path(run) if run else None)
    plant = task.dir / "clues" / "plant.json"
    ledger = resume(task, "replaced_at")
    entry = ledger["tasks"][0]
    clue_window = tuple(ledger["windows"]["clues"])
    herring_window = tuple(ledger["windows"]["herrings"])
    reach = corpus.reachable(clue_window)

    rows = [c for req in entry["requirements"] for c in req["clues"] if c["kind"] == "clue"]
    herrings = [c for req in entry["requirements"] for c in req["clues"] if c["kind"] == "herring"]
    if only:
        rows = [c for c in rows if c["clue_id"] in only]
        herrings = [c for c in herrings if c["clue_id"] in only]
    else:
        rebalance(rows, reach)

    # Slots already taken by remarks this pass is not touching stay taken.
    used, per_channel, per_page = occupancy(
        entry, {r["clue_id"] for r in rows + herrings})
    for row in rows:
        leaf = {"id": row["clue_id"], "text": row["text"], "holder": row["holder"],
                "source": row["source"], "settles": row["settles"],
                "leaves_open": row["leaves_open"], "verbatim": row["verbatim"],
                "forbidden_terms": row["forbidden_terms"],
                "subconclusion": row["subconclusion"], "covers": row["covers"]}
        leaf = place_one(task, corpus, leaf, clue_window, used, per_channel, budget,
                         per_page)
        row["carrier"] = leaf["slot"]
        row["placement"] = leaf["placement"]
        row["invented"] = leaf["invented"]
        row["text"] = leaf["adapted"] or row["text"]
        where = leaf["slot"]["room"] if leaf["slot"] else "nowhere"
        kind = (leaf["slot"] or {}).get("kind", "-")
        print(f"  {row['clue_id']:22} {row['source']:6} -> {kind:12} {where}")

    dated = [c["carrier"]["date"] for c in rows if c.get("carrier") and c["carrier"].get("date")]
    cutoff = min(dated) if dated else clue_window[0]
    for row in herrings:
        leaf = {"id": row["clue_id"], "text": row["text"], "holder": row["holder"],
                "source": row["source"], "settles": row["settles"], "leaves_open": "",
                "verbatim": row["verbatim"], "forbidden_terms": row["forbidden_terms"],
                "subconclusion": "", "covers": []}
        leaf = place_one(task, corpus, leaf, (herring_window[0], min(cutoff, herring_window[1])),
                         used, per_channel, budget, per_page)
        if leaf["slot"]:
            leaf["slot"]["reversed_on"] = cutoff
        row["carrier"] = leaf["slot"]
        row["placement"] = leaf["placement"]
        row["invented"] = leaf["invented"]
        row["text"] = leaf["adapted"] or row["text"]
        print(f"  {row['clue_id']:22} herring -> "
              f"{(leaf['slot'] or {}).get('room', 'nowhere')}")

    return finish(task, corpus, ledger, "replaced_at")


def reverse(slug: str, *, run: str | None = None, budget: float = 3.0,
            redo: bool = False) -> dict:
    """Add the missing retraction to a plant that already has its herrings.

    A separate pass rather than part of `plan()` alone because the plants that
    need it most are the ones already measured: re-planting to gain a reversal
    would re-roll every remark that was right, and the settle pass that made them
    right costs more than this does.
    """
    task = load(slug)
    corpus = Corpus(pathlib.Path(run) if run else None)
    plant = task.dir / "clues" / "plant.json"
    ledger = resume(task, "reversed_at")
    entry = ledger["tasks"][0]
    clue_window = tuple(ledger["windows"]["clues"])
    reach = corpus.reachable(clue_window)
    people = [p for p in corpus.people() if p in corpus.cast and p in reach]

    if redo:
        for req in entry["requirements"]:
            req["clues"] = [c for c in req["clues"] if c.get("kind") != "reversal"]

    used, per_channel, per_page = occupancy(entry)
    added = 0
    for req in entry["requirements"]:
        facts = [f for f in FACT_FIELDS if (req.get("requirement") or {}).get(f)]
        herrings = [c for c in req["clues"]
                    if c["kind"] == "herring" and c.get("carrier")]
        already = {c.get("reverses") for c in req["clues"]
                   if c.get("kind") == "reversal"}
        open_ones = [{"id": h["clue_id"], "holder": h["holder"], "text": h["text"],
                      "slot": h["carrier"]}
                     for h in herrings if h["clue_id"] not in already]
        if not open_ones:
            print(f"  {req['req_id']}: every herring is already taken back")
            continue
        said = [c for c in req["clues"] if c["kind"] != "herring" and c.get("carrier")]
        rows = stage_reversals(task, corpus, req["req_id"], req, open_ones, said,
                               people, facts, budget)
        for row in rows:
            after = next((h["slot"]["date"] for h in open_ones
                          if h["id"] == row["reverses"]), clue_window[0])
            row = place_one(task, corpus, row,
                            (max(after, clue_window[0]), clue_window[1]),
                            used, per_channel, budget, per_page)
            if row.get("adapted") is None:
                row["adapted"] = row["text"]
            req["clues"].append(as_row(row))
            added += 1
            where = row["slot"]["room"] if row["slot"] else "nowhere"
            when = row["slot"]["date"] if row["slot"] else "-"
            print(f"  {row['id']:22} reverses {row['reverses']:14} -> {where} ({when})")

    print(f"\n{added} reversal(s) added")
    return finish(task, corpus, ledger, "reversed_at")


# ---------------------------------------------------------------------------
# re-knit — a conversation the team had, not a fact dropped into one
# ---------------------------------------------------------------------------
# The first version of this forced the whole remark into one turn, verbatim, and
# guarded it with a substring test. That guaranteed the information was there and
# guaranteed it read as planted: one person reciting a specification, sometimes in
# answer to a question about something else entirely. Twelve of g1's fifty were a
# single message inserted into a real conversation, and one of those was a reversal
# landing in the middle of a code review at the same minute as the message above it.
#
# What replaces it: the exchange exists BECAUSE the team was working this out.
# Somebody raises it, somebody answers part, the first pushes on what is still
# unclear, the answer completes it. Nobody says the whole thing, and nobody reports
# having built it -- the implementation is the agent's job, so the corpus has to
# read as a decision taken and not yet carried out.
#
# The check moves with it. A remark split across four turns is not findable by
# substring, so carriage is judged claim by claim against the finished thread, by a
# call that is shown the remark rather than the writer's own account of where it put
# things, and `carried` is computed here from those rows.
MINUTE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def turns_of(clue: dict) -> list[dict]:
    return (clue.get("invented") or {}).get("messages") or []


def said(msg: dict) -> str:
    return msg.get("text") or msg.get("body") or ""


def who(msg: dict) -> str:
    """Who said one turn, whichever shape the exchange is in.

    The twin of `said` above, and it exists for the same reason. An exchange is
    written by a stage that speaks chat -- `author`/`text` -- while a mail turn
    comes back as `sender`/`body`. Ten readers in this file reached for `author`
    alone and three of them remembered `sender`, so `unknit` read g3's three
    mail threads as monologues by nobody: four authorless turns each, eighteen
    blocking findings, and a plant that was in fact well formed.

    `inject.who_said` had already learned this exact lesson -- "each grew its own
    idea of the field names, and each was wrong in a different way" -- and the
    fix never reached this file. One function, and every reader calls it.
    """
    return (msg.get("author") or msg.get("sender") or "").strip()


def identifiers_missing(clue: dict) -> list[str]:
    """Names the tests read that nobody in the exchange types. Free, and absolute.

    Fragmenting the remark is allowed; losing an identifier is not. A rule can be
    inferred from evidence and a name cannot, so this stays a literal search even
    though everything else about carriage is now a judgement.
    """
    joined = " ".join(said(m) for m in turns_of(clue))
    return [v for v in graded_names(clue) if v not in joined]


# English words and bare literals the tree sometimes lists as `verbatim`. g2's
# plant asked for `A`, `The`, `0`, `False`, `True`, `Optional` and `Execution` to
# appear literally. `The` is free and harmless; `True` is not -- an exchange can
# be rejected for failing to type a Python keyword nobody would say aloud, and
# then rewritten to no purpose. A name worth gating on is one somebody had to
# invent, which is the same judgement `leak.strong` already makes.
_NOT_A_NAME = {"a", "an", "the", "true", "false", "none", "null", "optional",
               "str", "int", "bool", "list", "dict", "execution", "error"}


def graded_names(clue: dict) -> list[str]:
    """The `verbatim` entries worth enforcing: real identifiers, not English."""
    out = []
    for raw in clue.get("verbatim") or []:
        name = raw.strip("`").strip()
        # Drop ONLY bare English words and Python keywords. A first version also
        # dropped anything without punctuation or digits, and took `{budget}` and
        # `{streams}` with it -- the two placeholder names `settle` had just added
        # to close the one gap the clues arm could not recover. Enforcing a common
        # word like `stdout` is free, because it is always said anyway; failing to
        # enforce a real anchor is not.
        if name.isalpha() and name.lower() in _NOT_A_NAME:
            continue
        out.append(raw)
    return out


def thread_problems(clue: dict, people: set[str] | None = None) -> list[str]:
    """Whatever makes an exchange unfit to write into the corpus.

    `people` is every name the corpus already knows -- `corpus.people()`, which is
    wider than `corpus.cast` because petar, theo and otto really are in there, just
    rarely. A speaker outside it is somebody this company has never employed.

    That check is here because nothing had it and it shipped. g1's plant invented
    nine of them -- wes, lena, rhea, ines, marek, mira, petra, tomas, marta -- and
    `inject` wrote 37 messages from them into the world, where each has exactly
    four messages, all inside planted threads, and no history anywhere in the other
    9,591. An agent who wonders who `rhea` is finds nobody. g2's first reknit
    invented thirteen.

    The prompt already names who was posting in that room that week and the model
    adds more anyway, which is the usual result of asking a prompt to enforce
    something.
    """
    out = []
    msgs = turns_of(clue)
    if people:
        for msg in msgs:
            speaker = who(msg)
            if not speaker:
                out.append("a turn with no author")
            elif speaker not in people:
                out.append(f"{speaker!r} is not in this company — invented speaker")
    # The holder has to be in their own conversation. `clue_thread.md` asks for it
    # in as many words -- "{holder} is in it, and is the one who settles the point"
    # -- and nothing enforced it, so four of g2's exchanges settled a point in the
    # absence of the person the plant records as settling it. Everything
    # downstream reads `holder`: the answer key attributes the remark to them, and
    # `room_of` picks the room from where THEY post.
    holder = (clue.get("holder") or "").strip()
    voices = {who(m) for m in msgs if who(m)}
    if msgs and holder and holder not in voices:
        out.append(f"{holder} holds this remark but never speaks in the exchange")
    # Two speakers minimum. `clue_thread.md` asks for it in those words -- "Two
    # speakers minimum, and no one turn may contain the whole of it" -- because a
    # person talking to themselves is not a conversation somebody had, and the
    # fragmenting that hides the remark needs someone to fragment it ACROSS.
    # Ungated, it produced a six-message mail thread in which dario emails himself
    # six times; `write_mail` then had nobody to address it to, returned no
    # Message-ID, and the read-back reported "6 of 6 turns not in the corpus" --
    # three layers away from the sentence that caused it.
    if len(msgs) > 1 and len(voices) < 2:
        only = next(iter(voices), "nobody")
        out.append(f"only {only} speaks — a monologue, not an exchange")
    for row in clue.get("double_booked") or []:
        out.append(row)
    # Hedging the SUBSTANCE, anywhere in the exchange. This lived only in
    # `voice_problems`, which `finish` computes and `reknit` does not consult -- so
    # reknit would write "the shape isn't settled", the gate would report it after
    # the fact, and fixing it meant a hand-typed `--only`. Here it drives the retry
    # reknit already has. Hedging the SCHEDULE is fine and stays fine; this is the
    # kind that says there is no decision to recover.
    if clue.get("covers"):
        for msg in msgs:
            if (hit := UNSETTLED.search(said(msg))):
                out.append(f"{who(msg)} leaves the decision open "
                           f"({hit.group(0)!r}) — not built yet is right, "
                           "not decided means there is nothing to recover")
    # Fragmenting is a CHAT rule, and only a chat rule. A page comment is one
    # person writing a whole thought down and somebody replying; a mail is a letter
    # and an answer. Two turns is the shape `clue_doc_thread.md` and
    # `clue_mail_thread.md` ASK for, and holding them to the chat minimum reported
    # seven correctly-shaped document exchanges as broken and had `reknit` rewrite
    # them for nothing — 36 exchanges written for 31 remarks.
    kind = str((clue.get("invented") or {}).get("kind")
               or (clue.get("carrier") or {}).get("kind") or "")
    chat = not (kind.startswith("mail") or kind.startswith("doc"))
    floor = 3 if chat else 2
    if len(msgs) < floor:
        out.append(f"{len(msgs)} message(s) — a remark alone in a room is not a "
                   "conversation somebody had")
    # The inverse of the old guard, and the point of the rewrite. A turn holding
    # the whole remark is somebody reading out a requirement -- in a chat room.
    # In a comment or a letter it is just somebody making their point, which is
    # what people do there, so this does not apply outside chat.
    if chat:
        whole = re.sub(r"\s+", " ", clue.get("text") or "").strip()
        for m in msgs:
            if whole and whole in re.sub(r"\s+", " ", said(m)):
                out.append(f"{who(m)} says the whole remark "
                           "in one turn — nothing is left for the rest of the exchange")
    for name in identifiers_missing(clue):
        out.append(f"nobody types `{name}`")
    for m in msgs:
        if not MINUTE.match(str(m.get("minute") or "")):
            out.append(f"minute {m.get('minute')!r} is not HH:MM")
        if not said(m).strip():
            out.append(f"an empty message from {who(m)}")
    # `forbidden_terms` says what this remark must LEAVE FOR A SIBLING, and until
    # now it was checked only against `clue["text"]` -- the one string that cannot
    # contain them, since `split` wrote it that way. The conversation reknit
    # invents around the remark, which is where the risk actually lives, was
    # checked against nothing.
    #
    # `l-kept-nils` forbids 'tail', 'both ends', 'head+tail'. Its job was "a
    # head-only cut loses what people came for", full stop -- the RATIO belongs to
    # konrad's remark the next day. reknit wrote "so the cut takes from both ends:
    # first 16k, last 48k", which is a forbidden phrase carrying an invented ratio,
    # and the inverse of the true one. An agent read it, believed it, and shipped
    # `head_budget = max_bytes // 4`.
    # Multi-word phrases only. Measured: the whole list flags 29 of 46 clues,
    # because `split` writes single common words into it -- 'head', 'tail', 'cap',
    # 'only', 'until'. A conversation about capping output cannot avoid the word
    # "head", and a gate that says it must is a gate nobody can satisfy. Restricted
    # to phrases, the same check flags 3, one of which is this bug.
    for term in clue.get("forbidden_terms") or []:
        if not term or " " not in term.strip():
            continue
        for m in msgs:
            if term.lower() in said(m).lower():
                out.append(f"{who(m)} says {term!r}, which this remark is supposed "
                           "to leave for a sibling — reknit is filling in the "
                           "neighbouring fact rather than writing around the gap")
                break
    # NOT a check on invented numbers, though that was the obvious next move and
    # it was written and measured before being deleted. `r1.rule`'s requirement
    # contains 3, 4, 8, 64, 48, 29 and 16; the invention that cost the fact was
    # "first 16k, last 48k" -- two of the requirement's OWN numbers, in each
    # other's roles. No arithmetic on the digits separates that from a correct
    # remark, because nothing about it is numerically wrong. It is wrong about
    # which end gets which, and only something that reads the sentence can tell.
    # `fact_consistency()` is that something.
    for part in clue.get("uncarried") or []:
        out.append(f"nothing in the exchange carries: {part}")
    return out



# Two kinds of hedge, and only one is a defect.
#
# Hedging the SCHEDULE is not merely allowed, it is the truth of this corpus: the
# feature genuinely has not been written, because writing it is the task the agent
# is given. "somebody will pick it up", "not this sprint", "when we get to it" all
# say the right thing about the world.
#
# Hedging the SUBSTANCE says there is no decision here to recover. That is what
# broke the sidecar: with the entire corpus in front of it and nothing to search
# for, a model failed to write `batch_plan.json` on two builds in three, because
# the exchanges that settle it end "the shape isn't settled" and "don't write
# anything against it yet".
#
# The stock-phrase check below catches a schedule hedge that has become a tic.
# This one catches only the kind that destroys information.
UNSETTLED = re.compile(
    r"\b(isn'?t settled|not settled|nothing settled|still moving|still in flux|"
    r"don'?t write anything|nothing firm|nobody'?s decided|no decision|"
    r"up in the air|still arguing|tbd)\b", re.I)


# Somebody reporting the work as ALREADY DONE. `clue_thread.md` forbids this
# already -- "Nobody reports having finished it" -- and nothing enforced it.
#
# It is not the same failure as UNSETTLED and it is worse in a specific way. An
# unsettled remark says there is no decision to find; a finished one says the
# code is already there, so an agent greps for the identifier, does not find it,
# and concludes the corpus is stale. g1's page-7 comment said the planner module
# "already has the name pinned PLAN_FILE_NAME" about a module the ticket asks the
# agent to CREATE.
#
# THE TENSE ALONE IS NOT THE DEFECT, and a first version of this that matched on
# it flagged ten exchanges of which nine were fine: "the sizer already had the
# answer on tuesday night" (a past run), "the directory is already there, the
# sizing pass mkdirs up front" (a directory that does exist), "the same numbers we
# already write into metadata_0.json" (files that do exist). Engineers talk about
# what exists constantly, and most of what exists really does.
#
# What makes it a defect is claiming a GRADED IDENTIFIER already exists -- a name
# the suite requires the agent to create. So the match below is only half the
# test; `voice_problems` also requires one of the clue's `verbatim` names in the
# same message.
FINISHED = re.compile(
    r"\b(already (has|have|had|got|pinned|landed|shipped|does|did)|"
    r"it'?s (written|in there|done)|its (written|in there|done)|"
    r"is already (there|in)|we already)\b", re.I)


def voice_problems(entry: dict) -> list[str]:
    """Remarks whose wording destroys the information they were planted to carry.

    Two classes, and the line between them and ordinary engineer-speak is the
    whole point -- get it wrong in either direction and the corpus stops being
    worth reading.

    NOT a defect, and deliberately not detected here: DEFERRAL. "that's its own
    ticket", "when we get to it", "rides along with the restart work". Real teams
    settle a design and then do not get to it, which is precisely why there is a
    ticket now, and stripping it would buy a higher world score by making the
    world less real. g1's world runs did decline `r1` on those grounds -- three
    rollouts out of three, quotably -- but the fix for that is in the
    INSTRUCTION, which now says carrying out a parked decision is part of the
    job. The corpus was right.

    A defect: saying the decision is not made (`UNSETTLED`), and saying the work
    is already finished (`FINISHED`).

    Scanned over the WHOLE exchange, not the tail. The hedge that cost g1 three
    rollouts sat at position 5 of 7, and `stock_phrasing` -- which only ever read
    `msgs[-2:]` -- never saw it.

    Herrings and reversals are exempt via `covers`, as they were before: a herring
    is a decision the team really made and later overturned, so it is SUPPOSED to
    be contradicted by something later.
    """
    out = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            if not clue.get("covers"):
                continue
            for msg in turns_of(clue):
                if (hit := UNSETTLED.search(said(msg))):
                    out.append(
                        f"{clue['clue_id']}: {who(msg)} leaves the decision "
                        f"open — {hit.group(0)!r}. Saying it is not built yet is "
                        "right; saying it is not decided means there is nothing "
                        "here to recover")
    return out


def finished_claims(entry: dict) -> list[str]:
    """Remarks that may describe a graded identifier as already built. ADVISORY.

    Reported and not gated, because it was measured and does not survive as a
    gate. Matching the tense alone flagged ten exchanges on g1, nine of them fine.
    Adding "and a graded name appears in the same message" cut it to seven, still
    five of them fine -- because in every false positive the phrase has its own
    object and the graded name is merely nearby:

        "the directory itself is already there, the sizing pass mkdirs up front"
        "the same numbers we already write into metadata_0.json"
        "the way its written now it makes a tmp dir, runs the writer, asserts
         plan_format_version comes out 2"

    Deciding which noun "already" attaches to is a parse, not a regex, and a gate
    that cries wolf five times in seven is a gate people learn to skip. So this
    prints and `voice_problems` fails. The one true positive it found is worth
    the noise:

        g1.r1.l2 -- "its in the planner module, PLAN_FILE_NAME = "batch_plan.json"
        ... its written and thats it"

    about a module the ticket asks the agent to CREATE. An agent greps for it,
    does not find it, and reads the corpus as stale.
    """
    out = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            if not clue.get("covers"):
                continue
            for msg in turns_of(clue):
                text = said(msg)
                hit = FINISHED.search(text)
                named = [v for v in (clue.get("verbatim") or [])
                         if v.strip("`").lower() in text.lower()]
                if hit and named:
                    out.append(
                        f"{clue['clue_id']}: {who(msg)} may be reporting "
                        f"{named[0]} as already built — {hit.group(0)!r}. Read it: "
                        "if the claim really is about that name, the agent will "
                        "grep for it, miss it, and distrust the corpus")
    return out


def stock_phrasing(entry: dict) -> list[str]:
    """Closing wording that repeats across exchanges — a tell only at corpus scale.

    `clue_thread.md` once offered "we can do that when we get to it" as an example
    of how an exchange might close; the model used it as a template and
    **twenty-two of fifty threads ended with that exact phrase**. Fifty
    conversations ending the same way is a louder tell than anything the version
    before it had.

    Tail-scoped on purpose, unlike `voice_problems`: this check is about where a
    phrase sits, not whether it appears.
    """
    out = []
    closers = collections.defaultdict(list)
    for req in entry["requirements"]:
        for clue in req["clues"]:
            msgs = turns_of(clue)
            if not msgs:
                continue
            tail = " ".join(said(m) for m in msgs[-2:])
            words = re.findall(r"[a-z']+", tail.lower())
            for i in range(len(words) - 3):
                closers[" ".join(words[i:i + 4])].append(clue["clue_id"])
    # Topic vocabulary repeats and that is not a tell: fifty exchanges about auto
    # sizing will all say "the auto sizing branch", and it appears nowhere in the
    # real corpus only because the real corpus never discusses this feature.
    # A CLOSING TIC is different -- it shows up at the end and nowhere else. So a
    # phrase is only suspicious if it is concentrated in closings.
    #
    # Calibrated against the corpus rather than guessed: fifty real conversations
    # share 1.3 four-grams across their last two messages on average, up to 5, so
    # a handful is normal and the threshold is three.
    body = collections.Counter()
    for req in entry["requirements"]:
        for clue in req["clues"]:
            msgs = turns_of(clue)
            words = re.findall(r"[a-z']+", " ".join(said(m) for m in msgs[:-2]).lower())
            for i in range(len(words) - 3):
                body[" ".join(words[i:i + 4])] += 1
    for phrase, ids in sorted(closers.items()):
        seen = set(ids)
        if len(seen) >= 3 and body[phrase] <= 1:
            out.append(f"{len(seen)} exchanges END with words used nowhere else: "
                       f"{phrase!r} ({', '.join(sorted(seen)[:4])}…)")
    return out


def unknit(entry: dict, people: set[str] | None = None) -> list[str]:
    """Every exchange that cannot be written into the world as it is."""
    out = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            if not turns_of(clue):
                continue
            for problem in thread_problems(clue, people):
                out.append(f"{clue['clue_id']}: {problem}")
    return out


def render_thread(inv: dict) -> str:
    return "\n".join(
        f"  {m.get('minute') or '--:--'}  {who(m)}: "
        + said(m).replace("\n", "\n           ")
        for m in inv.get("messages") or [])


def too_wordy(entry: dict, corpus: Corpus, limit: float = 5.0) -> list[str]:
    """Exchanges that INFLATE the remark rather than spread it.

    The obvious reading of "planted turns are too long" is that reknit fails to
    fragment. It is the opposite. Remarks are already short -- median 157
    characters, near the corpus median of 89 -- and the exchanges built from them
    run 8.9x that, a 146-character remark becoming 1,288 characters over seven
    turns. Pure fragmentation would give ~26 characters a turn, which is too
    short; the conversation legitimately needs somebody to ask and somebody to
    push back. Nine times is not scaffolding, it is padding, and it is what makes
    every planted turn a paragraph in a corpus of one-liners.

    So the measure is the ratio, not the length: it scales with the remark instead
    of punishing a long one, and it names the thing to change. Roughly 3x gets
    turns near the corpus median at six turns, so 5x is the complaint threshold.

    g1 sits at 8.4x and shipped -- blind 0.00, clues 0.86 -- so this is a realism
    defect and not a solvability one. Reported, never gated.
    """
    out = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            turns = turns_of(clue)
            source = len(clue.get("text") or "")
            if not turns or not source:
                continue
            ratio = sum(len(said(m)) for m in turns) / source
            if ratio > limit:
                out.append(f"{clue['clue_id']}: the exchange is {ratio:.1f}x the "
                           f"remark ({source} chars over {len(turns)} turns) — "
                           "inflated rather than spread")
    return out


# A number written as code or prose: `cap/2`, `max_bytes // 2`, `three parts`,
# `65536`, `3/4`. Enough to notice two exchanges pinning the same quantity
# differently, which is the only thing this is for.
# A split expressed as a RULE for the cap, not the word for a fraction. The first
# version matched bare "half" and "quarter" and returned eight hits, of which the
# ones it found were "half a character", "half the setup cells", "the last line
# half eaten" -- prose about halves, pinning nothing. Same mistake as the first
# `finished_claims`, measured the same way and narrowed the same way: the phrase
# has to bind a number TO the budget.
_QUANTITY = re.compile(
    r"\b(?:cap|max_bytes|budget)\s*(?://|/)\s*\d+"                 # cap/2
    r"|\b\d+\s*/\s*\d+\s+(?:split|of the (?:cap|budget))"          # 50/50 split
    r"|\b(?:even|equal)\s+split\b"                                  # even split
    r"|\b(?:three|two|1|2|3)\s+(?:parts?|quarters?)\s+(?:of\s+)?"
    r"(?:the\s+)?(?:cap|budget)"                                     # three parts of the cap
    r"|\b(?:three\s+quarters|a\s+quarter|half)\s+of\s+the\s+(?:cap|budget)",
    re.I)


def fact_consistency(task: Task, entry: dict, *, budget: float = 1.0) -> list[str]:
    """Per fact: does anything in the corpus state it wrongly and get away with it?

    The gate the pattern-matching one could not be. `contradictions()` looks for
    phrases that bind a number to the cap, and it does catch "cap/2" -- but the
    invention that actually cost g2 a fact was "first 16k, last 48k" against a
    requirement holding 16, 48, 64, 29, 3 and 4. Two of its own numbers with their
    roles swapped. Nothing about it is numerically wrong, so no arithmetic on the
    digits separates it from a correct remark. Only a reader of the sentence can.

    The rule this enforces, and it is not the judge's to bend: a wrong statement
    is FINE if a later remark plainly overturns it -- names the old decision, says
    it is gone -- and fine if the corpus settles the right answer after it. What
    is not fine is a wrong statement that is the LAST WORD. Recency is the
    tiebreaker a reader reaches for, and one rollout said so in as many words: "I
    took the most recent". g2's `cap/2` line was the final message in the whole
    plant, stated as settled background, inside a thread about something else, so
    nothing challenged it and nothing could.

    The judge returns conflicts and the reversal it found for each; the verdict is
    arithmetic here, over dates. A judge asked "is this fair" answers about the
    corpus it has just read whole, not about the reader who meets it in order.
    """
    out: list[str] = []
    for req in entry["requirements"]:
        requirement = req.get("requirement") or {}
        for fact, stated in requirement.items():
            rows = [c for c in req["clues"] if fact in (c.get("covers") or [])]
            if len(rows) < 2:
                continue                    # nothing to disagree with
            when = {c["clue_id"]: _clue_date(c) for c in rows}
            remarks = "\n\n".join(
                f"### {c['clue_id']} — {when[c['clue_id']] or 'undated'}\n"
                + (render_thread(c.get("invented") or {}) or c.get("text") or "")
                for c in sorted(rows, key=lambda c: when[c["clue_id"]] or ""))
            ask = prompt("clue_consistency.md", requirement=stated or "",
                         remarks=remarks)
            label = f"clue-consistency-{req['req_id']}.{fact}"
            result = agent.run(ask, repo=REPO, label=label, cwd=task.dir, tools="",
                               schema=cs.consistency_schema(), budget_usd=budget,
                               log_dir=task.dir / "logs")
            _record(task, label, ask, result)
            for row in (result.data or {}).get("conflicts") or []:
                cid = row.get("clue_id") or "?"
                rev = (row.get("reversed_by") or "").strip()
                if rev and (when.get(rev) or "") > (when.get(cid) or ""):
                    continue                # overturned later, which is the design
                latest = max((when.get(c["clue_id"]) or "") for c in rows)
                tail = ("and it is the LAST word on this fact"
                        if (when.get(cid) or "") >= latest
                        else "and nothing later overturns it")
                out.append(
                    f"{req['req_id']}.{fact}: {cid} says {row.get('quote','')!r} "
                    f"— {row.get('says','')} — {tail}")
    return out


def _clue_date(clue: dict) -> str:
    """The day a reader meets this remark, however it was placed."""
    inv = clue.get("invented") or {}
    return (inv.get("date") or (clue.get("carrier") or {}).get("date") or "")


def contradictions(entry: dict) -> list[str]:
    """Turns that pin a quantity a DIFFERENT remark already pinned differently.

    Every other check asks whether an exchange still CARRIES its remark. None
    asked whether it had invented a claim that defeats another one, and that is
    what cost g2 four of its nine facts in a single line.

    `g2.r1.l-bytes-emil` is a remark about UTF-8 boundary trimming. Dressing it up,
    `reknit` had emil say "we take the tail as the last cap/2 bytes" -- a ratio
    that appears nowhere in any remark, in an exchange with no business stating
    one, dated nine months after the two remarks that say three-to-one. The world
    agent found both, saw nothing retracting the later one, wrote "I took the most
    recent" in its PR, split 50/50, and lost `r1.rule` plus the three facts whose
    tests assert exact capped strings.

    It behaved correctly. The corpus lied to it.

    Reported rather than gated: this is a regex over prose, and the same measure
    that made `finished_claims` advisory applies. What it buys is that the line
    shows up in an audit instead of in a failed rollout three hours later.
    """
    seen: dict[str, list[tuple[str, str]]] = {}
    for req in entry["requirements"]:
        for clue in req["clues"]:
            for msg in turns_of(clue):
                for hit in _QUANTITY.finditer(said(msg)):
                    word = hit.group(0).lower().strip()
                    seen.setdefault(req["req_id"], []).append((word, clue["clue_id"]))
    # ACROSS exchanges, never within one. A single conversation weighing "even
    # split or weighted then" before settling on "three parts of the cap" is a
    # decision being taken, which is the whole point; flagging that would reject
    # the one exchange doing its job properly. Two different exchanges each
    # asserting a different answer is the defect.
    out = []
    for rid, rows in seen.items():
        by_clue: dict[str, list[str]] = {}
        for word, cid in rows:
            by_clue.setdefault(cid, []).append(word)
        # An exchange's answer is its LAST word on the matter, not every option it
        # weighed: `l-kept-konrad` raises "even split", then "cap/2", and settles
        # on "three parts of the cap". Taking the set would exclude it for being
        # undecided, and the one exchange doing its job properly would be the one
        # this check ignored.
        settled = {cid: words[-1] for cid, words in by_clue.items()}
        answers = set(settled.values())
        if len(answers) > 1:
            where = ", ".join(f"{w} ({c})" for c, w in sorted(settled.items()))
            out.append(f"{rid}: two exchanges give different answers — {where}. "
                       "One is invented scaffolding, and a reader who takes the "
                       "most recent will follow the wrong one")
    return out


def unclash(entry: dict, corpus: Corpus) -> list[str]:
    """Nudge a turn off a minute its speaker already occupies elsewhere.

    Deterministic, because asking was tried and does not work. `room_of` shows the
    writer exactly where each person already is that day, and sixteen freshly
    written exchanges still landed on an occupied minute -- which is unsurprising,
    since it is arithmetic across twenty timestamps while also writing dialogue.

    Moving the clock changes nothing a reader cares about: not who spoke, not what
    they said, not the order. So it is done here rather than sent back for a
    rewrite that costs a call and re-rolls everything else in the exchange.

    Only forward, and only within the same hour, so a turn cannot overtake the one
    after it or drift into the evening.
    """
    busy: dict[tuple[str, str], set[str]] = {}
    for m in corpus.messages:
        busy.setdefault((m.author, m.date), set()).add(m.created_at[11:16])
    moved = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            date = (clue.get("carrier") or {}).get("date")
            if not date:
                continue
            for msg in turns_of(clue):
                speaker, when = who(msg), str(msg.get("minute") or "")
                if not speaker or ":" not in when or when not in busy.get((speaker, date), ()):
                    continue
                hh, mm = when.split(":")
                for step in range(1, 6):
                    nudged = f"{hh}:{int(mm) + step:02d}"
                    if int(mm) + step < 60 and nudged not in busy.get((speaker, date), ()):
                        msg["minute"] = nudged
                        moved.append(f"{clue['clue_id']}: {speaker} {when} -> {nudged}")
                        break
    return moved


def double_booked(entry: dict, corpus: Corpus, window: int = 0) -> list[str]:
    """A planted turn from somebody who is really posting elsewhere that minute.

    The only availability question worth asking. Who happened to be at their desk
    on a given Tuesday does not decide whether a conversation is plausible --
    knowing the subject does -- so `room_of` offers the whole company and lets the
    topic choose. But a person cannot be in two rooms at once, and an agent who
    notices dario answering in #pipeline at 14:07 while the corpus already has him
    in #releases at 14:06 has found the plant.

    `window` is minutes either side, and it is 0: only the same displayed minute
    counts. Measured before choosing -- of 22 findings at a four-minute window,
    exactly 2 were the same minute and the other 20 were one to four minutes
    apart, which is somebody with two tabs open and is what the corpus itself
    looks like. A four-minute window would have sent sixteen freshly written
    exchanges back for rewriting to fix two real collisions.
    """
    def minutes(stamp: str) -> int | None:
        try:
            hh, mm = stamp.split(":")
            return int(hh) * 60 + int(mm)
        except Exception:
            return None

    real: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for m in corpus.messages:
        when = minutes(m.created_at[11:16])
        if when is not None:
            real.setdefault((m.author, m.date), []).append((when, m.channel))

    out = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            car = clue.get("carrier") or {}
            date, here = car.get("date"), (car.get("channel") or "").lstrip("#")
            if not date or not here:
                continue
            for msg in turns_of(clue):
                speaker = who(msg)
                when = minutes(str(msg.get("minute") or ""))
                if not speaker or when is None:
                    continue
                for other, room in real.get((speaker, date), ()):
                    if room != here and abs(other - when) <= window:
                        out.append(
                            f"{clue['clue_id']}: {speaker} speaks in #{here} at "
                            f"{msg.get('minute')} on {date}, but the corpus has them "
                            f"in #{room} {abs(other - when)} minute(s) away")
                        break
    return out


def room_of(corpus: Corpus, clue: dict) -> tuple[str, str, list, str]:
    """The channel, the day, the real traffic in it, and who was actually there."""
    car = clue["carrier"]
    channel = (car.get("channel") or "engineering").lstrip("#")
    date = car.get("date") or ""
    real = corpus.by_channel_day.get((channel, date)) or []
    # People who actually spoke in that room that week, holder first. A remark
    # attributed to somebody who was not there is the cheapest tell there is.
    # Everybody who works here, holder first, then the people this room hears
    # from most. Deliberately NOT "who posted that week": that produced rooms
    # containing one person, and asking for two speakers from a list of one got
    # invented colleagues and, once, `TODO_second_speaker` as an author name.
    #
    # Availability is not modelled on purpose. Whether somebody happened to be
    # typing that Tuesday is not what makes a conversation plausible -- knowing
    # the subject is. The prompt asks for people the topic would actually reach,
    # and `double_booked` catches the one thing that IS absurd: being in two
    # rooms at the same minute.
    regulars = [a for a, _ in collections.Counter(
        m.author for m in corpus.messages if m.channel == channel).most_common()]
    loudest = [a for a, _ in collections.Counter(
        m.author for m in corpus.messages).most_common()]
    others = [m.author for m in real] + regulars + loudest
    people = list(dict.fromkeys([clue["holder"]] + others))[:8]
    nearby = ("## What else is in that channel that day\n\n" + "\n".join(
        f"  {m.created_at[11:16]}  {m.author}: {m.text[:110]}" for m in real[:14])
        if real else "")
    # Where these people already are that day, so the exchange can be put in a gap
    # instead of on top of them. Nobody is in two rooms at the same minute, and an
    # agent who spots dario answering in #pipeline at 14:07 while the corpus has
    # him in #releases at 14:06 has found the plant. Availability is otherwise not
    # modelled -- the topic decides who speaks, not the calendar.
    elsewhere = sorted({
        (m.created_at[11:16], m.author, m.channel) for m in corpus.messages
        if m.date == date and m.channel != channel and m.author in set(people)})
    if elsewhere:
        nearby += ("\n\n## Where these people already are that day\n\n"
                   "Do not put a turn within a few minutes of one of these — the "
                   "same person cannot be in two rooms at once.\n\n" + "\n".join(
                       f"  {when}  {who} is in #{room}" for when, who, room in elsewhere[:20]))
    return channel, date, people, nearby


def used_closers(entry: dict, exclude: str, limit: int = 14) -> str:
    """How the other exchanges already ended, so this one does not end that way.

    Banning one phrase in the prompt moved the problem rather than fixing it: the
    first version offered "we can do that when we get to it" as an example and got
    it back in 22 of 50, and removing it produced a FAMILY of schedule-handoff
    closers instead -- "stick it on the", "whoever picks up the", "best we can do".
    A model writing fifty conversations about one subject converges on an ending
    unless it is shown the endings already taken.
    """
    seen = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            if clue["clue_id"] == exclude:
                continue
            msgs = turns_of(clue)
            if msgs:
                seen.append(" ".join(said(m) for m in msgs[-1:]).strip()[:90])
    if not seen:
        return ""
    return ("**These are how other conversations in this corpus already end. Do "
            "not end like any of them, and do not reach for the same move — a "
            "different way of handing the work to somebody later is still the "
            "same ending.**\n\n"
            + "\n".join(f"- …{t}" for t in seen[:limit]))


def stage_thread(task: Task, corpus: Corpus, clue: dict, entry: dict,
                 budget: float, defect: list[str] | None = None) -> dict:
    """Write the exchange in which this decision got taken.

    `defect` is what `thread_problems()` said about the last attempt. Reknit used
    to retry by calling this again with identical arguments and printing the
    finding, so the second attempt was a re-roll: the same prompt, a different
    sample, and no reason for it to come out better. `stage_tree` has fed its own
    gate's finding back since the names re-ask was written; this is the same move
    one function over, on the stage that costs nine dollars rather than one.
    """
    kind = str((clue.get("invented") or {}).get("kind")
               or clue["carrier"].get("kind") or "")
    mail, doc = kind.startswith("mail"), kind.startswith("doc")
    channel, date, people, nearby = room_of(corpus, clue)
    if doc:
        # The page it hangs off, so the exchange reads as people arguing in the
        # margin of that document rather than in a channel.
        rel = (clue["carrier"].get("key") or "|").split("|")[1]
        page = next((pg for pg in corpus.pages if pg.path == rel), None)
        channel = f"the comments under {rel}"
        nearby = ("## The page they are commenting on\n\n"
                  + (page.body[:1200] if page else "(not found)"))

    reversal = ""
    if clue.get("kind") == "reversal":
        was = next((c for req in entry["requirements"] for c in req["clues"]
                    if c["clue_id"] == clue.get("reverses")), None)
        if was:
            reversal = (
                "## It overturns something\n\n"
                "The team had settled on this, and is dropping it:\n\n"
                f"> {was['text']}\n\n"
                "Somebody names the old thing in its own nouns, says plainly that it "
                "is gone and what broke, and says what replaces it. Recalling the old "
                "decision out loud is what makes the change legible to a reader who "
                "saw it agreed months ago — do not skip it, and do not narrate it as "
                "bookkeeping.")

    # One prompt per register. `clue_thread.md` says "Write the conversation",
    # "two speakers minimum", "do not put that in one message" -- correct for a
    # chat room and wrong everywhere else. Run over a mail carrier it turned a
    # letter into chat turns; run over a page comment it produced g1's `r2.l9`,
    # a wiki comment that opens "Look, the working dir today holds more than
    # those two:". Placement already writes each kind in its own voice
    # (`clue_conversation.md` / `clue_mail.md` / `clue_document.md`); reknit was
    # the one stage that flattened them all back to chat.
    register = ("clue_mail_thread.md" if mail else
                "clue_doc_thread.md" if doc else "clue_thread.md")
    told = ""
    if defect:
        told = ("## What your last attempt at this exchange got wrong\n\n"
                + "\n".join(f"- {d}" for d in defect)
                + "\n\nWrite it again, fixing exactly those and keeping whatever "
                  "else worked. Every rule above still holds — a fix that breaks "
                  "one of them is not a fix.")
    text = prompt(register, text=clue["text"], holder=clue["holder"],
                  channel=channel, date=date, reversal=reversal, defect=told,
                  verbatim=("**These names must be typed literally, somewhere in the "
                            "exchange:** " + ", ".join(f"`{v}`" for v in clue["verbatim"])
                            if clue.get("verbatim") else ""),
                  people=", ".join(people), nearby=nearby,
                  # What this remark must LEAVE FOR A SIBLING. Computed by the
                  # tree stage, stored on every clue, and until now read by
                  # nothing but a check against `clue["text"]` -- the one string
                  # that cannot contain them. The conversation invented around
                  # the remark, which is where the risk lives, was never shown
                  # them at all.
                  leave=("**These belong to other people's remarks. Do not put "
                         "them in anybody's mouth here:** "
                         + ", ".join(f"`{x}`" for x in clue["forbidden_terms"])
                         if clue.get("forbidden_terms") else ""),
                  avoid=used_closers(entry, clue["clue_id"]),
                  voices="\n\n".join(
                      f"**{p}**\n{describe_voice(corpus.voice(p), written=mail)}"
                      for p in people[:4]))
    tag = "mail" if mail else "doc" if doc else "thread"
    result = agent.run(text, repo=REPO, label=f"clue-{tag}-{clue['clue_id']}",
                       cwd=task.dir, tools="", schema=cs.THREAD, budget_usd=budget,
                       log_dir=task.dir / "logs")
    _record(task, f"clue-{tag}-{clue['clue_id']}", text, result)
    msgs = (result.data or {}).get("messages") or []
    if not msgs:
        return clue.get("invented") or {}

    # The real messages from that day are in the prompt as context, and three
    # threads once came back with a dozen of them copied into the thread itself.
    already = {m.text.strip() for m in
               (corpus.by_channel_day.get((channel, date)) or [])}
    msgs = [m for m in msgs if (m.get("text") or "").strip() not in already]

    out = {"channel": channel, "date": date, "messages": msgs,
           "pieces": (result.data or {}).get("pieces") or []}
    if doc:
        out["kind"] = "doc_comment"
    if mail:
        out["kind"] = "mail_new"
        out["subject"] = (clue.get("invented") or {}).get("subject") or ""
        out["participants"] = people
    if clue["carrier"].get("kind") == "chat_insert":
        # Where the exchange joins the day that already happened.
        out["seed_after"] = clue["carrier"].get("insert_after") or ""
    return out


def check_carriage(task: Task, clue: dict, budget: float) -> list[str]:
    """Claim by claim: is every part of the remark somewhere in the exchange?

    Shown the remark and the finished thread, and NOT the writer's own `pieces`.
    A model handed its own account of where it put things confirms that account.
    """
    # The prompt spends most of its length saying what is NOT a claim. Its first
    # version decomposed the remark into pragmatics as well as facts and marked
    # five exchanges short for things like "the pinning is already done (past
    # tense)" and "the seeding and the run are a single completed act by the
    # speaker" -- properties of one person's sentence that an exchange between
    # four people cannot have, and in the tense case one the new contract removes
    # on purpose. All five carried every fact. A judge asked "is it all there"
    # will find a difference if a difference exists, so it has to be told which
    # differences are the point.
    ask = prompt("clue_carriage.md", text=clue["text"],
                 thread=render_thread(clue.get("invented") or {}))
    result = agent.run(ask, repo=REPO, label=f"clue-carry-{clue['clue_id']}",
                       cwd=task.dir, tools="", schema=cs.carriage_schema(),
                       budget_usd=budget, log_dir=task.dir / "logs")
    _record(task, f"clue-carry-{clue['clue_id']}", ask, result)
    # Computed here, never asked for. A judge that returns both the parts and an
    # overall verdict answers the two about different texts.
    return [row["part"] for row in (result.data or {}).get("parts") or []
            if not row.get("present")]


def reknit(slug: str, *, run: str | None = None, budget: float = 3.0,
           only: list[str] | None = None, redo: bool = False) -> dict:
    """Give every remark the conversation it would really have been made in."""
    task = load(slug)
    corpus = Corpus(pathlib.Path(run) if run else None)
    plant = task.dir / "clues" / "plant.json"
    ledger = resume(task, "reknit_at")
    entry = ledger["tasks"][0]
    # Everyone this company has ever employed, so an invented speaker is
    # caught before it is written into the world rather than after.
    cast = set(corpus.people())

    todo = []
    for req in entry["requirements"]:
        for clue in req["clues"]:
            if not clue.get("carrier"):
                continue
            # A page comment gets the same treatment for the same reason, and one
            # extra: BookStack does not index comments, so a lone one is the least
            # findable thing in the world. A short thread under the page at least
            # rewards anybody who opens it.
            if only and clue["clue_id"] not in only:
                continue
            # A `doc_edit` is prose in somebody's own page, not a conversation.
            # Reknitting one produces chat turns, and `write_doc_edit` then has to
            # flatten them back into paragraphs -- a page that reads like a Slack
            # thread is a tell, and the round trip loses whatever sections the
            # document stage wrote. The other wiki kind, `doc_comment`, DOES get
            # an exchange, and for one extra reason: BookStack does not index
            # comments, so a lone one is the least findable thing in the world,
            # and a short thread under the page at least rewards anybody who
            # opens it.
            if (clue.get("carrier") or {}).get("kind") == "doc_edit":
                continue
            if redo or thread_problems(clue, cast) or not turns_of(clue):
                todo.append(clue)
    if not todo:
        print("  every remark already sits in an exchange that carries it")
        return finish(task, corpus, ledger, "reknit_at")

    print(f"  {len(todo)} exchange(s) to write\n")
    failed = []
    for clue in todo:
        # What the last attempt got wrong, handed to the next one. Empty on the
        # first pass; `thread_problems()`' own rows after that.
        told: list[str] = []
        # Attempt 1's exchange, kept so a worse attempt 2 can be discarded rather
        # than shipped. `stage_tree` guards its re-ask the same way: "a second
        # attempt that fixes the names and loses something else cannot make
        # things worse" -- and a directed retry makes that more likely, not less,
        # because it is now aiming at one finding instead of resampling.
        best: tuple[int, dict, list[str]] | None = None
        for attempt in (1, 2):
            # One bad call must not cost the rest of the pass. A single
            # `reasoning_extraction` error took this loop down 36 exchanges into
            # 46, and the ten it never reached -- the whole tail of r2 -- kept
            # their previous conversations while `finish` wrote the plant and
            # reported as though the pass had completed. The audit that followed
            # showed numbers that were partly from this run and partly from the
            # one before, which is worse than an obvious failure.
            try:
                # MERGE, not replace. `stage_thread` returns messages; the dict it
                # overwrites may also hold what `stage_document` or `stage_mail`
                # wrote -- a page title and body, a mail subject. Replacing it
                # wholesale threw those away, and the three `doc_new` remarks
                # became comments on wiki pages that existed nowhere: "unknown
                # document 'engineering/capping-code-executor-output.md'", from a
                # writer that had produced that page an hour earlier.
                written = stage_thread(task, corpus, clue, entry, budget,
                                       defect=told)
                clue["invented"] = {**(clue.get("invented") or {}), **written}
                clue["uncarried"] = check_carriage(task, clue, budget)
            except Exception as err:                      # noqa: BLE001
                if attempt == 2:
                    failed.append(f"{clue['clue_id']}: {type(err).__name__}: "
                                  f"{str(err)[:120]}")
                    break
                print(f"  ..  {clue['clue_id']:14} call failed, retrying — "
                      f"{type(err).__name__}")
                continue
            left = thread_problems(clue)
            if best is None or len(left) < best[0]:
                best = (len(left), dict(clue["invented"]), list(clue["uncarried"] or []))
            if not left or attempt == 2:
                break
            told = left
            print(f"  ..  {clue['clue_id']:14} retrying — {left[0][:70]}")
        # Attempt 2 was told what was wrong, so it usually wins; when it does not,
        # the exchange that was closest to right is the one that ships.
        if best is not None:
            clue["invented"] = best[1]
            clue["uncarried"] = best[2]
        left = thread_problems(clue)
        print(f"  {'ok ' if not left else 'FAIL'} {clue['clue_id']:14} "
              f"{clue['holder']:8} {len(turns_of(clue))} turns")
        for problem in left:
            print(f"       ! {problem}")
        # One exchange is ~30s of model time and this pass runs 45 of them, so it
        # outlives most things that can interrupt it. `finish()` is the only other
        # write.
        checkpoint(task, ledger, "reknit_at")

    adrift = unknit(entry, cast)
    print(f"\n{len(todo) - len(failed)} of {len(todo)} written, "
          f"{len(adrift)} finding(s)")
    for row in failed:
        print(f"  !! never written: {row}")
    if failed:
        print(f"  !! {len(failed)} exchange(s) still carry their PREVIOUS "
              f"conversation. Re-run: cli.py reknit {slug} --only "
              f"{','.join(r.split(':')[0] for r in failed)} --redo")
    return finish(task, corpus, ledger, "reknit_at")


# ---------------------------------------------------------------------------
# chronology — a decision cannot precede the problem that caused it
# ---------------------------------------------------------------------------
# What a remark is DOING, read off the clause it settles. Two shapes: reporting
# that something is broken today, or recording what the team decided. The split is
# a regex over `settles` rather than a model call so the classification is
# inspectable and the same every run -- it is printed in the README beside each
# remark, so a wrong call is visible rather than buried.
SYMPTOM = re.compile(
    r"\b(currently|no record|leaves no|left me|gets? read back|misreport|"
    r"destroys?|blew up|still sitting|outlived|cannot|can't|lost|paid for|"
    r"is a problem|nothing (?:says|stopped|on disk)|had to)\b", re.I)


def stance(clue: dict) -> str:
    """`problem` if this remark reports today's behaviour, `decision` if it settles."""
    if clue.get("kind") == "herring":
        return "herring"
    text = (clue.get("settles") or "") + " " + (clue.get("text") or "")
    return "problem" if SYMPTOM.search(text) else "decision"


# Turning a statement back into a proposal. Not a list of hedge words -- "honestly",
# "look," and "i'd say" are this cast's voice, and stripping them would fight the
# personas rather than the vagueness. These are the openings that make a settled
# thing sound like it is still up for discussion.
PROPOSES = re.compile(
    r"\b(should we|shall we|can we|could we|do we want|are we going to|"
    r"any reason we|wondering if|i wonder|what if|would it be worth|"
    r"maybe we|might want|i'm not sure we|does anyone know)\b", re.I)


def hedged(text: str) -> bool:
    """Does this read as somebody asking rather than somebody saying?

    Used as a guard on the placement stage, which rewrites a remark to fit the room
    it lands in and was for a long time told to "stop at the observation". A sentence
    minted precisely because it states a decision could come back from that as one
    more person noticing something, and the identifier guard cannot see the
    difference.
    """
    return bool(text.strip().endswith("?") or PROPOSES.search(text))


def out_of_order(entry: dict) -> list[dict]:
    """Decisions dated before the first complaint their own step is answering.

    Placement chooses each slot on its own merits and never looks at the other
    remarks, so the plant came out with konrad naming `batch_plan.json` as settled
    house style on 9 April and gideon first complaining that nothing records the
    split on the 23rd. Each placement is defensible; together they are a decision
    that precedes its own motivation, which is the kind of thing a reader notices
    without being able to say why.
    """
    out = []
    for req in entry["requirements"]:
        by_sub: dict[str, list[dict]] = collections.defaultdict(list)
        for clue in req["clues"]:
            if clue.get("carrier") and clue.get("subconclusion"):
                by_sub[clue["subconclusion"]].append(clue)
        for sub, clues in by_sub.items():
            problems = [c for c in clues if stance(c) == "problem"]
            if not problems:
                continue                      # nothing to be out of order with
            first = min(c["carrier"]["date"] for c in problems)
            for clue in clues:
                if stance(clue) == "decision" and clue["carrier"]["date"] < first:
                    out.append({"clue_id": clue["clue_id"], "subconclusion": sub,
                                "dated": clue["carrier"]["date"], "not_before": first})
    return out


def reorder(slug: str, *, run: str | None = None, budget: float = 3.0) -> dict:
    """Re-place the remarks whose date contradicts the story, and only those."""
    task = load(slug)
    corpus = Corpus(pathlib.Path(run) if run else None)
    plant = task.dir / "clues" / "plant.json"
    ledger = resume(task, "reordered_at")
    entry = ledger["tasks"][0]
    violations = out_of_order(entry)
    if not violations:
        return {"ledger": ledger, "moved": [], "still_wrong": []}

    by_id = {c["clue_id"]: c for req in entry["requirements"] for c in req["clues"]}
    used, per_channel, per_page = occupancy(
        entry, {v["clue_id"] for v in violations})

    window_end = ledger["windows"]["clues"][1]
    moved = []
    for violation in violations:
        row = by_id[violation["clue_id"]]
        # The day after the complaint, at the earliest. Same remark, same person,
        # same source -- only the moment moves.
        window = (next_day(violation["not_before"]), window_end)
        leaf = {"id": row["clue_id"], "text": row["text"], "holder": row["holder"],
                "source": row["source"], "settles": row["settles"],
                "leaves_open": row["leaves_open"], "verbatim": row["verbatim"],
                "forbidden_terms": row["forbidden_terms"],
                "subconclusion": row["subconclusion"], "covers": row["covers"]}
        leaf = place_one(task, corpus, leaf, window, used, per_channel, budget, per_page)
        was = row["carrier"]["date"]
        row["carrier"], row["placement"] = leaf["slot"], leaf["placement"]
        row["invented"], row["text"] = leaf["invented"], leaf["adapted"] or row["text"]
        moved.append(f"{row['clue_id']} {was} -> "
                     f"{(leaf['slot'] or {}).get('date', 'nowhere')} "
                     f"(after {violation['not_before']}, {violation['subconclusion']})")

    return {"ledger": finish(task, corpus, ledger, "reordered_at"),
            "moved": moved, "still_wrong": out_of_order(entry)}


def next_day(date: str) -> str:
    return (dt.date.fromisoformat(date) + dt.timedelta(days=1)).isoformat()
