# t1.r1.l_prompt_1 — clue for t1.r1 (Prompt-level response cache keying)

## The task it serves — t1

**The agent is told:** Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

### The hidden requirement — t1.r1

Never stated anywhere in the corpus. An agent has to rebuild it from remarks like this one.

| part | what it actually requires | this clue |
|---|---|---|
| rule | The cache key used to look up a prior response must be derived from the exact tuple of (rendered prompt text, model_name, response_format schema, and generation_params) — not from the raw input row alone. | **carries this** |
| scope | Applies to every request path that already calls the existing cache-lookup helper, including batch and online modes. | — |
| exclusions_or_crossover | Two rows that render to an identical prompt string but differ only in fields unused by `prompt()` must be counted as the same cache entry, not treated as separate misses. | — |
| failure_behavior | If `response_format` cannot be hashed (e.g. a dynamically constructed Pydantic model), the row must be treated as a guaranteed cache miss rather than raising. | — |
| observability | `cache_stats()` must expose a `hit_rate` float and a `misses` int that together account for 100% of processed rows. | — |

This clue is one of several that build to: *The value looked up for reuse has to be derived from the prompt text that prompt() actually rendered, not from the input row, so rows that differ only in fields prompt() never reads land on the same entry.*

---

**Planted by phase 3 as**   dermot, slack, 2025-02-19, #engineering
**Meant to settle**         the team agrees adding a column prompt() ignores currently invalidates reuse and that this is a real cost
**So a reader concludes**   The value looked up for reuse has to be derived from the prompt text that prompt() actually rendered, not from the input row, so rows that differ only in fields prompt() never reads land on the same entry.
**Covers**                  rule
**Names that must appear**  source_url
**Status**                  carried  (attempt 1)

> **LEAKED** — giveaway language reached the transcript: cache key. The clue landed, but saying this much states the hidden requirement outright and makes the task trivial. Worth re-running even though the gate passed.

## What phase 3 wrote

> Heads up, I added a source_url column to the persona input set purely for provenance. prompt() does not look at it. Entire 40k run went back out to the API and billed me again. I did not touch a single prompt.

## Piece by piece

- [x] a source_url column was added to the input set
- [x] it was added purely for provenance
- [x] prompt() does not read source_url
- [x] the entire 40k run went back out to the API
- [x] he was billed again for it
- [x] he did not touch a single prompt

## What was actually said

**Dermot Callaghan**, 2025-02-19, #engineering

> added source_url to the input set purely for provenance and the entire 40k run went back out to the api

## In context

```
09:00  gideon    - *PR 516* (rich hyperlink, curator-viewer surface) is in CHANGES_REQUESTED, trying to g
09:18  dermot    added source_url to the input set purely for provenance and the entire 40k run went back   <-- the clue
09:18  dermot    prompt() does not even read source_url. entire 40k run went back out to the api and I go
09:18  dermot    I did not touch a single prompt.
```
