#!/usr/bin/env python3
"""Running the days, and proving what came out of them.

Split out of `phase4_simulate.py` for one reason: importing this imports
`bespoke_user`, and `bespoke_user` resolves authentication the moment it is
touched. Keeping it behind a function call means `resolve_auth` has already run
by the time anything here loads, which is the difference between the persona
turns going on the subscription and going on the API key.

Three things happen here. The days run. Every planted clue is checked against
what was actually said, and a channel-day that dropped one is run again — told
what it failed to convey, so the retry is a correction rather than the same
attempt with a different seed. Every clue then gets a file of its own showing
the line that carried it in the conversation around it, because "did it land"
is a boolean and whether it reads like a person said it is not.

What the gate asks is whether the INFORMATION arrived, not whether the words
did. A clue is a fact the corpus has to teach and the persona carrying it has
their own vocabulary, so the point is fixed and the phrasing is theirs. Two
things stay literal: an identifier, because a name paraphrased is a different
name, and phase 3's forbidden terms, because a persona free to reword is free
to reword straight into giving the requirement away.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl          # noqa: E402
import worldapps as wa        # noqa: E402
import phase4_render as render  # noqa: E402
from phase4_simulate import (DAY_OPEN_HOUR, build_channel,  # noqa: E402
                             check_auth, check_clues_runnable, people_specs)

UTC = dt.timezone.utc

# How many sockets the one-shot client may hold open to the API at once. Small
# on purpose: see `_harden_oneshot_client`. Four measured fastest here, and the
# calls it serialises are short.
_ONESHOT_POOL = 4


def waking_hours(open_hour: int) -> dict:
    """Chronotypes that are awake when the working day is.

    The engine ships three: most people up at 08:00, early risers at 06:00, and
    18% of the cast as owls who do not wake until 10:30. That last group is the
    problem. A conversation opening at 09:00 has nobody the director can choose
    between, so it falls back to picking at random and says so — 72 times
    across a three-day run, which is a lot of unsteered conversation.

    The variation is worth keeping: it is what makes one person answer at dawn
    and another go quiet until mid-morning. What is not worth keeping is a
    fifth of the company asleep through the first hour of every day. So the
    wake times are pulled inside the working day and the PEAKS are left alone,
    which is what actually shapes when somebody is talkative.

    Derived from the hour the day opens rather than hardcoded, so the two
    cannot drift apart.
    """
    early = max(5.0, open_hour - 2.5)
    return {"chronotypes": (
        # name        weight  wake          sleep  peak_am        peak_pm
        ("standard",  0.68,  float(open_hour) - 1.0, 23.0, 10.0, 15.5),
        ("early",     0.14,  early,                  21.5,  8.0, 13.5),
        ("owl",       0.18,  float(open_hour),       24.0, 13.0, 21.0),
    )}


def _open_run(root: Path, name: str) -> Path:
    """The directory this run writes into, and nothing else writes into.

    Every run gets its own, because the stores are append-only by design: a
    page written on Monday has to still be there on Thursday, so `Wiki` and
    `Mail` never delete. Pointed at one shared directory that is exactly wrong
    across runs — a three-day run in February inherited two "week of Mar 31"
    mails and an April design doc from the run before it, dated outside its own
    window and indistinguishable from what it had just produced. The clue
    reports did the same thing more quietly: eleven files in a directory whose
    index listed six.

    Naming the run is what makes a split run possible: give two invocations the
    same `--run` and they accumulate into one directory on purpose, which is
    the only case where mixing is the point. The default is a timestamp, so
    that never happens by accident.

    `latest` follows the most recent one, so the paths people actually type do
    not have to carry a stamp.
    """
    run = root / "runs" / name
    fresh = not run.exists()
    run.mkdir(parents=True, exist_ok=True)
    _claim(run)

    link = root / "latest"
    # Not `exists()`: that follows the link, so a symlink left pointing at a
    # deleted run reads as absent and then fails to be replaced.
    if link.is_symlink() or link.exists():
        link.unlink() if link.is_symlink() or link.is_file() else shutil.rmtree(link)
    link.symlink_to(Path("runs") / name, target_is_directory=True)

    rl.ok(f"{run} — {'new run' if fresh else 'CONTINUING an existing run'}"
          f"; {root / 'latest'} points here")
    return run


def _cast_file(root: Path) -> Path:
    """The drawn voices, shared by every run rather than owned by one.

    This is the one thing that must NOT be per-run. The cast file is what makes
    a person sound like the same person: their chronotype, their burst length,
    whether they leave typos. Redrawing it per run would give the corpus a
    Dermot who writes one way in February and another in April, and the whole
    point of the corpus is that it reads as one company over months.

    So it sits at the phase 4 root and every run reads it. A copy goes into the
    run directory at the end, so a run's output is still self-describing.
    """
    root.mkdir(parents=True, exist_ok=True)
    return root / "cast.json"


def _claim(out: Path) -> None:
    """Refuse to start if another run already owns this directory.

    Two processes writing one output directory is not a theoretical race: it
    silently cost a day's transcript, and then cost two rounds of debugging
    aimed at the merge, which was innocent. A stale lock from a killed run is
    cleared automatically — the check is whether that pid is still alive.
    """
    import os
    lock = out / ".run.pid"
    if lock.exists():
        try:
            owner = int(lock.read_text().strip())
        except ValueError:
            owner = 0
        if owner and owner != os.getpid():
            try:
                os.kill(owner, 0)
            except OSError:
                pass                       # it died; the lock is stale
            else:
                rl.fail(f"another phase 4 run (pid {owner}) is already writing "
                        f"{out}. Two runs sharing one output directory overwrite "
                        "each other's days. Wait for it, or use --run.")
    lock.write_text(str(os.getpid()))


def _harden_oneshot_client() -> str:
    """Give the director's calls a connect budget this network can actually meet.

    The persona turns go over the OAuth CLI, but every one-shot — the director
    picking who speaks next, the voice pass, the clue judge — goes through
    `AsyncAnthropic`, and the SDK builds that client with `connect=5.0` and two
    retries. On this host that is the wrong side of a cliff. Sequential
    connections to the API open in 13ms; several opened at once have their SYNs
    dropped, and the kernel's retransmit backoff (1s, +2s, +4s) lands the
    connection at about 7.2s. Five seconds gives up in the middle of that, three
    times, which surfaces as `APITimeoutError` at ~16s and the engine drops the
    whole channel — a paid conversation thrown away for a connection that was
    about to succeed.

    Nothing here is generation latency, so a long read timeout was never the
    fix. Two things are. The connect budget goes to 30s with more retries, so a
    burst rides out the retransmit rather than dying inside it — but measured on
    its own that only survives the burst, at ~42s a call. The cap is what avoids
    it: a warm connection is 13ms, the damage is done only by cold sockets
    opening together, and holding the pool to a few reused ones put the same
    eight-call burst back at 0.5-1.2s. Both are kept, the cap for the common
    case and the connect budget for the socket that still has to be opened.

    Returns a line describing what it did, or "" when the one-shots are on
    OAuth and no such client is ever built.
    """
    from anthropic import AsyncAnthropic
    import anthropic._base_client as base
    # Taken from the SDK rather than imported by name, because WHICH httpx it
    # wants is a property of the SDK version and not of this environment.
    # anthropic 1.0 moved to a vendored `httpx2` and type-checks the client it
    # is handed, so a plain `import httpx` here raises `Invalid http_client
    # argument` on import of the module and takes the whole run with it.
    # Whichever one it imported is bound as an attribute of `_base_client`.
    httpx = getattr(base, "httpx2", None) or base.httpx
    # Imported as a submodule explicitly rather than reached through the
    # package: `bespoke_user.__init__` is lazy, so `bespoke_user.user` is not
    # reliably bound as an attribute of it.
    import bespoke_user.user as user

    if user._ONESHOTS_OAUTH or not user._ONESHOT_API_KEY:
        return ""
    # Assigned rather than passed: `_anthropic_client()` builds this lazily on
    # first use, so seeding the global is what stops the default from ever
    # being constructed.
    limits = httpx.Limits(max_connections=_ONESHOT_POOL,
                          max_keepalive_connections=_ONESHOT_POOL)
    timeout = httpx.Timeout(600.0, connect=30.0)
    user._anthropic = AsyncAnthropic(
        api_key=user._ONESHOT_API_KEY, timeout=timeout, max_retries=5,
        http_client=httpx.AsyncClient(timeout=timeout, limits=limits),
    )
    return (f"one-shot client: pool {_ONESHOT_POOL}, connect 30s, 5 retries "
            "(SDK default is unbounded, 5s, 2)")


# =============================================================================
# The review surface
# =============================================================================
def context_document(world, days: list[str], built: dict) -> str:
    """Every input to every model call, before any of it is spent.

    This IS the complete input — nothing else reaches a model — so if a
    conversation comes out wrong, the cause is visible here.
    """
    L = ["# Phase 4: what the simulation is told", "",
         "Four things reach a model: the channel scenario and briefing (which "
         "the DIRECTOR sees, to pick who speaks next), the shared ground "
         "(which EVERYONE in the channel holds), each person's own grounding, "
         "and the turn budget.", "",
         "Worth keeping in mind while reading:", "",
         "1. **This is today, not history.** Everyone is told the state as of "
         "that morning.",
         "2. **MUST RAISE** belongs to the person driving it; the engine holds "
         "the conversation open until it lands. **MUST SETTLE** is a planted "
         "clue: the engine pushes for it to be stated as a conclusion, and a "
         "channel-day that does not get its INFORMATION across is run again — "
         "told what was missing. The words are the persona's own; what is "
         "fixed is the point, and any identifier named under it.",
         "3. **The forbidden list does not exist yet** on that date. Naming it "
         "is the failure this whole pipeline is built to prevent.", ""]

    for date in days:
        channels = built[date]
        L += ["", "=" * 78, f"# {date} — {len(channels)} conversation(s), "
              f"{sum(c['max_turns'] for c in channels)} turns budgeted", "=" * 78]
        for channel in channels:
            spec = channel.get("projectSpec")
            L += ["", "-" * 78,
                  f"## #{channel['name']} — {channel['max_turns']} turns, "
                  f"{len(channel['memberIds'])} people", "-" * 78,
                  "", "### 1. What the DIRECTOR is told", "",
                  f"Channel #{channel['name']}: {channel['scenario']}", ""]
            L += ["    " + line for line in channel["briefing"].split("\n")]

            if spec:
                truth = spec["ground_truth"]
                L += ["", "### 2. What EVERYONE in the channel shares", "",
                      f"    Project    {spec['name']}",
                      f"    Milestone  {spec['milestone']}", "",
                      "    Settled"]
                L += [f"      - {x}" for x in truth["completed"]] or ["      - (none)"]
                L += ["", "    On the table"]
                L += [f"      - {i['what']} ({i['who']})" for i in truth["in_progress"]] \
                    or ["      - (none)"]
                L += ["", "    Settled decisions everyone works to"]
                L += [f"      - {x}" for x in truth["decisions"]] or ["      - (none)"]
                L += ["", "    Open questions"]
                L += [f"      - {x}" for x in truth["known_unknowns"]] or ["      - (none)"]
                L += ["", f"    DOES NOT EXIST YET ({len(truth['forbidden'])} names)"]
                L += [f"      - {x}" for x in truth["forbidden"][:12]]
                if len(truth["forbidden"]) > 12:
                    L.append(f"      ... and {len(truth['forbidden']) - 12} more")

            L += ["", "### 3. What EACH PERSON is told", ""]
            for persona in channel["memberIds"]:
                ctx = (channel.get("projectContext") or {}).get(persona)
                L.append(f"  {world.label(persona)}  ({persona})")
                if not ctx:
                    L += [f"    background  {(channel.get('memberBackgrounds') or {}).get(persona, '')}",
                          f"    goal        {(channel.get('goals') or {}).get(persona, '')}", ""]
                    continue
                L += [f"    role        {ctx['role_line']}",
                      f"    owns        {ctx['owns'] or '(nothing specific)'}",
                      "    agenda"]
                for n, item in enumerate(ctx["agenda"], 1):
                    mark = ("   *** MUST SETTLE (clue %s) ***" % item.get("leaf", "?")
                            if item.get("must_settle")
                            else "   *** MUST RAISE ***" if item.get("must_raise") else "")
                    L.append(f"      {n}. {item['about']}{mark}")
                    if item.get("verbatim"):
                        L.append(f"         must contain literally: "
                                 f"{', '.join(item['verbatim'])}")
                L += [f"    goal        {ctx['current_goal']}",
                      f"    available   {ctx['availability']}", ""]

            if channel.get("end_state"):
                L += ["### 4. How it should land", "",
                      f"    lands as  {channel.get('resolution') or 'no posture'}",
                      f"    leaving   {channel['end_state']}", ""]
    return "\n".join(L) + "\n"


# =============================================================================
# The clue gate
# =============================================================================
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "elements": {
            "type": "array",
            "description": "the remark broken into the distinct things it tells "
                           "a reader, each checked on its own",
            "items": {
                "type": "object",
                "properties": {
                    "part": {"type": "string",
                             "description": "one thing the remark tells a "
                                            "reader, in your own words"},
                    "present": {"type": "boolean",
                                "description": "does a reader of this "
                                               "conversation come away with it"},
                    "why": {"type": "string",
                            "description": "one short sentence"},
                },
                "required": ["part", "present", "why"],
                "additionalProperties": False,
            }},
        "carried": {"type": "boolean",
                    "description": "is ALL of this information present in what "
                                   "was said, in whatever words"},
        "quote": {"type": "string",
                  "description": "the message that carries it, copied exactly, "
                                 "or empty"},
        "said_by": {"type": "string",
                    "description": "the name of the person whose message "
                                   "carries it, or empty"},
        "missing": {"type": "array", "items": {"type": "string"},
                    "description": "each piece of the information that is NOT "
                                   "there, said plainly enough that the person "
                                   "could act on it. Empty when nothing is."},
        "why": {"type": "string"},
    },
    "required": ["elements", "carried", "quote", "said_by", "missing", "why"],
    "additionalProperties": False,
}


def _norm_ident(text: str) -> str:
    """An identifier reduced to what is actually identifying about it.

    `_response_cache_key()`, `` `_response_cache_key` `` and "response cache
    key()" are the same name typed by three people in three moods, and a corpus
    that only accepts the first is measuring formatting. What it must still
    reject is "the cache key function", where the name is gone and a reader
    could not recover it — so the letters have to be there, in order, and only
    the punctuation and casing between them is forgiven.
    """
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _identifiers_missing(planted: dict, said: list[str]) -> list[str]:
    """Required names that nobody typed, in any spelling of them."""
    body = _norm_ident(" ".join(said))
    return [v for v in (planted.get("verbatim") or [])
            if _norm_ident(v) and _norm_ident(v) not in body]


def _leaked_terms(planted: dict, said: list[str]) -> list[str]:
    """Giveaway language that turns a hidden requirement into a stated one.

    Phase 3 keeps every clue clear of the words that would name the requirement
    outright, and then checks its own text for them. Phase 4 never did, which
    was survivable only while the clue text was near-scripted. Once the point
    is what is fixed and the words are the persona's, the persona is free to
    reword straight into the giveaway — so this is checked exactly where the
    freedom was granted. Substring and lowercase, the same test phase 3's
    `giveaways` uses, because these are phrases rather than identifiers.
    """
    body = " ".join(said).lower()
    return [t for t in (planted.get("forbidden_terms") or [])
            if t and re.search(r"(?<!\w)" + re.escape(t.lower()) + r"(?!\w)", body)]


def channel_of(workspace: dict, channel: str) -> dict | None:
    for got in workspace.get("channels") or []:
        if got.get("name") == channel or got.get("id", "").startswith(channel):
            return got
    return None


def transcript_of(workspace: dict, channel: str) -> list[dict]:
    got = channel_of(workspace, channel) or {}
    return sorted(got.get("messages") or [], key=lambda m: m.get("ts", ""))


def _transcript_lines(messages: list[dict], world) -> str:
    """A run of messages as a model reads them: time, who, what."""
    return "\n".join(f'{m["ts"][11:16]}  {world.label(m.get("userId", ""))}: '
                     f'{m.get("text", "")}' for m in messages)


def check_clue(llm, planted: dict, messages: list[dict], world) -> dict:
    """Did the information in this clue reach the transcript?

    Not "were these words said". A clue is a fact the corpus has to teach, and
    the persona saying it is a person with their own vocabulary — so the point
    is fixed and the phrasing is not. Four consequences, each of which was a
    real failure before it was a rule:

    The whole remark is judged, element by element, and not just the `settles`
    clause that summarises it. Free phrasing is not free abridgement: the point
    a persona keeps is reliably the flat observation, and the half they drop is
    the one that says why anybody minds — which is the half a reader needs to
    know there is a requirement here at all.

    Identifiers are checked in code, because a name paraphrased is a different
    name and no judgement improves on that — but normalised, so backticks and
    casing are not what decides whether a corpus teaches its own API.

    The point itself is read for INFORMATION rather than for speech act. The
    old gate demanded assertion and rejected anything "framed as an open
    question", which threw away a clue whose scope fact was stated perfectly,
    inside a question. What a reader can learn from a line does not depend on
    its punctuation.

    A miss comes back as a LIST of what is absent, not a boolean. The retry is
    what spends money, and a retry that cannot say what was missing is the same
    attempt again — which is exactly how two clues burned three tries each.
    """
    holder = planted.get("holder", "")
    mine = [m.get("text") or "" for m in messages if m.get("userId") == holder]
    # The room, not just the holder: a point made by whoever was standing next
    # to them is in the corpus at the right date in the right room, which is
    # what solvability actually asks. The holder is who the PLAN picked, and
    # that choice is about spreading clues across people and weeks, not about
    # attribution. Drift is recorded rather than punished.
    room = [m.get("text") or "" for m in messages]

    gaps = _identifiers_missing(planted, mine) or _identifiers_missing(planted, room)
    # The holder's own words, because that is what phase 3's forbidden list is
    # about: a remark must not give away the requirement it is a clue to. The
    # rest of the room talking around the subject is the haystack doing its job.
    leaked = _leaked_terms(planted, mine)

    lines = _transcript_lines(messages, world)
    if not lines.strip():
        return {"carried": False, "quote": "", "said_by": "", "why":
                "nothing was said in this room", "missing": [planted["settles"]],
                "elements": [], "missing_verbatim": gaps, "leaked": leaked}

    clue = world.clue_of.get(planted.get("clue", "")) or {}
    # What the requirement actually needs out of this clue, when phase 3 wrote
    # it down. The `settles` clause is one person's remark; the subconclusion is
    # the thing a reader is supposed to be able to conclude, and judging against
    # both is what stops a verdict of "close enough" on a fact that is not there.
    behind = (clue.get("subconclusion_text") or "").strip()
    # `settles` alone is not enough to judge against. It is phase 3's one-clause
    # condensation of the remark, and a persona who says only that has said less
    # than they were asked to: a live run passed "it's half the sync rate" for a
    # clue whose text also carried that the preview matched sync price exactly
    # and that the estimate would scare people off submitting. Both halves were
    # gone, `missing` came back empty, and the gate reported a clean carry.
    remark = (planted.get("text") or "").strip()
    if remark.lower() == (planted["settles"] or "").strip().lower():
        remark = ""

    verdict = llm.complete(
        system="You read a chat transcript and decide whether a specific piece "
               "of information is present in it. You output strict JSON and "
               "nothing else.",
        prompt=("Here is a conversation between colleagues.\n\n" + lines[:12000]
                + "\n\nSomebody in this room was supposed to get this across:"
                  f"\n\n    {planted['settles']}\n"
                + (f"\nThat is the short of it. What they were actually asked "
                   f"to say, in their own words, was all of this:\n\n"
                   f"    {remark}\n" if remark else "")
                + (f"\nFor background only — across the whole corpus, and NOT "
                   f"from this one conversation, a reader is eventually meant "
                   f"to be able to conclude:\n\n    {behind}\n\nOther remarks "
                   f"elsewhere carry the rest of that. Do not require this "
                   f"conversation to establish all of it.\n" if behind else "")
                + "\nBreak the remark into the distinct things it tells a "
                  "reader — a fact, a number, a name, what it rules out, what "
                  "the person wants, what they mind about. ONE thing per "
                  "element, never two joined by 'and' or a slash. Keep what is "
                  "HAPPENING apart from what the person says SHOULD be true "
                  "instead: those teach a reader different things, and the "
                  "second is usually the one that tells them there is anything "
                  "to fix at all. Leave stylistic detail out of the list — who "
                  "pulled up what, and how they phrased it, is not something a "
                  "reader learns.\n\n"
                  "Then say for each whether a reader of this conversation "
                  "comes away with it. An element is present only where you "
                  "could point at a line that gives it. For an objection or a "
                  "want, that means a line saying the behaviour is wrong, or "
                  "saying what should happen instead — reporting the behaviour "
                  "is not objecting to it, however unhappily it is worded, and "
                  "sounding bothered is not the same as saying what you want. "
                  "Do not credit an element because the tone implies it, "
                  "because it follows from the rest of the remark, or because a "
                  "reasonable person would think it.\n\n"
                  "Judge the INFORMATION, not the wording and not the grammar. "
                  "These are their own words, so no phrasing is required, and a "
                  "point made inside a question, a complaint or an aside counts "
                  "every bit as much as one stated flatly — what matters is "
                  "whether a reader comes away knowing it. It does NOT count if "
                  "the conversation only touches the subject without anyone "
                  "giving the substance, or if somebody asks about it and "
                  "nothing in the room answers.\n\n"
                  "Quote the message that carries the point and name who said "
                  "it. If any part is missing, list each missing part plainly, "
                  "as you would tell the person what they still have not "
                  "said."),
        schema=JUDGE_SCHEMA, label=f"clue:{planted.get('clue', '')}",
        max_tokens=1500)

    # The verdict is arithmetic over the elements, not the model's own summary
    # boolean. Asked both ways in one call, a judge that has just written
    # `present: false` against the objection still answers `carried: true`,
    # because the point it was shown first — the `settles` clause — really did
    # get across. Which of the two it means is settled here rather than there.
    #
    # The elements REPLACE the free-text miss list rather than joining it. Both
    # describe the same absence in slightly different words, and a retry told
    # six things when three are missing reads as six separate failures.
    thin = [e["part"] for e in verdict.get("elements") or [] if not e["present"]]
    verdict["missing"] = thin or list(verdict.get("missing") or [])
    verdict["carried"] = bool(verdict.get("carried")) and not thin
    verdict["missing_verbatim"] = gaps
    verdict["leaked"] = leaked
    if gaps:
        verdict["carried"] = False
        verdict["missing"] = list(verdict.get("missing") or []) + [
            f"the name {v} itself, typed the way it is written" for v in gaps]
        verdict["why"] = (f"nobody typed {', '.join(gaps)}; "
                          + verdict.get("why", ""))
    return verdict


def _drifted(world, row: dict) -> bool:
    """Did somebody OTHER than the planned holder carry this?

    The judge answers with the name it was shown, which is the display name the
    cast types under; the plan speaks persona ids. Comparing the two raw reports
    every clue in the corpus as having drifted, including the ones its own
    holder said perfectly.
    """
    by = (row.get("said_by") or "").strip()
    return bool(by) and by not in (row["holder"], world.label(row["holder"]))


REPAIR_SCHEMA = {
    "type": "object",
    "properties": {
        "burst": {"type": "array", "items": {"type": "string"},
                  "description": "one or two short messages, sent seconds after "
                                 "their own, carrying the part that never made "
                                 "it. Empty only if it truly cannot be added."},
        "rewrite": {"type": "string",
                    "description": "a replacement for the message they already "
                                   "sent, if adding the missing part means "
                                   "changing it. Empty to leave it as it is, "
                                   "which is the normal answer."},
        "why": {"type": "string", "description": "one sentence"},
    },
    "required": ["burst", "rewrite", "why"],
    "additionalProperties": False,
}


def _carrier(messages: list[dict], planted: dict, quote: str) -> int:
    """Index of the holder's message the missing part belongs onto.

    The judge's quote, when it points at one of theirs; otherwise the last
    message they sent about it. Not the last message in the room: a beat added
    after four other people have spoken is a person answering a question nobody
    asked.
    """
    holder = planted.get("holder", "")
    mine = [i for i, m in enumerate(messages) if m.get("userId") == holder]
    want = _norm_ident(quote)
    if want:
        for i in mine:
            said = _norm_ident(messages[i].get("text", ""))
            if said and (want in said or said in want):
                return i
    return mine[-1] if mine else -1


def repair_clue(llm, world, planted: dict, row: dict, messages: list[dict],
                attempt: int = 1) -> dict | None:
    """The missing half of a thinned clue, as a message the holder sends next.

    Re-running a whole channel-day because one remark came out half-said costs
    a full simulation and rolls the dice on everything else in the room that
    was already right. What went wrong is narrower than that: the observation
    landed and the part that says why anybody minds did not, which in chat is
    one more bubble seconds later — the way somebody adds the thing they
    actually meant.

    Only ever a repair, never authorship. A clue nobody touched at all has no
    message to add a beat to, and a burst invented into that silence is a
    person answering a question nobody asked, so those go back to the re-run
    path (`None`).

    The bare claim is left alone by default. `_bare` in the engine's turn
    prompt asks for exactly that shape, and it is what makes the corpus read
    like chat rather than like minutes — the fix is a second bubble, not a
    longer sentence.
    """
    if not (row.get("missing") or []):
        return None
    # Nothing of it landed: that is a clue that never got said, which is a
    # different failure and has its own path.
    if not any(e.get("present") for e in row.get("elements") or []):
        return None
    at = _carrier(messages, planted, row.get("quote", ""))
    if at < 0:
        return None

    holder = planted["holder"]
    name = world.label(holder)
    voice = [m["text"] for m in messages
             if m.get("userId") == holder and m is not messages[at]][-6:]
    before = _transcript_lines(messages[max(0, at - 6):at + 1], world)
    after = _transcript_lines(messages[at + 1:at + 8], world)
    forbidden = list(planted.get("forbidden_terms") or [])
    names = list(planted.get("verbatim") or [])

    patch = llm.complete(
        system="You write chat messages in somebody else's voice, for a "
               "conversation that already happened. You output strict JSON and "
               "nothing else.",
        prompt=(f"{name} was in this conversation:\n\n{before}\n\n"
                f"Their last message there is the one that matters. They meant "
                f"to get all of this across:\n\n    {planted['text']}\n\n"
                "These parts never made it:\n"
                + "".join(f"  - {m}\n" for m in row["missing"])
                + (f"\nWhat was said after, which you cannot contradict and "
                   f"must not repeat:\n\n{after}\n" if after.strip() else "")
                + f"\nHow {name} types, from their own messages:\n\n"
                + "".join(f"  {v}\n" for v in voice)
                + "\nWrite what they send NEXT — one or two short messages, "
                  "seconds after their own, carrying the parts that never made "
                  "it. This is the same person continuing, not a summary and "
                  "not a correction: no 'to clarify', no 'what I meant was', "
                  "no restating what they already said. Say the missing part "
                  "the way somebody says the thing that has been bothering "
                  "them — plainly, and as their own position rather than as a "
                  "question for the room.\n\n"
                  "Their first message stays as it is unless the missing part "
                  "genuinely cannot follow from it, in which case give a "
                  "replacement for it as well — same claim, same length, same "
                  "voice. Leaving it alone is the normal answer.\n\n"
                  "Match their typing exactly, from the sample above: if they "
                  "start sentences with a capital and end them with a full "
                  "stop, so do you; if they type in lower case and skip the "
                  "stop, so do you. Same length, same punctuation, same names "
                  "for things. A message that reads more casually — or more "
                  "carefully — than the ones around it is wrong even when it "
                  "says the right thing."
                + (f"\n\nThese are names, and people type names rather than "
                   f"describing them: {', '.join(names)}. Whichever of them the "
                   f"missing part turns on goes in literally, spelled the way "
                   f"it is written here — a reader cannot get a name back from "
                   f"'the usual thing'." if names else "")
                + (f"\n\nThese words must not appear, in any form: "
                   f"{', '.join(forbidden)}. They name the thing this remark is "
                   f"a hint about, and saying them outright makes the hint "
                   f"pointless." if forbidden else "")),
        schema=REPAIR_SCHEMA, label=f"repair:{row['clue']}:{attempt}",
        max_tokens=1200)

    burst = [t.strip() for t in (patch.get("burst") or []) if t.strip()][:2]
    if not burst and not (patch.get("rewrite") or "").strip():
        return None
    return {"at": at, "burst": burst,
            "rewrite": (patch.get("rewrite") or "").strip(),
            "why": patch.get("why", "")}


def apply_repair(messages: list[dict], patch: dict, planted: dict) -> list[dict]:
    """Fold a repair into a channel's message list, in place.

    Timestamps are stepped into the gap before the next message rather than
    added blindly: a burst that lands after the reply it prompted reads as
    somebody answering their own question backwards. Where there is no gap the
    stamps are simply equal, which is what a real burst looks like anyway —
    `transcript_of` sorts stably, so insertion order survives.
    """
    at = patch["at"]
    if patch.get("rewrite"):
        messages[at] = {**messages[at], "text": patch["rewrite"]}
    if not patch["burst"]:
        return messages
    here = dt.datetime.fromisoformat(messages[at]["ts"])
    nxt = (dt.datetime.fromisoformat(messages[at + 1]["ts"])
           if at + 1 < len(messages) else here + dt.timedelta(minutes=1))
    room = (nxt - here) / (len(patch["burst"]) + 1)
    step = min(dt.timedelta(seconds=20), room) if room.total_seconds() > 0 \
        else dt.timedelta(0)
    added = [{"userId": planted["holder"], "text": text,
              "ts": (here + step * (i + 1)).isoformat()}
             for i, text in enumerate(patch["burst"])]
    messages[at + 1:at + 1] = added
    return messages


def written_text(stores: list, kind: str, title: str, by: str) -> tuple[str, str]:
    """(what was written, where it landed) for an artifact somebody owed today.

    Matched the way `artifact_audit` matches — person, kind, and the title the
    plan asked for against the title they actually gave it — because a persona
    writes their own headline and an exact-match lookup calls a page that exists
    a page that does not.
    """
    import bespoke_user.sim_engine as G
    for store in stores:
        for row in getattr(store, "inventory", lambda: [])() or []:
            if row.get("by") != by or not G._same_action(
                    "write" if kind == "doc" else "send", row.get("action", "")):
                continue
            if not (G._norm_key(row.get("title")) == G._norm_key(title)
                    or G._title_overlap(title, row.get("title"))):
                continue
            page = (getattr(store, "_pages", {}) or {}).get(row.get("id"))
            if page:
                return page.get("body", ""), row.get("id", "")
            for thread in (getattr(store, "_threads", {}) or {}).values():
                if thread.get("subject") == row.get("title"):
                    return thread.get("body", ""), row.get("title", "")
    return "", ""


def _check_artifacts(world, llm, date: str, channels: list, stores: list,
                     attempt: int = 1) -> list[dict]:
    """Did the clues hidden in today's DOCUMENTS and MAIL get written down?

    The transcript gate reads `spec["planted"]`, which is only ever the clues
    planted in a conversation. A clue planted on a page is checked nowhere —
    it was reported as neither said nor missed, and the only proof it landed
    was somebody opening the file. Same judge, same report, different haystack.
    """
    import phase4_simulate as ps
    rows = []
    for channel in channels:
        for spec in [x for x in world.day(date)["specs"]
                     if x["channel"] == channel["name"]]:
            for goal in spec.get("goals") or []:
                owner = goal.get("owner")
                for ref in goal.get("writes") or []:
                    planted = ps.planted_in(world, ref["kind"], ref["id"])
                    if not planted or not owner:
                        continue
                    title = world.title_of(ref["kind"], ref["id"])
                    body, where = written_text(stores, ref["kind"], title, owner)
                    for one in planted:
                        rows.append(_artifact_row(world, llm, one, owner, date,
                                                  ref, title, body, where,
                                                  attempt, channel["name"]))
    return rows


def _artifact_row(world, llm, planted, owner, date, ref, title, body, where,
                  attempt, room: str) -> dict:
    """One artifact clue's verdict, keyed to the ROOM that owes the artifact.

    `channel` has to be the real conversation, not a `mail:<id>` label. The
    retry loop reads it as a room to re-simulate: a pseudo-channel matches
    nothing, so the retry ran zero channels and then filtered the row out of the
    results — the clue was not merely missed, it disappeared from the report,
    and the day showed 0/0 with a planted clue in it. Re-running the room the
    writer is in is also the only retry that could help, since that is where
    they would write the page again.
    """
    kind = "page" if ref["kind"] == "doc" else "mail"
    if not body.strip():
        return {"clue": planted.get("clue", ""), "holder": owner, "date": date,
                "channel": room, "wrote_into": f"{kind}:{ref['id']}",
                "attempt": attempt,
                "said": False, "quote": "", "said_by": "",
                "why": f"the {kind} was never written, so nothing can carry it",
                "missing": [planted.get("settles", "")], "missing_verbatim": [],
                "leaked": [], "context": [], "artifact": title}
    gaps = _identifiers_missing(planted, [body])
    verdict = llm.complete(
        system="You read a document and decide whether one specific point is "
               "made in it. You output strict JSON and nothing else.",
        prompt=(f"Here is a {kind} written by a colleague.\n\n{body[:12000]}\n\n"
                "Somebody was supposed to get this across in it:\n\n"
                f"    {planted['settles']}\n\nIs that information there? Judge "
                "the INFORMATION, not the wording — a document says things in "
                "its own shape, as a heading, a checklist line or an aside, and "
                "any of those count. It does NOT count if the document only "
                "touches the subject without giving the substance.\n\n"
                "The point above is phrased as something a ROOM concluded, "
                "because that is how it is recorded for a conversation. This is "
                "ONE PERSON writing on their own. Do not require consensus, "
                "agreement, or any 'the team decided' framing — nobody can "
                "write that alone, and demanding it fails a document that "
                "states the point perfectly. The author asserting it, or "
                "describing the behaviour it is about as a plain fact, is the "
                "same information and counts.\n\n"
                "Quote the line that carries it. If any part is missing, list "
                "each missing part plainly."),
        schema=JUDGE_SCHEMA, label=f"artifact:{planted.get('clue', '')}",
        max_tokens=1500)
    missing = list(verdict.get("missing") or [])
    if gaps:
        missing += [f"the name {v} itself, typed the way it is written" for v in gaps]
    return {"clue": planted.get("clue", ""), "holder": owner, "date": date,
            "channel": room, "wrote_into": f"{kind}:{ref['id']}",
            "attempt": attempt,
            "said": bool(verdict.get("carried")) and not gaps,
            "quote": verdict.get("quote", ""), "said_by": owner,
            "why": verdict.get("why", ""), "missing": missing,
            "missing_verbatim": gaps,
            "leaked": _leaked_terms(planted, [body]),
            "context": [], "artifact": title, "written_as": where}


def written_body(run: Path, row: dict) -> tuple[str, str]:
    """(what actually got written, the file it is in) for an artifact clue.

    Read back off disk rather than carried on the row, so a report can be
    regenerated for a run that has already finished — and because the file IS
    the artifact. A quote alone does not tell you whether the page is about the
    right thing; the page does.
    """
    into = row.get("wrote_into") or ""
    title = (row.get("artifact") or "").strip()
    if not into or not title:
        return "", ""
    want = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48]
    if into.startswith("page"):
        for f in sorted((run / "docs").rglob("*.md")):
            head = f.read_text(encoding="utf-8", errors="replace")[:400]
            if want[:24] in f.stem or (f'title: "{title}"' in head):
                body = f.read_text(encoding="utf-8", errors="replace")
                return body.split("---", 2)[-1].strip(), str(f.relative_to(run))
    else:
        import email as _email
        for f in sorted((run / "emails").rglob("*.eml")):
            if want[:24] not in f.stem:
                continue
            msg = _email.message_from_bytes(f.read_bytes())
            payload = msg.get_payload(decode=True) or b""
            return payload.decode("utf-8", "replace").strip(), str(f.relative_to(run))
    return "", ""


def clue_report(world, row: dict, run: Path | None = None) -> str:
    """One clue, with the line that carried it and its neighbours."""
    clue = world.clue_of.get(row["clue"], {})
    where = clue.get("carrier") or {}
    L = [f"# {row['clue']} — {clue.get('kind', 'clue')} for "
         f"{clue.get('req', '?')} ({clue.get('task', '')})", ""]

    # What this clue is FOR, in full, so the file answers on its own. Reading a
    # clue report used to mean holding `phase3_plant.md` open beside it to find
    # out which requirement the remark served and which part of it this one was
    # carrying — and a report you cannot read alone is one nobody reads.
    L += [f"## The task it serves — {clue.get('task_id', '?')}", "",
          f"**The agent is told:** {clue.get('task_description', '') or '—'}", "",
          f"### The hidden requirement — {clue.get('req', '?')}", "",
          "Never stated anywhere in the corpus. An agent has to rebuild it from "
          "remarks like this one.", "",
          "| part | what it actually requires | this clue |",
          "|---|---|---|"]
    covers = set(clue.get("covers") or [])
    req = clue.get("requirement") or {}
    for fact in ("rule", "scope", "exclusions_or_crossover", "failure_behavior",
                 "observability"):
        if not req.get(fact):
            continue
        L.append(f"| {fact} | {str(req[fact]).replace('|', chr(92) + '|')} "
                 f"| {'**carries this**' if fact in covers else '—'} |")
    if not req:
        L.append("| — | (the ledger has no requirement text for this clue) | — |")
    L += ["",
          f"This clue is one of several that build to: "
          f"*{clue.get('subconclusion_text', '') or '(no subconclusion recorded)'}*",
          "", "---", ""]

    L += [f"**Planted by phase 3 as**   {row['holder']}, {where.get('source', '?')}, "
          f"{where.get('date', '?')}, {where.get('room', '?')}"
          + (f"\n**Had to be written into**  {row['artifact']}"
             if row.get("artifact") else ""),
          f"**Meant to settle**         {clue.get('settles', '')}",
          f"**So a reader concludes**   {clue.get('subconclusion_text', '') or '—'}",
          f"**Covers**                  {', '.join(clue.get('covers') or []) or '—'}",
          f"**Names that must appear**  {', '.join(clue.get('verbatim') or []) or '—'}",
          f"**Status**                  {'carried' if row['said'] else 'NOT CARRIED'}"
          f"  (attempt {row['attempt']})", ""]
    if _drifted(world, row):
        L += [f"> Carried by {row['said_by']}, not {row['holder']} who was "
              "planned to. The information is in the room on the right day, so "
              "this counts — noted because it moves who the corpus attributes "
              "it to.", ""]
    if row.get("leaked"):
        L += [f"> **LEAKED** — giveaway language reached the transcript: "
              f"{', '.join(row['leaked'])}. The clue landed, but saying this "
              "much states the hidden requirement outright and makes the task "
              "trivial. Worth re-running even though the gate passed.", ""]
    if row.get("missing"):
        L += ["> Information that never reached the room:", ""]
        L += [f"> - {m}" for m in row["missing"]]
        L.append("")
    if row.get("missing_verbatim"):
        L += [f"> No spelling of {', '.join(row['missing_verbatim'])} appears "
              "anywhere — the name itself is unrecoverable from this "
              "conversation.", ""]

    L += ["## What phase 3 wrote", ""]
    L += ["> " + line for line in (clue.get("text") or "").split("\n")]
    if row.get("elements"):
        # The remark broken up, because "carried" on its own hides the failure
        # this document exists to show: three of four parts said, the fourth —
        # the one that says why anybody minds — quietly gone.
        L += ["", "## Piece by piece", ""]
        L += [f"- [{'x' if e['present'] else ' '}] {e['part']}"
              for e in row["elements"]]
    L += ["", "## What was actually said", ""]
    if row["said"] and row.get("quote"):
        # An artifact clue is IN the page or the mail, not in the room. The row
        # is keyed to the room so a retry knows what to re-run, and printing
        # that as the location sent a reader to #code-review looking for a line
        # that lives in a wiki page the conversation merely asked for.
        seen_in = (f"{row['artifact']} (written from #{row['channel']})"
                   if row.get("wrote_into") else f"#{row['channel']}")
        L += [f"**{row.get('said_by') or row['holder']}**, {row['date']}, "
              f"{seen_in}", "",
              "> " + row["quote"].replace("\n", "\n> "), ""]
    elif row.get("rendered") is False:
        # Not "searched and not found" — never searched, because there was
        # nothing to search. Phase 3 seats some of its own pages and mail, and
        # no day spec's `goals[].writes[]` claims them, so nobody was ever
        # asked to write one. Saying "the page does not carry it" about a page
        # that does not exist sends a reader looking for a file.
        L += [f"**Never rendered.** {row.get('why', '')}", "",
              "This is not a persona who left something out — the carrier was "
              "never written at all, so there was never anything to judge. The "
              "clue is absent from the corpus and the requirement is that much "
              "harder to recover.", ""]
    else:
        # Name the haystack that was actually searched. For an artifact clue
        # that is the page or the mail — saying "nothing in #code-review
        # carried it" sends a reader to a transcript the gate never read, and
        # the document it DID read goes unmentioned.
        where_looked = (f"The {row['wrote_into'].split(':')[0]} *{row['artifact']}*"
                        if row.get("wrote_into") else f"Nothing in #{row['channel']}")
        verb = ("does not carry it." if row.get("wrote_into")
                else "on %s carried it." % row["date"])
        L += [f"{where_looked} {verb} {row.get('why', '')}".strip(), ""]

    if row.get("repair"):
        fix = row["repair"]
        L += ["## Repaired", "",
              f"The first attempt came out thinner than it was planted, so "
              f"{row['holder']} said the rest of it in "
              f"{len(fix['added'])} more message(s)"
              + (", and the message before them was rewritten"
                 if fix.get("rewrote") else "")
              + f" ({fix['attempts']} repair attempt(s)). This is an edit to the "
                "transcript after the fact, not something the simulation "
                "produced on its own:", ""]
        L += [f"> {text}" for text in fix["added"]]
        L.append("")

    # For an artifact clue the page or the mail IS the evidence, so show it
    # rather than one quoted line: whether the document came out about the right
    # subject is the question, and a single sentence cannot answer it.
    if row.get("wrote_into") and run is not None:
        body, where = written_body(run, row)
        if body:
            L += ["## What was actually written", "",
                  f"`{where}`", "", "```"]
            L += body.splitlines()[:60]
            if len(body.splitlines()) > 60:
                L.append(f"... ({len(body.splitlines()) - 60} more lines)")
            L += ["```", ""]
        else:
            L += ["## What was actually written", "",
                  "> Nothing on disk matches this artifact — it was never "
                  "written, which is why the clue could not land.", ""]

    if row.get("context"):
        L += ["## In context", "", "```"]
        for line in row["context"]:
            L.append(line)
        L += ["```", ""]
    return "\n".join(L)


def clue_index(world, rows: list[dict]) -> str:
    said = sum(1 for r in rows if r["said"])
    leaks = [r for r in rows if r.get("leaked")]
    L = ["# Phase 4: every planted clue, and whether its information landed", "",
         f"{said} of {len(rows)} carried.", "",
         "A clue is a fact the corpus has to teach. It does not have to be "
         "worded the way it was planted — the persona saying it has their own "
         "vocabulary — but the information has to be there, or the requirement "
         "it serves becomes unrecoverable and the task unscoreable. Each row "
         "links to the line that carried it, in the conversation around it.", ""]
    if leaks:
        L += [f"**{len(leaks)} clue(s) leaked giveaway language.** Those landed, "
              "but state the hidden requirement plainly enough to make the task "
              "trivial — a worse outcome than a miss, because a miss is visible "
              "in this table and a leak is not.", ""]
    fixed = [r for r in rows if r.get("repair")]
    if fixed:
        L += [f"**{len(fixed)} clue(s) were repaired in place.** They came out "
              "thinner than they were planted — the observation said, the part "
              "that says why anybody minds dropped — and the holder was given "
              "one more message to finish the thought instead of the whole day "
              "being run again. Each one names the added message in its own "
              "page.", ""]
    L += ["| clue | task | holder | said by | date | where | kind | carried "
          "| leaked | repaired | attempt |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for row in sorted(rows, key=lambda r: (r["date"], r["clue"])):
        clue = world.clue_of.get(row["clue"], {})
        drift = row.get("said_by", "") if _drifted(world, row) else "—"
        fix = row.get("repair") or {}
        mended = "+%d msg" % len(fix["added"]) if fix else "—"
        # A clue in a page and a clue in a room answer the same question of
        # different haystacks, and "NO" means something different in each — one
        # is a conversation that skirted it, the other a document that omitted
        # it. The reader of this table needs to know which.
        into = row.get("wrote_into") or ""
        kind = into.split(":")[0] if into else "chat"
        room = (f"{(clue.get('carrier') or {}).get('room', into)}"
                if into else f"#{row['channel']}")
        L.append(f"| [{row['clue']}]({row['clue']}.md) | {clue.get('task_id', '')} "
                 f"| {row['holder']} | {drift} | {row['date']} "
                 f"| {room} | {kind} | {'yes' if row['said'] else '**NO**'} "
                 f"| {', '.join(row.get('leaked') or []) or '—'} "
                 f"| {mended} | {row['attempt']} |")
    return "\n".join(L) + "\n"


# =============================================================================
# The run
# =============================================================================
def simulate(world, days: list[str], only: set[str] | None, args) -> int:
    import bespoke_user as bu
    import bespoke_user.sim_engine as G

    rl.info(f"auth: {check_auth(args.auth)}")
    hardened = _harden_oneshot_client()
    if hardened:
        rl.info(hardened)

    root = Path(args.out)
    out = _open_run(root, args.run)

    # Build every channel first, so the review document describes exactly what
    # will run and a dry run costs nothing.
    built: dict[str, list[dict]] = {}
    cast_of: set[str] = set()
    for date in days:
        day = world.days.get(date) or {}
        specs = [s for s in world.day(date)["specs"]
                 if not only or s["channel"] in only]
        nth: dict[str, int] = {}
        built[date] = []
        for one in specs:
            seen = nth.get(one["channel"], 0)
            nth[one["channel"]] = seen + 1
            built[date].append(build_channel(world, day, one, seen))
        cast_of.update(p["id"] for s in specs for p in s["participants"])

    people = G.resolve_people(people_specs(world, cast_of), reset_pool=True)
    world.display.update({p["id"]: p["name"] for p in people})

    total = sum(len(built[d]) for d in days)
    turns = sum(c["max_turns"] for d in days for c in built[d])
    clues = sum(len(s.get("planted") or []) for d in days
                for s in world.day(d)["specs"] if not only or s["channel"] in only)
    rl.ok(f"{total} conversation(s), {turns} turns, {len(people)} people, "
          f"{clues} clue(s) to land")

    (out / "context.md").write_text(
        context_document(world, days, built), encoding="utf-8")
    rl.ok(f"{out / 'context.md'} — everything a model will be told")

    # Before anything is spent. A clue that cannot pass does not become able to
    # pass by being re-run, and the re-run is what costs.
    check_clues_runnable(world, days, only)

    if args.dry_run:
        rl.warn("--dry-run: nothing was simulated and nothing was spent")
        return 0

    return asyncio.run(_run(world, days, built, people, root, out, args))


async def _run(world, days, built, people, root: Path, out: Path, args) -> int:
    import bespoke_user as bu
    import bespoke_user.sim_engine as G

    bu.reset_cost_ledger()
    clock = wa.Clock()
    stores = _stores(world, out, clock)
    tools = G.attach_tools(stores, clock)

    # ONE prepared cast for the whole run: every day is the same people, and a
    # profiles file makes a run split across invocations draw the same voices.
    prepared = await G.build_cast(people, profiles_path=str(_cast_file(root)),
                                 world=world.company["company"].get("slug", "world"),
                                 quiet=args.verbose < 1)

    llm = rl.LLM(rl.DEFAULT_CACHE_DIR / "llm", model=rl.MODEL, effort="low",
                 backend="cli", verbose=args.verbose)

    clue_rows: list[dict] = []
    art_rows: list[dict] = []
    for n, date in enumerate(days, 1):
        channels = built[date]
        if not channels:
            continue
        base = dt.datetime.fromisoformat(date).replace(hour=DAY_OPEN_HOUR)
        end = dt.datetime.fromisoformat(date).replace(hour=18, minute=30)
        clock.set_day(base.replace(tzinfo=UTC))

        # The engine's message cap is ONE counter shared by every channel in
        # the run. At its default of 70 a six-channel day is decapitated
        # part-way through — unevenly, and with no warning.
        budget = sum(c["max_turns"] + _landing_extra(c) for c in channels)
        cap = max(70, len(channels) * 45, int(budget * 1.8))
        settings = G.SimSettings(
            max_total_messages=cap, day_start=8, day_end=19,
            timing=waking_hours(DAY_OPEN_HOUR),
            **({"turn_model": args.model} if args.model else {}))

        rl.heading(f"{date} — {len(channels)} conversation(s), "
                   f"{sum(c['max_turns'] for c in channels)} turns, cap {cap}")
        name = args.workspace or f"SWEWorld {world.company['company'].get('slug', '')}"
        # In batches, all stamped the same date. Five conversations at once is
        # fifteen live agent sessions plus a director call per turn, and the
        # answer to that was APITimeoutError on four of the five — which the
        # engine reports by skipping the channel, quietly, because a concurrent
        # run collects exceptions instead of raising them. `concurrent=False`
        # is not the alternative: it puts each channel on its own DAY, which
        # would scatter one day's conversations across a week.
        doc = None
        for group in _batches(channels, args.concurrency):
            part = await _one_day(G, name, n, group, prepared, tools, base, end,
                                  settings, out)
            if doc is None:
                doc = part
            else:
                _splice(doc, part, out / f"day-{n}.json")

        # A channel that timed out is absent from the transcript, not empty in
        # it, and the engine drops it without raising. Retry those on their own
        # before the clue gate sees the day — otherwise the gate blames the
        # personas for not saying something in a conversation that never ran.
        for attempt in range(2, 4):
            missing = [c for c in channels
                       if c["name"] not in {x.get("name") for x in
                                            (doc or {}).get("channels") or []}]
            if not missing:
                break
            rl.warn(f"{len(missing)} conversation(s) produced nothing "
                    f"({', '.join('#' + c['name'] for c in missing)}) — "
                    f"rerunning alone, attempt {attempt}")
            for one in missing:
                part = await _one_day(G, name, n, [one], prepared, tools, base,
                                      end, settings, out, tag=f" alone {attempt}")
                if doc is None:
                    doc = part
                else:
                    _splice(doc, part, out / f"day-{n}.json")
        _blank(doc, channels)

        art_rows += [{**r, "date": date} for c in channels
                     for r in G.artifact_audit(c, stores) if r["action"] != "read"]

        rows = _check_day(world, llm, date, channels, doc, attempt=1)
        # The documents and mail this day owed, checked the same way. A separate
        # haystack, folded into the same rows, because "did this clue land" is
        # one question and a reader should not have to look in two places.
        rows += _check_artifacts(world, llm, date, channels, stores, attempt=1)
        # Repair before re-running: what a thinned clue needs is one more
        # bubble, and re-simulating the day for it re-rolls every other clue in
        # the room that was already right.
        rows = _repair_day(world, llm, date, doc, out / f"day-{n}.json", rows,
                           args.clue_repairs)
        for attempt in range(2, args.clue_tries + 1):
            missing = [r for r in rows if not r["said"]]
            if not missing:
                break
            # An artifact clue drives a re-run exactly like a conversation one.
            # Writing the page IS part of the day: `member_grounding` rebuilds
            # the writer's agenda from the spec, so re-running the room gives
            # them another go at the document with the same instruction. The
            # earlier version excluded them on the grounds that re-running would
            # re-roll chat clues that had already passed — true, and not a
            # reason to leave a document wrong. The day is re-checked in full
            # afterwards, so a chat clue that regresses is caught and retried
            # like any other; what must not happen is a corpus that quietly
            # keeps a page missing the point it was written to carry.
            bad = {r["channel"] for r in missing}
            for r in missing:
                rl.warn(f"{r['clue']} in #{r['channel']} — still missing: "
                        + ("; ".join(r.get("missing") or []) or r.get("why", ""))[:150])
            rl.info(f"re-running {len(bad)} channel-day(s), attempt {attempt}/"
                    f"{args.clue_tries}")
            # A fresh cast for the retry, same people. These agents are
            # persistent sessions with memory, so reusing them would have the
            # personas recalling the attempt being replaced and referring back
            # to messages that no longer exist anywhere.
            retry = await G.build_cast(people, quiet=True,
                                       profiles_path=str(_cast_file(root)),
                                       world=world.company["company"].get("slug", "world"))
            redo = _corrective([c for c in channels if c["name"] in bad],
                               missing, world)
            fixed_doc = await _one_day(G, name, n, redo, retry, tools, base, end,
                                       settings, out, tag=f" retry {attempt}")
            _splice(doc, fixed_doc, out / f"day-{n}.json")
            # Everything in a re-run room is re-judged — the transcript AND the
            # documents that room owed. Checking only the transcript left the
            # stale artifact verdict in place, so a page rewritten correctly on
            # the retry would still be reported as missing its clue.
            rows = [r for r in rows if r["channel"] not in bad] + \
                _repair_day(world, llm, date, doc, out / f"day-{n}.json",
                            _check_day(world, llm, date, redo, doc,
                                       attempt=attempt),
                            args.clue_repairs) + \
                _check_artifacts(world, llm, date, redo, stores, attempt=attempt)
        clue_rows += rows

        rl.ok(f"{date}: {sum(1 for r in rows if r['said'])}/{len(rows)} clue(s) said")

    return _finish(world, root, out, clue_rows, art_rows, stores, args)


def _batches(channels: list, budget: int) -> list[list]:
    """Group a day's conversations so that only so many PEOPLE talk at once.

    The load is people, not conversations: each participant is a live agent
    session, so one five-person channel costs more than two two-person ones.
    Batching by channel count put ten sessions on four cores and the director's
    own call timed out waiting for a slice — which the engine reports by
    dropping the channel.

    A channel bigger than the whole budget still runs, alone: refusing it would
    silently delete the busiest conversations of the day.
    """
    budget = max(2, budget)
    out, group, load = [], [], 0
    for channel in sorted(channels, key=lambda c: -len(c["memberIds"])):
        size = len(channel["memberIds"])
        if group and load + size > budget:
            out.append(group)
            group, load = [], 0
        group.append(channel)
        load += size
    if group:
        out.append(group)
    return out


def _blank(doc, wanted: list[dict]) -> None:
    """Say which conversations produced nothing.

    A channel the engine gave up on is absent from the transcript rather than
    empty in it, and absent looks exactly like never-asked-for. Naming them is
    the difference between a short day and a broken one.
    """
    got = {c.get("name") for c in (doc or {}).get("channels") or []}
    for channel in wanted:
        if channel["name"] not in got:
            rl.warn(f"#{channel['name']} produced nothing — it failed and was "
                    "skipped, which the engine does quietly")


async def _one_day(G, name, n, channels, cast, tools, base, end, settings, out,
                   tag: str = ""):
    return await G.simulate(
        f"{name} Day {n}{tag}",
        [{k: v for k, v in c.items() if not k.startswith("_")} for c in channels],
        cast=cast, out_path=str(out / f"day-{n}{tag.replace(' ', '-')}.json"),
        tools=tools, concurrent=True, base=base, end=end, quiet=True,
        settings=settings)


def _landing_extra(channel: dict) -> int:
    """Turns a channel may spend past its budget landing what it still owes.

    Mirrors the engine's own arithmetic — one directed turn per must-raise
    item plus its retries, and a settle item gets more — so the message cap
    cannot be the thing that stops the turn meant to land a clue.
    """
    return sum(4 if item.get("must_settle") else 2
               for ctx in (channel.get("projectContext") or {}).values()
               for item in (ctx.get("agenda") or []) if item.get("must_raise"))


def _stores(world, out: Path, clock: wa.Clock) -> list:
    collections = {}
    for doc in world.artifacts["docs"]:
        collections.setdefault(doc.get("collection") or "engineering", "")
    domain = "world.local"
    return [
        wa.Wiki(out, clock, collections=collections,
                scrub=__import__("bespoke_user").scrub_prose),
        wa.Mail(out, clock, domain=domain,
                addresses={p: f"{p}@{domain}" for p in world.people}),
        wa.Forge(out, clock, items=world.forge),
    ]


def _planted_at(world, date: str, channel: str) -> list[dict]:
    return [p for s in world.day(date)["specs"] if s["channel"] == channel
            for p in (s.get("planted") or [])]


def _clue_row(world, llm, planted: dict, messages: list[dict], date: str,
              channel: str, attempt: int) -> dict:
    verdict = check_clue(llm, planted, messages, world)
    return {
        "clue": planted.get("clue", ""), "holder": planted.get("holder", ""),
        "date": date, "channel": channel, "attempt": attempt,
        "said": bool(verdict.get("carried")),
        "quote": verdict.get("quote", ""),
        "said_by": verdict.get("said_by", ""),
        "why": verdict.get("why", ""),
        "elements": verdict.get("elements") or [],
        "missing": verdict.get("missing") or [],
        "missing_verbatim": verdict.get("missing_verbatim") or [],
        "leaked": verdict.get("leaked") or [],
        "context": _around(messages, verdict.get("quote", ""), world),
    }


def _check_day(world, llm, date, channels, doc, attempt: int) -> list[dict]:
    rows = []
    for channel in channels:
        planted = _planted_at(world, date, channel["name"])
        if not planted:
            continue
        messages = transcript_of(doc, channel["name"])
        rows += [_clue_row(world, llm, one, messages, date, channel["name"],
                           attempt)
                 for one in planted]
    return rows


def _repair_day(world, llm, date, doc, path: Path, rows: list[dict],
                tries: int) -> list[dict]:
    """Add the missing beat to each thinned clue, in the transcript that exists.

    Between the gate and the re-run, because the two failures it sits between
    are not the same size. A clue nobody said needs the conversation held
    again; a clue said with its second half missing needs one more bubble, and
    re-simulating the day for that re-rolls every other clue in the room that
    was already right — a live run took three attempts on one clue and came
    back with a THINNER version of it each time.

    Repairs are recorded on the row, never silently: a transcript edited after
    the fact must be visible in the review document as an edit.
    """
    out = []
    for row in rows:
        if row["said"]:
            out.append(row)
            continue
        planted = next((p for p in _planted_at(world, date, row["channel"])
                        if p.get("clue") == row["clue"]), None)
        added: list[str] = []
        for attempt in range(1, tries + 1):
            if planted is None:
                break
            messages = transcript_of(doc, row["channel"])
            patch = repair_clue(llm, world, planted, row, messages, attempt)
            if not patch:
                break
            channel_of(doc, row["channel"])["messages"] = apply_repair(
                messages, patch, planted)
            path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
            added += patch["burst"]
            rl.info(f"{row['clue']}: repaired in place — "
                    + " / ".join(patch["burst"] or ["rewritten"])[:110])
            row = {**_clue_row(world, llm, planted,
                               transcript_of(doc, row["channel"]), date,
                               row["channel"], row["attempt"]),
                   "repair": {"attempts": attempt, "added": added,
                              "rewrote": bool(patch["rewrite"])}}
            if row["said"]:
                break
        out.append(row)
    return out


def _corrective(channels: list[dict], rows: list[dict], world) -> list[dict]:
    """The channels to re-run, each told what it did NOT get across last time.

    A retry that repeats the original instruction is the original attempt with
    a different random seed, which is what three tries bought before: two clues
    went to their third attempt having been asked the identical thing three
    times. The judge already says what is missing — putting that in front of
    the person who owes it is the whole difference between rolling again and
    correcting.

    It goes into `about`, because that is the field the engine renders into the
    prompt (`slack_prompts` reads `about`/`must_raise`/`must_settle` and nothing
    else). The channel dicts are rebuilt per attempt, so mutating this copy
    cannot leak into a later day.
    """
    gaps: dict[str, list[str]] = {}
    for row in rows:
        if row["said"]:
            continue
        # `why` when the judge named no parts. A miss with an empty list built
        # no key at all here, which left the retry prompt byte-identical to the
        # attempt it was replacing — the exact thing this function exists to
        # stop, hidden in the case nobody looked at.
        for gap in (row.get("missing") or [row.get("why", "")] or []):
            if gap:
                gaps.setdefault(
                    f"{row['channel']}|{row['holder']}|{row['clue']}",
                    []).append(gap)

    out = []
    for channel in channels:
        one = json.loads(json.dumps(channel))       # deep copy; agendas nest
        for persona, ctx in (one.get("projectContext") or {}).items():
            for item in ctx.get("agenda") or []:
                key = f"{one['name']}|{persona}|{item.get('leaf', '')}"
                if not item.get("must_settle") or key not in gaps:
                    continue
                item["about"] = (
                    item["about"] + "  — you talked around this last time "
                    "without ever getting it across. Still not said: "
                    + "; ".join(gaps[key]) + ". Say that part, plainly, in your "
                    "own words.")
        out.append(one)
    return out


def _around(messages: list[dict], quote: str, world, span: int = 2) -> list[str]:
    """The clue with its neighbours, so it can be read as conversation."""
    if not quote:
        return [f'{m["ts"][11:16]}  {m.get("userId", ""):9s} {m.get("text", "")[:90]}'
                for m in messages[:6]]
    hit = next((i for i, m in enumerate(messages)
                if quote[:40] and quote[:40] in (m.get("text") or "")), None)
    if hit is None:
        return []
    out = []
    for i in range(max(0, hit - span), min(len(messages), hit + span + 1)):
        m = messages[i]
        mark = "   <-- the clue" if i == hit else ""
        out.append(f'{m["ts"][11:16]}  {m.get("userId", ""):9s} '
                   f'{m.get("text", "")[:88]}{mark}')
    return out


def _splice(day_doc: dict, redo: dict, path: Path) -> None:
    """Fold the re-run channels in, keeping every other one exactly as it was.

    Replacing by name is not enough. A channel that FAILED on its first attempt
    is not in the day document at all, so a replace-only merge silently dropped
    every re-run of it — the conversation was generated, paid for and thrown
    away, and the clue gate then re-checked the same empty day and failed it
    again for three attempts. Anything not already there is appended.
    """
    have = {c.get("name"): i for i, c in enumerate(day_doc.get("channels") or [])}
    day_doc.setdefault("channels", [])
    for channel in redo.get("channels") or []:
        name = channel.get("name")
        if name in have:
            day_doc["channels"][have[name]] = channel
        else:
            day_doc["channels"].append(channel)
    seen = {u["id"] for u in day_doc.get("users") or []}
    for user in redo.get("users") or []:
        if user["id"] not in seen:
            day_doc.setdefault("users", []).append(user)
    path.write_text(json.dumps(day_doc, indent=2), encoding="utf-8")


def merge_days(out: Path, workspace: str) -> dict:
    """Fold every day into ONE transcript, and take the per-day parts away.

    Channels merge BY NAME, so #engineering reads as one continuous history
    across the run rather than as three separate workspaces somebody has to
    click between. Messages already carry their real dates, so concatenating
    and sorting is the whole job.

    A retry file is a duplicate of what was already spliced into its day, so it
    is skipped here and deleted with the rest — leaving it would put the same
    conversation in the corpus twice.
    """
    parts = sorted(p for p in out.glob("day-*.json"))
    existing = out / "transcript.json"
    if not parts:
        # Nothing new to fold. Returning {} here would let the caller render an
        # EMPTY transcript over a run that already holds days.
        return json.loads(existing.read_text(encoding="utf-8")) if existing.exists() else {}
    users: dict[str, dict] = {}
    channels: dict[str, dict] = {}

    # What this invocation is about to write. A run is built up in batches, and
    # this used to fold ONLY the day files it could see — every earlier batch
    # having already folded and deleted its own — so each batch overwrote the
    # transcript with just its own days and silently threw away every day before
    # it. Five days of corpus, gone, with the run reporting success.
    #
    # So the transcript already on disk is folded in first, minus any date this
    # invocation is re-simulating: a day that comes round again REPLACES its old
    # self rather than doubling it.
    fresh: set[str] = set()
    for path in parts:
        if "retry" in path.name or "alone" in path.name:
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        fresh |= {m["ts"][:10] for c in doc.get("channels") or []
                  for m in c.get("messages") or [] if m.get("ts")}
    if existing.exists():
        before = json.loads(existing.read_text(encoding="utf-8"))
        kept = 0
        for user in before.get("users") or []:
            users.setdefault(user["id"], user)
        for channel in before.get("channels") or []:
            older = [m for m in channel.get("messages") or []
                     if m.get("ts", "")[:10] not in fresh]
            kept += len(older)
            if older:
                into = channels.setdefault(
                    channel["name"], {**channel, "id": channel["name"], "messages": []})
                into["messages"] += older
        rl.info(f"  carried forward: {kept} message(s) from earlier batches")

    for path in parts:
        if "retry" in path.name or "alone" in path.name:
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        rl.info(f"  {path.name}: " + (", ".join(
            f"#{c['name']} {len(c.get('messages') or [])}"
            for c in doc.get("channels") or []) or "nothing"))
        for user in doc.get("users") or []:
            users.setdefault(user["id"], user)
        for channel in doc.get("channels") or []:
            name = channel["name"]
            into = channels.setdefault(
                name, {**channel, "id": name, "messages": []})
            into["messages"] += channel.get("messages") or []
            into["memberIds"] = sorted(set(into.get("memberIds") or [])
                                       | set(channel.get("memberIds") or []))
    for channel in channels.values():
        channel["messages"].sort(key=lambda m: m.get("ts") or "")

    merged = {"workspace": workspace, "users": list(users.values()),
              "channels": [channels[k] for k in sorted(channels)]}
    (out / "transcript.json").write_text(
        json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    if not merged["channels"]:
        rl.warn("the merge found no conversations in any day file; the per-day "
                "files are being kept so they can be looked at")
        return merged
    for path in parts:
        path.unlink()

    dates = sorted({m["ts"][:10] for c in merged["channels"]
                    for m in c["messages"]})
    total = sum(len(c["messages"]) for c in merged["channels"])
    rl.ok(f"{out / 'transcript.json'} — {len(merged['channels'])} channel(s), "
          f"{total} message(s), {dates[0] if dates else '?'} to "
          f"{dates[-1] if dates else '?'}, {len(parts)} day file(s) folded in "
          "and removed")
    return merged


def _specs_on(world, date: str) -> list[dict]:
    """That day's conversation specs, or none if the day never had a file."""
    try:
        return world.day(date)["specs"]
    except SystemExit:
        return []


