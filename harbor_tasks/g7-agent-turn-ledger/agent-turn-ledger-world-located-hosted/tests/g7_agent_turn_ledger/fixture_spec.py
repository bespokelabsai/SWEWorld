"""g7 — the INPUTS of one grading run, derived from the seed root chose.

Stdlib only, and imported by both sides: the worker gets it in the jail (it has
to build the scenarios), the judge gets it beside `judge.py` (it has to know what
was asked in order to work out what the answer should have been). One
derivation, so the two cannot drift.

WHY A SEED AT ALL. The worker/judge split stopped the worker rewriting the
verdict; it did not stop the worker inventing the values the judge reads. With
the old fixed fixture every value was the same every run — the two agent names,
the byte counts of the checkpoint they are spelled into, a dozen `is_completed`
booleans — so an observations file captured from one correct run, or a file of
constant booleans, passed facts on a tree that implemented nothing. Measured on
the pre-seed suite: a replayed oracle capture scored 1.0 on all eight hidden
facts, and a constant file of booleans passed r2.scope and r2.failure_behavior.

WHAT MAY NOT LIVE HERE. Expected outputs, and the answers the hidden
requirements fix: the checkpoint's file name, its version, its key set and
spelling, the status and completion-reason words, and the completion token. The
candidate replies below are RECIPES — a kind and some random text — that the
worker renders with whatever token it discovered in the submission and the judge
renders with the one the requirement names. So the order and the shape of the
list move every run, and which of them should complete is known only to a
process that holds the token and the matching rule.

Names are drawn at variable width on purpose: they are spelled into the
checkpoint, so its byte count moves with them. A fixed-width draw would leave
every size where it was, and a size captured from one run would fit the next
(see tasks/lessons.md, 2026-09-14: "randomising an input that does not change
the answer is decoration").
"""
from __future__ import annotations

import json
import random

# The log file is part of the openly stated feature, not a hidden answer.
LOG = "responses_0.jsonl"

# The clock `now_fn` is pinned to, in the form a hand-written log line carries.
CLOCK_ISO = "2025-01-02T03:04:05"

_ALPHABET = "abcdefghijkmnpqrstuvwxyz"
# Names a conversation role could plausibly be keyed on; a drawn agent name that
# collided with one would grade the fixture, not the submission.
_RESERVED = {"user", "assistant", "system", "seed", "tool", "developer", "function",
             "response", "nobody", "none", "null", "true", "false"}

# Only these three: they are what "trailing whitespace" means in the ticket, and
# a wider set (form feed, NBSP) would grade `str.rstrip()`'s Unicode table
# rather than the requirement.
_WHITESPACE = " \t\n"


def _word(rnd: random.Random, lo: int = 3, hi: int = 9) -> str:
    return "".join(rnd.choice(_ALPHABET) for _ in range(rnd.randint(lo, hi)))


def _name(rnd: random.Random, taken=()) -> str:
    while True:
        name = _word(rnd, 4, 11)
        if name not in _RESERVED and name not in taken:
            return name


def _text(rnd: random.Random) -> str:
    return " ".join(_word(rnd) for _ in range(rnd.randint(1, 4)))


def _ws(rnd: random.Random, lo: int = 1) -> str:
    return "".join(rnd.choice(_WHITESPACE) for _ in range(rnd.randint(lo, 4)))


# ---------------------------------------------------------------------------
# candidate replies for `Agent.is_completed`
# ---------------------------------------------------------------------------
def _recipe(rnd: random.Random, kind: str) -> list:
    """[kind, params]: everything a rendering needs except the token."""
    params: dict = {}
    if kind in ("tail", "glued", "plain", "chopped", "head", "punct", "middle",
                "tail_ws", "case", "dict"):
        params["text"] = _text(rnd)
    if kind == "middle":
        params["more"] = _text(rnd)
    if kind == "head":
        params["more"] = _text(rnd)
    if kind in ("tail_ws", "exact_ws"):
        params["ws"] = _ws(rnd)
    if kind == "case":
        params["ws"] = _ws(rnd, lo=0)
        params["flips"] = rnd.randrange(1 << 30)
    if kind == "punct":
        params["mark"] = rnd.choice(".!?;")
    if kind == "int":
        params["value"] = rnd.randint(-10_000, 10_000)
    if kind == "float":
        params["value"] = round(rnd.uniform(-1000, 1000), 3)
    if kind == "bool":
        params["value"] = rnd.random() < 0.5
    return [kind, params]


def _family(rnd: random.Random, required, optional, lo: int, hi: int) -> list:
    kinds = list(required)
    kinds += [rnd.choice(optional) for _ in range(rnd.randint(lo, hi) - len(kinds))]
    rnd.shuffle(kinds)
    return [_recipe(rnd, kind) for kind in kinds]


def _flip_case(token: str, flips: int) -> str:
    """Swap the case of a non-empty random subset of the token's letters."""
    letters = [i for i, ch in enumerate(token) if ch.isalpha()]
    if not letters:
        return token
    rnd = random.Random(flips)
    chosen = set(rnd.sample(letters, rnd.randint(1, len(letters))))
    return "".join(ch.swapcase() if i in chosen else ch for i, ch in enumerate(token))


