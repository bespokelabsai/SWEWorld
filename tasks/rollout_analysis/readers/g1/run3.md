# g1 run 3 (a653d6d4) — reward 1.0

## What this run found

A textbook full-corpus sweep. Search for planner-related terms in `/api/search` and simple
chat grep came up thin, and the agent explicitly diagnosed *why* rather than giving up: wiki
JSON was markdown/JSON-escaped (`batch\_size`), so two conversion attempts failed silently
before it settled on fetching every page's full `/api/pages/{id}` body **and comments** and
grepping loosened patterns (line 1092–1745) — exactly the path the answer key requires, since
BookStack's search does not index comments. That is how both wiki-comment remarks
(`g1.r1.l2` — `PLAN_FILE_NAME = "batch_plan.json"`, `g1.r2.l9` — the full untouched-file list
including `batch_objects.jsonl`/`.arrow`) were recovered (lines 4486, 4523).

Mail got the same full-mailbox treatment: all 107 IMAP messages dumped, keyword-grepped, and
triaged by subject line into "highly relevant" threads (line 1951). Chat got a full 10k-message
dump across every Mattermost channel, followed by iterative, increasingly tight keyword passes
and ~300-line context reads (steps 51–64, lines 3157–3826) that recovered the bulk of the
corpus: the fingerprint recipe (`g1.r1.l6`, line 3640 — the single most load-bearing remark),
the strict envelope order (`g1.r1.say22`), the fragmentation-error family (`g1.r1.f1/f2/f3`),
and both sweep-ordering reversals (`g1.r2.rev1`/`rev2`).

By the end the agent had independently re-derived and verified two of the three pinned digests
with a live `sha256` computation (line 4612) rather than trusting the quotes, and caught a real
regression risk on its own — the ticket's api-specific payload measurement could shift existing
integration-test splits, so it computed the actual per-row byte size (156 bytes) and confirmed
the pinned tests still held before writing the auto branch (lines 6244–6398). All 22 of its own
new unit tests passed, the change was pushed, CI went green, and the deployed release's `/health`
confirmed the new commit — all ten graded facts scored 1.

## What it missed and why

18 of 50 remarks (36%) never surfaced in this transcript, concentrated in two identifiable
gaps rather than scattered randomly:

- **`#incidents` produced zero hits all run.** All three of its remarks (`g1.r1.say30`,
  `g1.r1.l8`, `g1.r2.l10`) are absent. The agent's grep passes simply never matched anything
  there — a full-channel blind spot.
- **`#engineering` was explicitly abandoned** after its early hits turned out to be an
  unrelated cache-fingerprint feature ("Engineering hits are about cache fingerprints,
  unrelated," line 3008), taking `g1.r2.l4`, `g1.r1.l5`, and `g1.r1.f4` down with it.
- **One genuine near-miss in mail**: the subject list at lines 1927–1932 plainly shows
  "mail: resumed batch run double-submitted ~400 requests" (mails 89–94, carrying
  `g1.r2.l6`/`g1.r2.scope`), but the very next Analysis (line 1951) names only two "highly
  relevant" threads and this one is never opened anywhere else in the run — triage by subject
  line rather than by content cost this one.
- Scattered elsewhere: individual exchanges inside otherwise well-covered channels
  (`#pipeline`, `#code-review`, `#releases`, `#viewer`) that the tightening keyword passes
  didn't happen to net (`g1.r1.l1`, `l9`, `l15`, `l16`, `say25`, `say28`, `g1.r2.l1`, `l5`,
  `l7`, `l12`, `l13`).

None of this cost a fact, because the plant is redundant by design (no leaf closes its
subconclusion alone) — every missed remark's information reappeared in at least one other
remark the agent did read. The one exception is `g1.r2.scope`: all three of its dedicated
remarks (`l5`, `l6`, `l7`) were missed, and the fact still passed because it follows directly
from the ticket's own explicit line that the integer `batch_size` branch "keeps its current
behaviour exactly" — a "ticket"-derived pass, not a remark-derived one.

## What it believed, and why

All four herrings were seen, and all four were correctly rejected in favor of their
reversals — the run never shows a moment of genuine indecision, only progressive discovery.
The r1 herring (fold the plan into `metadata_i.json`) never appears as a standalone hit; it
only surfaces embedded inside the same tool dump that also carries its own reversal
(`g1.r1.rev2`, transcript lines 3742–3746), so the pointer sheet's 0-hit count for `g1.r1.h2`
undersells what was actually on screen. The r2 herring (sweep files before planning) was seen
directly in two channels (`#releases`, `#cookbooks`) and reversed by both `rev1` and `rev2`
independently; the agent's running summaries converge on "sweep after planning" well before
implementation (line 5222) and the shipped code matches. `code_followed_herring` is false
across the board.

## Lost facts

None — reward is 1.0 across all ten graded facts. There is nothing to attribute to
`not_found`/`herring_followed`/`grader_overspecifies`/etc.
