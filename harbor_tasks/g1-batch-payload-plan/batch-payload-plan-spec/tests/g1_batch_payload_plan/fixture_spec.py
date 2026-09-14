"""g1 — the INPUTS of one grading run, derived from the seed root chose.

Stdlib only, and imported by both sides: the worker gets it in the jail (it has
to build the scenarios), the judge gets it beside `judge.py` (it has to know what
was asked in order to work out what the answer should have been). One derivation,
so the two cannot drift.

WHY A SEED AT ALL. The worker/judge split stopped the worker rewriting the
verdict; it did not stop the worker inventing the values the judge reads. With a
fixed fixture those values never change, and g1's are published in the world the
agent is told to read — `batch_plan.json`, the 512 cap, "sha256 … first twelve
hex", `{"num_jobs": n}` — so a tree that implements nothing can hardcode a
passing `observations.json`. Measured: reward 1.0 from pristine `main` plus one
`atexit` hook. Re-drawing the inputs every run means the answers are not
knowable in advance, and the only way to produce them is to run an
implementation that actually works.

WHAT MAY NOT LIVE HERE. Expected outputs, and anything an expected output can be
computed FROM. The row sizes are the sharp case: hand the worker the shape of a
serialised request and it can price every row, pack them, and hash the cuts
without implementing a thing. So this file names prompts, counts and limits, and
the judge prices the rows itself from the request files the run actually wrote.

The one input that is also an answer is the fan-out cap. It cannot be re-drawn —
512 IS the requirement — so the probe reads the limit off the implementation and
reports it, and the judge checks that number against its own copy and against the
module source. A wrong constant fails, and the probe never carries the right one.
"""
from __future__ import annotations

import random

# Prompt tokens avoid look-alike characters: these end up in failure messages a
# human reads when a run goes wrong.
_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"


def _token(rnd: random.Random, n: int = 4) -> str:
    return "".join(rnd.choice(_ALPHABET) for _ in range(n))


def _prompt_token(rnd: random.Random) -> str:
    """Variable width on purpose: it is what makes a ROW SIZE differ run to run.

    A fixed-width token re-draws the prompts and leaves every byte count where
    it was, and a plan captured from one run then fits the next. Measured: a
    forgery replaying a captured run passed 3 of 10 facts that way.
    """
    return "".join(rnd.choice(_ALPHABET) for _ in range(rnd.randint(3, 11)))


def derive(seed: str) -> dict:
    """Every input this run uses, as a plain dict. Same seed, same dict."""
    rnd = random.Random(seed)
    tok = _prompt_token(rnd)

    # Every dataset row is f"{prefix}{i}", and the token's width moves with the
    # seed, so this run's rows are a size no other run's are. The byte band
    # below is wide enough that 2-3 of them still fit whatever the width.
    prefix = f"say {tok} "

    spec: dict = {
        "seed": seed,
        "token": tok,
        "prefix": prefix,

        # --- the main "auto" run: the 5-row/3/400 scenario, re-drawn ----------
        # max_bytes is banded to hold 2-3 rows: below ~320 a single row would not
        # fit and the run would raise instead of planning, which grades nothing.
        "rows": rnd.randint(4, 8),
        "max_requests": rnd.randint(2, 4),
        "max_bytes": rnd.randrange(340, 521, 20),

        # --- one request per batch ------------------------------------------
        "wide_rows": rnd.randint(9, 13),

        # --- plan_batches over explicit sizes (byte-driven cuts) -------------
        # Sizes are handed to the planner directly, so naming them here leaks
        # nothing: the judge holds the same numbers and packs them itself.
        "unit_size": rnd.randint(8, 14),
        "unit_rows": rnd.randint(6, 9),
        "unit_per_batch": rnd.randint(2, 3),

        # a second explicit-size run, cut by count rather than bytes
        "count_rows": rnd.randint(5, 8),
        "count_per_batch": rnd.randint(2, 3),

        # --- the row that cannot fit on its own ------------------------------
        "oversize_rows": rnd.randint(3, 5),
        "oversize_len": rnd.randrange(600, 901, 25),

        # --- values echoed straight back out of curator ----------------------
        # BatchLimits(max_requests, max_bytes) read back off the processor, and
        # the three constructor arguments of SingleRequestTooLargeError.
        "echo_max_requests": rnd.randint(5, 9),
        "echo_max_bytes": rnd.randrange(3000, 6001, 37),
        "err_num_requests": rnd.randint(2, 6),
        "err_size_bytes": rnd.randint(80, 140),
        "err_limit_bytes": rnd.randint(30, 70),

        # --- the explicit-integer branch -------------------------------------
        "explicit_batch_size": rnd.randint(2, 3),

        # --- an explicit fan-out cap, well below the default ------------------
        "cap_rows": rnd.randint(3, 6),

        # --- generation params, per row --------------------------------------
        "gp_rows": rnd.randint(5, 8),
        "gp_temperature": round(rnd.uniform(0.1, 0.95), 2),
        "gp_max_requests": rnd.randint(2, 3),

        # --- the working dir an earlier run left behind ----------------------
        "prepop_n": rnd.randint(5, 8),
        "stale_request": f"stale {tok}\n",
        "stale_metadata": "{}\n",
    }

    # `max_batches_per_plan` for the explicit-cap scenario: one fewer than the
    # plan needs, so the run is one batch over its own ceiling.
    spec["cap_max_batches"] = spec["cap_rows"] - 1

    # Bystanders a sweep must not touch. Names and bodies both carry the token,
    # so a worker cannot report a directory it prepared before this run started.
    spec["keepers"] = {
        f"responses_0.jsonl": f"keep {tok}\n",
        f"batch_objects.jsonl": '{"id": "batch_%s"}\n' % tok,
        f"{tok}.arrow": f"not really arrow {tok}",
        f"notes-{tok}.txt": f"hand-written {tok}\n",
    }
    # A stale sidecar under the implementation's own name, for the failure path
    # that must leave the directory exactly as it found it. Its body names no
    # key the document format uses: this file is in the worker's jail, and even
    # an envelope key is a hint about an answer it should have to earn.
    spec["stale_sidecar"] = '{"left_by": "an earlier run", "tag": "%s"}\n' % tok
    return spec