def render(recipe, token: str):
    """The value one recipe stands for, given a completion token."""
    kind, p = recipe
    if kind == "exact":
        return token
    if kind == "exact_ws":
        return f"{token}{p['ws']}"
    if kind == "tail":
        return f"{p['text']} {token}"
    if kind == "tail_ws":
        return f"{p['text']} {token}{p['ws']}"
    if kind == "glued":
        return f"{p['text']}{token}"
    if kind == "plain":
        return p["text"]
    if kind == "head":
        return f"{token} {p['more']}"
    if kind == "middle":
        return f"{p['text']} {token} {p['more']}"
    if kind == "case":
        return f"{p['text']} {_flip_case(token, p['flips'])}{p['ws']}"
    if kind == "chopped":
        return f"{p['text']} {token[:-1]}"
    if kind == "punct":
        return f"{p['text']} {token}{p['mark']}"
    if kind == "dict":
        return {"text": f"{p['text']} {token}"}
    if kind == "list":
        return [token]
    if kind == "tuple":
        return (token,)
    if kind == "none":
        return None
    if kind in ("int", "float", "bool"):
        return p["value"]
    raise ValueError(f"unknown recipe kind {kind!r}")


# ---------------------------------------------------------------------------
# a hand-written log, byte for byte
# ---------------------------------------------------------------------------
def alternating(seeder: str, partner: str, contents) -> list:
    """(author, content) rows that take turns, the seeder first."""
    return [[seeder if i % 2 == 0 else partner, c] for i, c in enumerate(contents)]


def log_text(rows) -> str:
    """The exact text `probe_support.write_log` puts on disk for these rows.

    Shared so the judge can compare the log a scenario left behind against the
    bytes that were planted, rather than asking the worker whether it changed.
    """
    out = []
    for index, (author, content) in enumerate(rows):
        record = {
            "name": author,
            "response_message": content,
            "parsed_response_message": None,
            "response_errors": None,
            "raw_response": None,
            "raw_request": None,
            "generic_request": {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": content}],
                "response_format": None,
                "original_row": {"prompt": content},
                "original_row_idx": 0,
                "generation_params": {},
                "is_multimodal_prompt": False,
            },
            "created_at": CLOCK_ISO,
            "finished_at": CLOCK_ISO,
            "token_usage": None,
            "response_cost": 0.0 if index == 0 else 0.001,
            "finish_reason": "seed" if index == 0 else "stop",
        }
        out.append(json.dumps(record) + "\n")
    return "".join(out)


def derive(seed: str) -> dict:
    """Every input this run uses, as a plain dict. Same seed, same dict."""
    rnd = random.Random(seed)
    seeder = _name(rnd)
    partner = _name(rnd, taken={seeder})

    def lines(lo=2, hi=7):
        return [_text(rnd) for _ in range(rnd.randint(lo, hi))]

    spec: dict = {"seed": seed, "seeder": seeder, "partner": partner}

    # --- r1.rule: a run that dies on call `die_on` has appended die_on - 1
    # responses; the budget is left above that so the checkpoint is mid-run.
    spec["rule_die_on"] = rnd.randint(2, 6)
    spec["rule_max_length"] = spec["rule_die_on"] + rnd.randint(0, 3)

    # --- r1.scope: a hand-written log, and a checkpoint that agrees with it on
    # the two compared values and lies about every other one.
    spec["scope_contents"] = lines(2, 8)
    spec["scope_lies"] = {
        "turns": rnd.randint(20, 99),
        "next_speaker": _name(rnd, taken={seeder, partner}),
        "interleave_faults": rnd.randint(1, 9),
        "completed": True,
        "completion_reason": _word(rnd, 5, 10),
    }
    spec["scope_fresh_max_length"] = rnd.randint(2, 6)

    # --- r1.failure_behavior: the three arms against one hand-written log.
    spec["fail_contents"] = lines(2, 7)
    n_responses = len(spec["fail_contents"]) - 1
    spec["fail_garbage"] = "{" + _text(rnd)
    spec["fail_old_bump"] = rnd.choice([-1, 1]) * rnd.randint(1, 5)
    spec["fail_recorded_responses"] = rnd.choice(
        [r for r in range(0, 12) if r != n_responses])
    spec["fail_run_max_length"] = len(spec["fail_contents"]) + rnd.randint(2, 4)

    # --- r1.observability: the first write, the last write, a truncation behind
    # the checkpoint's back, and an older-version checkpoint.
    spec["obs_opening_max_length"] = rnd.randint(2, 5)
    spec["obs_marker"] = _word(rnd, 4, 8).upper()
    k = rnd.randint(2, 5)
    spec["obs_done_replies"] = [_text(rnd) for _ in range(k - 1)] + [
        f"{_text(rnd)} {spec['obs_marker']}"]
    spec["obs_done_max_length"] = k + rnd.randint(1, 3)
    spec["obs_truncate_to"] = rnd.randint(2, k)          # lines kept, < k + 1
    spec["obs_resume_reply"] = f"{_text(rnd)} {spec['obs_marker']}"
    spec["obs_older_contents"] = lines(2, 7)
    spec["obs_older_bump"] = rnd.choice([-1, 1]) * rnd.randint(1, 5)

    # --- r2: three shuffled candidate lists, and one conversation.
    spec["r2_rule"] = _family(rnd, ("exact", "tail", "plain"),
                              ("exact", "tail", "glued", "plain"), 10, 16)
    spec["r2_scope"] = _family(rnd, ("tail_ws", "exact_ws", "head", "case", "tail"),
                               ("tail_ws", "exact_ws", "head", "middle", "case",
                                "chopped", "punct", "plain", "tail"), 12, 18)
    spec["r2_fail"] = _family(rnd, ("dict", "none", "list", "int", "tail", "exact"),
                              ("dict", "none", "list", "tuple", "int", "float", "bool",
                               "tail", "tail_ws"), 10, 16)
    k2 = rnd.randint(2, 5)
    spec["r2_obs_replies"] = [_text(rnd) for _ in range(k2 - 1)]
    spec["r2_obs_last_text"] = _text(rnd)
    spec["r2_obs_max_length"] = k2 + rnd.randint(1, 3)
    return spec