def _day_slice(doc: dict, date: str) -> dict:
    """One day's messages, in the shape the gates already read.

    `transcript_of` wants a workspace, so an audit that replays a finished
    corpus hands it the same thing a live day would have: the channels, but
    holding only the messages stamped with this date.
    """
    return {"channels": [{**ch, "messages": [m for m in ch.get("messages") or []
                                             if str(m.get("ts", ""))[:10] == date]}
                         for ch in doc.get("channels") or []]}


def audit_corpus(world, root: Path, out: Path, args) -> int:
    """Re-judge a finished corpus from its own transcript. No simulation.

    The ledgers are written at the END of a run, after the render — so when one
    corrupt timestamp killed `render.render()`, `_finish` died before writing
    either of them, for every batch after it appeared. The transcript kept
    growing (it is written first) and the batch loop swallowed the exception,
    so 61 of 161 simulated days were never audited at all while the ledger they
    left behind still read as a complete 49/49.

    Nothing here needs the personas back: `check_clue` takes a plain list of
    messages, and the pages and mail are on disk. So the whole corpus can be
    re-judged for the price of the judge calls.
    """
    import bespoke_user.sim_engine as G
    import phase4_simulate as ps                       # see this module's note

    doc = json.loads((out / "transcript.json").read_text())
    dates = sorted({str(m.get("ts", ""))[:10]
                    for ch in doc.get("channels") or []
                    for m in ch.get("messages") or []} - {""})
    llm = rl.LLM(rl.DEFAULT_CACHE_DIR / "llm", model=rl.MODEL, effort="low",
                 backend="sdk", auth="api-key", verbose=args.verbose)

    # Every clue the plant put on a day this corpus actually simulated. The
    # denominator is the point: a ledger that counts only what it happened to
    # look at cannot tell you it looked at a third of the corpus.
    planned = [(d, s["channel"], p) for d in dates
               for s in world.day(d)["specs"] for p in (s.get("planted") or [])]
    stores = _stores(world, out, clock=wa.Clock())
    for store in stores:
        if hasattr(store, "rehydrate"):
            store.rehydrate()

    rl.heading(f"Auditing {len(dates)} simulated day(s) — "
               f"{len(planned)} planted clue(s), no simulation")

    clue_rows, art_rows = [], []
    for n, date in enumerate(dates, 1):
        day = _day_slice(doc, date)
        spoke = {ch["name"] for ch in day["channels"] if ch.get("messages")}
        # The obligations have to come along, not just the name: `artifact_audit`
        # reads them off the channel to know what the day OWED. A channel dict
        # carrying only a name audits cleanly against nothing and reports 0/0,
        # which is how a rewrite once replaced 120 artifact rows with none.
        channels = [{"name": s["channel"],
                     "obligations": ps.obligations_of(world, s)}
                    for s in _specs_on(world, date) if s["channel"] in spoke]
        if not channels:
            continue
        rows = _check_day(world, llm, date, channels, day, attempt=1)
        rows += _check_artifacts(world, llm, date, channels, stores, attempt=1)
        clue_rows += rows
        art_rows += [{**r, "date": date} for c in channels
                     for r in G.artifact_audit(c, stores) if r["action"] != "read"]
        if rows or n % 20 == 0:
            said = sum(1 for r in rows if r["said"])
            rl.info(f"{date}: {said}/{len(rows)} clue(s) said "
                    f"({n}/{len(dates)} days)")

    # A clue the audit never reached still needs a row, or the ledger counts
    # only what it happened to look at — which is how 49/49 came to describe a
    # third of the corpus. These are clues whose CARRIER was never written:
    # phase 3 seats some of its own pages and mail, and no day spec's
    # `goals[].writes[]` claims them, so nobody was ever asked to produce one.
    seen = {r["clue"] for r in clue_rows}
    for cid, where in sorted(_every_planted(world).items()):
        if cid in seen:
            continue
        clue_rows.append({
            "clue": cid, "holder": where.get("holder", ""),
            "date": where.get("date", ""), "channel": "",
            "wrote_into": where.get("where", ""),
            "artifact": where.get("where", "").split(":", 1)[-1], "attempt": 0,
            "said": False, "rendered": False, "quote": "", "said_by": "",
            "why": f"never rendered: the {where.get('kind', 'artifact')} it was "
                   f"planted in ({where.get('where', '?')}) was never written, "
                   "so there was nothing to judge",
            "elements": [], "missing": [], "missing_verbatim": [],
            "leaked": [], "context": "",
        })
    unrendered = [r for r in clue_rows if r.get("rendered") is False]
    if unrendered:
        rl.warn(f"{len(unrendered)} clue(s) were never rendered — their carrier "
                "was never written: " +
                ", ".join(sorted(r["clue"] for r in unrendered)))
    return _finish(world, root, out, clue_rows, art_rows, stores, args,
                   planted_total=len(_every_planted(world)), rewrite=True)


