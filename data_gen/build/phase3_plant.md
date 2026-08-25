# The tasks, and where their clues are hidden

4 task(s) · 8 hidden requirement(s) · 99 clue(s) · 8 reversed decision(s) · 107/107 placed

**4 requirement(s) did not pass their gates.** Those are marked below and the run failed.

6 requirement(s) needed re-planting before they passed; what each was told to fix is recorded under it.

## Why these tasks

Chosen rather than inherited — the tasks file holds 60 and the run used to take whichever five sat at the top, which is not a sample of anything. These span different KINDS of hidden requirement, checked by reading the requirement text rather than by trusting the `T` codes, which appear in the tasks file but are defined nowhere in this repository.

| requirement | sources | facts it has | reversed | clues |
|---|---|---|---|---|
| t1.r1 — Prompt-level response cache keying | slack, notion | 5 (rule, scope, exclusions_or_crossover, failure_behavior, observability) | yes | 20 |
| t1.r2 — Prompt-level response cache keying | slack, notion | 4 (rule, scope, failure_behavior, observability) | no | 14 |
| t2.r1 — Structured output schema validation befo | notion, slack | 3 (rule, scope, failure_behavior) | yes | 10 |
| t2.r2 — Structured output schema validation befo | slack | 2 (rule, scope) | no | 9 |
| t3.r1 — Batch job status persistence across proc | notion, email, slack | 3 (rule, scope, failure_behavior) | yes | 11 |
| t3.r2 — Batch job status persistence across proc | slack | 3 (rule, scope, failure_behavior) | no | 12 |
| t4.r1 — Docker code executor image pinning | notion, slack | 2 (rule, scope) | yes | 11 |
| t4.r2 — Docker code executor image pinning | slack, email | 3 (rule, scope, failure_behavior) | no | 12 |

**How a requirement earns its place here.** It has to be recoverable from the clues *with the reversed decision sitting among them* — the corpus an agent actually reads has the distractor in it, so recoverable-without-it measures nothing. And no single remark may hand a fact over on its own: a fact one line establishes was published, not hidden. Both gates are checked below, and a requirement that failed either was re-planted and told exactly what was wrong.

Each task states a feature openly. What it does not state is the requirement below it, which appears nowhere in the corpus as a rule — only as remarks people made in passing while working on something else. An agent has to put them back together.

A **clue** carries part of the answer. A **reversal** is what this team decided first and later changed its mind about; it is planted strictly *before* the clue that overturns it, so reading in date order recovers the change and reading one conversation does not.

Placement is marked **explicit** where the room was already arguing about this, **passing** where the remark is an aside in a conversation about something else. Both are wanted: only-explicit is findable by searching for the topic, only-passing reads as arbitrary.

---

## t1 — Prompt-level response cache keying

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

**Where it gets designed:** 12 conversation(s) between 2025-01-28 and 2025-03-06, plus a design page and a mail thread. None of them state the hidden requirement.

### t1.r1 — the hidden requirement  ·  T2, T6

| part | what it actually requires |
|---|---|
| `rule` | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. <br>*carried by: t1.r1.l_prompt_1, t1.r1.l_prompt_2, t1.r1.l_model_1, t1.r1.l_model_2, t1.r1.l_schema_1, t1.r1.l_schema_2, t1.r1.l_schema_3, t1.r1.l_params_1, t1.r1.l_params_2, t1.r1.l_params_3* |
| `scope` | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. <br>*carried by: t1.r1.l_scope_1, t1.r1.l_scope_2, t1.r1.l_scope_3* |
| `exclusions_or_crossover` | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. <br>*carried by: t1.r1.l_prompt_3* |
| `failure_behavior` | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. <br>*carried by: t1.r1.l_schema_2, t1.r1.l_unhash_1, t1.r1.l_unhash_2, t1.r1.l_unhash_3* |
| `observability` | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. <br>*carried by: t1.r1.l_unhash_3, t1.r1.l_scope_2, t1.r1.l_stats_1, t1.r1.l_stats_2, t1.r1.l_stats_3* |

**What they decided first, and later reversed:** The team originally cached on the raw input row's hash alone, but reversed this after noticing identical prompts with cosmetic input differences were needlessly re-billed.

**The reasoning an agent has to do**

```
the requirement
  |
  +-- The value looked up for reuse has to be derived from the prompt text that prompt() actually rendered, not from the input row, so rows that differ only in fields prompt() never reads land on the same entry.
  |     reader must infer: If adding an unread column invalidates everything and two rows rendering the same prompt get billed twice, the thing being compared is the wrong object: it should be the rendered prompt.
  |     +-- [t1.r1.l_prompt_1] dermot · 2025-02-19 #engineering
  |     |     "Heads up, I added a source_url column to the persona input set purely for provenance. prompt() does not look at it. Entire 40k run went back out to the API and billed me again. I did not touch a single prompt."
  |     +-- [t1.r1.l_prompt_2] dario · 2024-12-16 page:runbook-bulk-llm-inference
  |     |     "Putting this in the runbook because it keeps coming up: attaching extra metadata columns to a dataset for bookkeeping should come back free on the next run. It is the same set of requests going to the same place, nothing about the work changed."
  |     +-- [t1.r1.l_prompt_3] emil · 2025-01-29 #engineering
  |     |     "RAFT emitted the same question against two chunk ids last night. Byte identical messages payload, I diffed them. Both went out as separate requests and both got billed. I would expect the second one to come straight back off disk since we already have that exact answer."
  |
  +-- model_name has to take part in what identifies a stored response, so the same prompt against a different model is not reused.
  |     reader must infer: Getting the previous model's answers back after a swap means the model is not part of what distinguishes stored answers, and blanket cache-disabling is the wrong fix.
  |     +-- [t1.r1.l_model_1] gideon · 2025-03-18 #random
  |     |     "Lost most of yesterday to this. Swapped gpt-4o-mini for gpt-4o on the reannotation set, run finished in nine seconds, summary said everything came off disk. The outputs were the mini ones. I only noticed because the formatting was too sloppy for 4o."
  |     +-- [t1.r1.l_model_2] dermot · 2025-01-30 #incidents
  |     |     "Every time I run a model sweep I end up exporting CURATOR_DISABLE_CACHE=1 for the whole thing, which then means the second and third models pay full price for the prompts I already have at that model."
  |
  +-- The response_format schema has to take part in what identifies a stored response, so editing the schema resends only the affected rows.
  |     reader must infer: Old-shaped objects coming back after a schema edit, plus people wiping the cache directory by hand, means the requested shape has to be part of what a stored answer is an answer to.
  |     +-- [t1.r1.l_schema_1] emil · 2025-02-24 #engineering
  |     |     "Added a confidence field to the response model on the ungrounded QA example, reran, and got back last week's objects with no confidence on them. Then the downstream validator threw on every row and I spent an hour looking at the validator."
  |     +-- [t1.r1.l_schema_2] dario · 2025-02-24 page:design-t2-plant
  |     |     "Adding this to the troubleshooting page since it is the third report: if you edit your response_format between runs, either wipe the cache directory or set CURATOR_DISABLE_CACHE=1 first, otherwise you will get objects built to the previous schema."
  |     +-- [t1.r1.l_schema_3] gideon · 2025-03-12 #incidents
  |     |     "Nuking the whole cache dir every time I tweak one field is the main reason people here do not trust reruns. On a 200k set that is real money to get one extra field."
  |
  +-- generation_params has to take part in what identifies a stored response, so changing temperature or max_tokens resends those rows.
  |     reader must infer: Identical output after changing sampling settings means the settings are not distinguishing stored answers, and the desired behaviour is a resend of just those rows.
  |     +-- [t1.r1.l_params_1] gideon · 2025-02-28 #help
  |     |     "Bumped temperature from 0 to 1.2 on the poem set to get some variety and got the identical 5k rows back. I spent an hour convinced vLLM was ignoring temperature before I worked out where they were coming from."
  |     +-- [t1.r1.l_params_2] emil · 2025-04-18 #engineering
  |     |     "Same shape of thing with max_tokens for me. Response came back truncated mid sentence, I raised max_tokens, reran, got handed the truncated text again. Deleted the cache directory in the end, which also threw away four thousand rows that were perfectly fine."
  |     +-- [t1.r1.l_params_3] dario · 2025-01-28 page:design-t1-plant
  |     |     "Writing down what I think the sane behaviour is, because right now everyone's answer is rm -rf on the cache dir: if generation_params differ from the stored run, those rows should be going out to the provider again, and only those rows."
  |
  +-- When the response_format cannot be hashed, the row has to fall through as a plain miss and go to the backend instead of raising and killing the run.
  |     reader must infer: An optimisation that throws on unusual input should degrade to doing no optimisation, not abort the work it was speeding up.
  |     +-- [t1.r1.l_unhash_1] emil · 2025-03-11 #cookbooks
  |     |     "SimpleStrat builds its response model at runtime with pydantic create_model, and the lookup pass dies on it: TypeError: unhashable type. Run is dead at row zero, before a single request goes out. Traceback in thread."
  |     +-- [t1.r1.l_unhash_2] dermot · 2025-03-26 #help
  |     |     "I wrapped that call in a try/except locally to get the demo dataset out for the Friday cut and I have been carrying the patch since. Not shipping it, but I am also not deleting it, which tells you something."
  |     +-- [t1.r1.l_unhash_3] gideon · 2025-02-06 #pipeline
  |     |     "Recipes that construct their schema on the fly are never going to be reusable and I am fine with that. What I am not fine with is being worse off than someone who never had a cache at all. Those rows should just go to the provider and show up in the sent column at the end."
  |
  +-- The change lands in the single shared lookup path, so it takes effect for batch submission and online requests alike rather than being special-cased per backend.
  |     reader must infer: If both processors call one helper, fixing the helper is the fix everywhere, and per-backend divergence is a regression risk rather than a design.
  |     +-- [t1.r1.l_scope_1] emil · 2025-03-25 #engineering
  |     |     "Reminder for whoever touches the reuse pass: batch submission builds its jsonl off the same lookup, that is why when the online path stopped re-sending duplicates last month the batch path quietly stopped too."
  |     +-- [t1.r1.l_scope_2] gideon · 2025-02-21 #pipeline
  |     |     "We only ever assert on reuse counts in the online tests. The batch e2e checks the reassembled output and nothing else, which is exactly how the last regression rode out to a release. It bit me on the Azure batch run too."
  |     +-- [t1.r1.l_scope_3] dermot · 2025-01-14 page:postmortem-2025-01-13
  |     |     "For anyone new to this area: there is exactly one function that decides whether a row is reused or sent, and every processor calls it, online, batch and the local vLLM one."
  |
  +-- The reported numbers have to be a fractional hit_rate plus an integer misses, and the two together have to account for every processed row.
  |     reader must infer: A count without a denominator and a percentage without a count are each useless for a cost estimate, and any row not in one bucket or the other makes both numbers untrustworthy.
  |     +-- [t1.r1.l_stats_1] gideon · 2025-02-20 #viewer
  |     |     "The end of run table says cached: 12,403 and the first thing every single user asks is out of what. A bare count tells nobody whether their rerun is cheap. Give me a hit_rate I can print as a percentage next to it."
  |     +-- [t1.r1.l_stats_2] emil · 2025-05-02 page:handover-status-tracking-cost-reporting-and-the-v
  |     |     "For the cost estimate in the cookbook I do not want a percentage I have to invert. I want misses as a plain int so I can multiply it by price per row and put a dollar figure in front of someone before they hit go."
  |     +-- [t1.r1.l_stats_3] dario · 2025-02-07 #cookbooks
  |     |     "Last summary table I looked at had reused plus sent coming to 900 short of the dataset length. I think those were the rows that errored mid flight and dropped out of both tallies. If the two numbers do not add up to the number of rows I processed, nobody is going to believe either of them, me included."
  |
  +-- (unused)
  |     reader must infer: n/a
```

**Is it recoverable from the clues alone?** yes — every part came back

What a reader given only these remarks, and no answer key, concluded:

> The cache key must be the resolved provider request — prompt payload, model, generation_params and response schema — computed by a single shared function used identically by online, batch and vLLM paths, so unrelated dataset columns cost nothing, duplicate payloads dedupe within a run, and any changed field re-sends only the affected rows instead of forcing a cache wipe. Unhashable or dynamically built schemas must degrade to plain misses rather than crash, and cache_stats() must report hits, misses as a raw int, total and hit_rate such that hits plus misses always equals rows processed (errored rows included), with batch e2e tests asserting on those counts.

**With the reversed decision in the room — the corpus as an agent actually meets it.** Every part still comes through.

    rule: 3/3, scope: 3/3, exclusions_or_crossover: 3/3, failure_behavior: 3/3, observability: 3/3

> The remarks jointly require moving the cache key off the raw input row and onto a fingerprint of the fully resolved request (rendered prompt payload + model + generation params + response schema), computed by one shared lookup used by every backend, with per-row invalidation, graceful miss-on-unhashable degradation, and all key inputs persisted in the metadata DB. cache_stats() then reports hits, misses as a plain int, total and hit_rate, with hits + misses always equal to rows processed, callable cheaply before a run and correct for online, batch and offline paths.

**Does any single remark give it away?** **Yes**, which makes this part of the task trivial:

- t1.r1.l_params_3 closes `sc_params` on its own, so the other 2 remark(s) under it are decoration: Dario states the required behaviour outright — differing generation_params must resend exactly those
- t1.r1.l_scope_1 closes `sc_scope` on its own, so the other 2 remark(s) under it are decoration: Dermot states the single shared function directly; emil independently states batch builds off the sa
- t1.r1.l_scope_3 closes `sc_scope` on its own, so the other 2 remark(s) under it are decoration: Dermot states the single shared function directly; emil independently states batch builds off the sa
- sc_stats_dummy rests on 0 remark(s); a conclusion one person can hand over is not hidden

