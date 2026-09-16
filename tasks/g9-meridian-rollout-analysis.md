# g9 under meridian — 10 rollouts read against the answer key

Eval `de47e209-cdf4-4d17-a3f8-7359a9cccb16` · task `g9-example-encoding-world-hosted` v8 ·
model **meridian**, agent `typhoon`, 10 runs, 2026-09-15. Read with
`tasks/rollout_analysis/` (targets key `g9-meridian`); per-run verdicts in
`readers/g9-meridian/`, checks in `readers/corrections.md`.

The comparison throughout is **lumen on the identical task and version** (eval `3b0b259f`,
`readers/g9/`).

## Scoreboard

| | meridian | lumen |
|---|---|---|
| mean reward | **0.857** | 0.843 |
| perfect runs | 2/10 | 1/10 |
| agent steps per run (mean) | **53** | 132 |
| remarks found (of 57 × 10) | 341 (60%) | 390 (69%) |

Nearly the same score for **40% of the steps**. Meridian is not a weaker reader; it is a
much shorter one, and the whole difference shows up in *where* it stops looking.

| source | meridian found | lumen found |
|---|---|---|
| chat | 197/290 (68%) | 202/287 (70%) |
| mail | 85/130 (65%) | 98/130 (75%) |
| **wiki comment** | **59/150 (39%)** | 90/150 (60%) |

## Where the ten points went

Every run pushed, went green in CI and deployed. No infra losses, no run that never shipped.
Five of the seven hidden facts are at or near ceiling; all ten losses sit in three facts.

| fact | meridian | lumen | causes (meridian) |
|---|---|---|---|
| `g9.r1.rule` / `scope` / `exclusions_or_crossover` | 10/10 | 9–10/10 | — |
| `g9.r2.rule` | 9/10 | 9/10 | `not_found` ×1 |
| `g9.r2.scope` | 10/10 | 10/10 | — |
| `g9.r1.failure_behavior` | 8/10 | 7/10 | `not_found` ×2 |
| **`g9.r2.failure_behavior`** | **3/10** | 4/10 | `herring_followed` ×5, `not_found` ×2 |

| run | reward | lost | cause |
|---|---|---|---|
| 1 | 0.857 | r2.failure_behavior | herring_followed |
| 2 | 0.714 | r2.rule, r2.failure_behavior | not_found, not_found |
| 3 | 0.857 | r2.failure_behavior | herring_followed |
| 4 | **1.000** | — | — |
| 5 | 0.857 | r2.failure_behavior | herring_followed |
| 6 | 0.857 | r2.failure_behavior | not_found |
| 7 | 0.857 | r1.failure_behavior | not_found |
| 8 | 0.857 | r2.failure_behavior | herring_followed |
| 9 | 0.714 | r1.failure_behavior, r2.failure_behavior | not_found, herring_followed |
| 10 | **1.000** | — | — |

## The finding: one reversal is in the wrong room

`g9.r2.failure_behavior` says `format_batch` absorbs **only** the over-long refusal —
`InvalidRoleSequenceError` and `TokenizerCapabilityError` abort the pass and leave
`last_report` untouched. The herring `g9.r2.h-role-row` (mail) argues the opposite: *"Length
and role sequence are row problems … those get counted and skipped."* It is retracted by
`g9.r2.rev3` — **the only reversal in g9 that lives in a wiki comment**.

| herring → reversal | surface of reversal | saw herring | saw reversal | believed herring | shipped it |
|---|---|---|---|---|---|
| `g9.r1.h1` → `rev1` | chat | 9/10 | **10/10** | 0/10 | 0/10 |
| `g9.r1.h2` → `rev2` | chat | 8/10 | **10/10** | 0/10 | 0/10 |
| `g9.r2.g9-tuple-return-1` → `rev1` | chat | 9/10 | **10/10** | 0/10 | 0/10 |
| `g9.r2.g9-tuple-return-2` → `rev2` | chat | 9/10 | **10/10** | 0/10 | 0/10 |
| **`g9.r2.h-role-row` → `rev3`** | **wiki comment** | 6/10 | **0/10** | **5/10** | **5/10** |

Under lumen the same row reads: saw reversal 4/10, believed herring 6/10, shipped 6/10.

Four herrings in chat are harmless — the reversal arrives in the same channel dump as the
herring, so an agent that finds one finds the other. The fifth is a herring in **mail**
whose reversal is in a **wiki comment**, and it converts directly into shipped wrong code:
five runs wrote `except (InvalidRoleSequenceError, ExampleTooLongError): dropped_indices.append(i)`.

### Why rev3 cannot be reached by search

