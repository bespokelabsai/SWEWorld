# g7 run 1 (rollout 40414285) — reward 0.75

## What this run found

The agent's search was surface-sequenced: repo code and tests first, then Gitea
issues (keyword search), then BookStack wiki (keyword search, but every hit page
fetched *whole* via `/api/pages/{id}` — which bundles comments, so it caught
essentially all 8 wiki-comment remarks it touched: l14, l5, l11, g7r2-l07,
g7r2-l13, g7r2-l14, plus the page-body remark g7r2-l04 and its sibling comment
l2 on `weekly-sync-notes-week-of-jun-2-release-ci.md`, transcript lines
4403–4529). Then mail: an IMAP `TEXT` search restricted to exactly four literal
keywords (`ledger`, `sentinel`, `next_speaker`, `turn_ledger`, line 2478), which
surfaced 12 of the mailbox's messages and read them in full. Finally Mattermost —
here the agent did something better than keyword search: it dumped **every**
channel to local files in full (code-review 3243 lines, cookbooks 774,
engineering 2501, incidents 243, pipeline 2009, releases 665, viewer 312, line
3084–3097) and then grepped those dumps for a rotating set of terms, reading
whatever windows the hits pointed to.

This strategy recovered 26 of the 43 chat clues plus all 4 herrings/all 4
reversals it encountered as full multi-turn exchanges (not snippets), including
both reversals for r1 (rev1 at line 2602/3941, rev2 at line 3044) and both for r2
(rev1 at line 3055, rev2 at line 3052 and again in full at 3949–3958). It never
followed a herring into shipped code — in every case the reversal was read and
the herring's earlier, wrong design was explicitly discarded.

## What it missed and why

Two structurally different gaps:

1. **Mail: keyword net too narrow.** Four of the eight planted mail threads
   (`g7.r1.l9`, `g7.r1.l7`, `g7.r2.g7r2-l05`, `g7.r2.g7r2-l08`) never contain the
   literal words "ledger", "sentinel", "next_speaker" or "turn_ledger" anywhere
   in their body (verified by grepping the answer key's own quoted text for
   each). They were invisible to the IMAP search used and were never surfaced by
   any other route. None of these misses cost a graded fact in the end — the
   facts they carry (comparison is only two keys; non-text reply returns False;
   suffix-only "tail end" framing) were independently recovered from other
   remarks (l6/l8/rev1 for the former, rev2 for the latter two).

2. **Chat: un-visited channels/date-windows.** #releases was never dumped or
   read at all (missing `g7.r2.say18`). #viewer, #cookbooks and #incidents were
   each read only in narrow windows clustered around dates the agent already
   had a lead on, missing five more clues (`g7.r2.g7r2-l01`, `g7.r2.g7r2-l06`,
   `g7.r1.say22`, `g7.r1.say23`, `g7.r2.g7r2-l09`) and both original herrings
   (`g7.r1.g7-h2-truncate-is-the-pattern`, `g7.r2.h2-sentinel-placement-free` —
   the agent only ever saw these as paraphrased inside their own reversals,
   never as the standalone remark). None of these misses were output-truncation
   artifacts (`| head`, pager cutoffs) — they are genuine un-visited
   date-ranges, confirmed by grepping the full transcript for each remark's
   distinctive phrasing and finding zero hits anywhere.

None of the above misses cost a fact. The two lost facts trace to a single root
cause described below.

## What it believed and why

All four herrings were seen alongside (or, in two cases, only via) their
reversals, and the agent believed the reversal in every case:

- **r1 checkpoint-authoritative → reversed.** Herring read in full (line
  3047–3052: "settled on resume semantics: turn_ledger.json is the source of
  truth ... we truncate it back"). Reversal (rev1, line 2602/3941) explicitly
  states the truncation was pulled because "resume was binning paid turns" and
  the shipped `verify_sidecar` never truncates the log — only adopts or raises.
- **r1 truncate-is-the-pattern → reversed.** The herring itself was never
  independently read, but its wording surfaces verbatim inside the reversal
  exchange the agent did read (line 3044–3046: "checkpoint wins on the
  mismatch, log gets trimmed back to the recorded count ... thats what we
  agreed and it threw away turns we had already paid for. so it's gone.").
- **r2 sentinel-substring-ci → reversed.** One turn of the herring surfaced
  (line 3059), the full reversal did (line 3054–3058: "is_completed is
  `response.rstrip().endswith(COMPLETION_SENTINEL)`, nothing else"). Shipped
  code matches the reversal exactly.
- **r2 sentinel-placement-free → reversed.** Herring never independently
  found; its content is recapped inside the reversal, which the agent read in
  full twice (line 3052 and again at 3949–3958: "no. scrap that one, its wrong
  ... there is no scan anywhere. it only looks at the end").

## Why each lost fact was lost

Both zero-scored facts — `g7.r1.failure_behavior` and `g7.r1.observability` —
fail on the identical assertion pattern: `TurnLedgerDesyncError` is missing a
`recorded_responses`/`recorded_last_author` attribute
(`AttributeError: 'TurnLedgerDesyncError' object has no attribute
'recorded_responses'`). Every other value in both tests (the 186/189-byte
sidecar contents, `.path`, `.log_responses`, `.log_last_author`, the three-way
`adopted`/`verified`/raise split) passes.

This traces to one remark, `g7.r1.l12` (mail "which state files does the resume
consistency check actually cover"), which the agent read in full across three
assistant turns (transcript lines 2796–2869). The email's final reply, **as it
is actually rendered in this world**, is unambiguous: "Dermot, on your
question: yes, the log side only. That was deliberate ... .log_responses is the
count and .log_last_author is the name ... with .log_responses and
.log_last_author on the exception carrying the log side." (line 2855–2866). The
agent's own analysis at that point (line 2825) records exactly this reading —
"`TurnLedgerDesyncError` with `.log_responses`/`.log_last_author`" — and it is
repeated unchanged at every subsequent consolidation (lines 3941, 5156, 7862).
The shipped class (lines 5259–5285) stores only `self.path`, `self.log_responses`,
`self.log_last_author`, with a docstring reading "keeping the log side on the
object" — nearly a direct quote of nikolai's phrasing in the mail. This is not
a misread: it is a faithful, careful implementation of what the world actually
told the agent.

The catch: this is very likely a **corpus/plant desync**, not an agent error.
The answer key's own "Where every remark is" section quotes a *different, opposite*
final reply for this same message id (`hidden_requirements.md` lines
1566–1573): "no, both sides ... .recorded_responses and .recorded_last_author
are what the file claims, .log_responses and .log_last_author are what we
rebuilt from the log." And the plant's own `plant.json`-derived "must be typed
literally" list for `g7.r1.l12` (hidden_requirements.md line 1511) never
requires the strings `recorded_responses` or `recorded_last_author` — only
`.log_last_author`/`.log_responses`. So both the literal-terms contract and the
simulated corpus text agree with each other and with what the agent shipped;
it is the answer key's recorded "as it appears" quote for this one remark that
disagrees with the world the agent could actually read. A second remark,
`g7.r1.l16` (found and read in full, lines 2628–2765), does use the prose
"recorded_responses 3 and recorded_last_author advisor" describing the values
the error reported — but as ordinary prose describing what appeared in a
message, not as an explicit attribute-naming claim, and it does not rebut
l12's explicit "log side only, that was deliberate" design statement. Given
both, the agent reasonably sided with the remark that discussed the object's
attributes directly.

Net effect: a well-evidenced, correctly-reasoned implementation choice lost
2/8 facts (0.25 of the reward) because of what looks like a discrepancy between
the world actually served to this rollout and the answer key's documentation of
one of its own planted remarks.
