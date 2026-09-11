# g7 run 4 (eval 8deffce4, rollout 625bf84c) — reward 0.625

## What this run found

The search strategy here was unusually disciplined for the wiki and chat surfaces. Rather than
relying on BookStack's search box (which the answer key notes does not index comments), the agent
enumerated every page id it found and fetched each page's body **and** its `/api/pages/{id}`
comments in one pass — recovering `g7.r1.l14`, `g7.r1.l5`, `g7.r1.l2`, `g7.r2.g7r2-l04`,
`g7.r2.g7r2-l10`, `g7.r2.g7r2-l13`, `g7.r2.g7r2-l14`, `g7.r1.l11`, and (via a later targeted fetch)
`g7.r2.g7r2-l07` — nine of the nine wiki-comment/page clues. Chat was mined with broad multi-term
greps repeatedly narrowed to line windows, recovering most of `#code-review`, `#engineering`,
`#pipeline`, `#incidents` and `#cookbooks` traffic (30 of 34 chat remarks, both herrings and both
reversals). Mail was dumped completely and correctly via a hand-rolled IMAP script (135 messages to
`/tmp/mail.txt`), but the *listing* step (`sort | uniq -c | sort -rn | head -40`) surfaces
duplicated subjects first and truncates the 40-of-135 mostly-unique remainder — `g7.r1.l9`,
`g7.r1.l16`, and `g7.r2.g7r2-l08` never appeared in that list and no later keyword grep caught
them by content either, even though the full dump holding them was sitting on disk the whole time.

`g7.r2` scored a clean 4/4. The decisive exchange is one `#engineering` thread (lines 3990–4000)
where the team explicitly retracts the case-insensitive/anywhere-in-text herring and states
`is_completed` as `response.rstrip().endswith(COMPLETION_SENTINEL)`, case-sensitive, `False` (no
exception) for non-strings — the agent found this, quoted it faithfully in its own Analysis, and
shipped exactly that. Supporting clues (`g7r2-l04`, `g7r2-l10`, `g7r2-l13`, `g7r2-l11`) filled in
scope, failure_behavior and observability without contradiction.

## What it missed, and why

All three lost `g7.r1` facts (`scope`, `failure_behavior`, `observability`) trace to **one bug**:
`verify_sidecar()` returns `"created"` for any absent sidecar file, without checking whether the
log itself is pre-existing. The answer key's rule is that `"created"` belongs only to a genuinely
fresh run (no log yet); a *load* of an existing log with a missing or deleted sidecar should read
`"adopted"`. All three failing tests fail on the identical first assertion —
`"created" != "adopted"` — before ever reaching their later, correctly-implemented assertions (the
186/189-byte serialization and the `TurnLedgerDesyncError` message/attributes, both of which match
the answer key character-for-character in the shipped code).

The agent even caught and partially fixed a version of this bug on its own (pytest.log lines
7079–7105): a local test showed an *unparseable* sidecar coming back `"created"` when it should be
`"adopted"`. Its own Analysis at that point (`"I must distinguish absent from unreadable"`) shows
exactly where the wrong split was drawn — it corrected the unreadable case but left the absent case
alone. The one remark that would have corrected this, `g7.r1.l9` ("deleted the json by hand to
test resume ... Missing file is benign — we adopt the log, then exactly one
`call_single_request(advisor, 2)`"), is never found: grepping the transcript for its distinctive
phrases returns nothing. Its sibling `g7.r1.l16` (mail: "not one call should have fired, no line
appended") is likewise absent. What the agent *did* find — a chat exchange about "verify_sidecar…
when there's nothing on disk yet… I pointed it at a freshly built ledger, status created" — happens
to describe a genuinely fresh ledger, so it read as confirmation of the overgeneralized rule rather
than as a counter-example.

A secondary, non-costly miss: the agent explicitly judged two wiki pages (143 "Reading
completion_reason", 144 "Recovering an interrupted agent turn") as describing "a different,
neighbouring artifact" / "likely decoys" (Analysis at transcript lines 2211, 2362, 2513). Both are
genuine plant carriers for this ticket. It only avoided losing facts here because chat separately
supplied the same content (`fix28`, `l12`).

## Believed vs. reversed

Both herrings were correctly abandoned. `g7-h1-checkpoint-authoritative` (truncate-the-log) and
`g7-h2-sentinel-placement-free`/`g7-h1-sentinel-substring-ci` (lowercase/anywhere match) were never
implemented; the agent found their reversals (`rev1`, `rev2` for r1; `rev1`, `rev2` for r2) and
built the corrected behavior directly. No herring reasoning survives in the shipped code.

## Lost-fact summary

| fact | cause | one line |
|---|---|---|
| `g7.r1.scope` | not_found | absent-sidecar status bug; `g7.r1.l9` never found |
| `g7.r1.failure_behavior` | not_found | same bug; raise-path itself is correct but never reached |
| `g7.r1.observability` | not_found | same bug; 186/189-byte details are correct but never reached |
