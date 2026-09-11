# g11 run 9 (rollout 1daa88e2, eval 94bf8242) — reward 0.8889

## What this run found

This is a near-clean run: `open_feature`, all five `g11.r1` facts, and three of the
four declared `g11.r2` facts scored 1. The agent built a two-tool local search
index early (a full JSON dump of Mattermost plus two helper scripts, `/tmp/gc.py`
for cross-channel keyword grep and `/tmp/cc.py` for a single channel/date-range
window read) and drove nearly the whole investigation through keyword-sweep-then-
window-read cycles. That strategy surfaced 44 of the 47 answer-key remarks,
including every clue behind `g11.r1` and eight of `g11.r2`'s nine sub-facts.

It also handled the herrings correctly in every case: for `g11.r1` it recovered
both the twin-checkpoint/alphabetical-sort decision (`ledger-twin-checkpoints-
dario`/`-emil`) and both reversals (`rev1`/`rev2`, lines 3007/2729), and its
shipped `canonical_reasons` docstring names the herring it is avoiding almost
verbatim ("rather than alphabetical, which used to put final ahead of interval
and read as though the run had ended before it looped"). For `g11.r2` it found
both decay-to-zero herrings and both reversals (line 2560-2588, 2510-2523) and
shipped the `MIN_LR_RATIO`/`effective_warmup` design, not the zero-decay/strict-
compare one. No herring was followed into the shipped code.

## What it missed, and why

The one lost fact is `g11.r2.rule`, and it fails on a single narrow assertion:
`test_r2.py` checks `inspect.signature(learning_rate_at).parameters["min_lr_ratio"]
.kind is inspect.Parameter.KEYWORD_ONLY` before it checks any numeric value, and
the agent shipped `min_lr_ratio: float = MIN_LR_RATIO` with no bare `*` in front
of it — an ordinary keyword-with-default, not keyword-only. Its own new tests
call the function both positionally and with `min_lr_ratio=` as a keyword,
showing the distinction was never on its radar.

The reason is a clean, provable search gap. The single remark that carries this
fact, `g11.r2.l10` ("also did a pass on 663 - min_lr_ratio sits behind a bare *
so callers have to name it, MIN_LR_RATIO stays the module-level default"),
sits in `#code-review` on 2025-05-30 and never surfaces anywhere in the
transcript or the raw rollout JSON — a grep for "663", "bare", "spellings
drift", "keyword-only" and the date itself all come back empty. The agent's
`#code-review` reads stop at 2025-04-14; its LR keyword sweeps used
`'learning_rate_at' 'effective_warmup' 'cosine'` and a broad `'accumulation'
'warmup' 'loss_history' 'signature' 'trailing'` pass, but never the literal
string `min_lr_ratio` or `MIN_LR_RATIO` — despite typing both dozens of times
in its own analysis while discussing the *semantics* of the ratio (recovered
correctly from `g11.r2.rev1` and `g11.r2.say20`). It declared the LR design
"fully determined" (line 3536) and "complete" (lines 4093, 4907, 5008) once
the schedule shape and the rescaling behavior checked out numerically, and
moved on to writing code without a final sweep on the identifier itself. Two
other remarks (`g11.r2.l7`, `g11.r2.l11`) also never surfaced, for the same
reason (their wording shares no vocabulary with any swept term and their
channels/dates were never dumped), but those facts still scored 1 because
other found remarks independently carried the same information.

## Why the passing facts passed

Every `g11.r1` fact and three of `g11.r2`'s rested on remarks the agent did
find and correctly reason about — `canonical_reasons` ordering/dedup/error
behavior, the six-digit padded name template, scope (final unconditional,
Fireworks writes nothing), epoch-from-plan, dedupe-on-repeat-name, and the
full numeric LR schedule including the floor/clamp and the clipped-warmup
failure case. The agent cross-checked essentially every quoted number against
its own implementation before committing (lines 5420, 5571), which is why
`observability` on both requirements passed cleanly even though a couple of
their individual carrier remarks were never separately surfaced.

## Bottom line

One lost fact, one clean cause: `g11.r2.rule` failed because the sole remark
carrying "min_lr_ratio is keyword-only" (`g11.r2.l10`, #code-review, 2025-05-30)
was never found — a keyword-sweep gap (the agent never grepped for the
identifier itself) compounded by the agent's `#code-review` reads stopping
six weeks before that remark's date. This is `not_found`, not a reasoning or
implementation slip: everything the agent did find about the LR schedule, it
implemented correctly.