def _every_planted(world) -> dict[str, dict]:
    """Every clue the plant seated anywhere, by id.

    The specs are only one of four surfaces phase 3 uses. Counting just those
    is what made a ledger of 49 look complete beside a plant of 99.
    """
    out: dict[str, dict] = {}

    def take(items, kind, where, date=""):
        for p in items or []:
            cid = p.get("clue")
            if cid:
                out.setdefault(cid, {"kind": kind, "where": where, "date": date,
                                     "holder": p.get("holder", "")})

    for date in world.days:
        # `world.days` spans the calendar, not the days that got a spec file;
        # asking for one that has none is fatal, and a missing spec is simply
        # a day nothing was planted on.
        try:
            specs = world.day(date)["specs"]
        except SystemExit:
            continue
        for spec in specs:
            take(spec.get("planted"), "conversation",
                 f"#{spec.get('channel')}", date)
    for doc in world.artifacts["docs"]:
        take(doc.get("planted"), "page", f"page:{doc['id']}",
             doc.get("created_at", "")[:10])
    for thread in world.artifacts["threads"]:
        for msg in thread.get("messages") or []:
            take(msg.get("planted"), "mail", f"mail:{thread['id']}",
                 str(msg.get("date", ""))[:10])
    for com in world.artifacts.get("comments") or []:
        take(com.get("planted"), "comment", f"comment:{com['id']}",
             str(com.get("created_at", ""))[:10])
    return out


