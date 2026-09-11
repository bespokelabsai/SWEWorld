# g7 run 3 (world-hosted v5, eval 8deffce4, rollout e53e89fc) — reward 0.875

## What this run found

The agent ran a thorough, if keyword-bound, investigation: it read the curator source tree first,
checked Gitea PR 685 (no useful comments there), then queried BookStack search with seven terms
(`ledger`, `COMPLETION_SENTINEL`, `multi-turn agent`, `seed message`, `curator+agent`,
`next_speaker`, `status tracker`) to find seven wiki pages, fetched each one whole via
`/api/pages/{id}` (correctly picking up comments, which it knew BookStack search does not index —
line 143 of the ticket text says so explicitly and the agent internalised it), searched IMAP mail
with a single `TEXT ledger` query (12 hits, all read in full), and finally dumped every Mattermost
channel to a local file and grepped it repeatedly for `sidecar|turn_ledger|ledger|sentinel|
next_speaker|interleave` and separately for `sentinel|<<END|stop marker|end marker`. This recovered
both reversals (`g7.r1.rev1`, `g7.r1.rev2`, `g7.r2.rev1`, `g7.r2.rev2`) with their full dialogue,
and 27 of 43 clues directly. It correctly reconstructed and implemented: the `turn_ledger.json`
sidecar (name, version, eight keys, 186/189-byte serialisation), `read_sidecar`/`write_sidecar`/
`verify_sidecar`/`load_ledger`, the `created`/`adopted`/`verified` tri-state, `TurnLedgerDesyncError`
with its exact message and four attributes, `COMPLETION_SENTINEL`, and a case-sensitive
suffix-only `is_completed`. All four herrings were correctly abandoned in favour of their
reversals — see below.

## What it missed, and why

16 of 51 remarks (31%) never surfaced, but for three structural reasons rather than one:

1. **Single-keyword mail search.** The IMAP query was `TEXT ledger` only. Three mail clues
   (`g7.r1.l9`, `g7.r2.g7r2-l08`, `g7.r2.g7r2-l05`) are squarely on-topic (the sidecar/stop-check
   design) but their bodies never use the literal word "ledger", so the search never surfaced them.
2. **Keyword drift between counting and printing.** The agent's own broad grep
   (`sidecar|turn_ledger|ledger|sentinel|next_speaker|interleave`) counted 69 chat hits, but the
   *printing* commands that followed used a narrower pattern that dropped `next_speaker` and
   `sentinel`. `g7.r1.say24` ("next_speaker is nothing more than the partner of last_author") was
   counted but never displayed. Several other clues (`g7.r2.g7r2-l01`, `g7.r2.g7r2-l06`,
   `g7.r2.g7r2-l09`, `g7.r2.g7r2-l03`, `g7.r1.l1`, `g7.r1.l8`, `g7.r1.say22`, `g7.r1.say23`,
   `g7.r2.say18`) simply share no vocabulary with any keyword list the agent ever ran, despite being
   present verbatim in the captured channel dumps.
3. **Wiki truncation and one page never found.** Page 211 (weekly-sync-notes-week-of-jun-2, which
   carries two found remarks) was only ever read via `head -60`, cutting off its later comment
   `g7.r2.g7r2-l10` (dated 2025-12-29, sorting after the comments actually shown); the neighbouring
   page 210 was fetched to disk and never read at all. The page carrying `g7.r2.g7r2-l07`
   ("stop-marker-matching-what-ends-a-generation") was never found by any of the seven search terms
   tried and was never independently enumerated, so it was never even fetched.

Two herrings' *original* posts (`g7.r1.g7-h2-truncate-is-the-pattern`, 2025-01-21;
`g7.r2.h1-sentinel-substring-ci`, 2025-01-22; `g7.r2.h2-sentinel-placement-free`, 2025-03-11) were
also never read directly, but their content survived intact because each is fully recapped inside
its own reversal's dialogue (e.g. rev2: *"no, that ones dead. 'checkpoint wins on the mismatch, log
gets trimmed back to the recorded count, run carries on' — thats what we agreed and it threw away
turns we had already paid for."*, line 2818). The fourth herring, `g7.r1.g7-h1-checkpoint-authoritative`,
was read directly (line 2705-2713) in addition to its reversal.

## What it believed

All four herrings were correctly disbelieved. In every case the agent's synthesis (e.g. line 3298:
*"verify_sidecar returns status 'adopted' when the sidecar is absent or at an older version,
'verified' when a current-version file agrees, raises TurnLedgerDesyncError on disagreement, and
never writes"*) matches the reversed, not the herring, position, and the shipped code implements the
tri-state adopted/verified/raise scheme with no truncation anywhere — confirmed by
`test_scope`/`test_failure_behavior` both passing.

## Why the one lost fact was lost

**`g7.r1.rule` scored 0**, with `junit.xml` recording: `probe error: TypeError: expected str, bytes
or os.PathLike object, not TurnLedger`, raised inside `test_rule__a_versioned_checkpoint_rewritten
_after_every_appended_response` at the line `write_sidecar(str(tmp_path), ledger)`.

The agent implemented `def write_sidecar(ledger: TurnLedger, working_dir: str)` and
`def verify_sidecar(ledger: TurnLedger, working_dir: str)` (transcript lines 4541, 4560) — ledger
first — while its own `sidecar_path(working_dir)`/`read_sidecar(working_dir)` take only
`working_dir`. The oracle instead defines `write_sidecar(working_dir, ledger)` /
`verify_sidecar(working_dir, ledger)` (oracle.patch lines 834, 850), working_dir first, and
`test_r1.py` calls the function positionally in that order, so under the agent's reversed signature
`working_dir` and `ledger` swap, and `sidecar_path` crashes trying to `os.path.join` a `TurnLedger`
object.

This is a **grader defect (`grader_overspecifies`)**, not a missed remark or an implementation slip.
Every remark that mentions `write_sidecar` by name (`g7.r1.l4`, `g7.r1.say20`/l6-area, `g7.r1.l15`,
`g7.r1.fix27`, `g7.r1.fix28`) was grepped, and none — nor the ticket, nor any chat/mail/wiki text —
ever shows a call site or states the parameter order. The two orderings are equally natural (the
agent's own `sidecar_path`/`read_sidecar` convention of "working_dir alone" gives no signal about
where a second `ledger` argument should go), and nothing in the 51-remark plant pins it either way.
The rest of `write_sidecar`'s behaviour — returning an absolute path, sorted/indented JSON,
rewriting after every append — was correctly recovered and is exercised successfully by the
`scope`/`failure_behavior`/`observability` tests, which never call `write_sidecar` positionally
themselves.

## Facts that passed

`g7.r1.scope`, `g7.r1.failure_behavior`, `g7.r1.observability`, `g7.r2.rule`, `g7.r2.scope`,
`g7.r2.failure_behavior`, `g7.r2.observability` all scored 1, each relying on 2-6 independently
found remarks (see `passed_facts` in the JSON) — the plant's redundancy is what let 8/9 facts
survive a search that missed a third of the individual remarks.
