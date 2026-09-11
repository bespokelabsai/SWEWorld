---
title: "turn_ledger.json \u2014 the per-turn ledger artifact"
author: dario
created_at: 2025-05-13T09:30:00+00:00
---

## why this file exists

**date:** 2025-05-13  
**status:** artifact written, nothing consumes it yet

up to now the only record of what happened turn by turn has been the run log. anything that wanted turn counts or cumulative cost had to replay the log and re-derive them, which is fine when you have one run in front of you and less fine when the end-of-run summary and the viewer both want the same numbers and both pay for them separately.

so the per-turn ledger is being pulled out of the log into its own file, `turn_ledger.json`, written alongside the other run artifacts. gideon did the extraction on the writer side. i am writing it up now, before the summary and the viewer are switched over, because i think it is easier to argue about the shape of a file while nothing depends on it yet. once two consumers are reading it we are stuck with whatever we shipped.

to be honest the log is not going away and this is not a replacement for it. the log is the narrative, the ledger is the accounting.

## what is in it

one object per turn, in turn order, under a top-level `turns` key, plus a small header block for the run itself (run id, model, start time).

per turn, currently:

- `index` — zero based, monotonic, no gaps
- `role` — who produced the turn
- `input_tokens` / `output_tokens` — as reported by the provider, not estimated
- `cost_usd` — computed at write time from the rate table in effect for that run
- `started_at`, `duration_ms`
- `tool_calls` — count only, not the payloads. the payloads stay in the log, they are large and they are not accounting

the deliberate omission is anything derived. no running totals, no averages, no "turns so far". consumers can sum. every derived field we put in here is a field that can disagree with the rows underneath it, and honestly i would rather not spend an afternoon later on explaining which one is right.

## how it is written out

the serialisation is fixed and should be treated as part of the contract, not as a formatting preference.

`turn_ledger.json` goes out with `sort_keys` on and `indent 2`, with a trailing newline at the end of the file. the byte counts asserted in the tests ride on all three of those, so a change to any of them is a change to the tests.

this is not arbitrary. key order moved once already and every diff downstream of it went noisy — real changes buried in reordering, review slowed to nothing for a day. deterministic key order and a stable indent mean a ledger diff between two runs shows what actually differed in the run. in any case, if there is ever a good reason to change the shape of the output, fine, but it is a coordinated change with the tests and not something to fold into an unrelated pr.

## open questions

two things are genuinely undecided and i do not want to settle them by whatever the current implementation happens to do.

- **when it gets flushed.** either we write once at end of run, which is simple and gives us an atomic rename and a file that is either complete or absent, or we append per turn so that a crashed or killed run still leaves a partial ledger behind. the viewer arguments point at per-turn, the correctness arguments point at end-of-run. i lean end-of-run with an explicit flush hook for long runs, but that is a lean, not a decision.
- **which side wins on disagreement.** if the ledger and the log report different token counts or a different number of turns, is the ledger authoritative because it is the accounting record, or is the log authoritative because it is the primary source and the ledger is derived from it? whichever we pick, the summary and the viewer need to pick the same one, and it needs to be written down here rather than being implied by whichever code path someone read first.

both of these want a decision before the first consumer lands. best we can do until then is not build anything that assumes an answer.

## what to do if you are touching this

- do not add derived or cumulative fields without raising it first, see above
- new per-turn fields are additive and go at the end of the schema doc, existing keys keep their meaning
- if you change what is written, run the artifact tests, they assert on exact bytes and they will tell you
- consumers should tolerate an absent ledger for now, the flush question is open and nothing should hard-fail on a missing file this week