def _finish(world, root: Path, out: Path, clue_rows, art_rows, stores, args,
            planted_total: int | None = None, rewrite: bool = False) -> int:
    """Write everything a finished run owes: transcript, ledgers, reports.

    `planted_total` is how many clues the plant put on the days this run
    covered, which is not the same as how many it managed to judge — see the
    coverage warning below. `rewrite` replaces the ledgers instead of merging
    into them, which is what an audit of the whole corpus wants: a `_carry`
    merge is exactly what let a ledger covering 37 days go on reading as a
    complete account of 161.
    """
    import bespoke_user as bu

    # -- one transcript, then the shape the ingest reads --------------------
    # The ledgers below are EVIDENCE; this render is a projection of it. One
    # corrupt timestamp used to kill the render and take the artifact audit and
    # the clue ledger down with it — for fifteen batches, silently, while the
    # batch loop reported success. A projection failing must never cost us the
    # evidence, so it is contained here and re-raised at the very end.
    merged = merge_days(out, args.workspace or "SWEWorld")
    render_failed = None
    try:
        rows = render.render(merged) if merged else []
        size = render.write(rows, out / "messages.jsonl")
        rl.ok(f"{out / 'messages.jsonl'} ({rl.human_bytes(size)}) — {len(rows)} message(s)")
    except Exception as exc:                       # noqa: BLE001 - re-raised below
        render_failed, rows = exc, []
        rl.fail(f"render failed: {exc}")
        rl.warn("writing the ledgers anyway — they are the evidence, "
                "messages.jsonl is only a projection of it")

    # -- the wiki's own manifest, from the shelves that got used ------------
    for store in stores:
        if isinstance(store, wa.Wiki):
            shelves = store.manifest().count("- dir:")
            rl.ok(f"{store.docs / 'collections.yaml'} — {shelves} collection(s)")

    # -- did the planned artifacts get made? --------------------------------
    art_rows = art_rows if rewrite else _carry(
        out / "artifacts.json", art_rows,
        key=lambda r: (r["date"], r["by"], r["action"], r["title"]))
    if rewrite:
        rl.write_json(out / "artifacts.json", art_rows)
    made = sum(1 for r in art_rows if r["done"])
    (out / "artifact_audit.md").write_text(
        _artifact_report(art_rows), encoding="utf-8")
    rl.ok(f"{out / 'artifact_audit.md'} — {made}/{len(art_rows)} "
          "planned artifact(s) actually made")

    # -- every clue, one file each ------------------------------------------
    # Rebuilt from the rows every time, and anything in the directory that the
    # rows do not account for is deleted. A clue file is a claim about THIS
    # corpus; one left behind from a run of different days is a claim about a
    # conversation that is no longer anywhere, and it looks exactly like the
    # real ones. The index said six while the directory held eleven.
    clue_rows = clue_rows if rewrite else _carry(
        out / "clues.json", clue_rows, key=lambda r: r["clue"])
    if rewrite:
        rl.write_json(out / "clues.json", clue_rows)
    clues_dir = out / "clues"
    clues_dir.mkdir(parents=True, exist_ok=True)
    keep = {"index.md"}
    for row in clue_rows:
        keep.add(f"{row['clue']}.md")
        (clues_dir / f"{row['clue']}.md").write_text(
            clue_report(world, row, out), encoding="utf-8")
    (clues_dir / "index.md").write_text(clue_index(world, clue_rows),
                                        encoding="utf-8")
    for stale in clues_dir.glob("*.md"):
        if stale.name not in keep:
            stale.unlink()
            rl.warn(f"removed {stale.name} — no clue in this run accounts for it")
    lost = [r for r in clue_rows if not r["said"]]
    rl.ok(f"{clues_dir}/ — {len(clue_rows) - len(lost)}/{len(clue_rows)} clue(s) "
          "said, one file each")
    # Said-out-of-judged is a ratio that flatters: it can read 49/49 while
    # saying nothing about the 58 clues nobody looked at. Report the plant's
    # own total whenever we know it, and shout when the two disagree.
    if planted_total is not None and planted_total != len(clue_rows):
        rl.warn(f"COVERAGE: {len(clue_rows)} of {planted_total} planted clue(s) "
                f"were judged — {planted_total - len(clue_rows)} were not "
                "looked at, so this ledger is not an account of the whole corpus")
    elif planted_total is not None:
        rl.ok(f"coverage: every one of {planted_total} planted clue(s) was judged")

    # Split, because the total is misleading. The persona turns are the bulk
    # of the tokens and they run on the subscription, but the ledger prices
    # every row at API rates — so the grand total reads like a bill and mostly
    # is not one. Only the one-shots (director, landing judge, annotator) go
    # through the API key, and those are Haiku.
    ONESHOT = ("director", "landing", "annotate")
    billed = [r for r in bu.COST_LEDGER
              if any(str(r.get("label", "")).startswith(x) for x in ONESHOT)]
    agents = [r for r in bu.COST_LEDGER if r not in billed]
    api = sum(r.get("cost", 0) for r in billed)
    sub = sum(r.get("cost", 0) for r in agents)
    rl.info(f"{len(bu.COST_LEDGER)} model call(s): "
            f"{len(billed)} on the API key (${api:.2f} — director, landing, "
            f"annotator, all Haiku) and {len(agents)} persona turn(s) on the "
            f"OAuth subscription (${sub:.2f} at API rates, not billed)")

    # The voices this run drew, kept beside its output so the run is readable
    # on its own even though the file itself is shared (see `_cast_file`).
    cast = _cast_file(root)
    if cast.exists():
        shutil.copy2(cast, out / "cast.json")

    (out / "run.json").write_text(json.dumps({
        "run": out.name,
        "days": sorted({r["date"] for r in clue_rows}
                       | {r["date"] for r in art_rows}) or None,
        "channels": sorted({c["name"] for c in merged.get("channels") or []}),
        "messages": len(rows),
        "clues": {"said": len(clue_rows) - len(lost), "of": len(clue_rows)},
        "artifacts": {"made": made, "of": len(art_rows)},
        "args": {k: str(v) for k, v in sorted(vars(args).items())},
    }, indent=2), encoding="utf-8")

    if render_failed is not None:
        raise RuntimeError(
            "the ledgers were written, but messages.jsonl was not — "
            f"re-render once the transcript is fixed: {render_failed}"
        ) from render_failed

    if args.install:
        _install(out)

    if lost:
        for row in lost:
            rl.warn(f"{row['clue']} ({row['holder']}, #{row['channel']} "
                    f"{row['date']}): {row['why'][:90]}")
        rl.fail(f"{len(lost)} planted clue(s) never got said. A clue nobody "
                "carries is a requirement the corpus cannot teach, so the task "
                "would be unscoreable. The transcripts are still on disk and "
                f"still worth reading — see {clues_dir}/index.md.")
    return 0


