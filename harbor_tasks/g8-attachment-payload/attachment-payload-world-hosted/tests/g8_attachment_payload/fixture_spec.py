"""g8 — the INPUTS of one grading run, derived from the seed root chose.

Stdlib only, and imported by both sides: the worker gets it in the jail (it has
to build the attachments it hands curator), the judge gets it beside `judge.py`
(it has to know what was attached in order to work out what the answer should
have been). One derivation, so the two cannot drift.

WHY A SEED AT ALL. The worker/judge split stopped the worker rewriting the
verdict; it did not stop the worker INVENTING the values the judge reads. With a
fixed fixture those values are the same every run, so a tree that implements
nothing can replay an earlier run's `observations.json`. Measured on g8 before
this file existed: reward 1.0 from a pristine curator — no `types/attachment.py`
at all — plus a twelve-line `atexit` hook that copied a recorded observations
file over the one the probe wrote.

Re-drawing the ATTACHED BYTES is what breaks that replay, and it is chosen
rather than re-drawing sizes or counts because it moves the answers a forger
cannot compute without the hidden requirements: the base64 every provider render
embeds, and the `sha256:`-prefixed twelve-hex fingerprint r2 grades over that
base64. A recorded observations file from another run carries the previous run's
payload, so it fails the moment the judge re-derives this run's.

WHAT MAY NOT LIVE HERE. Expected outputs, and anything an expected output can be
computed from without implementing the requirement. The ceilings, the count
limit, the token price, the filename cap and the fingerprint FORMULA are all
answers — they stay in the judge, which the worker cannot read.
"""
from __future__ import annotations

import random

# No look-alike characters: these bytes end up in failure messages a human reads
# when a run goes wrong, and in a base64 they have to compare by eye.
_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"


def derive(seed: str) -> dict:
    """Every input this run re-draws, as a plain dict. Same seed, same dict."""
    rnd = random.Random(seed)
    tag = "".join(rnd.choice(_ALPHABET) for _ in range(10))
    return {
        "seed": seed,
        "tag": tag,
        # The PDF marker plus four drawn bytes: NINE bytes, exactly as many as
        # the fixed payload it replaces. The length is deliberate — the measured
        # size in megabytes is a graded value with a stated tolerance, so the
        # bytes move while `get_base64_size` of them does not, and every size
        # this suite grades (and the arithmetic task.toml states) is untouched.
        # The base64 the renders embed and the sha256 fingerprint r2 grades are
        # what move. Its MIME type is never sniffed from these bytes: the local
        # copy is written to a `.pdf` path and the in-memory one is constructed
        # with `mime_type="application/pdf"`.
        "pdf_bytes": b"%PDF-" + tag[:4].encode(),
        # The four bytes behind `chart.png`, four as before: written to a `.png`
        # path, so the kind still comes from the extension and only the base64
        # moves.
        "png_bytes": tag[4:8].encode(),
    }
