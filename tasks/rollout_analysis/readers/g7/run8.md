# g7 run 8 (world-hosted v5, eval 8deffce4, rollout 4df9fa70) — reward 0.875

## What this run found

This is close to a full reconstruction. Of 51 planted remarks (43 clues, 4 herrings, 4
reversals), the agent's search recovered roughly two-thirds directly and, because the plant
guarantees redundancy (>=2 sources / >=3 weeks / >=2 channels per requirement), every single
graded fact except one was still assembled correctly from whichever remarks it *did* see. The
wiki strategy was excellent: it enumerated pages by keyword search and then fetched each one
*whole* via `/api/pages/{id}` (msg ~85 onward), which returns comments alongside the body — the
exact move the answer key says defeats BookStack's comment-blind search — and this alone
recovered essentially all 9 wiki remarks (`l14`, `l5`, `l11`, `g7r2-l13`, `g7r2-l14`, `l2`,
`g7r2-l07`, `g7r2-l04`, `g7r2-l10`). Chat search used a channel-wide dumper plus repeated keyword
passes (`ledger`, `sidecar`, `TURN_LEDGER_VERSION`, `sentinel`, `next_speaker`, `interleave`,
`status`, `COMPLETION`, `write_sidecar`), which caught most remarks but is keyword-anchored, not
exhaustive-by-date: remarks whose exact wording shared none of the searched tokens
(`g7.r1.l1`, `say23`, `fix26`, `g7.r2.g7r2-l01/l03/l06/l09`, `say18`, both herring originals)
were never located even though their channels were opened elsewhere.

## What it missed and why

Mail search was the weakest link: subject/body keyword search only (`ledger` -> 12 hits, then
`TurnLedger`/`sentinel`/`next_speaker`/`interleave`/`adopt_ledger`/`num_cached`/
`COMPLETION_SENTINEL`, transcript lines 2199-2224), never a full-mailbox enumeration. Two threads
sent the identical minute (2025-04-09 08:12) — `g7.r1.l9` ("resume when the metadata json isn't
on disk") and `g7.r2.g7r2-l08` ("stop condition in the turn loop — does it assume string
content?") — have subjects and bodies containing none of the searched tokens and were never
listed. Both facts they carry (`r1.failure_behavior`, `r2.failure_behavior`) still scored 1
because other remarks (`l16`/`l12`/`fix28`; `rev2`/`g7r2-l10`) covered the same ground.

## What it believed, and why

All four herrings were correctly bypassed. The two r1 herrings (`g7-h1-checkpoint-authoritative`,
`g7-h2-truncate-is-the-pattern`) both describe the same false belief — "the checkpoint is
authoritative, truncate the log to match it" — and the agent only ever saw them already reversed
(`rev1` at transcript line 3901, `rev2`'s restatement at line 3052) or, for `h2`, never saw the
original at all, only its reversal's paraphrase. The r2 herrings (case-insensitive, position-free
sentinel matching) were seen (`h1`, line 2584) or missed (`h2`, never surfaced) but in both cases
the shipped `is_completed` matches the reversal (`response.rstrip().endswith(COMPLETION_SENTINEL)`,
case-sensitive, `False` for non-str) exactly. No herring reached the shipped code.

## Why the lost fact was lost

`g7.r1.rule` failed with a probe error — `TypeError: expected str, bytes or os.PathLike object,
not TurnLedger` — inside `test_rule__a_versioned_checkpoint_rewritten_after_every_appended_response`,
at the line `write_sidecar(str(tmp_path), ledger)`. The shipped module defines `write_sidecar`
and `verify_sidecar` as `(ledger, working_dir)` — ledger first — while the oracle and grader call
them `(working_dir, ledger)`, matching the working_dir-first convention every *other* function in
the ticket uses (`read_log(working_dir)`, `load_ledger(working_dir, ...)`, and the agent's own
`read_sidecar(working_dir)`). At the grader's call site this silently binds `tmp_path`'s string to
the `ledger` parameter and the real `TurnLedger` object to `working_dir`, and
`os.path.join(working_dir, TURN_LEDGER_FILENAME)` throws exactly the observed error on a
`TurnLedger` instance. This is a self-inconsistency in the agent's own code, not a corpus
contradiction: grepping both the transcript and the answer key's actual dialogue (not its
task-author paraphrase) turns up no remark that states either function's argument order in either
direction. The agent's own Analysis (transcript line 3936) shows it explicitly settling on
`verify_sidecar(ledger, work_dir)` mid-run and then carrying the same order into `write_sidecar`
without ever checking it against the working_dir-first pattern it had itself just written for
`read_log`/`load_ledger`/`read_sidecar` — a plain implementation slip, cause `implementation_slip`.
A second, unscored instance of the same class of miss: `write_sidecar` also drops the oracle's
`os.path.abspath()`, which only didn't cost a fact because `tmp_path` is always already absolute.