def _carry(path: Path, rows: list[dict], key) -> list[dict]:
    """This invocation's rows, plus whatever an earlier one in the SAME run left.

    A split run — `--run feb --days 2025-02-21`, then the same `--run` for the
    rest — only ever checks the days it was asked for, so writing the reports
    from those rows alone would replace February's findings with Thursday's.
    Persisting the rows makes the reports describe the whole run, which is the
    only thing anyone wants to read.

    New rows win on collision: a re-check of a day is a correction of it, not a
    duplicate. And this is the ONLY way anything from before this invocation
    survives — the run directory is otherwise built from what just happened, so
    a report can no longer inherit a claim about a conversation nobody kept.
    """
    prior = []
    if path.exists():
        try:
            prior = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            rl.warn(f"{path} is not readable JSON; starting its history over")
    fresh = {key(r) for r in rows}
    out = [r for r in prior if key(r) not in fresh] + list(rows)
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


# =============================================================================
# Is the corpus that now EXISTS still solvable?
# =============================================================================
def _spoken_clue(doc: dict, clue: dict, holder: str) -> dict | None:
    """What somebody actually said for this clue, if its day has been run.

    Matched by room and date rather than by content, because content is the one
    thing that changed: the persona reworded it, which is the whole point of
    letting them speak. If the day was simulated and the room has messages, the
    holder's words from it ARE the clue as the corpus now carries it.
    """
    where = clue.get("carrier") or {}
    date, room = where.get("date"), where.get("channel")
    if not date or not room:
        return None
    said = [m.get("text", "") for m in transcript_of(doc, room)
            if m.get("ts", "")[:10] == date and m.get("userId") == holder]
    if not said:
        return None
    return {"text": " ".join(said), "holder": holder, "date": date,
            "room": "#" + room}


