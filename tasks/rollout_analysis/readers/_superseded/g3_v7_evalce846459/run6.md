# g3 run 6 (rollout 3b3fcb93, eval ce846459) — reward 0.8889

## What this run found

This is the strongest kind of run: methodical, exhaustive, and largely correct. The agent
didn't trust any UI's own search box. It cloned the repo, checked `git log --all --grep` and
the open issues (207/233) for real repository history, then bulk-dumped every source
programmatically: all 228 wiki pages fetched whole via `/api/pages/{id}` (bodies *and*
comments — it had read the ticket's own hint that BookStack search doesn't index comments),
the full IMAP mailbox via `grep -n 'Subject:'` followed by full-thread reads, and every
Mattermost channel via the API into one flat text file. Against that dump it ran several
keyword greps, then printed the surrounding context of every hit (transcript lines 2050–2900
and 3900–4000 are almost entirely this).

That gave it excellent coverage of both requirements' herring/reversal structure. Before
writing any code, it explicitly reconstructed the timeline for r1 (throttle costs nothing,
no ceiling → reversed to a 6-waiver pool after "a permanently throttled key re-queued for
hours") and r2 (plain-assignment cooldown → reversed to `max()` after "a 1.0s throttle
landing behind a 40s one pulled the horizon in and we flooded again"), writing at line 4014:
*"Timeline: Jan 2025 plain assignment; Mar/Apr 2025 changed to max(). Latest decision: max()."*
Its final PR summary (line 7894) independently re-derives the r1 fix and even names the
incident that motivated it — real synthesis, not a lucky grep hit.

## What it missed, and why

The largest keyword grep (`'free pass|throttle|classif|failure class|retry polic|backoff|jitter'`)
was piped through `| head -60`. That silently truncated before the grep reached `#releases`,
`#pipeline`, or `#viewer` — channels holding 10 of the 49 remarks. Two later, differently
keyworded re-greps (`waiver`, `verdict`) were *not* head-limited and happened to reach those
tail channels, recovering several remarks (`g3.r1.l2`, `g3.r2.rev1`) the first pass missed.
Several other remarks were simply never going to match any searched keyword — some use the
corpus's deliberate typos (`backof` vs. `backoff`), others just don't contain any of the
chosen terms at all (`g3.r1.l9`, `g3.r1.l1`, `g3.r2.s2b`, `g3.r2.s2a`, `g3.r2.s4c`,
`g3.r2.say23`, `g3.r1.l16`, `g3.r1.say23`, `g3.r1.l11`). None of this cost a fact — every
requirement had enough redundant carriers that the gaps were covered elsewhere.

Separately, both wiki-comment remarks the run needed (`g3.r1.l5` on page 184, `g3.r2.s1a` on
page 207) came back from the live `/api/pages/{id}` fetch with only the *opening line* of the
multi-turn exchange the answer key quotes. Nikolai's and Dario's replies — the ones carrying
`retry_policy.py`, `DEFAULT_THROTTLE_WAIVERS`, `throttle_cooldown_until` — never appeared in
`comments.active` for this rollout. This may be the key-newer-than-world case the reader
instructions warn about; it cost nothing here because the same facts had independent chat/mail
carriers.

## The one lost fact

`g3.r2.exclusions_or_crossover` scored 0, but not from a research or implementation failure.
Every behavioral assertion in `test_exclusions__the_seconds_to_pause_knob_survives_in_config_and_is_never_read_again`
passed: the config field survives at 10, and `cool_down_if_rate_limit_error` correctly derives
the pause from the cooldown horizon and nothing else. The agent had found two of the four
carrying remarks (`g3.r2.s4b`, `g3.r2.s4d` — the mail thread) and clearly understood the
requirement; its own docstring on `cool_down_if_rate_limit_error` (diff at transcript line
~7215) reads *"config.seconds_to_pause_on_rate_limit is intentionally left in place and
unread: user configs in the wild still set it, and a dead field costs less than a config that
blows up on load"* — almost a direct quote of remark `g3.r2.s4d`'s mail. The final assertion,
`"seconds_to_pause_on_rate_limit" not in inspect.getsource(BaseOnlineRequestProcessor)`,
fails on that docstring, because `inspect.getsource` includes comments. Nothing in the answer
key or any planted remark says the identifier can't be *named* in an explanatory comment —
only that the pause must not be *derived* from it, which the code correctly doesn't do. This
reads as a task/grader defect (`grader_overspecifies`), not an agent error.

## Herrings

All four herring/reversal pairs were read and correctly resolved — the agent believed the
reversal in every case and shipped code matching it (6-waiver pool for r1, monotonic `max()`
horizon for r2). No herring was followed into the final code.

## Coordinator follow-up: `finish_reason == "length"` — terminal or CONTRACT?

**Yes, the shipped code treats it correctly as CONTRACT** (charged 2 attempts, retryable),
not as terminal/non-retryable, despite the risk the coordinator flagged. Grader evidence is
direct: `test_r1.py:221-227` (part of the `g3.r1.observability` fact, which scored 1) calls
`policy.decide(ValueError("finish_reason was length"), attempts_made=0, attempts_left=1,
throttle_waivers_left=6)` and asserts `v_reason(last) == "contract:exhausted"` — not
`terminal:abort` — with `v_budget(last) == 0` reached by a 2-attempt charge. The message-marker
table the agent wrote (transcript lines 4445–4451) has only the ticket's three groups
(throttle/transient/terminal substrings); no "length" or "finish_reason" entry was added, and
the ticket's own signal order checks exception type (`ValueError` → CONTRACT) *before* message
markers, so there was no opening for a table- or call-site-based terminal reclassification even
if one had been attempted. The pre-existing call site that raises this `ValueError` (transcript
line 1480) flows into the same rewritten `except Exception as e:` block as every other failure —
no special-casing was added there either.

Separately: the agent never quoted or reasoned about konrad's invented "fail it out on the
first" line, because remark `g3.r1.l1` (#code-review, 2025-06-03, the thread that line appears
in) was never surfaced by any of its chat greps — none of its search keywords match that
remark's wording (see the remarks table). It reconstructed the correct CONTRACT/2-attempt rule
instead from `g3.r1.l2` and `g3.r1.rev2`, never encountering the misleading phrasing at all.
