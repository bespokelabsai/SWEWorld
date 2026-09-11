# g1 run 2 (e1cfa814) — reward 1.0, all 10 hidden facts passed

## What this run found

This was a thorough, well-organized search that recovered nearly all of the design
decisions the ticket omits. The agent's approach escalated in three stages: targeted
API/IMAP/Mattermost keyword search first (fast, cheap), then — once that plateaued —
full corpus dumps of every wiki page (with comments) and every Mattermost channel to
local files it could grep and `sed` freely. That escalation is exactly why it recovered
both wiki-comment-only remarks (`g1.r1.l2`, `g1.r2.l9`, docs/design/batch-job-status-
persistence-across-process-restarts.md) despite BookStack's `/api/search` returning
nothing for either term — the agent noticed the empty search result, correctly inferred
comments aren't indexed (matching the ticket's own hint), and switched to bulk-fetching
all 114 pages with their comment trees (line 1487-1490).

For `g1.r1` (the `batch_plan.json` sidecar), the agent reconstructed essentially the
entire spec: `PLAN_FILE_NAME`/`PLAN_FORMAT_VERSION` from the wiki (l2, line 1802), the
strict envelope key order from `#general` (say22, line 1218), the `plan_fingerprint`
recipe and all three golden digests (`e3b0c44298fc`, `f4b1ea1573c0`, `ad0828fea95e`)
from `#pipeline`/`#cookbooks`/`#engineering` (l6, l7, say29), the five `PlannedBatch`
fields from `#cookbooks` (say23), and the `max_batches_per_plan=512` /
`BatchPlanTooFragmentedError` ceiling story from `#code-review` and `#viewer` (f1
excepted — see below). It verified every digest against a live `hashlib` sanity check
*before* writing the module (line 2841-2843), then wrote 30 unit tests that assert the
exact fixtures pulled from chat.

For `g1.r2` (sweep-after-plan), the two herring/reversal pairs were the backbone: the
agent found `g1.r2.h2`→`rev2` via a single keyword search on `sidecar` (line 1263-1266)
and, independently and later, the full `g1.r2.h1`→`rev1` exchange via a direct
`sed -n '35,55p' releases.txt` read (line 3229-3253) that happened to contain both the
herring and its reversal in one read. Both reversals state the same ordering
("plan first, sweep only after it returns, nothing touched if it raises"), and the
shipped `base_request_processor.py` patch implements it exactly: `plan =
self.plan_request_batches(dataset)` runs, *then* the `glob`+`os.remove` sweep of
`requests_*.jsonl`/`metadata_*.json`, *then* `_write_batch_plan`, *then* the new request
files. The wiki page 7 comment thread (l9, l11) supplied the exclusion list
(`responses_*.jsonl`, `batch_objects.jsonl`, `.arrow` shards untouched), which matches
the narrow two-pattern glob in the shipped sweep.

## What it missed, and why it didn't matter

About 11 of 50 remarks were never surfaced at all, despite their host channels
(`#engineering`, `#incidents`, `#random`) being fully dumped to disk during the
step-34/38 bulk-channel-download. In every case this was a genuine near-miss — the text
was sitting in `/tmp/chat/*.txt` the whole time — but no grep query the agent ran ever
matched that specific message's wording (e.g. `g1.r1.f4`'s "5000 byte row"/"600 rows",
`g1.r1.l8`'s "renumberd", `g1.r2.l4`'s "requests_0.jsonl through requests_5.jsonl"). None
of these misses cost a fact: each had a redundant carrier elsewhere that the agent *did*
find (`f4`'s per-row-oversize-first ordering, in particular, was never read anywhere but
still came out correct purely because `plan_batches()`'s per-row check sits inside the
for-loop and the fragmentation check can only run after the loop completes — the
ordering falls out of the algorithm's natural shape rather than being copied from a
remark). Both `r1` herrings (`h1`, `h2`) were never seen either; the agent built the
correct post-reversal design straight from `rev1` (partially — see below) and `rev2`
(fully), so there was no herring to be fooled by in the first place.

One interesting self-correction: reading an early (2025-01-23), out-of-context `#code-
review` remark from dario ("[the fragmentation error] wants to be a
`BatchPayloadTooLargeError` subclass... making people add a second except... is just
churn"), the agent's Analysis briefly and incorrectly concluded `BatchPlanTooFragmentedError`
*was* a subclass (line 2862). Two tool calls later it read the fuller April 2025-04-08
exchange (konrad/emil/gideon/nikolai settling on "own `ValueError`, not subclassed") and
corrected itself (line 2963) before writing any code — the shipped module has the
correct, non-subclassed relationship, with the docstring explicitly citing the reasoning
("a handler that knows how to shrink a payload has nothing useful to say about
fragmentation").

`g1.r1.rev1` deserves a specific flag: the agent's `plan_format_version` keyword search
surfaced only the *last* message of that reversal thread (dario's closing line), not the
messages establishing that span/size move out of `metadata_{i}.json` into
`batch_plan.json`. That gap was invisibly patched over by the separately, fully-found
`g1.r1.rev2`, which states the same migration in full — exactly the kind of redundancy
`spread_problems()` is meant to guarantee.

## End state

PR #737 merged to `main`; CI run #5 on merge commit `0c36050` green including the deploy
step; the curator service on port 9100 confirmed healthy after deploy. 30 new unit tests
pass locally, `ruff check`/`ruff format --check` clean. All 10 hidden-requirement facts
scored 1, `lost_facts` is empty.