def prove_corpus(world, out: Path, args) -> int:
    """Re-run phase 3's solvability proof against what the personas really said.

    Phase 3 proved each requirement recoverable from the clue text it WROTE.
    Nobody has ever asked whether it is still recoverable from what was
    SAID — and between those two sits every rewording a persona made in their
    own voice, which is exactly the freedom this gate was loosened to allow. A
    fact phase 3 recovered and this pass misses is a fact the corpus lost in
    translation, and nothing else in the pipeline is looking for it.

    Run over the whole corpus rather than one run's days: a requirement's clues
    span four to six months, so no three-day slice can prove one by itself.
    Every remark is labelled spoken or planned, and the tally is reported, so a
    verdict is never mistaken for more evidence than it rests on.
    """
    import phase3_plant as p3

    doc = {}
    path = out / "transcript.json"
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
    else:
        rl.warn(f"{path} does not exist yet — proving against planned text "
                "only, which is what phase 3 already did")

    llm = rl.LLM(rl.DEFAULT_CACHE_DIR / "llm", model=rl.MODEL, effort="low",
                 backend="cli", verbose=args.verbose)

    rows, gone = [], 0
    for task in world.clues.get("tasks") or []:
        for req in task["requirements"]:
            remarks, spoken = [], 0
            for clue in req["clues"]:
                if clue.get("kind") == "herring":
                    continue
                real = _spoken_clue(doc, clue, clue.get("holder", ""))
                if real:
                    spoken += 1
                    remarks.append(real)
                else:
                    where = clue.get("carrier") or {}
                    remarks.append({"text": clue["text"],
                                    "holder": clue.get("holder", ""),
                                    "date": where.get("date", ""),
                                    "room": where.get("room", "")})
            rl.info(f"{req['req_id']}: {len(remarks)} remark(s), {spoken} spoken, "
                    f"{len(remarks) - spoken} still planned")
            proof = p3.prove_solvable(llm, task, req["requirement"], req["req_id"],
                                      remarks, rounds=3, label="spoken")
            was = ((req.get("solvability") or {}).get("clues_only") or {})
            slipped = [f for f in proof["missed"] if f in (was.get("recovered") or [])]
            # A fact can only have been lost to REWORDING if some of the words
            # changed. With nothing spoken this pass re-read the very text
            # phase 3 read, so a disagreement is the reconstruction sampling
            # differently — which is the variance `vote` exists to smooth and
            # does not fully remove. Calling that a regression would fail the
            # run for the corpus being unchanged.
            lost = slipped if spoken else []
            fragile = slipped if not spoken else []
            gone += len(lost)
            rows.append({"req": req["req_id"], "task": task["task_id"],
                         "title": task["title"], "spoken": spoken,
                         "planned": len(remarks) - spoken, **proof,
                         "was_recovered": was.get("recovered") or [],
                         "lost": lost, "fragile": fragile})
            if lost:
                rl.warn(f"{req['req_id']}: no longer recoverable — "
                        f"{', '.join(lost)}")
            elif fragile:
                # Still worth saying. Phase 3 recovered it from this same text
                # and this reading did not, so the corpus carries it faintly
                # enough that which reader you ask decides the answer. Not a
                # failure — a thin place to thicken before it is spoken.
                rl.warn(f"{req['req_id']}: {', '.join(fragile)} recovered by "
                        "phase 3 but not by this reading, from the SAME text "
                        "(nothing spoken yet) — carried faintly")
            else:
                rl.ok(f"{req['req_id']}: {len(proof['recovered'])} fact(s) "
                      "recovered")

    (out / "solvability.md").write_text(_solvability_report(rows), encoding="utf-8")
    rl.ok(f"{out / 'solvability.md'} — {len(rows)} requirement(s) re-proved")
    if gone:
        rl.fail(f"{gone} fact(s) that phase 3 could recover from the planned "
                "clues cannot be recovered from what was actually said. The "
                "corpus no longer teaches them, so the tasks that need them "
                "cannot be scored.")
    return 0