BookStack does not index comments, so the page has to be opened by hand. That is by design —
but these two pages cannot be found:

| page holding the retraction | "encoding" | "finetuning" | "Fireworks" |
|---|---|---|---|
| `request-builder-what-we-drop-and-what-we-raise-on.md` (rev3, l17) | 0 | 0 | 0 |
| `what-format-batch-counts-as-a-drop-and-what-stops-the-pass-instead.md` (say24) | 0 | 0 | 0 |

Title and body both. The task is named **example encoding**, so `encoding` is the first query
every run typed. Runs 5 and 8 fetched page comments routinely — five or six pages each, body
and comments, via `/api/pages/{id}` — and still never opened these two, because they never
appeared in a result list. **The failure mode is not "the agent skips comments". It is that
the pages carrying the decisive comments share no vocabulary with the task's own subject.**

## The two perfect runs got the fact for free

Runs 4 and 10 scored `g9.r2.failure_behavior` = 1 having seen **none** of its five carriers,
and run 10 having seen only the herring. Both got there by code shape: `g9.r2.l19`'s mail
supplies "accumulate into locals, construct the report at the end, assign once", and the
`g9.r1.h1`/`rev1` thread supplies the narrow `except ExampleTooLongError`. Compose the two
and every other exception necessarily propagates before the single assignment. Run 10 even
wrote a regression test asserting `pytest.raises(InvalidRoleSequenceError)` through
`format_batch` — deliberate, not lucky, but arrived at without the half of the MuSR tree that
says role failures are not drops.

That fact is therefore scoring two different things: recovering the requirement, and
happening to pick the tidier of two `try` placements. Worth knowing before reading 3/10 as a
difficulty measurement.

## `g9.r1.failure_behavior`, and the thing that is not a grader bug

Runs 7 and 9 shipped `ExampleTooLongError` without `num_messages`. That attribute **is**
pinned in the world, exactly once, as the tail of the #pipeline refusal-string exchange
(`g9.r1.l-fail-3`, 2025-03-19 14:13, *"correct. num_messages rides along as an attribute, it
isn't printed."*). It surfaced in 8 of 10 runs — and the two where it did not are precisely
the two that lost the fact. Not a grader overspecification; the headline of that exchange is
the format string, and a run that greps for the string and stops gets four of the five
attributes.

## Corpus defect: `g9.r2.l15` was never rendered

The plant record's text is dario settling the question — *"the fireworks jsonl path never
loads a tokenizer, so a token total and a trim count coming back off it are just noise — both
read zero there."* The served world has only nikolai **asking** it (mail `9035`: *"Do we
return None, do we leave the keys out entirely, or do we put zeros in there?"*), leaning the
wrong way with *"I'd say leaving them out is cleanest"*. No reply exists in any mailbox, and
`both read zero` / `read zero there` have zero hits across `messages.jsonl`,
`comments.jsonl`, `docs/` and `emails/`. The plant's own carrier note names the shape that was
meant to land: *"someone asks what the returned counts mean per backend, dario settles the
Fireworks half"* — only the asking half rendered.

It cost one fact in one run (run 2's `g9.r2.rule`); the other nine derived the zero from
`to_jsonl_lines` never tokenizing. The readers scored it "found 9/10" because they found the
*thread*. A remark that was never rendered is invisible to the pre-pass — it looks exactly
like a remark nobody found.

## What to change

1. **Move `g9.r2.rev3`, or make its page findable.** Either put the retraction of
   `h-role-row` in chat like the other four, or give the two pages a title or body that a
   search for the task's own subject reaches. As it stands the herring is a coin flip on
   whether the agent ever sees the other side, and that is what `g9.r2.failure_behavior` is
   measuring.
2. **Render `g9.r2.l15`'s reply, or drop the remark.** The plant and the corpus disagree, and
   the resync check would have caught it.
3. **Treat 3/10 on `g9.r2.failure_behavior` as two effects, not one** — 5 runs lost it to an
   unreachable retraction, 2 to a mail they never opened, and 3 of the passes came from code
   shape rather than recovery.

## Tooling changed to read a non-lumen eval

- `pull.py` — targets carry a `model`; it hard-coded `lumen`.
- `prepass.py` — parses `junit.xml` when there is no `ctrf.json`. This grader is worker/judge
  and emits junit, so pointer sheets were printing "no failing tests" beside zeroed facts.
- `aggregate.py` — a target key may name a model (`g9-meridian`); facts key on the task,
  `OVERRIDES`/`NEVER_SHIPPED` stay on the folder key so one eval's overrule cannot land on the
  other's run numbers. Re-run on `g9`: summary byte-identical.
