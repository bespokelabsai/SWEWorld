# g1 run 9 (rollout 9016ab99, eval 8db49761) — reward 0.7

## What this run found

The search was genuinely thorough. It opened with a server-side Mattermost keyword search for
"planner" that alone surfaced snippets from 8 of 9 relevant channels, then dumped all 12 Mattermost
channels to disk in full (code-review 3183 lines, pipeline 1947, releases 661, plus cookbooks,
engineering, general, incidents, random, viewer, help, off-topic, town-square), and iterated
keyword greps (`BatchLimits|plan_request_batches|payload_bytes|measure_request|plan_id|Plann...`,
`total_requests|total_bytes|batch_plan|PLAN_FILE`, `log line|submitting|plan_fingerprint`) with
targeted `sed` windows around each identified thread. For the wiki it correctly bypassed
`/api/search` — which the ticket itself warns does not index comments — and instead enumerated
every page (7–121) and fetched each one whole with its comments, which is exactly why both
wiki-comment remarks (`g1.r1.l2`, `g1.r2.l9`) were caught. For mail it dumped the entire IMAP
mailbox in one pass rather than searching selectively and grepped it for identifiers. It even did
a deliberate final re-read pass at the very end of the run (transcript L6349–6520) specifically to
double-check two threads it worried it had skimmed. This is a strong, diligent search.

By the end the agent had correctly reconstructed almost the entire hidden design: `batch_plan.json`
written on the auto branch only, before any request file, with `plan_format_version` first in a
strict key order; the sweep of stale `requests_*.jsonl`/`metadata_*.json` moved to *after* planning
succeeds (not before, as the herring first claimed); `metadata_{i}.json` staying `{"num_jobs": n}`
only; `BatchPlanTooFragmentedError` as its own `ValueError`, checked after the per-row oversize
scan; and the exact digest recipe (`start-end:num_bytes` per batch, joined by `;`, sha256, first 12
hex). All 4 herrings were seen, all 4 reversals were seen and believed, and the shipped code follows
every reversal and none of the herrings — verified directly against the diffs of
`batch_payload_planner.py` and `base_request_processor.py`.

## What it missed, and why

Despite that, three of the ten graded facts (`g1.r1.rule`, `g1.r1.scope`, `g1.r1.observability`)
scored 0, and all three trace to **one** defect. `g1.r1.l6` (#pipeline, 2025-03-26) is the single
remark in the whole corpus that names the required function: "I was thinking of a short id derived
from it, call it plan_fingerprint." The agent found it, and its own Analysis at L2169 says so in
plain text: "Found the plan_fingerprint spec." Its own Plan text at L4363, written immediately
before appending the code, even names it explicitly: "Append plan_fingerprint (plan_id),
plan_document, write_plan." But the code that followed defines `def plan_id(plan) -> str:` — not
`plan_fingerprint` — and every later reference (the log line, the test imports, the golden-value
checks) consistently uses `plan_id`. This is a textbook `implementation_slip`: the agent's own
reasoning states the rule and the code does otherwise.

It is an understandable slip, not a careless one. Five or more other remarks (`l7`, `say24`,
`say29`, `l3`, `l12`) use "plan_id" colloquially throughout the corpus — but every one of those is
describing the *output field*/log-column name, which does match `plan_document`'s real `"plan_id"`
JSON key. Only `l6` — hedged with "or something in that direction" — names the *function*. The
recipe itself is provably correct: the agent verified both golden digests
(`ad0828fea95e`, `e3b0c44298fc`) against its own shipped code before moving on (L4470–4474). Every
other structural piece of `g1.r1.scope` (plan written before the first request file, empty-dataset
case still writes a 0-batch doc, explicit-batch_size branch never writes it) is also correctly
implemented — `test_scope` fails only on its last line, which cross-checks the stored `plan_id`
against `module.plan_fingerprint([])`, and dies with the identical `AttributeError` as the other
two tests. All three losses are one bug, not three.

Fourteen of the 50 remarks were never surfaced. All fall in channels the agent had fully dumped to
disk but stopped re-reading once it judged it had "a coherent set of decisions" (L3563) — mostly
single-fact reinforcements scattered on dates outside the specific windows it sampled (e.g.
`#incidents` was only ever grepped narrowly for `"planner|identical id"`, which doesn't match
`g1.r1.say30` or `g1.r2.l10`'s wording at all). None of these independently cost a fact: every one
is redundant with at least one other remark that *was* found and carried the same fact, which is
exactly the MuSR tree's designed redundancy working as intended — `g1.r2` scored a perfect 1.00
despite 7 of its own carrier remarks going unfound.

## Herrings

All four herring/reversal pairs were read chronologically and resolved correctly. The two most
striking cases: `g1.r2.h1`/`rev1` (sweep-order) were read back to back in the *same* `sed` call
(releases lines 300–320 then 495–515), and `g1.r1.h1`/`h2` (metadata-widening) were registered as
the working belief at L1799 — "Found a key decision: metadata_{i}.json widened..." — precisely
because that was the only information seen at that point in the chronological read, then correctly
overturned once the April reversal (L2885: "Latest decision (Apr 24) supersedes January") was
reached. `code_followed_herring` is `false` in all four cases; the shipped diffs match every
reversal.
