# g4 run 6 (ec814c80) — reward 0.875

## What this run found

This is a strong run against a chat-only arm (no wiki/mail carriers for g4). The agent dumped the
Mattermost export to `/tmp/chat2.txt` once (step ~31, transcript line 2585) and then ran a sequence
of increasingly targeted `grep -n -i -E '<keywords>' /tmp/chat2.txt` passes, following up promising
hits with `sed -n '<range>p'` reads. By transcript line 3327 (step 43) it already had the full
twelve-key `IDENTITY_COMPONENT_KEYS` list, the four-key `IDENTITY_BACKEND_PARAM_KEYS` allowlist, and
the `v3-nocache-<digest>` hash shape — the core of both requirements came together fast because most
remarks cluster around a small set of technical identifiers (`run_identity`, `components`,
`IDENTITY_BACKEND_PARAM_KEYS`, `run_hash`) that the agent's grep vocabulary converged on early.

It recovered 7 of 8 hidden facts. All four herrings (`backend-params-whole-dict` ×2, `uuid4` in the
nocache path, `isoformat` segment in the nocache path) were correctly identified and correctly
resolved in favor of their reversals — the shipped code never follows a herring. `g4.r2` (the
cache-disabled run identity) is fully correct: keyword-only `run_id`, `CURATOR_RUN_ID`-or-`uuid4().hex`
minted only in `LLM.__call__`, both refusal branches (`RunIdentityError` for a cached run handed an id,
and for a disabled-cache run with `None`/`""`), and the `v3-nocache-` / 27-char / no-randomness
observability checks (transcript lines 6727–6779, verified against test_r2.py's assertions).

## What it missed, and why

The one lost fact is `g4.r1.scope`, and it fails on a single, narrow point:
`LLM.backend_params` must hand back a **fresh copy** on every read, not the live internal dict.
The shipped property (transcript line 7079–7085) is:

```python
@property
def backend_params(self) -> Dict[str, Any]:
    return self._backend_params
```

— no `dict(...)` wrapper. The failing assertion (`test_r1.py:163`) mutates the dict returned by one
call to `configured.backend_params` and checks a second call is unaffected; under the shipped code it
isn't. Every other assertion in that same test function — the resolved-not-declared `backend`, and
`backend_params == {}` when none were passed — passed cleanly, so the agent got everything about
scope it actually saw evidence for right.

The two remarks that carry precisely this sub-fact were the weakest-surfaced clues in the whole run.
`g4.r1.l-params-copy` ("the processor trims backend_params in place mid-run, so we hold what came
into `__init__` off to one side... a `dict()` of what came into `__init__`") never appears anywhere
in the 9,123-line transcript — grepped for its distinctive phrases ("trims backend_params in place",
"dict() of what came into __init__", "copied before anything downstream") with zero hits.
`g4.r1.fix27` ("popped batch_size off what llm.backend_params handed me, read it again and batch_size
was still there — so mutating what you got back doesn't reach the LLM") is the closer call: it does
appear, but as exactly one line (transcript line 5145) buried inside a `grep ... | head -30` dump the
agent ran while chasing a different keyword list. The agent's very next Analysis ("Design largely
gathered. Now examine the repo's tests and CI workflow...", line 5190) shows no trace of having
registered it — no mention of mutation or copy semantics anywhere near that point in the transcript.
A closely related remark, `g4.r1.l-params-none` (the `None`→`{}` case), was similarly half-seen: its
opening line surfaced twice (lines 5144, 5530) but the terminal window scrolled past the punchline
before it appeared; that sub-fact happened to come out right anyway, most plausibly from ordinary
defensive-coding habit (`dict(x) if x else {}`) rather than from having read the clue.

This is a clean `not_found`: nothing else in the corpus argued the opposite (no
`overridden_by_other_corpus_text`), the ticket itself says only "Add `LLM.backend` and
`LLM.backend_params` properties" with no copy semantics, and the grader is not overspecifying — the
answer key itself states `LLM.backend_params` is a copy under `scope`. The agent simply never had the
requirement in front of it in a form it engaged with.

## What it believed, and why

For every herring/reversal pair, the agent read the herring, then read the reversal, and its running
"Analysis" summaries after each grep pass only ever restate the *reversed* (final) design — e.g. after
reading both `backend-params-whole-dict-dario` (herring) and `g4.r1.rev1` (its reversal) around
transcript lines 3690–4171, the next Analysis states "backend_params in digest but
api_key/request_timeout/max_retries excluded" — the corrected rule, not the herring's "whole dict,
sorted" claim. Same pattern for the `uuid4`/`isoformat` nocache herrings: both were seen and both
reversals were seen, and the shipped `compute_run_identity` implements only the reversed design (no
uuid4, no isoformat, a caller-supplied `run_id` instead).

## Provenance

Pushed to `main` at `fd0d5cb`, Gitea Actions CI green, deploy daemon flipped `current`/`last-good`,
health check passed (transcript line 9083). No infra issues; the 0.875 reward is entirely the one
missed sub-fact above.
