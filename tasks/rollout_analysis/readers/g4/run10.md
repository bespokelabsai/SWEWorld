# g4 run 10 (rollout 4359a8a5, eval 0ebb2b86) — reward 0.875

## What this run found

The agent read the whole source tree, then correctly ruled out wiki and mail (this task's
world genuinely carries none of the 48 remarks there — matching the answer key's "no wiki or
mail carriers" note) after real searches on both surfaces. It dumped all 12 Mattermost channels
to disk (11k lines) and worked a keyword-grep -> targeted `awk NR=...` read-in-context loop. That
loop recovered 33 of 48 remarks: all 4 herrings, all 4 reversals, and 25 of 40 clues, spread
across code-review, engineering, pipeline, cookbooks, incidents, random, releases, viewer,
general and help — enough to satisfy every fact except one.

**g4.r1** came back essentially complete. The twelve-key `IDENTITY_COMPONENT_KEYS` tuple, its
alphabetical order, the `dataset_hash`/`parse_func_hash`/`response_format` canonicalisation
rules, the resolved-`backend` vs `backend_params`-copy scope split, and the
`IDENTITY_BACKEND_PARAM_KEYS` four-key exclusion (both herrings about hashing `backend_params`
whole, and both of their reversals) were all recovered from chat and shipped nearly verbatim
(transcript lines 2934-3286, 4149-4980). All four r1 facts scored 1.

**g4.r2** came back mostly complete too: the keyword-only `run_id` parameter threaded from
`__call__` down to `compute_run_identity`, the `CURATOR_RUN_ID`-env-or-uuid4 default, the
`v3-nocache-<16hex>` hash format and its no-`uuid`/`random`/`secrets` constraint in
`run_identity.py`, and the "`run_id` null on a cached run" scope rule were all found and
implemented correctly — `rule`, `scope`, and `observability` all scored 1.

## What it missed and why

`g4.r2.failure_behavior` scored 0, and it is a real implementation bug, not a corpus defect.
`compute_run_identity` implements both refusals almost word-for-word from the answer key
(transcript lines 6453-6456): it raises `RunIdentityError` when `cache_enabled` and `run_id is
not None`, and when cache is off with no usable `run_id`. The agent found two of the five
failure-behavior clues that describe this (`g4.r2.l10`, incidents.txt, line 4171; `g4.r2.l12`,
engineering.txt, line 3525 — the latter almost dictating the exact rule) and paraphrased them
correctly in its own reasoning (line 8354).

But the wiring in `LLM.__call__` defeats its own check. The patch at transcript lines 6915-6920
reads:

```python
identity = self._run_identity(dataset_hash, cache_enabled=cache_enabled, run_id=None if cache_enabled else run_id)
```

Any caller-supplied `run_id` is silently replaced with `None` whenever `cache_enabled` is
`True`, *before* `compute_run_identity` ever sees it — so the "refuse a run_id on a cached run"
branch is dead code from the only public entry point. The grader's failing assertion
(`test_r2.py::test_failure_behavior__a_missing_id_and_an_unwanted_one_are_both_refused`) is
exactly this case: `llm(rows, run_id="x")` with caching enabled should raise and doesn't —
execution proceeds into `self._request_processor.run()` and is only stopped by the test's own
monkeypatch.

The agent never caught this because its own regression test
(`test_run_id_refused_on_a_cached_run`, lines 7774-7776) calls `compute_run_identity` directly,
never through `LLM.__call__` — so it exercised the one unit that *was* right and never touched
the integration that was broken. Its self-review at line 8352 ("in `__call__`, the mismatch is
raised before `os.makedirs`... Good.") checked ordering, not whether the value actually
propagates.

The other three failure-behavior clues (`g4.r2.l9` #viewer 2025-04-28, `g4.r2.l11` #engineering
2025-05-01, `g4.r2.say19` #releases 2025-05-02) were never surfaced at all — not a wording
problem, a coverage one. `viewer.txt` (345 lines) was fetched whole but only ever read for lines
155-185 in the transcript, so everything from mid-April on in that channel, including `l9`, was
invisible. `releases.txt` reads stopped at line 558; `say19` sits later in the file. Given the
bug lives in `__call__`'s glue code rather than in `compute_run_identity`, more failure-behavior
clues likely would not have changed the outcome — the agent already understood and could
paraphrase the rule from the two it did see; what it lacked was a test that actually called the
public API the way the grader does.

## Herrings

Both `g4.r1` backend-params-whole-dict herrings and both `g4.r2` uuid4/isoformat herrings were
read in full, correctly recognised as superseded (the agent explicitly flagged the
contradiction with the later reversal at line 3111), and not followed in the shipped code.

## Verdict

One lost fact, `g4.r2.failure_behavior`, cause `implementation_slip`: the rule was correctly
learned from chat and correctly implemented at the `compute_run_identity` level, but a one-line
glue bug in `LLM.__call__` (`run_id=None if cache_enabled else run_id`) makes the refusal
unreachable from the code path the grader actually exercises, and the agent's own test suite
tested around the bug rather than through it.