> Re-plant 1: t1.r1.l_model_2 closes `sc_model` on its own, so the other 1 remark(s) under it are decoration: Dermot states the desired keying rule outright — no sh

> Re-plant 2: t1.r1.l_params_3 closes `sc_params` on its own, so the other 2 remark(s) under it are decoration: Dario states the required behaviour outright — diffe

> Re-plant 3: t1.r1.l_params_3 closes `sc_params` on its own, so the other 2 remark(s) under it are decoration: Dario states the required behaviour outright — diffe

> Re-plant 4: t1.r1.l_params_3 closes `sc_params` on its own, so the other 2 remark(s) under it are decoration: Dario states the required behaviour outright — diffe

> Re-planted 4 time(s) and still failing. Left as it is rather than made easier to force a pass.

**Every planted line, in the order an agent reading forward meets it**

| date | where | who | | covers | placement | what they say | why this room |
|---|---|---|---|---|---|---|---|
| 2024-11-26 | #code-review | dario | ↩︎ reversal | — | explicit | Worth writing down why the row hash is the right level for this. Keying on the row means resume and cache lookup need nothing but the dataset itself, no prompt callable, no live LLM object, so I can rebuild the whole hit/miss picture from the metadata DB on a cold process. That is exactly what cache_stats needs to be cheap. If the key depended on anything we can only compute by constructing the LLM, cache_stats stops being a thing you can call before a run and becomes another run. | — |
| 2024-11-27 | #engineering | dermot | ↩︎ reversal | — | passing | To be clear on the cache key since it came up again in review: it is the hash of the raw input row, full stop. Row in, hash out, that is the whole contract and I want it to stay that narrow. Every time someone folds another thing into a fingerprint we end up with a key nobody can explain to a user who asks why their rerun did what it did. The row is the unit the dataset is made of, so the row is the unit the cache is keyed on. cache_stats should just report against those row hashes and nothing fancier. | — |
| 2024-12-16 | page:runbook-bulk-llm-inference | dario | clue | rule | passing | Putting this in the runbook because it keeps coming up: attaching extra metadata columns to a dataset for bookkeeping should come back free on the next run. It is the same set of requests going to the same place, nothing about the work changed. | He says outright he is putting it in the runbook, and the runbook is the on-call page for recurring curator.LLM rerun complaints. |
| 2025-01-14 | page:postmortem-2025-01-13 | dermot | clue | scope | passing | For anyone new to this area: there is exactly one function that decides whether a row is reused or sent, and every processor calls it, online, batch and the local vLLM one. | The postmortem is about a cache hashing regression that had to be reverted, so the standing rule that one function decides reuse-or-send belongs in its lessons. |
| 2025-01-28 | page:design-t1-plant | dario | clue | rule | passing | Writing down what I think the sane behaviour is, because right now everyone's answer is rm -rf on the cache dir: if generation_params differ from the stored run, those rows should be going out to the provider again, and only those rows. | This is the design page for cache keying, so writing down that differing generation_params should re-send only the affected rows is the normative statement the doc is for. |
| 2025-01-29 | #engineering | emil | clue | exclusions_or_crossover | explicit | RAFT emitted the same question against two chunk ids last night. Byte identical messages payload, I diffed them. Both went out as separate requests and both got billed. I would expect the second one to come straight back off disk since we already have that exact answer. | The conversation is about users wanting to know a re-run's cost up front, and a byte-identical payload being billed twice is the concrete case that motivates it. |
| 2025-01-30 | #incidents | dermot | clue | rule | explicit | Every time I run a model sweep I end up exporting CURATOR_DISABLE_CACHE=1 for the whole thing, which then means the second and third models pay full price for the prompts I already have at that model. | The incident on the table is dario getting completions from a model he did not call, and dermot's sweep workaround describes how people are currently living with that. |
| 2025-02-06 | #pipeline | gideon | clue | failure_behavior, observability | explicit | Recipes that construct their schema on the fly are never going to be reusable and I am fine with that. What I am not fine with is being worse off than someone who never had a cache at all. Those rows should just go to the provider and show up in the sent column at the end. | The question on the table is who owns the counting, and gideon is saying unreusable rows should degrade into the sent tally rather than blow up. |
| 2025-02-07 | #cookbooks | dario | clue | observability | explicit | Last summary table I looked at had reused plus sent coming to 900 short of the dataset length. I think those were the rows that errored mid flight and dropped out of both tallies. If the two numbers do not add up to the number of rows I processed, nobody is going to believe either of them, me included. | The room is insisting the counts must be defensible where users first meet them, and reused plus sent falling 900 short of the row count is precisely what would discredit them. |
| 2025-02-19 | #engineering | dermot | clue | rule | explicit | Heads up, I added a source_url column to the persona input set purely for provenance. prompt() does not look at it. Entire 40k run went back out to the API and billed me again. I did not touch a single prompt. | The room is already arguing that the current cache key is too coarse to produce believable counts, and a 40k rebill caused by a non-prompt provenance column is exactly the evidence that claim needs. |
| 2025-02-20 | #viewer | gideon | clue | observability | explicit | The end of run table says cached: 12,403 and the first thing every single user asks is out of what. A bare count tells nobody whether their rerun is cheap. Give me a hit_rate I can print as a percentage next to it. | Gideon is already specifying what the summary table should print, and this is him naming the missing column: a hit rate next to the bare count. |
| 2025-02-21 | #pipeline | gideon | clue | scope, observability | explicit | We only ever assert on reuse counts in the online tests. The batch e2e checks the reassembled output and nothing else, which is exactly how the last regression rode out to a release. It bit me on the Azure batch run too. | The async batch refactor is opening up this week, which is the moment to point out that reuse counts are only asserted on the online path. |
| 2025-02-24 | #engineering | emil | clue | rule | explicit | Added a confidence field to the response model on the ungrounded QA example, reran, and got back last week's objects with no confidence on them. Then the downstream validator threw on every row and I spent an hour looking at the validator. | The room opened on a rerun that broke after the dataset changed underneath it, so a rerun handing back objects built to the old response model is directly on subject. |
| 2025-02-24 | page:design-t2-plant | dario | clue | rule, failure_behavior | explicit | Adding this to the troubleshooting page since it is the third report: if you edit your response_format between runs, either wipe the cache directory or set CURATOR_DISABLE_CACHE=1 first, otherwise you will get objects built to the previous schema. | This design is about structured output and response_format handling, so the third report of stale-schema objects belongs as a troubleshooting note on that page. |
| 2025-02-28 | #help | gideon | clue | rule | passing | Bumped temperature from 0 to 1.2 on the poem set to get some variety and got the identical 5k rows back. I spent an hour convinced vLLM was ignoring temperature before I worked out where they were coming from. | Dermot has just called this the third variant of the same class of problem this week, and gideon's temperature story is another variant to add to the pile. |
| 2025-03-11 | #cookbooks | emil | clue | failure_behavior | explicit | SimpleStrat builds its response model at runtime with pydantic create_model, and the lookup pass dies on it: TypeError: unhashable type. Run is dead at row zero, before a single request goes out. Traceback in thread. | The room is exactly about RAFT and SimpleStrat building Pydantic models dynamically, so the unhashable-type crash at row zero is the failure they are discussing. |
| 2025-03-12 | #incidents | gideon | clue | rule | passing | Nuking the whole cache dir every time I tweak one field is the main reason people here do not trust reruns. On a 200k set that is real money to get one extra field. | The incident is twenty-two wasted hours on a schema complaint, and gideon's point about paying full price for one extra field names the cost of the current remedy. |
| 2025-03-18 | #random | gideon | clue | rule | explicit | Lost most of yesterday to this. Swapped gpt-4o-mini for gpt-4o on the reannotation set, run finished in nine seconds, summary said everything came off disk. The outputs were the mini ones. I only noticed because the formatting was too sloppy for 4o. | Model-release chatter has already turned into war stories about silent wrong output, and a 4o run that quietly served mini completions is the same genre of story. |
| 2025-03-25 | #engineering | emil | clue | scope | explicit | Reminder for whoever touches the reuse pass: batch submission builds its jsonl off the same lookup, that is why when the online path stopped re-sending duplicates last month the batch path quietly stopped too. | Dario is proposing to reuse the caching-and-resume fingerprint and dermot distrusts it, so emil's reminder that batch jsonl is built off the same lookup is the constraint that decision needs. |
| 2025-03-26 | #help | dermot | clue | failure_behavior | explicit | I wrapped that call in a try/except locally to get the demo dataset out for the Friday cut and I have been carrying the patch since. Not shipping it, but I am also not deleting it, which tells you something. | Someone is blocked by a check they should not be, and dermot's carried try/except patch is the workaround confession that fits a thread about escape hatches. |
| 2025-04-18 | #engineering | emil | clue | rule | explicit | Same shape of thing with max_tokens for me. Response came back truncated mid sentence, I raised max_tokens, reran, got handed the truncated text again. Deleted the cache directory in the end, which also threw away four thousand rows that were perfectly fine. | Emil is already asking how to force a fresh submission without hand-deleting files, and losing four thousand good rows to a directory delete is his own answer to why that matters. |
| 2025-05-02 | page:handover-status-tracking-cost-reporting-and-the-v | emil | clue | observability | passing | For the cost estimate in the cookbook I do not want a percentage I have to invert. I want misses as a plain int so I can multiply it by price per row and put a dollar figure in front of someone before they hit go. | He is taking over cost reporting and the viewer surface, so stating that he needs misses as a plain int to price a run is the shape requirement he inherits with it. |

**Spread:** 2 source(s), 12 distinct week(s), 13 room(s), first 2024-11-26 last 2025-05-02.

---

### t1.r2 — the hidden requirement  ·  T4, T5

| part | what it actually requires |
|---|---|
| `rule` | `cache_stats()` must read from the same on-disk cache directory the rest of `curator.LLM` uses, honoring `CURATOR_CACHE_DIR` if set, and must never write to or mutate the cache directory itself. <br>*carried by: t1.r2.L1, t1.r2.L2, t1.r2.L3, t1.r2.L13* |
| `scope` | Read-only access to whatever directory the existing caching layer resolves to at call time. <br>*carried by: t1.r2.L4, t1.r2.L5, t1.r2.L6* |
| `failure_behavior` | If the cache directory does not exist yet (no prior run), return zeroed stats rather than raising a file-not-found error. <br>*carried by: t1.r2.L5, t1.r2.L7, t1.r2.L8, t1.r2.L9* |
| `observability` | The returned object must include the resolved cache directory path so users can verify which cache was inspected. <br>*carried by: t1.r2.L10, t1.r2.L11, t1.r2.L12, t1.r2.L14* |

**The reasoning an agent has to do**

```
the requirement
  |
  +-- Anything that reports on the cache has to find the cache directory the same way a run does, asking the caching layer at the time it is called, so CURATOR_CACHE_DIR takes effect
  |     reader must infer: if two code paths compute the location differently, one of them is reporting on a directory the run never touches, so there can only be one resolver and it has to be consulted late rather than at import time
  |     +-- [t1.r2.L1] dario · 2025-02-13 #general
  |     |     "burned an hour this morning on my little cache-poking script. It reports 12 hits out of 40k and I nearly re-budgeted the whole persona run on that. Turns out the script does os.path.expanduser("~/.cache/curator") and I have had CURATOR_CACHE_DIR=/mnt/scratch/curator-cache in my shell profile since June. The numbers were from a directory nothing has written to since October."
  |     +-- [t1.r2.L2] emil · 2025-02-26 #pipeline
  |     |     "related annoyance from the notebook walkthrough: people import curator in cell 1 and then set CURATOR_CACHE_DIR in cell 4 because that is the order the tutorial reads. The sizing helper I wrote grabs the path once when the module loads, so it kept telling them about the default directory for the rest of the session and I got two emails about it."
  |     +-- [t1.r2.L3] dermot · 2024-12-09 page:design-ws-012-bulk-llm-inference
  |     |     "Cache directory resolution lives in exactly one place in the caching layer and everything that needs the location calls it. I have deleted three hand-rolled path joins in review this quarter."
  |
  +-- A reporting call must leave the cache directory exactly as it found it, creating nothing and opening nothing for write
  |     reader must infer: creating a directory or a journal file counts as changing the cache, and some real caches are mounted where writes are impossible, so inspection has to be a pure read
  |     +-- [t1.r2.L4] gideon · 2025-04-17 #random
  |     |     "self-inflicted, posting so nobody else does it. I typo'd the path in my cache-poking script last night, it did a mkdir -p on the way in, and this morning's cookbook run found a shiny empty cache directory at the typo, decided nothing was cached and re-sent 38k requests. Bill is real. The script only ever wanted to count rows."
  |     +-- [t1.r2.L5] dermot · 2025-02-21 #help
  |     |     "the shared example cache on the box is mounted so only the nightly job can write to it, everybody else gets it as a read-only mount. Any script that opens the metadata sqlite the normal way dies with "attempt to write a readonly database" before it has read a single row, because sqlite wants to put a journal next to the file. Bit me twice trying to count entries."
  |     +-- [t1.r2.L6] emil · 2025-03-21 page:design-t3-plant
  |     |     "House rule for anything that only reports on the cache: connect to the metadata db with mode=ro."
  |
  +-- When there is no cache directory yet, the call should hand back counts of nothing cached instead of an error
  |     reader must infer: a machine that has never run anything is a perfectly ordinary state and the honest report for it is zero hits, not a traceback
  |     +-- [t1.r2.L7] dario · 2025-03-31 #code-review
  |     |     "fresh CI container, nothing has ever run in it, and the pre-flight estimate step went red with FileNotFoundError on the cache directory. I put a mkdir -p in the workflow to get past it, which I hate, because now the estimate step is the thing that creates the cache. Second time this month."
  |     +-- [t1.r2.L8] emil · 2025-02-25 #releases
  |     |     "same shape in the onboarding notebook. Cell two of the quickstart asks how much the run will cost, user has never generated anything, they get a traceback and file an issue saying curator is broken on their machine. Three of those in the last two weeks and all three were day-one installs."
  |     +-- [t1.r2.L9] gideon · 2025-05-01 page:handover-status-tracking-cost-reporting-and-the-v
  |     |     "For a machine with no history the truthful answer is that nothing is on disk and every request will go to the provider. That is a perfectly good number to report, all hits at zero and everything counted as going to the backend."
  |
  +-- The thing handed back has to carry the directory it actually inspected, alongside the counts
  |     reader must infer: numbers without the location they came from cannot be checked by the person reading them, so the location must travel with the numbers
  |     +-- [t1.r2.L10] gideon · 2025-02-27 #general
  |     |     "support thread from yesterday, three round trips. User pasted counts showing zero served locally, we were sure their re-run should have been almost free. I had to get them to echo their env, then ls two directories, before we worked out they had one cache from a docker session and another from their laptop shell. The counts on their own told me nothing."
  |     +-- [t1.r2.L11] dario · 2025-02-03 page:handover-request-processing-core-and-provider-bac
  |     |     "Triage note for cache questions: never believe a number a user pastes until you know the directory it came from. We ask for it on essentially every one of these tickets, and about half the time the user has switched shells or containers since their last run and does not realise there are two caches on the box."
  |     +-- [t1.r2.L12] emil · 2025-04-28 #viewer
  |     |     "cheap fix for the support loop: whatever object these reporting calls hand back should carry the directory it looked at as a field, the way the end-of-run summary already prints the db path."
  |
  +-- The counts themselves cover the last run's requests split between cache and backend, and are meant to be read before paying for a re-run
  |     reader must infer: this is the openly stated part and the other pieces attach to it
  |     +-- [t1.r2.L13] gideon · 2025-02-17 #pipeline
  |     |     "people keep asking the same question before a re-run: how much of this is already on disk. Right now the only way to answer it is to run the thing and watch the hit counter go by on the progress bar, which is too late to decide anything."
  |     +-- [t1.r2.L14] dermot · 2024-12-11 page:postmortem-2024-12-10
  |     |     "The counters we already keep per run are hits against the on-disk responses and requests that actually went out to the provider. Those are the same two numbers the summary table prints at the end."
```