def _solvability_report(rows: list[dict]) -> str:
    L = ["# Phase 4: is the corpus that exists still solvable?", "",
         "Phase 3 proved each hidden requirement recoverable from the clue text "
         "it wrote. This asks the same question of what the personas actually "
         "said, in their own words. A fact in the **lost** column is one the "
         "rewording cost: the corpus can no longer teach it, and the task that "
         "needs it cannot be scored.", "",
         "`spoken` counts clues whose day has been simulated; `planned` counts "
         "those still standing in as phase 3 wrote them. A requirement's clues "
         "span months, so a short run leaves most of them planned — read a "
         "verdict against its own mix.", "",
         "A fact is only **lost** when this requirement had something spoken. "
         "Where nothing has been simulated yet the remarks are phase 3's own "
         "words unchanged, so a disagreement there is the reconstruction "
         "sampling differently, not the corpus losing anything — those are "
         "listed as **faint** instead: real, but carried thinly enough that "
         "which reader you ask decides the answer.", "",
         "| requirement | task | spoken | planned | recovered | missed | lost | faint |",
         "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['req']} | {r['task']} | {r['spoken']} | {r['planned']} "
                 f"| {', '.join(r['recovered']) or '—'} "
                 f"| {', '.join(r['missed']) or '—'} "
                 f"| {'**' + ', '.join(r['lost']) + '**' if r['lost'] else '—'} "
                 f"| {', '.join(r.get('fragile') or []) or '—'} |")
    for r in rows:
        L += ["", "-" * 70, "", f"## {r['req']} — {r['title']}", "",
              f"    spoken   {r['spoken']}", f"    planned  {r['planned']}",
              f"    votes    " + ", ".join(f"{f}:{n}/{r['rounds']}"
                                           for f, n in r["votes"].items()), ""]
        if r["unsteady"]:
            L += [f"> Unsteady across readings: {', '.join(r['unsteady'])}. "
                  "Carried by something the corpus states only faintly.", ""]
        L += ["### What a reader reconstructs", "",
              "> " + (r.get("reconstruction") or "(nothing)").replace("\n", "\n> "),
              "", "### Constraints they come away with", ""]
        L += [f"- {c}" for c in (r.get("constraints") or [])] or ["- (none)"]
        L += ["", "### How the grader scored it", "", r.get("notes") or "—", ""]
    return "\n".join(L) + "\n"


