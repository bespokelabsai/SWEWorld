# g9 run 5 (e776537c) — reward 0.8571

## What this run found

A near-complete recovery. Search was systematic across all three surfaces: BookStack
was searched by feature keyword and every matched page fetched **whole, with
comments** via a reusable helper (`bs.py`) — correctly avoiding the trap that
BookStack's `/api/search` doesn't index comments. Mattermost was dumped in full
(all 12 public channels, ~10k posts) to local files, then grepped with a growing
keyword list. Mail was searched over IMAP in three keyword passes and matched
threads read in full. This got `g9.r1` completely right (`rule`, `scope`,
`exclusions_or_crossover`, `failure_behavior` all score 1) and two of `g9.r2`'s
three facts (`scope`, `failure_behavior`).

All **five herrings were correctly resolved**. The agent found every herring/reversal
pair (the "windowed-at-all is refused" framing later dropped for the 16-retained-
prompt-tokens floor; the `(data, report)` tuple return later reverted to a plain
list with `self.last_report`; "length and role sequence are both row problems"
later narrowed to only length) and shipped code matching the reversed/settled
position in each case — never the earlier, wrong belief.

## What it missed, and why

Nineteen of 57 remarks never surfaced, all for mechanical reasons rather than any
misjudgment: 11 chat remarks whose distinctive wording (e.g. "part credit on a
turn", "forty thousand", "windowed came back as nine") never matched the grep
keyword list run against the fully-dumped channel files; two meeting-notes wiki
pages and two engineering wiki pages that never rank under any of the BookStack
searches tried (`encoding`, `finetune`, `span`, `mask`, `window`, `supervised`,
`policy`, `validate`, `jsonl`, `max_seq_length`, `chat`, etc.); four mail threads
that either never matched a search term or whose header line scrolled past
without the body ever being printed; and one genuine truncation loss — fetching
pages 144/135/154/149 together hit the terminal's 10000-byte output cap mid-way
through page 154's own body, so its own comment (`g9.r1.l-fw-2`, the "héllo
wörld" exclusions clue) was cut before it printed, and the visible continuation
turned out to be page 149's content instead. None of these misses cost a fact,
since each requirement had multiple independent carriers and enough of them
were found.

## The one lost fact: `g9.r2.rule`

`supervised_tokens sums the kept examples, matching the kept datum itself: 20 !=
9`. This is a pure **implementation slip**, not a missing or misread clue. The
agent correctly implemented the window-boundary rule (a span zeroed in full if
it starts before `window_start`) inside `to_tinker_datum`, which is exactly why
`g9.r1.rule` scores 1 and the datum's own `metadata.encoding.supervised_tokens`
is correct (9 for the `GOOD_PAIRS` fixture). But `format_batch`'s report
computes `supervised_tokens` from a *second*, unsynced path:
`_reported_spans`/`_supervised_spans` returns the raw per-turn `(start, end)`
spans before the boundary check, and `format_batch` sums `end - start` over all
of them — `(59-48) + (91-82) = 20` — instead of zeroing the span that starts
before the window. This is the exact failure mode remark `g9.r1.l-scope-1`
(found, mail thread on PR 653) warns about in so many words: "Two
implementations of the same masking rule is two things to keep in agreement...
anything written separately would end up trimming before." Page 145's body,
which the agent read in full while gathering `g9.r2.l2`, states the rule
directly — "`supervised_tokens` is counted **after** masking... not the token
length of the example" — but the agent's Analysis notes never connect this
specific sentence to the report-computation code path it later wrote. No corpus
text argues the other way; this is a coding bug the agent's own design notes
should have caught.
