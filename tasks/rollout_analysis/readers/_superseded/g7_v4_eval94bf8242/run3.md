# g7 run 3 (896aa47c) — reward 0.5

## What happened, in one line

The agent built the entire hidden checkpoint-sidecar design correctly in every
respect the grader checks *except two localized mistakes* — a wrong constant
name and a backwards status default — each of which alone is enough to zero
out a whole `g7.r1` fact under the grader's exact-value assertions. `g7.r2`
(the sentinel/`is_completed` requirement) scored a clean 1.00.

## Search behaviour

The agent's information gathering was unusually systematic for a 170-step
run: full per-channel Mattermost dumps (all 11 channels, ~9,800 messages) to
`/tmp/chat/<channel>.txt`; a full enumeration of all ~168 BookStack pages with
comment counts, followed by whole-page (body+comments) fetches of every page
it opened; and a single full IMAP mailbox dump with every one of the 8
relevant threads read start to finish (8/8 mail remarks recovered — mail was
its strongest surface). It correctly learned BookStack's search-vs-comments
trap early and explicitly fetched pages via `/api/pages/{id}` rather than
relying on `/api/search`.

Two structural weaknesses cost it, though:

1. **Chat search was keyword-driven, not exhaustive**, even though the full
   text of every channel sat on disk. Greps like `interleave|adopt_ledger|
   num_cached|turn_ledger.py|TurnEntry|TurnLedger` and `sentinel` recovered
   most of the design, but remarks phrased with different vocabulary (e.g.
   `say21`'s `read_sidecar`, `l8`'s `created`/`verified` pairing) were never
   surfaced despite being one grep away.
2. **One wiki page was found but never opened.** Page 211, "Weekly sync
   notes: week of Jun 2 (release + CI)," carries three of the corpus's
   remarks, including the *only* occurrence anywhere of the literal constant
   name `TURN_LEDGER_FILENAME`. A file-listing grep matched it
   (`grep -rli 'multiturn|multi-turn agent|seed_message|responses_0'
   /tmp/wiki/`, transcript line 4634) and its title was echoed via `head`
   (lines 4672-4673), but its body and 4 comments were never displayed — the
   agent moved on to pages 69/85/195 instead. This is a genuine open-vs-list
   gap, not a keyword-coverage gap.