def _artifact_report(rows: list[dict]) -> str:
    done = sum(1 for r in rows if r["done"])
    L = ["# Phase 4: did the planned artifacts get made?", "",
         f"{done} of {len(rows)} obligations met.", "",
         "An obligation is discharged by the artifact EXISTING, checked against "
         "what the store holds. Someone who says they wrote it and did not "
         "still shows as a miss, which is why this is separate from whether "
         "they said they would.", ""]
    if not rows:
        return "\n".join(L + ["No conversation in this run planned one.", ""])
    missed = [r for r in rows if not r["done"]]
    if missed:
        L += ["## Never made", "", "| date | who | action | artifact |",
              "|---|---|---|---|"]
        L += [f"| {r['date']} | {r['by']} | {r['action']} | {r['title']} |"
              for r in missed]
        L.append("")
    L += ["## Everything", "", "| date | who | action | made | artifact |",
          "|---|---|---|---|---|"]
    L += [f"| {r['date']} | {r['by']} | {r['action']} | "
          f"{r['at'][11:16] if r['done'] else 'NO'} | {r['title']} |" for r in rows]
    return "\n".join(L) + "\n"


def _install(out: Path) -> None:
    """Copy the result into data/, where the ingest scripts read from."""
    data = rl.REPO_ROOT / "data"
    for name in ("docs", "emails"):
        src, dst = out / name, data / name
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    for name in ("messages.jsonl", "comments.jsonl"):
        src = out / name
        if src.exists():
            shutil.copy2(src, data / name)
    rl.ok(f"installed into {data}/ — run the ingest scripts, or make bake-image")
