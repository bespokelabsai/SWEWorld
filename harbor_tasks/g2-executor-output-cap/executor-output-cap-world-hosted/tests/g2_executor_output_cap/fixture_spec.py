"""g2 — the INPUTS of one grading run, derived from the seed root chose.

Stdlib only, and imported by both sides: the worker gets it in the jail (it has
to build the scenarios), the judge gets it beside `judge.py` (it has to know
what was asked in order to work out what the answer should have been). One
derivation, so the two cannot drift.

WHY A SEED AT ALL. The worker/judge split stopped the worker rewriting the
verdict; it did not stop the worker inventing the values the judge reads. With a
fixed fixture those values never change — g2's were `"A" * 300` under a 64-byte
budget, every run — and the answers they imply are written down in the world the
agent is told to read: the marker spelling, the 3:1 split, the floor of 16, the
warning template. So a tree that implements nothing could hand back an
`observations.json` full of the values a correct run produced last time (an
`atexit` hook in `bespokelabs/curator/__init__.py` is enough; the same forgery
was measured at reward 1.0 on g1). Re-drawing the budgets, the payloads, the
exit code and the timeout every run means those values are not knowable in
advance: the only way to produce them is to run code that really caps.

WHAT MAY NOT LIVE HERE. Expected outputs, and anything an expected output can be
computed from. The cut itself is the sharp case: this file says a stream is
`over_stdout` bytes long under a budget of `budget`, and never where that stream
is cut, what the marker between the halves reads, or that a head and a tail are
kept at all. `judge.py` owns the rule and prices every scenario with it.

THE INPUTS THAT CANNOT BE RE-DRAWN are the requirement itself — the floor of 16,
the default of 65536, the marker and the log template. They stay in `judge.py`,
which the worker cannot read, and the probe reports what the submission believes
instead of being handed the right answer: the run that proves the floor is
accepted is made with the `MIN_MAX_OUTPUT_BYTES` the submission itself exports.
The budgets below the floor are drawn from 1..15, which is where they have always
come from; a worker learns nothing from them that the old probe did not say out
loud.

The payloads are deliberately NOT runs of one repeated character. `"A" * 300`
cannot tell a head-and-tail keep from a single 64-byte slice — both come back as
a run of A's — so the two long ASCII payloads are random letters, and the
multi-byte one mixes 2-, 3- and 4-byte codepoints so that a cut lands inside a
character on most seeds.
"""
from __future__ import annotations

import random

# Look-alike characters are out: these strings end up in the failure message a
# human reads when a run goes wrong, and an l/1 mix-up there costs an hour.
_LETTERS = "abcdefghijkmnpqrstuvwxyzACDEFGHJKLMNPQRSTUVWXYZ23456789"
# 2, 3 and 4 UTF-8 bytes apiece, so a byte cut lands mid-character on most
# seeds and the codepoint-boundary rule is really exercised.
_WIDE = "éλ€漢Ж\U0001f600\U0001f9eaअ"


def _token(rnd: random.Random, n: int = 4) -> str:
    return "".join(rnd.choice(_LETTERS) for _ in range(n))


def _text(rnd: random.Random, n: int) -> str:
    """`n` ASCII characters, hence `n` bytes: the budget arithmetic is in bytes."""
    return "".join(rnd.choice(_LETTERS) for _ in range(n))


def _wide(rnd: random.Random, n: int) -> str:
    return "".join(rnd.choice(_WIDE) for _ in range(n))


def derive(seed: str) -> dict:
    """Every input this run uses, as a plain dict. Same seed, same dict."""
    rnd = random.Random(seed)
    tok = _token(rnd)

    # The main budget. Any value at or above the floor works; kept off the
    # multiples of four so the head/tail arithmetic has a remainder to lose.
    budget = rnd.randrange(41, 121, 2)
    # A second, tighter budget for the same payload: one run's plan cannot be
    # replayed as the other's.
    narrow = rnd.randrange(17, budget - 12, 2)

    spec: dict = {
        "seed": seed,
        "token": tok,
        "budget": budget,
        "narrow_budget": narrow,

        # The budget handed to the backends through `backend_params`, well clear
        # of `budget` so a confusion between the two shows up.
        "plumb_budget": rnd.randrange(200, 641, 8),

        # Two long ASCII payloads, random so a head-and-tail keep is visible in
        # the result and a single slice is not mistaken for one.
        "over_stdout": _text(rnd, rnd.randint(260, 420)),
        "over_stderr": _text(rnd, rnd.randint(260, 420)),

        # A stream comfortably inside the budget, and one exactly at it.
        "under": _text(rnd, rnd.randint(8, budget - 8)),
        "exact": _text(rnd, budget),

        # The unlimited (budget 0) scenario: both streams come back whole.
        "unlimited_stdout": _text(rnd, rnd.randint(300, 520)),
        "unlimited_stderr": _text(rnd, rnd.randint(300, 520)),

        # The archive `_collect_sandbox_files` hands back. The long one is far
        # over every budget here, which is the point: `files` is never capped.
        "files": f"files-{tok}",
        "files_big": f"archive-{tok}-" + _text(rnd, rnd.randint(3000, 5000)),

        # A non-zero exit that is not the timeout's 124, and the seconds the
        # timeout message reports.
        "exit_code": rnd.choice([1, 2, 3, 5, 7, 9, 42, 77]),
        "timeout_secs": rnd.randint(3, 29),
        # A direct `_format_exit_code_error(code, stderr)` call.
        "fmt_exit_code": rnd.choice([1, 4, 8, 13, 64]),
        "fmt_stderr": _text(rnd, rnd.randint(4, 12)),

        # r1 rule: one payload, two budgets.
        "rule_payload": _text(rnd, rnd.randint(2 * budget, 3 * budget)),

        # r1 scope: mixed-width UTF-8 under four consecutive budgets, so at
        # least one of them cuts inside a character however the seed fell.
        "wide_payload": _wide(rnd, rnd.randint(40, 70)),

        # r1 failure behavior: budgets the floor refuses, and a negative one the
        # `ge=0` bound refuses first.
        "sub_floor": sorted(rnd.sample(range(1, 16), 3)),
        "refused_budget": rnd.randint(1, 15),
        "factory_bad": rnd.randint(1, 15),
        "negative": -rnd.randint(1, 9),

        # r2: the exception text an `__exit__` raises, long enough to be cut and
        # short enough elsewhere to be left alone.
        "exc_text": _text(rnd, rnd.randint(180, 320)),
        "exc_short": f"boom-{tok}",
        "exc_budget": rnd.randrange(17, 49, 2),
        # The stderr of a non-zero exit, on the path whose assembled message is
        # NOT re-capped.
        "exit_stderr": _text(rnd, rnd.randint(120, 260)),
        # Over `budget`, but by little: the assembled exit-code message then runs
        # well past the budget and must still come back at its full length.
        "exit_stderr_short": _text(rnd, budget + rnd.randint(8, 40)),
    }

    # Four consecutive budgets for the multi-byte payload. Consecutive on
    # purpose: whatever the seed, they do not all cut a character the same way.
    first_wide = rnd.randrange(20, 61)
    spec["wide_budgets"] = [first_wide, first_wide + 1, first_wide + 2, first_wide + 3]
    return spec