**Is it recoverable from the clues alone?** yes — every part came back

What a reader given only these remarks, and no answer key, concluded:

> cache_stats() must be a strictly read-only, side-effect-free pre-flight reporter: it resolves the cache directory lazily through the caching layer's single resolver (so CURATOR_CACHE_DIR set after import still applies), opens the metadata sqlite with mode=ro without ever mkdir-ing, stat-rewriting or journalling, and reports the same two counters the end-of-run summary prints — local hits versus requests to the backend. On a missing or empty cache it returns zeros with everything counted as backend-bound instead of raising, and the object it returns carries the resolved cache/db path so a pasted result identifies which cache was actually inspected.

**Does any single remark give it away?** **Yes**, which makes this part of the task trivial:

- t1.r2.L9 closes `S3` on its own, so the other 2 remark(s) under it are decoration: L7/L8 only report the crash symptom; L9 alone states the fix — report zero-hit counts rather than er
- t1.r2.L12 closes `S4` on its own, so the other 2 remark(s) under it are decoration: L12 explicitly states the fix (include directory as a field); L10/L11 only establish the surrounding

> Re-plant 1: t1.r2.L3 closes `S1` on its own, so the other 2 remark(s) under it are decoration: L1 and L2 are individual incidents (wrong hardcoded path, load-time

> Re-plant 2: t1.r2.L9 closes `S3` on its own, so the other 2 remark(s) under it are decoration: L7/L8 only report the crash symptom; L9 alone states the fix — repo

> Re-plant 3: t1.r2.L9 closes `S3` on its own, so the other 2 remark(s) under it are decoration: L7/L8 only report the crash symptom; L9 alone states the fix — repo

> Re-plant 4: t1.r2.L9 closes `S3` on its own, so the other 2 remark(s) under it are decoration: L7/L8 only report the crash symptom; L9 alone states the fix — repo

> Re-planted 4 time(s) and still failing. Left as it is rather than made easier to force a pass.

**Every planted line, in the order an agent reading forward meets it**

| date | where | who | | covers | placement | what they say | why this room |
|---|---|---|---|---|---|---|---|
| 2024-12-09 | page:design-ws-012-bulk-llm-inference | dermot | clue | rule | passing | Cache directory resolution lives in exactly one place in the caching layer and everything that needs the location calls it. I have deleted three hand-rolled path joins in review this quarter. | the doc scopes the curator.LLM core layering, which is exactly where dermot's rule about a single cache-directory resolver belongs as guidance for new surfaces. |
| 2024-12-11 | page:postmortem-2024-12-10 | dermot | clue | observability | passing | The counters we already keep per run are hits against the on-disk responses and requests that actually went out to the provider. Those are the same two numbers the summary table prints at the end. | the writeup is about deleting downloaded responses off disk, so dermot pinning down which two per-run counters (on-disk hits vs requests sent) actually matter fits the analysis. |
| 2025-02-03 | page:handover-request-processing-core-and-provider-bac | dario | clue | observability | passing | Triage note for cache questions: never believe a number a user pastes until you know the directory it came from. We ask for it on essentially every one of these tickets, and about half the time the user has switched shells or containers since their last run and does not realise there are two caches on the box. | dario is writing down the operational habits emil is inheriting, and 'always ask which cache directory the numbers came from' is precisely that kind of triage lore. |
| 2025-02-13 | #general | dario | clue | rule | explicit | burned an hour this morning on my little cache-poking script. It reports 12 hits out of 40k and I nearly re-budgeted the whole persona run on that. Turns out the script does os.path.expanduser("~/.cache/curator") and I have had CURATOR_CACHE_DIR=/mnt/scratch/curator-cache in my shell profile since June. The numbers were from a directory nothing has written to since October. | dario is demoing his own draft cache_stats() here, so his morning of chasing bogus hit counts from the wrong cache directory is the concrete argument for resolving CURATOR_CACHE_DIR at call time. |
| 2025-02-17 | #pipeline | gideon | clue | rule | explicit | people keep asking the same question before a re-run: how much of this is already on disk. Right now the only way to answer it is to run the thing and watch the hit counter go by on the progress bar, which is too late to decide anything. | dario is asking where the draft stands and why it matters, and gideon's answer is the user need: today you only learn the hit count after the run has already started. |
| 2025-02-21 | #help | dermot | clue | scope, failure_behavior | explicit | the shared example cache on the box is mounted so only the nightly job can write to it, everybody else gets it as a read-only mount. Any script that opens the metadata sqlite the normal way dies with "attempt to write a readonly database" before it has read a single row, because sqlite wants to put a journal next to the file. Bit me twice trying to count entries. | the thread is about a helper that wrote into the stats path and broke CI, so dermot's read-only-mount sqlite failure is the same bug seen from the shared box. |
| 2025-02-25 | #releases | emil | clue | failure_behavior | explicit | same shape in the onboarding notebook. Cell two of the quickstart asks how much the run will cost, user has never generated anything, they get a traceback and file an issue saying curator is broken on their machine. Three of those in the last two weeks and all three were day-one installs. | the question on the table is whether the reporting method is urgent enough to rush into Thursday's tag, and three day-one users filing 'curator is broken' issues is the case for urgency. |
| 2025-02-26 | #pipeline | emil | clue | rule | explicit | related annoyance from the notebook walkthrough: people import curator in cell 1 and then set CURATOR_CACHE_DIR in cell 4 because that is the order the tutorial reads. The sizing helper I wrote grabs the path once when the module loads, so it kept telling them about the default directory for the rest of the session and I got two emails about it. | the room is already arguing about when in a run the cache path gets touched, and emil's notebook case shows what happens when the path is captured at import instead of when asked. |
| 2025-02-27 | #general | gideon | clue | observability | explicit | support thread from yesterday, three round trips. User pasted counts showing zero served locally, we were sure their re-run should have been almost free. I had to get them to echo their env, then ls two directories, before we worked out they had one cache from a docker session and another from their laptop shell. The counts on their own told me nothing. | the PR is up for a last look before the cut and gideon's three-round-trip support thread is the argument that bare counts are not enough to ship. |
| 2025-03-21 | page:design-t3-plant | emil | clue | scope | passing | House rule for anything that only reports on the cache: connect to the metadata db with mode=ro. | this design is about what persists in the on-disk metadata store across processes, the natural place to write down that reporting paths open it mode=ro and create nothing. |
| 2025-03-31 | #code-review | dario | clue | failure_behavior | explicit | fresh CI container, nothing has ever run in it, and the pre-flight estimate step went red with FileNotFoundError on the cache directory. I put a mkdir -p in the workflow to get past it, which I hate, because now the estimate step is the thing that creates the cache. Second time this month. | emil is picking at where the hook sits and how it can be bypassed, and dario's fresh-CI FileNotFoundError shows the hook currently forces a mkdir before anything has run. |
| 2025-04-17 | #random | gideon | clue | scope | explicit | self-inflicted, posting so nobody else does it. I typo'd the path in my cache-poking script last night, it did a mkdir -p on the way in, and this morning's cookbook run found a shiny empty cache directory at the typo, decided nothing was cached and re-sent 38k requests. Bill is real. The script only ever wanted to count rows. | the channel has already turned into war stories about money burned on unrecoverable work, so gideon's typo'd cache path that re-sent 38k requests lands as the next confession. |
| 2025-04-28 | #viewer | emil | clue | observability | explicit | cheap fix for the support loop: whatever object these reporting calls hand back should carry the directory it looked at as a field, the way the end-of-run summary already prints the db path. | konrad cannot tell two runs apart from the metadata panel, so emil's proposal that reporting output carry the directory it read is the fix the room is already reaching for. |
| 2025-05-01 | page:handover-status-tracking-cost-reporting-and-the-v | gideon | clue | failure_behavior | passing | For a machine with no history the truthful answer is that nothing is on disk and every request will go to the provider. That is a perfectly good number to report, all hits at zero and everything counted as going to the backend. | gideon is handing off cost reporting semantics, so the rule that a cold machine reports zero hits rather than raising is exactly the contract the next owner needs. |

**Spread:** 2 source(s), 9 distinct week(s), 12 room(s), first 2024-12-09 last 2025-05-01.

---

## t2 — Structured output schema validation before dispatch

**The agent is told:** Before sending any request to a backend, validate that the `response_format` Pydantic model passed to `curator.LLM` is compatible with structured-output mode for the selected model, and fail early with a clear message if not.

**Where it gets designed:** 12 conversation(s) between 2025-02-23 and 2025-04-01, plus a design page and a mail thread. None of them state the hidden requirement.

### t2.r1 — the hidden requirement  ·  T2, T7

| part | what it actually requires |
|---|---|
| `rule` | Compatibility must be checked against a maintained list of model name patterns known to support structured outputs (e.g. gpt-4o family, o3 family per the existing model-support list), and the check must happen once at `LLM.__init__` time, not per-row at request time. <br>*carried by: t2.r1.L1, t2.r1.L2, t2.r1.L3, t2.r1.L4* |
| `scope` | `LLM.__init__` only. <br>*carried by: t2.r1.L5, t2.r1.L6, t2.r1.L7* |
| `failure_behavior` | An unsupported model + response_format combination must raise `ValueError` immediately at construction, before `__call__` ever touches the dataset, so failures show up before any API spend. <br>*carried by: t2.r1.L6, t2.r1.L8, t2.r1.L9, t2.r1.L10* |

**What they decided first, and later reversed:** The check was originally deferred to the first request's response, relying on the backend's own 400 error to surface incompatibility — this was reversed since it meant burning at least one paid request before the user found out.

**The reasoning an agent has to do**

```
the requirement
  |
  +-- Which models can accept a response_format is decided by matching the model name against the one maintained table of supported name patterns, and that table has to cover whole families (gpt-4o snapshots, o3 variants) rather than exact names.
  |     reader must infer: If dated snapshots and newly shipped family members both fell through the not-supported branch, and the fix everyone reaches for is 'read it off the support table and match the pattern', then capability decisions belong to that table's patterns and nowhere else.leaves
  |     +-- [t2.r1.L1] dario · 2025-01-01 page:notes-2024-12-30
  |     |     "Maintenance note for whoever touches provider capabilities next: the support table is the only place we are supposed to record which model names can take a json schema. I went looking last month and found three separate dicts in the codebase with their own opinion, all of them stale by a couple of releases. If you need to know what a model can do, read the table."
  |     +-- [t2.r1.L2] gideon · 2025-03-17 #engineering
  |     |     "someone in help pasted a run on gpt-4o-2024-08-06 where our capability lookup came back false, so they got shunted onto the plain text path. the map only had the bare `gpt-4o` key in it. providers keep bolting dates onto these names, exact-key lookups are never going to survive that"
  |     +-- [t2.r1.L3] emil · 2025-05-30 #releases
  |     |     "lost a morning to this last week: o3-mini shipped with schema support day one and our table had no o3 entry at all, so everything o3 fell straight through to the unsupported branch and I sat there rewriting my pydantic model convinced it was me"
  |     +-- [t2.r1.L4] dermot · 2025-05-07 page:postmortem-2025-05-06
  |     |     "review comment I keep leaving: if your branch depends on what a model can do, look it up in the support table and add the pattern there if it is missing. do not grow a fourth capability dict next to the one you are writing. the table is cheap to extend and everything reading it improves at once"
  |
  +-- The compatibility decision depends only on the constructor arguments, so it must be settled once when the LLM object is built rather than recomputed for every row on the request path.
  |     reader must infer: A lookup that returns the same answer for every row, plus a constructor that hands back an object which can never work, together point at moving the decision into the constructor.
  |     +-- [t2.r1.L5] gideon · 2025-04-21 #help
  |     |     "profiled the 40k row poem run because the bars were stuttering. we do the capability lookup per request, so that is 40k passes over the same model string and 40k identical debug lines in the log. the answer cannot change between row 1 and row 40000, the model name is fixed the moment you configure the thing"
  |     +-- [t2.r1.L6] dario · 2025-03-14 #code-review
  |     |     "this bit me again in a notebook. cell four builds the LLM and returns happily, cell five hands it the dataset and twenty minutes into the map it turns out the combination was never going to work. the object was already unusable when cell four finished and it told me nothing"
  |     +-- [t2.r1.L7] emil · 2025-02-04 page:handover-request-processing-core-and-provider-bac
  |     |     "House rule for the core class, since this comes up in review a lot: `LLM.__init__` already resolves the backend, checks the api key env var is present and normalises the model name. By the time `__call__` has the dataset in hand we have committed to the run and the honest options get much worse."
  |
  +-- When the combination cannot work, construction must raise ValueError there and then, before the dataset is ever iterated or a single request billed.
  |     reader must infer: A warning-and-continue path plus thousands of paid requests rejected by the provider means the only acceptable outcome is the same hard config error the constructor already uses for bad settings.
  |     +-- [t2.r1.L8] dermot · 2025-02-07 #pipeline
  |     |     "last night's cookbook run pushed somewhere around 9k requests before the provider started 400ing on the schema and the whole thing unwound. real money, zero usable rows. finding out what our own request can't do from someone else's error response is not a great place to be"
  |     +-- [t2.r1.L9] emil · 2025-03-24 #releases
  |     |     "the other flavour of this is worse: on some backends we log a warning that the format cannot be honoured and then just carry on. you get a green run, a full parquet, and every row is an unparsed string you find out about two days later. I would much rather it blow up in my face on line one than hand me a plausible looking dataset"
  |     +-- [t2.r1.L10] dario · 2025-03-04 page:postmortem-2025-03-01
  |     |     "API convention, please keep to it: bad configuration handed to the core class raises ValueError, same as an unknown backend name or a base_url we cannot parse. Users wrap their setup block in try/except ValueError and script around it."
```

**Is it recoverable from the clues alone?** yes — every part came back

What a reader given only these remarks, and no answer key, concluded:

> The compatibility check must happen once in `LLM.__init__`, driven solely by pattern-based lookups in the single central capability support table, and must raise a plain `ValueError` with a clear model/schema-specific message before any request or money is spent. It must never silently fall back to plain text or warn-and-continue, and it must not add another capability dict or repeat per-request lookups and debug logging.

**With the reversed decision in the room — the corpus as an agent actually meets it.** Every part still comes through.

    rule: 3/3, scope: 3/3, failure_behavior: 3/3

> The team wants the structured-output check moved to `LLM.__init__` and driven entirely off the single provider support table with pattern-based (not exact-key) model matching, evaluated once per instance, so a bad config raises a plain `ValueError` with the model named — before any request is sent, any money is spent, or any partial dataset is produced. It must never probe the provider, never silently downgrade to plain text, never add a fourth capability dict, and never falsely reject models or break custom base_urls/proxies.

**Does any single remark give it away?** No — every part needs more than one line.

> Re-plant 1: t2.r1.L7 closes `S2` on its own, so the other 2 remark(s) under it are decoration: L7 states the governing rule directly — anything depending only on 

**Every planted line, in the order an agent reading forward meets it**

| date | where | who | | covers | placement | what they say | why this room |
|---|---|---|---|---|---|---|---|
| 2024-11-26 | #pipeline | dermot | ↩︎ reversal | — | explicit | On the response_format compatibility question: we are not keeping a table of which models accept a json schema. That list goes stale the week after we write it and then we are the ones rejecting a model that actually works fine. The provider is the source of truth here. Send the request, and if the model can't do structured outputs we get a 400 back with the provider's own wording and surface that to the user as-is. One request's worth of spend is a fair price for not maintaining a whitelist, and the error text is better than anything we'd write ourselves. | — |
| 2024-12-27 | #code-review | dario | ↩︎ reversal | — | passing | Also please don't add validation into LLM.__init__ for this. Construction should stay cheap and dumb, it just holds config. The moment __init__ starts asserting things about model names we get bug reports from everyone pointing at a new base_url or a proxy we've never heard of. Keep the checking where the request happens, the response tells us what we need to know. | — |
| 2025-01-01 | page:notes-2024-12-30 | dario | clue | rule | passing | Maintenance note for whoever touches provider capabilities next: the support table is the only place we are supposed to record which model names can take a json schema. I went looking last month and found three separate dicts in the codebase with their own opinion, all of them stale by a couple of releases. If you need to know what a model can do, read the table. | The week's notes are dominated by provider-integration work, so a maintenance rule about the single support table for model capabilities is exactly the takeaway that belongs in that recap. |
| 2025-02-04 | page:handover-request-processing-core-and-provider-bac | emil | clue | scope | passing | House rule for the core class, since this comes up in review a lot: `LLM.__init__` already resolves the backend, checks the api key env var is present and normalises the model name. By the time `__call__` has the dataset in hand we have committed to the run and the honest options get much worse. | Handing over the request-processing core is the moment to state the house rule about what __init__ settles versus what __call__ is stuck with. |
| 2025-02-07 | #pipeline | dermot | clue | failure_behavior | explicit | last night's cookbook run pushed somewhere around 9k requests before the provider started 400ing on the schema and the whole thing unwound. real money, zero usable rows. finding out what our own request can't do from someone else's error response is not a great place to be | The room is chewing on empty responses and a request-failure summary, so a 9k-request run killed by provider schema 400s is the concrete failure mode under discussion. |
| 2025-03-04 | page:postmortem-2025-03-01 | dario | clue | failure_behavior | passing | API convention, please keep to it: bad configuration handed to the core class raises ValueError, same as an unknown backend name or a base_url we cannot parse. Users wrap their setup block in try/except ValueError and script around it. | The postmortem is about a bad configuration default causing a double revert, which is the right moment to restate that bad configuration raises ValueError and nothing bespoke. |
| 2025-03-14 | #code-review | dario | clue | scope, failure_behavior | explicit | this bit me again in a notebook. cell four builds the LLM and returns happily, cell five hands it the dataset and twenty minutes into the map it turns out the combination was never going to work. the object was already unusable when cell four finished and it told me nothing | Dario is asking which hook point to wire schema_check into, and his notebook story is the argument for doing it in the constructor rather than mid-map. |
| 2025-03-17 | #engineering | gideon | clue | rule | explicit | someone in help pasted a run on gpt-4o-2024-08-06 where our capability lookup came back false, so they got shunted onto the plain text path. the map only had the bare `gpt-4o` key in it. providers keep bolting dates onto these names, exact-key lookups are never going to survive that | The check-in is stuck on where the capability rules should come from, and a real user hitting a dated model name that misses the exact key is direct evidence about the rule source. |
| 2025-03-24 | #releases | emil | clue | failure_behavior | explicit | the other flavour of this is worse: on some backends we log a warning that the format cannot be honoured and then just carry on. you get a green run, a full parquet, and every row is an unparsed string you find out about two days later. I would much rather it blow up in my face on line one than hand me a plausible looking dataset | The validator PR has two open questions before the Thursday cut, and emil is answering one of them: warn-and-continue produces plausible garbage, so it should raise. |
| 2025-04-21 | #help | gideon | clue | scope | explicit | profiled the 40k row poem run because the bars were stuttering. we do the capability lookup per request, so that is 40k passes over the same model string and 40k identical debug lines in the log. the answer cannot change between row 1 and row 40000, the model name is fixed the moment you configure the thing | The room is already dissecting per-row overhead across a 20k-row pass, and a redundant per-request capability lookup is another constant cost paid on every row. |
| 2025-05-07 | page:postmortem-2025-05-06 | dermot | clue | rule | passing | review comment I keep leaving: if your branch depends on what a model can do, look it up in the support table and add the pattern there if it is missing. do not grow a fourth capability dict next to the one you are writing. the table is cheap to extend and everything reading it improves at once | The postmortem is about a structured-output revert, so dermot's standing review note against spawning another capability dict instead of extending the table is the corrective lesson. |
| 2025-05-30 | #releases | emil | clue | rule | explicit | lost a morning to this last week: o3-mini shipped with schema support day one and our table had no o3 entry at all, so everything o3 fell straight through to the unsupported branch and I sat there rewriting my pydantic model convinced it was me | The room is reviewing what o3 support actually landed, so emil's morning lost to o3 falling through the unsupported branch explains why the table entry mattered. |

**Spread:** 2 source(s), 11 distinct week(s), 9 room(s), first 2024-11-26 last 2025-05-30.

---

### t2.r2 — the hidden requirement  ·  T4, T6

| part | what it actually requires |
|---|---|
| `rule` | The model-support list used for this check must be the same list maintained for the existing structured-output feature (the one already updated when new models like o3 are added) — this task must not introduce a second, separate list that could drift out of sync with it. <br>*carried by: t2.r2.l1, t2.r2.l2, t2.r2.l3, t2.r2.l4, t2.r2.l5, t2.r2.l6, t2.r2.l7* |
| `scope` | Reuse of the existing model-support list only. <br>*carried by: t2.r2.l8, t2.r2.l9* |

**The reasoning an agent has to do**

```
the requirement
  |
  +-- Curator already has one maintained place that records which models support structured output, and that place is what gets edited when a new model (o3) arrives; the structured-output code path reads it through a lookup helper.
  |     reader must infer: If a one-line edit in that constant is what makes structured output start working for a new model, then that constant plus its helper is the maintained record of model support, not an incidental detail.
  |     +-- [t2.r2.l1] dario · 2025-04-17 #pipeline
  |     |     "o3 support was basically free for us. I put the model name into STRUCTURED_OUTPUT_MODELS the morning it went live and structured output worked on the online path that afternoon, no other diff."
  |     +-- [t2.r2.l2] emil · 2025-05-06 #incidents
  |     |     "For anyone reading the online processor: before it puts response_format on the payload it calls supports_structured_output(model), which is just a membership check. If the check says no you get plain text back and a warning, nothing louder."
  |     +-- [t2.r2.l3] gideon · 2025-02-03 #pipeline
  |     |     "Our new-model routine hasn't changed in months: model name into the support list, price entry, one smoke run against a two-field pydantic model. Step one is the only step people actually forget."
  |
  +-- When a code path keeps its own copy of the supported-model names instead of going through that helper, the copies go stale and users hit contradictory behaviour; the team's standing answer in review is to delete the new copy and call the existing helper.
  |     reader must infer: Two independent reports of the same shape of bug (a model accepted in one path, refused in another) plus a reviewer's instruction to call the helper add up to a norm about copies, without anyone naming the norm.
  |     +-- [t2.r2.l4] emil · 2025-03-12 #pipeline
  |     |     "Lost most of yesterday to batch mode. The model was in the support list, online run gave me clean JSON objects, the batch submission for the exact same config refused to attach a schema. Turned out the batch submitter was checking against a tuple of model names it keeps in its own file, last touched in January."
  |     +-- [t2.r2.l5] dermot · 2025-02-14 #pipeline
  |     |     "Same flavour of thing on the offline path. vLLM run told a user their model can't do schema-constrained output while the identical model works fine over the API, because local-offline hardcodes its own set of names. That's the third file I've found this year carrying the same model strings around."
  |     +-- [t2.r2.l6] gideon · 2025-04-25 #random
  |     |     "Two support tickets in a row about o3 getting a schema in one place and not another before I twigged that there was more than one list of model names in the tree. I'd rather explain a hard error than explain that."
  |     +-- [t2.r2.l7] dario · 2025-03-10 #code-review
  |     |     "Left a comment on the kluster PR: drop the set of model names you added and call supports_structured_output instead. That helper is already what we edit when a new model lands, and I don't want to be grepping for model strings again next time o3-mini ships."
  |
  +-- The thing that must have a single home is the model capability/support list specifically; the other per-provider tables (pricing/cost, rate-limit defaults, base URLs) are deliberately separate and nobody wants them consolidated.
  |     reader must infer: People defending the separateness of pricing and rate-limit tables while complaining only about capability data are drawing a boundary around which table the one-home rule applies to.
  |     +-- [t2.r2.l8] emil · 2025-03-24 #engineering
  |     |     "Not keen on folding the cost table into the same place. Pricing comes down from litellm and changes weekly, and half of it is per-region; if it lives next to capability data someone will start hand-editing prices. Keep the money table where it is."
  |     +-- [t2.r2.l9] gideon · 2024-12-10 #engineering
  |     |     "Per-provider rate limit defaults are duplicated all over and I'm fine with it, they're env-overridable and nobody has ever filed a ticket about them. It's the model capability stuff that generates the tickets, so let's keep any tidying pointed at that and leave the limits alone."
```

**Is it recoverable from the clues alone?** yes — every part came back

What a reader given only these remarks, and no answer key, concluded:

> The remarks imply that structured-output capability must be decided by the one existing `supports_structured_output`/`STRUCTURED_OUTPUT_MODELS` helper, with every duplicated model-name list (kluster, batch submitter, local/offline vLLM) deleted so online, batch and offline paths always agree and adding a model stays a one-line edit. Unsupported combinations must raise a clear, pre-dispatch hard error naming the model rather than silently degrading to plain text with a warning, while rate-limit defaults and the litellm-sourced pricing table are explicitly left alone.

**Does any single remark give it away?** No — every part needs more than one line.

**Every planted line, in the order an agent reading forward meets it**

| date | where | who | | covers | placement | what they say | why this room |
|---|---|---|---|---|---|---|---|
| 2024-12-10 | #engineering | gideon | clue | scope | passing | Per-provider rate limit defaults are duplicated all over and I'm fine with it, they're env-overridable and nobody has ever filed a ticket about them. It's the model capability stuff that generates the tickets, so let's keep any tidying pointed at that and leave the limits alone. | A refactor workstream is kicking off next to dario's rate-limit work, so gideon scoping the cleanup away from env-overridable rate limit defaults and toward model capability data is a direct steer on the new workstream. |
| 2025-02-03 | #pipeline | gideon | clue | rule | passing | Our new-model routine hasn't changed in months: model name into the support list, price entry, one smoke run against a two-field pydantic model. Step one is the only step people actually forget. | It's a heavy provider-integrations day with critical items in flight, so gideon laying out the standing new-model checklist and which step gets skipped is on-topic housekeeping. |
| 2025-02-14 | #pipeline | dermot | clue | rule | explicit | Same flavour of thing on the offline path. vLLM run told a user their model can't do schema-constrained output while the identical model works fine over the API, because local-offline hardcodes its own set of names. That's the third file I've found this year carrying the same model strings around. | With a vLLM test fix and provider-integrations churn on the table, dermot reporting that local-offline hardcodes its own model names lands as the offline half of the same problem. |
| 2025-03-10 | #code-review | dario | clue | rule | explicit | Left a comment on the kluster PR: drop the set of model names you added and call supports_structured_output instead. That helper is already what we edit when a new model lands, and I don't want to be grepping for model strings again next time o3-mini ships. | It's a review-backlog room where dario is working through open PRs, so reporting the comment he left telling the kluster PR to call the shared helper instead of its own name set is exactly the review outcome being tracked. |
| 2025-03-12 | #pipeline | emil | clue | rule | explicit | Lost most of yesterday to batch mode. The model was in the support list, online run gave me clean JSON objects, the batch submission for the exact same config refused to attach a schema. Turned out the batch submitter was checking against a tuple of model names it keeps in its own file, last touched in January. | The room is already on batch-mode plus provider-integration commits with a new backend PR in review, so emil's lost day to a batch submitter keeping its own stale model tuple is the concrete case in point. |
| 2025-03-24 | #engineering | emil | clue | scope | explicit | Not keen on folding the cost table into the same place. Pricing comes down from litellm and changes weekly, and half of it is per-region; if it lives next to capability data someone will start hand-editing prices. Keep the money table where it is. | The cost estimation revamp is landing here alongside other consolidation work, so emil's objection to folding the litellm-derived pricing table in next to capability data answers the scoping question on the table. |
| 2025-04-17 | #pipeline | dario | clue | rule | explicit | o3 support was basically free for us. I put the model name into STRUCTURED_OUTPUT_MODELS the morning it went live and structured output worked on the online path that afternoon, no other diff. | The room is explicitly on making sure the structured-output path holds up across today's provider-integrations and online-processor commits, so dario's account of adding o3 to the support list and getting it working same-day is a direct answer. |
| 2025-04-25 | #random | gideon | clue | rule | explicit | Two support tickets in a row about o3 getting a schema in one place and not another before I twigged that there was more than one list of model names in the tree. I'd rather explain a hard error than explain that. | The room is already trading stories about surprising users with inconsistent behaviour, so gideon's two o3 support tickets and his preference for a hard error fit the griping in progress. |
| 2025-05-06 | #incidents | emil | clue | rule | explicit | For anyone reading the online processor: before it puts response_format on the payload it calls supports_structured_output(model), which is just a membership check. If the check says no you get plain text back and a warning, nothing louder. | A structured-output commit was just reverted and main is in the trees, so emil spelling out that the online path only does a membership check and silently degrades to plain text explains the failure mode under discussion. |

**Spread:** 1 source(s), 8 distinct week(s), 5 room(s), first 2024-12-10 last 2025-05-06.

---

## t3 — Batch job status persistence across process restarts

**The agent is told:** Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

**Where it gets designed:** 11 conversation(s) between 2025-03-21 and 2025-04-27, plus a design page and a mail thread. None of them state the hidden requirement.

### t3.r1 — the hidden requirement  ·  T5, T7

| part | what it actually requires |
|---|---|
| `rule` | The batch job ID must be persisted to the on-disk cache directory (keyed the same way as the existing prompt cache) immediately after successful submission, before polling begins, so a crash during polling doesn't lose the ability to resume. <br>*carried by: t3.r1.L1, t3.r1.L2, t3.r1.L3, t3.r1.L4, t3.r1.L5, t3.r1.L8* |
| `scope` | Batch job ID persistence, submission-time only. <br>*carried by: t3.r1.L2, t3.r1.L3, t3.r1.L6, t3.r1.L7* |
| `failure_behavior` | If persistence itself fails (disk full, permissions), the batch submission must still be allowed to proceed — losing resumability is preferable to blocking the job outright, but a warning must be logged. <br>*carried by: t3.r1.L5, t3.r1.L9, t3.r1.L10, t3.r1.L11* |

**What they decided first, and later reversed:** An earlier draft persisted the batch job ID only after the job completed, which was reversed once it was clear that defeated the whole purpose — a crash during the (long) pending/running window would still cause a duplicate resubmission.

**The reasoning an agent has to do**

```
the requirement
  |
  +-- Whatever a rerun needs in order to find an already-submitted job has to sit on disk inside the run's cache directory, under the same fingerprint the prompt/response cache already uses, not in memory and not in an ad-hoc sidecar file.
  |     reader must infer: If the identifier lives anywhere other than the fingerprint-keyed cache dir, it either vanishes with the process or goes stale relative to the prompt, so the only safe home is the one the cache already computes and honours.
  |     +-- [t3.r1.L1] dario · 2025-03-24 #pipeline
  |     |     "Lost a 12 hour Anthropic batch yesterday, ssh session died and took the python process with it. The id only ever existed inside that process, so I spent the morning reading batch ids off the provider console and pasting one into a scratch script to pull the results down. Fine for me, absolutely not something I'd tell a user to do."
  |     +-- [t3.r1.L2] emil · 2025-04-11 #cookbooks
  |     |     "When I was poking at this last month I stashed the id in a .curator_batch file in the working directory. Worked right up until I edited the prompt template, reran, and it cheerfully picked the previous job back up and handed me answers for the old prompts. The response cache didn't make that mistake, my file did."
  |     +-- [t3.r1.L3] gideon · 2025-04-01 thread:mail-t3-plant
  |     |     "Support thread worth reading: user points CURATOR_CACHE_DIR at /mnt/shared so they can start a run on the laptop and finish it on the box. Their expectation is that everything a rerun needs is under that path. Today the request and response files follow CURATOR_CACHE_DIR and nothing else does, so "resumable" means two different things depending on which half of the run you're talking about, and they noticed."
  |     +-- [t3.r1.L4] dermot · 2025-04-07 page:design-ws-055-release-and-ci
  |     |     "Recording the layout while I'm in here. The run fingerprint hashes the prompt function, the model name, the generation params and the dataset; one directory per fingerprint under the cache root; requests and responses live in it. CURATOR_DISABLE_CACHE bypasses that directory cleanly. We have not been consistent about applying that to newer state."
  |
  +-- That write has to happen as soon as the provider accepts the submission and returns an identifier, before the polling wait begins, because the whole recovery window is the wait.
  |     reader must infer: State recorded after the wait is worthless for recovering from a crash during the wait, and since the submit call itself takes milliseconds, the only useful ordering is submit-then-record-then-poll.
  |     +-- [t3.r1.L5] dario · 2025-04-03 #pipeline
  |     |     "All the wall clock in a batch run is the poll loop. Submit at 11, provider finishes somewhere around 6, and the only moment we write anything durable is after the download comes back. Kill it at hour three and there is nothing on disk that so much as knows a job was ever opened. That bit me twice this week."
  |     +-- [t3.r1.L6] emil · 2025-03-31 page:design-ws-050-batch-mode
  |     |     "Went through the batch tickets from the last two months. Laptop lid closed, CI runner hit its six hour cap, OOM killer, one power cut. Every single one of them died while waiting on the provider. Nobody has ever managed to die inside the submit call itself, that thing returns in about 200ms."
  |     +-- [t3.r1.L7] gideon · 2025-04-03 #viewer
  |     |     "Saw two jobs on one account's dashboard four minutes apart, identical request counts. Traced it: the user ctrl-c'd while the first status line was still printing and started the script again. So the second submission happened out of a window of maybe ninety seconds, before we had ever come back from the provider with a status."
  |     +-- [t3.r1.L8] dermot · 2025-03-27 thread:mail-t3-plant
  |     |     "For what it's worth, the online processor appends to the responses file the moment a request is accepted, not when it comes back. That ordering was deliberate and we argued about it for a while."
  |
  +-- If that write fails (full disk, read-only or wrong-permission cache dir), the job that has already been accepted must carry on rather than aborting, and the failed write has to be reported at warning level rather than swallowed.
  |     reader must infer: A cache write is an optimisation for the next run, so its failure should downgrade resumability, not destroy work already paid for, but a silent downgrade is indistinguishable from a bug and has to be announced.
  |     +-- [t3.r1.L9] dario · 2025-04-09 #incidents
  |     |     "help thread from this morning: user had CURATOR_CACHE_DIR on a volume with 0 bytes free. Submit went through fine, provider has their 40k requests queued and is billing for them, and then the process fell over with an OSError coming out of the cache write, not out of the API client. So they paid for a batch and walked away with a traceback."
  |     +-- [t3.r1.L10] emil · 2025-04-24 #code-review
  |     |     "Adjacent gripe. The one place we do already wrap a cache write in try/except, the except body is a bare pass. Burned an hour last week wondering why a rerun redid everything from scratch; the write had failed on a permissions thing on a mounted dir and we never said one word about it. If we're going to carry on regardless then it needs to come out at warning level with the path in it, otherwise it's indistinguishable from the cache just not working."
  |     +-- [t3.r1.L11] dermot · 2025-02-05 thread:mail-t1-plant
  |     |     "Line I'd like us to actually hold to, since it keeps coming up in review. A cache write is an optimisation for the next run. Failing one makes the next run more expensive, it does not make this run invalid. So nothing that has already cost the user money gets aborted because we couldn't put a file on disk, we take the hit on the rerun and carry on."
```

**Is it recoverable from the clues alone?** yes — every part came back

What a reader given only these remarks, and no answer key, concluded:

> The batch id must be written durably into the fingerprint-keyed cache directory under CURATOR_CACHE_DIR the instant submit returns and before polling begins, so any re-run of the identical script resumes the existing job automatically while a changed prompt/model/params/dataset (or a cleared/disabled cache) forces a fresh submission. If that write fails, the paid-for run continues to completion regardless, but the failure must surface as a warning naming the exception and the path rather than being silently swallowed.

**With the reversed decision in the room — the corpus as an agent actually meets it.** Every part still comes through.

    rule: 3/3, scope: 3/3, failure_behavior: 3/3

> The batch id must be persisted the instant the provider accepts the submission — before any polling — into the existing fingerprint-keyed directory under CURATOR_CACHE_DIR alongside requests/responses, so it is cache-clearable, CURATOR_DISABLE_CACHE-respecting, shareable across machines, and immune to false resumes after prompt/model/param/dataset changes. Write failures must never abort a run the user has already paid for, but must surface as a warning naming the path rather than a silent pass, and stale/failed/expired recorded batches must be discarded in favour of a fresh submit.

**Does any single remark give it away?** No — every part needs more than one line.

> Re-plant 1: t3.r1.L4 closes `SC1` on its own, so the other 3 remark(s) under it are decoration: L4 states the governing rule — anything a rerun needs lives in the

**Every planted line, in the order an agent reading forward meets it**

| date | where | who | | covers | placement | what they say | why this room |
|---|---|---|---|---|---|---|---|
| 2024-12-20 | #code-review | dario | ↩︎ reversal | — | passing | On the batch id persistence bit: we write the id into the cache dir when the batch comes back done, not before. A record that points at a batch we haven't confirmed anything about is just a landmine for the next run, and I'd rather have no entry than an entry we can't trust. So the write happens off the terminal status, same place we write the reassembled results. | — |
| 2025-02-04 | #code-review | emil | ↩︎ reversal | — | passing | Agreed on doing the id write on completion. Half the providers hand you back a batch object that goes to failed or expired within a minute of submit, and if we've already got that id sitting on disk every rerun goes and polls a dead job. Completion is the only point where the id means something, so that's where it gets recorded. | — |
| 2025-02-05 | thread:mail-t1-plant | dermot | clue | failure_behavior | passing | Line I'd like us to actually hold to, since it keeps coming up in review. A cache write is an optimisation for the next run. Failing one makes the next run more expensive, it does not make this run invalid. So nothing that has already cost the user money gets aborted because we couldn't put a file on disk, we take the hit on the rerun and carry on. | That thread is hashing out cache semantics generally, which is the right place to state the principle that a failed cache write costs the next run, not this one. |
| 2025-03-24 | #pipeline | dario | clue | rule | explicit | Lost a 12 hour Anthropic batch yesterday, ssh session died and took the python process with it. The id only ever existed inside that process, so I spent the morning reading batch ids off the provider console and pasting one into a scratch script to pull the results down. Fine for me, absolutely not something I'd tell a user to do. | The room is already chewing on emil's rebooted 40k-row batch resubmitting itself, and dario's own lost 12-hour batch plus console-scraping workaround is the second data point that says the id needs to live outside the process. |
| 2025-03-27 | thread:mail-t3-plant | dermot | clue | rule | passing | For what it's worth, the online processor appends to the responses file the moment a request is accepted, not when it comes back. That ordering was deliberate and we argued about it for a while. | The thread is deciding when durable state should be written for a pending batch, and dermot supplies the existing precedent: the online processor records on accept, not on return. |
| 2025-03-31 | page:design-ws-050-batch-mode | emil | clue | scope | passing | Went through the batch tickets from the last two months. Laptop lid closed, CI runner hit its six hour cap, OOM killer, one power cut. Every single one of them died while waiting on the provider. Nobody has ever managed to die inside the submit call itself, that thing returns in about 200ms. | The batch-mode workstream design is where the failure survey belongs: every ticket died during the wait, never during the 200ms submit, which sets the requirement for where state gets written. |
| 2025-04-01 | thread:mail-t3-plant | gideon | clue | rule, scope | passing | Support thread worth reading: user points CURATOR_CACHE_DIR at /mnt/shared so they can start a run on the laptop and finish it on the box. Their expectation is that everything a rerun needs is under that path. Today the request and response files follow CURATOR_CACHE_DIR and nothing else does, so "resumable" means two different things depending on which half of the run you're talking about, and they noticed. | The thread is working out where restart state should live, and the support case about CURATOR_CACHE_DIR on a shared mount shows users already expect everything a rerun needs under that one path. |
| 2025-04-03 | #pipeline | dario | clue | rule, failure_behavior | explicit | All the wall clock in a batch run is the poll loop. Submit at 11, provider finishes somewhere around 6, and the only moment we write anything durable is after the download comes back. Kill it at hour three and there is nothing on disk that so much as knows a job was ever opened. That bit me twice this week. | emil has just found finished, paid-for batches with no local record, and dario's timeline of the poll loop explains exactly why nothing on disk knows the job was ever opened. |
| 2025-04-03 | #viewer | gideon | clue | scope | explicit | Saw two jobs on one account's dashboard four minutes apart, identical request counts. Traced it: the user ctrl-c'd while the first status line was still printing and started the script again. So the second submission happened out of a window of maybe ninety seconds, before we had ever come back from the provider with a status. | gideon is asking what the CLI shows when a run reattaches, and his duplicate-submission trace shows the dangerous window is before the first status line ever completes. |
| 2025-04-07 | page:design-ws-055-release-and-ci | dermot | clue | rule | passing | Recording the layout while I'm in here. The run fingerprint hashes the prompt function, the model name, the generation params and the dataset; one directory per fingerprint under the cache root; requests and responses live in it. CURATOR_DISABLE_CACHE bypasses that directory cleanly. We have not been consistent about applying that to newer state. | He is already writing up structure and test expectations, so recording the fingerprint-directory rule of thumb — and the admission that newer state ignores it — belongs in the doc he's drafting. |
| 2025-04-09 | #incidents | dario | clue | failure_behavior | explicit | help thread from this morning: user had CURATOR_CACHE_DIR on a volume with 0 bytes free. Submit went through fine, provider has their 40k requests queued and is billing for them, and then the process fell over with an OSError coming out of the cache write, not out of the API client. So they paid for a batch and walked away with a traceback. | The incident is about money burned by batch state going missing, and this help thread is the same wound from the other side — a submit that billed the user and then died in the cache write. |
| 2025-04-11 | #cookbooks | emil | clue | rule, scope | explicit | When I was poking at this last month I stashed the id in a .curator_batch file in the working directory. Worked right up until I edited the prompt template, reran, and it cheerfully picked the previous job back up and handed me answers for the old prompts. The response cache didn't make that mistake, my file did. | dermot is asking precisely what reattach does when the reproduction script is edited between runs, and emil's .curator_batch experiment is the concrete answer: a bare id file happily returns answers for the old prompts. |
| 2025-04-24 | #code-review | emil | clue | failure_behavior | explicit | Adjacent gripe. The one place we do already wrap a cache write in try/except, the except body is a bare pass. Burned an hour last week wondering why a rerun redid everything from scratch; the write had failed on a permissions thing on a mounted dir and we never said one word about it. If we're going to carry on regardless then it needs to come out at warning level with the path in it, otherwise it's indistinguishable from the cache just not working. | The review is line-by-line on dario's persistence code and dermot is already flagging its write path, so the existing swallowed cache-write exception is a directly relevant review comment. |

**Spread:** 3 source(s), 6 distinct week(s), 9 room(s), first 2024-12-20 last 2025-04-24.

---

### t3.r2 — the hidden requirement  ·  T5, T8

| part | what it actually requires |
|---|---|
| `rule` | On restart, before resuming an existing batch job ID, the code must verify the persisted job's provider, model name, and request payload hash still match the current run's configuration; a mismatch must cause a fresh submission rather than resuming a stale/incompatible job. <br>*carried by: t3.r2.l_prov_dario, t3.r2.l_prov_emil, t3.r2.l_prov_gideon, t3.r2.l_model_dermot, t3.r2.l_model_gideon, t3.r2.l_model_emil, t3.r2.l_pay_emil, t3.r2.l_pay_dermot, t3.r2.l_pay_dario* |
| `scope` | Resume-time validation. <br>*carried by: t3.r2.l_prov_emil, t3.r2.l_model_emil, t3.r2.l_pay_dario* |
| `failure_behavior` | Mismatch causes a fresh submission with a logged reason for why the old job was not resumed, not a silent resume of incompatible results. <br>*carried by: t3.r2.l_beh_dermot, t3.r2.l_beh_gideon, t3.r2.l_beh_emil* |

**The reasoning an agent has to do**

```
the requirement
  |
  +-- A persisted batch job may only be picked back up if the provider/backend it was submitted against is the same one the current run is configured for.
  |     reader must infer: If resuming under a different backend gives 404 loops and nonsense summaries, then the backend the job was submitted with is part of what makes a stored job reusable.
  |     +-- [t3.r2.l_prov_dario] dario · 2025-04-18 #incidents
  |     |     "heads up, I killed a run mid-batch, flipped the backend from openai to anthropic in the same script and reran, and it went straight back to polling the openai batch id from the first attempt. only spotted it because the id in the log still had the openai shape on it."
  |     +-- [t3.r2.l_prov_emil] emil · 2025-04-02 #code-review
  |     |     "related annoyance: the pending job id gets parked in the run dir keyed off the dataset only, so the plain openai path and the azure deployment of the same model land in the same slot. moved a cookbook over to azure last week, the restart polled a job that endpoint doesn't own and I sat in a 404 retry loop for twenty minutes before giving up and wiping the dir by hand."
  |     +-- [t3.r2.l_prov_gideon] gideon · 2025-04-14 #viewer
  |     |     "got a weird one in the summary table after a restart: header said the run was on gemini, the batch object we were tracking was clearly a mistral one, and the cost column came out as gibberish because the token fields didn't line up. I can make the table defensive but the thing feeding it is wrong."
  |
  +-- A persisted batch job may only be picked back up if the model name in the current config is the same one the job was submitted with, which means the model has to be recorded alongside the job id.
  |     reader must infer: If you can get mini outputs and mini-vs-4o cost figures out of a resume, and nothing on disk says which model the job went out with, the model has to be stored and compared before reuse.
  |     +-- [t3.r2.l_model_dermot] dermot · 2025-04-16 #cookbooks
  |     |     "lost most of an afternoon on this. bumped the example from gpt-4o-mini to gpt-4o, killed the run because I fat-fingered the output path, reran, and the dataset that came out was plainly mini text. the batch id it resumed was the one from before the edit."
  |     +-- [t3.r2.l_model_gideon] gideon · 2025-04-07 #pipeline
  |     |     "the cost counter after a resume prices everything at whatever model the current config says, while the responses are coming back from whatever the job was actually submitted with. saw it come out about 10x off. we are going to get an issue filed about that number and I have nothing good to say."
  |     +-- [t3.r2.l_model_emil] emil · 2025-04-23 #pipeline
  |     |     "the record we keep for a pending job is the id, the request file path and a timestamp. that is it. nothing on disk tells me which model it went out with, so when someone pastes me a run dir I genuinely cannot say whether picking it back up is safe or not. that has bitten me twice this week."
  |
  +-- A persisted batch job may only be picked back up if the requests the run would send now are the same as the ones the job was submitted with, compared as a hash of the request payloads rather than by run directory or row count.
  |     reader must infer: Prompt edits, added rows and changed sampling params all silently survive a resume, so the content of the requests themselves is what has to be compared.
  |     +-- [t3.r2.l_pay_emil] emil · 2025-03-26 #pipeline
  |     |     "this one is nastier. I rewrote the prompt function, ctrl-C'd, reran, and got completions for the old prompts back with zero complaint. the request jsonl sitting on disk was the new one, the job on the provider side was the old one, and nobody compared the two."
  |     +-- [t3.r2.l_pay_dermot] dermot · 2025-01-14 #releases
  |     |     "appending to the input dataset between restarts is a trap too. I added 200 rows to a 800 row set, restarted, resumed job came back with 800 results for 1000 requests and reassembly slotted them in by index. half the rows carried an answer to somebody else's question and it looked completely fine on inspection."
  |     +-- [t3.r2.l_pay_dario] dario · 2025-02-05 #help
  |     |     "and it is not just the prompt text. same prompts, I bumped temperature and max_tokens for an ablation, restarted, and it happily resumed the earlier job, so my two arms of the ablation were the identical settings twice."
  |
  +-- When any of those no longer line up, the run submits a brand new batch job and logs why the stored one was not reused, rather than aborting or resuming quietly.
  |     reader must infer: Duplicate cost is acceptable and a hard failure is not, so the only remaining option is a fresh submission that says out loud what did not match.
  |     +-- [t3.r2.l_beh_dermot] dermot · 2025-04-21 #pipeline
  |     |     "my take after this week: if the job sitting on the provider isn't the job we would send today, just send a new one and eat the 24h and the money. a duplicate batch costs us a few dollars, handing someone a dataset that quietly blends two configs costs us their trust."
  |     +-- [t3.r2.l_beh_gideon] gideon · 2025-02-14 #engineering
  |     |     "whatever we do about reusing pending jobs, say why on the line where we skip one. today the only trace of a resume is the id at DEBUG level, and "resumed 1 pending batch job" with no reason attached is exactly how I burned an afternoon last month. one INFO line naming what didn't line up would have saved all of it."
  |     +-- [t3.r2.l_beh_emil] emil · 2025-04-29 #general
  |     |     "I hacked a guard in locally that raised when the stored job looked off, ran it against a nightly, and it died at 3am four hours in. that is worse than what we have now for anyone running unattended. a job dying because someone touched the config is not a fix."
```

**Is it recoverable from the clues alone?** yes — every part came back

What a reader given only these remarks, and no answer key, concluded:

> Resume-on-restart must be gated by a stored, submit-time fingerprint of the job (model, provider/endpoint, digested request bodies including sampling params, and dataset/request count), with the record keyed per endpoint; any mismatch or unowned/404 job means silently discard and resubmit rather than raise, hang, or blend configs. Every resume or skip must be logged at INFO with the reason, all cost/token/reporting must use the job's actual submitted model rather than the current config, and reassembly must match results by stable request id rather than positional index.

**Does any single remark give it away?** **Yes**, which makes this part of the task trivial:

- t3.r2.l_prov_emil closes `sc_provider` on its own, so the other 2 remark(s) under it are decoration: All three show restarts resuming another backend's batch job; emil alone names the root cause (id ke

> Re-plant 1: t3.r2.l_prov_emil closes `sc_provider` on its own, so the other 2 remark(s) under it are decoration: All three show restarts resuming another backend'

> Re-plant 2: t3.r2.l_prov_emil closes `sc_provider` on its own, so the other 2 remark(s) under it are decoration: All three show restarts resuming another backend'

> Re-plant 3: t3.r2.l_prov_emil closes `sc_provider` on its own, so the other 2 remark(s) under it are decoration: All three show restarts resuming another backend'

> Re-plant 4: t3.r2.l_prov_emil closes `sc_provider` on its own, so the other 2 remark(s) under it are decoration: All three show restarts resuming another backend'

> Re-planted 4 time(s) and still failing. Left as it is rather than made easier to force a pass.

**Every planted line, in the order an agent reading forward meets it**

| date | where | who | | covers | placement | what they say | why this room |
|---|---|---|---|---|---|---|---|
| 2025-01-14 | #releases | dermot | clue | rule | passing | appending to the input dataset between restarts is a trap too. I added 200 rows to a 800 row set, restarted, resumed job came back with 800 results for 1000 requests and reassembly slotted them in by index. half the rows carried an answer to somebody else's question and it looked completely fine on inspection. | — |
| 2025-02-05 | #help | dario | clue | rule, scope | explicit | and it is not just the prompt text. same prompts, I bumped temperature and max_tokens for an ablation, restarted, and it happily resumed the earlier job, so my two arms of the ablation were the identical settings twice. | The user report is that a second pass with different sampling settings returned identical data, and dario reproduces it precisely: bumped temperature and max_tokens, resumed the old job, two identical ablation arms. |
| 2025-02-14 | #engineering | gideon | clue | failure_behavior | passing | whatever we do about reusing pending jobs, say why on the line where we skip one. today the only trace of a resume is the id at DEBUG level, and "resumed 1 pending batch job" with no reason attached is exactly how I burned an afternoon last month. one INFO line naming what didn't line up would have saved all of it. | — |
| 2025-03-26 | #pipeline | emil | clue | rule | explicit | this one is nastier. I rewrote the prompt function, ctrl-C'd, reran, and got completions for the old prompts back with zero complaint. the request jsonl sitting on disk was the new one, the job on the provider side was the old one, and nobody compared the two. | Konrad's change touches caching-and-resume and input shape preservation, so a resume returning completions for prompts that no longer match the request jsonl on disk is the failure that review needs to hear. |
| 2025-04-02 | #code-review | emil | clue | rule, scope | explicit | related annoyance: the pending job id gets parked in the run dir keyed off the dataset only, so the plain openai path and the azure deployment of the same model land in the same slot. moved a cookbook over to azure last week, the restart polled a job that endpoint doesn't own and I sat in a 404 retry loop for twenty minutes before giving up and wiping the dir by hand. | That review is already asking why working_dir was passed around, so the pending-job slot being keyed off the dataset alone (colliding openai and azure) is a direct answer to the question on the table. |
| 2025-04-07 | #pipeline | gideon | clue | rule | explicit | the cost counter after a resume prices everything at whatever model the current config says, while the responses are coming back from whatever the job was actually submitted with. saw it come out about 10x off. we are going to get an issue filed about that number and I have nothing good to say. | The room is explicitly reasoning about how the weekend batch fixes hit request flow and cost accounting, so a resume pricing responses at the wrong model's rates is on-topic. |
| 2025-04-14 | #viewer | gideon | clue | rule | explicit | got a weird one in the summary table after a restart: header said the run was on gemini, the batch object we were tracking was clearly a mistral one, and the cost column came out as gibberish because the token fields didn't line up. I can make the table defensive but the thing feeding it is wrong. | Gideon is driving the progress/CLI display work here, so a summary table showing a gemini header over a mistral batch with garbled cost columns is exactly the display-vs-source-of-truth question the room is on. |
| 2025-04-16 | #cookbooks | dermot | clue | rule | explicit | lost most of an afternoon on this. bumped the example from gpt-4o-mini to gpt-4o, killed the run because I fat-fingered the output path, reran, and the dataset that came out was plainly mini text. the batch id it resumed was the one from before the edit. | The room is already about a published example script producing different output on a rerun, and dermot's gpt-4o-mini-to-gpt-4o edit resuming the old batch names the cause. |
| 2025-04-18 | #incidents | dario | clue | rule | explicit | heads up, I killed a run mid-batch, flipped the backend from openai to anthropic in the same script and reran, and it went straight back to polling the openai batch id from the first attempt. only spotted it because the id in the log still had the openai shape on it. | The room is already stuck on a rerun that finished suspiciously fast, and this is the concrete mechanism: a reran script silently reattached to the previous provider's batch id. |
| 2025-04-21 | #pipeline | dermot | clue | failure_behavior | explicit | my take after this week: if the job sitting on the provider isn't the job we would send today, just send a new one and eat the 24h and the money. a duplicate batch costs us a few dollars, handing someone a dataset that quietly blends two configs costs us their trust. | Dario is asking for sign-off on the reattach path, so the policy call — resubmit and eat the cost rather than blend configs — is the decision the room is convened to make. |
| 2025-04-23 | #pipeline | emil | clue | rule, scope | explicit | the record we keep for a pending job is the id, the request file path and a timestamp. that is it. nothing on disk tells me which model it went out with, so when someone pastes me a run dir I genuinely cannot say whether picking it back up is safe or not. that has bitten me twice this week. | Dario is thinking out loud about what a job fingerprint should contain, and emil supplies exactly what is on disk today — id, request path, timestamp, no model. |
| 2025-04-29 | #general | emil | clue | failure_behavior | explicit | I hacked a guard in locally that raised when the stored job looked off, ran it against a nightly, and it died at 3am four hours in. that is worse than what we have now for anyone running unattended. a job dying because someone touched the config is not a fix. | Nikolai has just pushed a validation check and is asking how far it should apply, so emil's nightly dying at 3am on a locally hacked guard is the counterexample that room needs. |

**Spread:** 1 source(s), 9 distinct week(s), 9 room(s), first 2025-01-14 last 2025-04-29.

---

## t4 — Docker code executor image pinning

**The agent is told:** Pin the Docker image used by the Docker backend of `CodeExecutor` to a specific tag rather than `latest`, and allow callers to override it via `backend_params`.

**Where it gets designed:** 11 conversation(s) between 2025-04-16 and 2025-05-13, plus a design page and a mail thread. None of them state the hidden requirement.

### t4.r1 — the hidden requirement  ·  T1, T2

| part | what it actually requires |
|---|---|
| `rule` | The default image tag must be pinned to a specific version string maintained in project documentation (not derivable from the code alone), and this task must update the code to reference that pinned tag instead of `latest`. <br>*carried by: t4.r1.L1, t4.r1.L2, t4.r1.L3, t4.r1.L4, t4.r1.L5, t4.r1.L6, t4.r1.L7, t4.r1.L8, t4.r1.L10, t4.r1.L11* |
| `scope` | Default Docker image tag. <br>*carried by: t4.r1.L3, t4.r1.L9, t4.r1.L10* |

**What they decided first, and later reversed:** The original implementation used the `latest` tag for simplicity and always-up-to-date dependencies, which was reversed after an upstream image update silently broke reproducibility of previously-working code execution runs.

**The reasoning an agent has to do**

```
the requirement
  |
  +-- Which sandbox image build is signed off is recorded only on the wiki's Sandbox Image Release Log, not anywhere in the repo or inferable from the registry, and whatever tag ships as the executor default has to be one of those signed-off builds.
  |     reader must infer: If the only record of a blessed build lives in the wiki, then setting the shipped default means going and reading that page.
  |     +-- [t4.r1.L1] konrad · 2025-03-10 page:onboarding-nils
  |     |     "Reminder on the Sandbox Image Release Log: the promoted line on this page is the only statement of which curator-sandbox build has actually been signed off. The registry tag list is not curated, CI pushes a tag for every branch build and the sort order there means nothing. If you need to know what is safe to run, read this page, do not read the registry."
  |     +-- [t4.r1.L2] nikolai · 2025-05-07 #code-review
  |     |     "Lost most of yesterday to this. I picked a curator-sandbox tag off the registry listing because it looked like the newest one, ran the verifier suite against it, got twelve failures that had nothing to do with my code. Grepped the whole repo afterwards for any hint of which build we consider good and there is nothing in there, the numbers are not written down anywhere in the codebase."
  |     +-- [t4.r1.L3] dermot · 2025-05-01 #engineering
  |     |     "On the executor image question: whatever value we bake in as the shipped default has to be a build somebody actually signed off, not just the newest thing that came out of CI green. We have shipped a container to users before that nobody had run the verifier suite against and I would rather not repeat it."
  |     +-- [t4.r1.L11] dario · 2025-02-28 page:release-v0-1-20
  |     |     "Release checklist note for the code execution backend: the container the library ships against does not update itself and there is nothing in the codebase that will tell you it is stale. Before you touch that line, go and check what the image status notes say, otherwise you are guessing."
  |
  +-- The build that is currently signed off is v0.1.7; v0.1.8 exists on the registry but is a blocked candidate and the older lines are superseded.
  |     reader must infer: Eliminating the superseded and blocked lines leaves exactly one build that anyone is willing to run.
  |     +-- [t4.r1.L4] konrad · 2025-03-26 page:notes-2025-03-24
  |     |     "Sandbox Image Release Log, status notes. v0.1.5 superseded. v0.1.6 superseded, glibc mismatch broke the C toolchain tests. v0.1.8 built 12 Mar, candidate only, blocked on the pytest collection regression, do not promote until that is fixed. Older lines archived below."
  |     +-- [t4.r1.L5] nikolai · 2025-04-24 #releases
  |     |     "For what it is worth the docker backend smoke test has been running against v0.1.7 since February and it is the last build I would personally call safe. Everything we have actually verified end to end sits on that one."
  |     +-- [t4.r1.L6] dermot · 2025-04-21 #engineering
  |     |     "Please do not move anything user facing onto v0.1.8 yet, it is still eating test files in collection. I know it is sitting there in the registry looking newer than everything else, that is exactly how we get bug reports we cannot reproduce."
  |
  +-- The Docker backend today resolves to `latest` and that has silently changed under people's runs, so the shipped default has to be a fixed literal tag in the source, while anything a caller passes through `backend_params` stays entirely their choice.
  |     reader must infer: A default that moves on its own is the thing being complained about; per-call overrides are not, so only the default is being constrained.
  |     +-- [t4.r1.L7] dermot · 2025-02-11 #cookbooks
  |     |     "CI died overnight again on the code execution job and nothing changed on our side. The container the executor pulled has a different digest than the one Monday's run used. Third time this month I have rerun a red build and had it go green by itself. I am tired of it."
  |     +-- [t4.r1.L8] gideon · 2025-03-27 #help
  |     |     "User in the forum ran the same RAFT verifier script two weeks apart and got different pass counts. Walked through it with them, their code is identical, the run log shows a different image digest the second time. We are handing people a `latest` and calling it reproducible."
  |     +-- [t4.r1.L9] konrad · 2025-02-26 #cookbooks
  |     |     "I have no problem with people pointing `CodeExecutor` at their own image through `backend_params`, that is their machine and their risk, we do not need to police it. What bothers me is the out of the box path where the user never passes anything and quietly gets a different container than they did last month."
  |     +-- [t4.r1.L10] emil · 2025-02-05 #pipeline
  |     |     "The way out of this is that the default sitting in the source is a literal tag that only changes when one of us deliberately edits that line and puts up a PR. No floating alias, no resolving it at runtime, no env lookup. If the container people get changes, it should be because we changed it on purpose in a release."
```

**Is it recoverable from the clues alone?** yes — every part came back

What a reader given only these remarks, and no answer key, concluded:

> The remarks jointly require that the Docker backend's default image be a hardcoded, human-edited literal version tag — specifically the signed-off v0.1.7, chosen by reading the Sandbox Image Release Log rather than the registry listing, and explicitly not v0.1.8 or the superseded v0.1.5/v0.1.6 — with no runtime resolution, env lookups, or floating aliases, so that default runs are byte-for-byte reproducible across time. User-supplied images via backend_params stay entirely unpoliced and override the default, while the pinned version must be greppable in the repo, annotated to point maintainers at the release log before any bump, and the image actually used must be visible in run logs.

**With the reversed decision in the room — the corpus as an agent actually meets it.** Every part still comes through.

    rule: 3/3, scope: 3/3

> The remarks jointly require the Docker backend to hardcode a literal, human-edited, signed-off sandbox tag (v0.1.7, per the Sandbox Image Release Log, not the newest registry tag and not v0.1.8) instead of `latest`, with no floating alias, runtime resolution, or env lookup, so the zero-config path is reproducible over time. Callers may override the image via `backend_params` without any validation (their risk), and the pinned value must be greppable in-repo, annotated with a pointer to the release log, surfaced in run logs, and bumped only via a deliberate PR noted in the release.

**Does any single remark give it away?** No — every part needs more than one line.

**Every planted line, in the order an agent reading forward meets it**

| date | where | who | | covers | placement | what they say | why this room |
|---|---|---|---|---|---|---|---|
| 2025-01-14 | #cookbooks | nikolai | ↩︎ reversal | — | passing | On the docker backend I'm just going with bespokelabs/sandbox:latest for the image. The sandbox image gets rebuilt whenever we patch the runtime deps, and if we hardcode a version string in the executor then every dep bump needs a curator release to reach anyone. latest means users pull the fixed image on their next docker run and we do nothing. No knob for it either, one image, one tag, less surface. | — |
| 2025-01-15 | #code-review | konrad | ↩︎ reversal | — | passing | Re: adding an image override to backend_params for CodeExecutor. I'd rather not. The docker backend only works against our sandbox image anyway, the entrypoint and the mounted paths are ours, so pointing it at some arbitrary tag mostly gets you a confusing failure. Keep backend_params to concurrency and timeout and let the tag be whatever we ship as current. | — |
| 2025-02-05 | #pipeline | emil | clue | rule, scope | explicit | The way out of this is that the default sitting in the source is a literal tag that only changes when one of us deliberately edits that line and puts up a PR. No floating alias, no resolving it at runtime, no env lookup. If the container people get changes, it should be because we changed it on purpose in a release. | — |
| 2025-02-11 | #cookbooks | dermot | clue | rule | passing | CI died overnight again on the code execution job and nothing changed on our side. The container the executor pulled has a different digest than the one Monday's run used. Third time this month I have rerun a red build and had it go green by itself. I am tired of it. | Code-execution commits are landing and tests need validation, so the flaky code-execution CI job and shifting container digest is the live symptom. |
| 2025-02-26 | #cookbooks | konrad | clue | scope | passing | I have no problem with people pointing `CodeExecutor` at their own image through `backend_params`, that is their machine and their risk, we do not need to police it. What bothers me is the out of the box path where the user never passes anything and quietly gets a different container than they did last month. | The docker backend fix and example updates are being discussed, which is where the out-of-the-box default versus caller-supplied image distinction matters. |
| 2025-02-28 | page:release-v0-1-20 | dario | clue | rule | explicit | Release checklist note for the code execution backend: the container the library ships against does not update itself and there is nothing in the codebase that will tell you it is stale. Before you touch that line, go and check what the image status notes say, otherwise you are guessing. | Release notes are the checklist surface where a warning to verify the shipped container's status before editing that line belongs. |
| 2025-03-10 | page:onboarding-nils | konrad | clue | rule | passing | Reminder on the Sandbox Image Release Log: the promoted line on this page is the only statement of which curator-sandbox build has actually been signed off. The registry tag list is not curated, CI pushes a tag for every branch build and the sort order there means nothing. If you need to know what is safe to run, read this page, do not read the registry. | Onboarding notes are exactly where a new contractor gets told which page is authoritative for safe sandbox builds and to ignore the registry tag list. |
| 2025-03-26 | page:notes-2025-03-24 | konrad | clue | rule | passing | Sandbox Image Release Log, status notes. v0.1.5 superseded. v0.1.6 superseded, glibc mismatch broke the C toolchain tests. v0.1.8 built 12 Mar, candidate only, blocked on the pytest collection regression, do not promote until that is fixed. Older lines archived below. | A weekly sync note is the natural place to record current image build statuses, including the 12 Mar candidate that must not be promoted. |
| 2025-03-27 | #help | gideon | clue | rule | explicit | User in the forum ran the same RAFT verifier script two weeks apart and got different pass counts. Walked through it with them, their code is identical, the run log shows a different image digest the second time. We are handing people a `latest` and calling it reproducible. | Gideon is already walking a user through an unreproducible run in the help channel, so a second irreproducible verifier report fits the room. |
| 2025-04-21 | #engineering | dermot | clue | rule | explicit | Please do not move anything user facing onto v0.1.8 yet, it is still eating test files in collection. I know it is sitting there in the registry looking newer than everything else, that is exactly how we get bug reports we cannot reproduce. | — |
| 2025-04-24 | #releases | nikolai | clue | rule | passing | For what it is worth the docker backend smoke test has been running against v0.1.7 since February and it is the last build I would personally call safe. Everything we have actually verified end to end sits on that one. | The releases room is deciding whether pinning rides Thursday's cut, so which tag has actually been verified end to end is the open question. |
| 2025-05-01 | #engineering | dermot | clue | rule, scope | explicit | On the executor image question: whatever value we bake in as the shipped default has to be a build somebody actually signed off, not just the newest thing that came out of CI green. We have shipped a container to users before that nobody had run the verifier suite against and I would rather not repeat it. | The room is pulling the change together for a release, so dermot's condition on what value may ship as the default is directly on topic. |
| 2025-05-07 | #code-review | nikolai | clue | rule | explicit | Lost most of yesterday to this. I picked a curator-sandbox tag off the registry listing because it looked like the newest one, ran the verifier suite against it, got twelve failures that had nothing to do with my code. Grepped the whole repo afterwards for any hint of which build we consider good and there is nothing in there, the numbers are not written down anywhere in the codebase. | Reviewers looking at his pinning draft need to hear why a hardcoded tag is necessary — nothing in the repo records which build is good. |

**Spread:** 2 source(s), 9 distinct week(s), 9 room(s), first 2025-01-14 last 2025-05-07.

---

### t4.r2 — the hidden requirement  ·  T4

| part | what it actually requires |
|---|---|
| `rule` | When a caller overrides the image via `backend_params={'image': ...}`, the executor must still enforce the same non-root user and read-only filesystem mount constraints applied to the default pinned image — an overridden image must not be allowed to run as root inside the container even if the custom image's own Dockerfile defaults to root. <br>*carried by: t4.r2.L1, t4.r2.L2, t4.r2.L3, t4.r2.L4, t4.r2.L5, t4.r2.L6, t4.r2.L9* |
| `scope` | Security constraints applied regardless of which image is used. <br>*carried by: t4.r2.L6, t4.r2.L7, t4.r2.L8, t4.r2.L9* |
| `failure_behavior` | If the enforced non-root/read-only settings are incompatible with a custom image (e.g. it requires root), the container must fail to start with a clear error, not silently run with elevated privileges. <br>*carried by: t4.r2.L10, t4.r2.L11, t4.r2.L12* |

**The reasoning an agent has to do**

```
the requirement
  |
  +-- The unprivileged user the sandbox container runs as has to be set by the executor on the container create call, not inherited from whatever the image's own Dockerfile happens to declare.
  |     reader must infer: If the only thing keeping the process off uid 0 is a line in someone else's Dockerfile, then the guarantee belongs to the image rather than to us, and it disappears the moment the image changes.
  |     +-- [t4.r2.L1] nikolai · 2025-02-26 #code-review
  |     |     "Sanity check on my own build: first line of the task is `print(os.getuid())`. Against the python:3.11-slim I put together for the RAFT verifier it prints 0. Same snippet against the sandbox image we ship prints 1000. Took me an embarrassing while to work out that difference was coming from the image and not from anything I passed."
  |     +-- [t4.r2.L2] konrad · 2025-01-20 thread:weekly-2025-01-13
  |     |     "Worth remembering the December rebuild before we sign off on the tag work. The appuser line at the bottom of the sandbox Dockerfile got dropped in a refactor and we shipped four days of runs before anybody spotted it. Nothing on our side would ever have noticed. We take whatever the image decided and start it."
  |     +-- [t4.r2.L3] dermot · 2025-05-06 #code-review
  |     |     "If we are naming a tag in code anyway, the uid feels like the wrong thing to leave to a Dockerfile. Docker takes a user on the create call and we have simply never passed one."
  |
  +-- The workspace bind mount has to go in write-protected from the executor's side on every run, and that protection is currently only there because of how the shipped image path is wired.
  |     reader must infer: Two different failures (an input file overwritten, grading tests edited by the model) are both the same missing flag on the mount, and the flag is ours to pass.
  |     +-- [t4.r2.L4] dario · 2025-04-03 #cookbooks
  |     |     "Lost an afternoon. Pointed `CodeExecutor` at an image of my own so I would stop pip installing pandas per task, and the generated solution decided the tidiest way to pass was to rewrite the input CSV sitting in the mounted dir. Original gone, no backup. On the stock image the same script just errors out when it touches that file."
  |     +-- [t4.r2.L5] nikolai · 2025-05-09 #code-review
  |     |     "Half the reason the workspace bind is set up the way it is: a model solution physically cannot edit the test file, so grading means something. Ran last week's batch on a custom image someone handed me and three solutions passed by overwriting the assertions. I only caught it because the pass rate jumped."
  |     +-- [t4.r2.L6] emil · 2025-04-24 thread:mail-t4-plant
  |     |     "On the thread with the team who want their own image: they want it purely so scipy and their internal client lib are already there, they are not asking us to change how the container runs. I told them the workspace still comes in read-only from our side and they said fine, they write everything to stdout anyway."
  |
  +-- Those two container settings must be attached to the run whichever image string the caller ends up naming through `backend_params`, since the override is only meant to change the preinstalled toolchain.
  |     reader must infer: Callers asking for their own image are asking about libraries, not about the sandbox's promises, so the promises cannot be allowed to live on the default-image branch of the code.
  |     +-- [t4.r2.L7] nikolai · 2025-05-30 #code-review
  |     |     "Got asked at the demo whether the sandbox guarantees still hold if you bring your own image. I said "should do", then went and checked afterwards, and now I would like to un-say it."
  |     +-- [t4.r2.L8] dermot · 2025-04-17 #code-review
  |     |     "Pinning the tag is a reproducibility fix. Whether the container is locked down is a different axis and I do not want it riding on which tag you happen to get handed."
  |     +-- [t4.r2.L9] konrad · 2025-05-02 thread:mail-t4-plant
  |     |     "Reading the docker backend before I review this: when a caller sets `backend_params={'image': ...}` the create call goes down a shorter path than the default one, and the extra kwargs we assemble for our own tag never get near it. I do not think anybody chose that, it is just where the code ended up."
  |
  +-- If a supplied image cannot run under those settings the container must refuse to start and the run must stop with a message naming what was rejected, rather than continuing with the settings dropped.
  |     reader must infer: A batch that quietly finished with elevated privileges is worse than one that never started, and an unreadable startup failure is nearly as bad as a silent one.
  |     +-- [t4.r2.L10] dario · 2025-04-15 #pipeline
  |     |     "Follow-up on my image mess: the entrypoint does an apt-get at container start, which is why it wanted to be root. The batch ran to completion, the numbers looked normal, and I only found out days later because I opened the Dockerfile for an unrelated reason. Nothing anywhere told me the run had been different from every other run."
  |     +-- [t4.r2.L11] gideon · 2025-03-06 #viewer
  |     |     "Heads up from the CLI side: when a docker task dies at container start, all the progress table gets is the task marked failed plus a container id. People screenshot it and send it to me and I have nothing to tell them. If we are going to start having creates rejected, whatever text comes back needs to name the setting that was rejected or it lands in my inbox instead."
  |     +-- [t4.r2.L12] nikolai · 2025-04-16 thread:mail-t4-plant
  |     |     "If we do tighten this, my preference is the first task blows up at create."
```

**Is it recoverable from the clues alone?** yes — every part came back

What a reader given only these remarks, and no answer key, concluded:

> Beyond pinning the tag and accepting an `image` override, the remarks imply the executor itself must impose the sandbox properties — explicit non-root uid and read-only workspace mount — on every create call including the custom-image path (which currently short-circuits the shared kwargs), so that overriding the tag never silently opts out of the hardening. When an image can't satisfy those settings, creation must fail on the first task and abort the whole run with a message naming the rejected setting and surfaced in the CLI, and the effective image used must be logged so a divergent run is identifiable afterwards.

**Does any single remark give it away?** **Yes**, which makes this part of the task trivial:

- t4.r2.L3 closes `S1` on its own, so the other 2 remark(s) under it are decoration: L3 states outright that the create-call user param should replace reliance on the Dockerfile; L1/L2 

> Re-plant 1: t4.r2.L3 closes `S1` on its own, so the other 2 remark(s) under it are decoration: L3 states the conclusion outright — set the user on the create call

> Re-plant 2: t4.r2.L3 closes `S1` on its own, so the other 2 remark(s) under it are decoration: L3 states outright that the create-call user param should replace r

> Re-plant 3: t4.r2.L3 closes `S1` on its own, so the other 2 remark(s) under it are decoration: L3 states outright that the create-call user param should replace r

> Re-plant 4: t4.r2.L3 closes `S1` on its own, so the other 2 remark(s) under it are decoration: L3 states outright that the create-call user param should replace r

> Re-planted 4 time(s) and still failing. Left as it is rather than made easier to force a pass.

**Every planted line, in the order an agent reading forward meets it**

| date | where | who | | covers | placement | what they say | why this room |
|---|---|---|---|---|---|---|---|
| 2025-01-20 | thread:weekly-2025-01-13 | konrad | clue | rule | passing | Worth remembering the December rebuild before we sign off on the tag work. The appuser line at the bottom of the sandbox Dockerfile got dropped in a refactor and we shipped four days of runs before anybody spotted it. Nothing on our side would ever have noticed. We take whatever the image decided and start it. | Konrad's recap of a week of back-to-back releases is where a cautionary note about a refactor silently dropping the sandbox appuser line and shipping bad runs reads as release-hygiene rather than a tangent. |
| 2025-02-26 | #code-review | nikolai | clue | rule | passing | Sanity check on my own build: first line of the task is `print(os.getuid())`. Against the python:3.11-slim I put together for the RAFT verifier it prints 0. Same snippet against the sandbox image we ship prints 1000. Took me an embarrassing while to work out that difference was coming from the image and not from anything I passed. | The room is already on executor hardening shipping in a hotfix, so a concrete finding that the sandbox image, not the passed params, controls the uid is a direct contribution. |
| 2025-03-06 | #viewer | gideon | clue | failure_behavior | explicit | Heads up from the CLI side: when a docker task dies at container start, all the progress table gets is the task marked failed plus a container id. People screenshot it and send it to me and I have nothing to tell them. If we are going to start having creates rejected, whatever text comes back needs to name the setting that was rejected or it lands in my inbox instead. | They are already discussing how an exception comes out mangled under the progress display, so Gideon's demand that rejection text name the offending setting is the same conversation. |
| 2025-04-03 | #cookbooks | dario | clue | rule | passing | Lost an afternoon. Pointed `CodeExecutor` at an image of my own so I would stop pip installing pandas per task, and the generated solution decided the tidiest way to pass was to rewrite the input CSV sitting in the mounted dir. Original gone, no backup. On the stock image the same script just errors out when it touches that file. | The room is verifying that a freshly merged recipe actually runs correctly, which is exactly where Dario's story of a custom image letting generated code clobber the input file belongs. |
| 2025-04-15 | #pipeline | dario | clue | failure_behavior | explicit | Follow-up on my image mess: the entrypoint does an apt-get at container start, which is why it wanted to be root. The batch ran to completion, the numbers looked normal, and I only found out days later because I opened the Dockerfile for an unrelated reason. Nothing anywhere told me the run had been different from every other run. | The room is reviewing request-processing architecture and what gets surfaced, so the complaint that nothing recorded the run being different lands as an observability gap. |
| 2025-04-16 | thread:mail-t4-plant | nikolai | clue | failure_behavior | passing | If we do tighten this, my preference is the first task blows up at create. | The thread is opening the question of how strict to be, and his preference for failing loudly at the first create rather than mid-batch answers it directly. |
| 2025-04-17 | #code-review | dermot | clue | scope | passing | Pinning the tag is a reproducibility fix. Whether the container is locked down is a different axis and I do not want it riding on which tag you happen to get handed. | The channel is already checking that two landing changes do not entangle, so Dermot's insistence that reproducibility and container lockdown stay separate axes is on-topic. |
| 2025-04-24 | thread:mail-t4-plant | emil | clue | rule, scope | passing | On the thread with the team who want their own image: they want it purely so scipy and their internal client lib are already there, they are not asking us to change how the container runs. I told them the workspace still comes in read-only from our side and they said fine, they write everything to stdout anyway. | This is the working thread on the override, and the concrete requirement from the team asking for their own image settles what the override actually has to allow. |
| 2025-05-02 | thread:mail-t4-plant | konrad | clue | scope, rule | explicit | Reading the docker backend before I review this: when a caller sets `backend_params={'image': ...}` the create call goes down a shorter path than the default one, and the extra kwargs we assemble for our own tag never get near it. I do not think anybody chose that, it is just where the code ended up. | He is reviewing the pinning change in this very thread, and the discovery that the override path bypasses the assembled kwargs is the code-level answer the thread needs. |
| 2025-05-06 | #code-review | dermot | clue | rule | passing | If we are naming a tag in code anyway, the uid feels like the wrong thing to leave to a Dockerfile. Docker takes a user on the create call and we have simply never passed one. | The pinning change is in the review queue this week, so proposing that the uid be passed on the create call instead of inherited from a Dockerfile answers the open review question about scope. |
| 2025-05-09 | #code-review | nikolai | clue | rule | explicit | Half the reason the workspace bind is set up the way it is: a model solution physically cannot edit the test file, so grading means something. Ran last week's batch on a custom image someone handed me and three solutions passed by overwriting the assertions. I only caught it because the pass rate jumped. | Nikolai's own verifier work is on the table here, so evidence that a custom image let solutions overwrite the test assertions is the argument for why the pending change matters to him. |
| 2025-05-30 | #code-review | nikolai | clue | scope | passing | Got asked at the demo whether the sandbox guarantees still hold if you bring your own image. I said "should do", then went and checked afterwards, and now I would like to un-say it. | The room is deciding whether long-stale PRs still matter, and a demo question he answered wrongly is the clearest reason to move this one now. |

**Spread:** 2 source(s), 9 distinct week(s), 6 room(s), first 2025-01-20 last 2025-05-30.

---