The agent also twice correctly identified and rejected a **decoy wiki page
body** that closely echoes the real plant's wording while describing a
different design: page 144's `turn_ledger.json`/`turn_ledger.jsonl` two-file
scheme (line 1951: "likely the neighbouring question, not what the ticket
asks"), and page 143's `budget_exhausted`/`agent_signal`/`error`/`cancelled`
four-value `completion_reason` scheme (line 4808: "This page is a
neighbouring artifact"). Its instinct to distrust body text that looked like
a *different* code artifact than the one the ticket wants was sound. But on
page 144 this cost it: the terminal's screen-buffer cut the `cat` off right
at the end of the decoy body, one comment away from nils' actual remark
(`g7.r1.l11`, about a half-written `turn_ledger.json` being treated as
absent) — the agent never scrolled further to see it.

## What it believed, and why it was mostly right

Every herring the agent actually encountered, it correctly rejected in favor
of its reversal — it never implemented truncate-the-log-to-match-the-
checkpoint (the `g7.r1` herring) or case-insensitive/anywhere-in-text sentinel
matching (the `g7.r2` herrings). Two of the four herrings were never seen
directly (`g7.r1.g7-h2-truncate-is-the-pattern`,
`g7.r2.h2-sentinel-placement-free`), but their reversals were, and the
reversals restate the wrong original decision as context before overturning
it — so the agent inherited the correct belief secondhand without ever
believing the wrong one. This is visible in the code: `TurnLedgerDesyncError`
is raised rather than truncating, and `is_completed` is a case-sensitive
suffix check via `response.rstrip().endswith(COMPLETION_SENTINEL)` — both
exactly right.

## Why `g7.r2` scored 1.00

Unusually, the open ticket itself already primes most of `g7.r2.rule` — it
names the `COMPLETION_SENTINEL` constant and explicitly instructs "give it a
real default implementation" for `Agent.is_completed`, which was previously
dead code. The *hidden* part — case-sensitive, suffix-only, not
case-insensitive substring — needed only one high-yield grep
(`grep -rn -i 'sentinel' /tmp/chat/*.txt`, line 2612) to surface both `g7.r2`
reversal remarks nearly verbatim ("is_completed is
`response.rstrip().endswith(COMPLETION_SENTINEL)`, nothing else... case
sensitive now"). `scope`, `failure_behavior` and `observability` were each
independently confirmed via full reads of three wiki-comment threads (pages
147, 152, 143) and two mail threads (the json-mode `AttributeError` thread,
the prototype-transcript-closing-message thread). Every fact traces to a
remark the agent actually read and quoted in its own reasoning.

## Why `g7.r1` scored 0.0 — two separate, localized causes

**Cause 1 (`rule`): a missing constant name, from a page never opened.**
The grader's very first assertion, `sym("TURN_LEDGER_FILENAME") ==
"turn_ledger.json"`, fails outright because the shipped module (transcript
line 9496) defines `SIDECAR_FILENAME`, not `TURN_LEDGER_FILENAME`. The single
remark carrying that literal name is `g7.r1.l2`, a wiki *comment* on the
never-opened page 211. Lacking it, the agent had to invent a name, and it
chose wrong. This is a pure "not found" loss — nothing it read pointed the
other way, and the constant otherwise behaves correctly (right value, right
type, right 186/189-byte serialization).

**Cause 2 (`scope`, `failure_behavior`, `observability`): a misread of the
one remark that actually answers the question.** All three of the remaining
facts fail on the identical assertion — `read_field(ledger, "status") ==
"adopted"` returns `"created"` instead, whenever `load_ledger` is called on a
directory that already has a log but no sidecar file. The agent's own
reasoning shows exactly how this happened. At line 3565, right after reading
`g7.r1.fix27` and `g7.r1.fix30` in `#pipeline`, it wrote: *"verify_sidecar
returns status 'created' when nothing on disk, 'adopted' when version
missing/<2..."* — but `fix27`'s actual text is "i pointed it at a **freshly
built ledger, status created** [describing the input] ... first with
`turn_ledger.json` **deleted**, then nils' old record. **came back adopted
both times, not verified**." The agent took "status created" — which
describes the ledger object *fed into* `verify_sidecar` — and misapplied it
to the *output* for a missing file, ignoring the sentence that immediately
follows and says "adopted both times." It then compounded this by
over-generalizing `fix30` (which is about a wholly *fresh run with no log at
all*, where `verify_sidecar` genuinely never fires) onto `load_ledger`'s
different case of resuming an *existing* log with a missing sidecar. It
restated and kept this same mistaken belief at line 5681 ("So verify_sidecar
with no file → 'created'. Keep as implemented.") without ever revisiting it.
The one remark that states the correct rule in plain terms, `g7.r1.l8`
("first write carries created, verified is only a load where both matched"),
was never found.

Notably, everything *else* in these three tests passes: the exact 186/189
byte counts and sorted/indented JSON shape, the `TurnLedgerDesyncError`
raised with the right `.path`/`.log_responses`/`.recorded_responses`/
`.log_last_author`/`.recorded_last_author` and message wording, and zero
calls before the raise. Roughly twenty distinct remarks were found and acted
on correctly for `g7.r1` — the requirement was reconstructed almost
completely — but the grader's exact-value assertions mean that one missing
page and one misread sentence were each individually sufficient to zero out
a fact whose other nine-tenths were right.

## Note on a corpus mismatch (not scored)

`g7.r1.l12`'s mail thread, in the world this rollout actually ran against,
reads "yes, the log side only. That was deliberate... there is deliberately
no matching pair for the ledger side" (line 3996) — an older text than the
current answer key's "no, both sides." The agent shipped both
`.recorded_responses`/`.recorded_last_author` and `.log_responses`/
`.log_last_author` anyway (most likely inferred from `g7.r1.l16`'s
vocabulary), so this had no effect on scoring; it is flagged here only
because it is a genuine divergence between the answer key text and what the
transcript shows, per the coordinator's note.
