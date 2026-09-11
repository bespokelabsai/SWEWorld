# g4 run 2 (rollout 342998b2, eval 0ebb2b86) — reward 0

## Why it scored 0

Not a solving failure — an infra failure. The agent wrote a complete, well-researched
implementation and it stayed uncommitted. A whole-transcript grep for `git commit`/`git push`
turns up zero successful invocations; the only commit-adjacent output is two `no changes added
to commit` prints (lines 9751, 9850), and `git status --short` at lines 9852–9859 shows
`db.py`, `llm.py`, `base_request_processor.py`, `curator_response.py` still **modified but
unstaged**, and `run_identity.py` / `tests/unittests/test_run_identity.py` still **untracked**.
From ~line 9600 the agent pivoted to a baseline-vs-mine integration-test parity check (git
stash/pop, re-running `tests/integrations` and `tests/code_executor` under VCR cassettes),
repeatedly hit "terminal output has not changed for several turns" watchdog warnings, and the
transcript simply runs out of turns at line 11541 still inside that comparison loop — no
`git add`, no `git commit`, no `git push`. Since "Done means" merged-to-main + CI-green +
deployed, the grader's `submission/src` checkout has no `run_identity` module at all, so every
graded test in `test_r1.py`/`test_r2.py` fails at the same `importable()` guard
(`ImportError: cannot import name 'run_identity'`). All 8 declared facts are scored `cause:
infra`.

## What it found

Search strategy: dump all 12 Mattermost channels (10,319 lines) to a local file via the REST
API, then work entirely by `grep -n` + `sed -n` region reads rather than the UI. This recovered
36 of 48 remarks, many read in full multi-turn context (not just a single grep hit) — including
all four herrings and all four reversals, correctly identified as superseded (e.g. "Found older
nocache dir discussion (Jan). Later decisions supersede," line 3479, before reading the
reversal). Its own closing design summary (line 5398) states essentially the whole of both
requirements: 12-key alphabetical `IDENTITY_COMPONENT_KEYS`, the 4-key backend-param frozenset,
`v3-nocache-` prefix semantics, `run_id` refusal rules, resolved-backend scoping, and
canonical `response_format`/`generation_params` serialisation.

The 12 misses (`g4.r1.l-schema-dump`, `l-keys-onelist`, `l-retries-fork`, `l-window-reuse`,
`l-backend-resolved`, `l-genparams-empty`, `l-genparams-fix`; `g4.r2.l1`, `l3`, `l9`, `l14`; and
the `ilse`/Jan-28 `backend-params-whole-dict-konrad` herring) were a pure keyword-recall gap —
the full corpus sat in `/tmp/chat.txt` the whole time, but phrases like "flake hunt", "three
jobs, one directroy", or "completion_window to 24h" never matched any grep query the agent
tried, and `#help` in particular was never read at all. Because carriers overlap heavily, none
of the 8 graded facts actually depended on a missed remark — the redundancy in how the task was
planted absorbed the recall gap.

## What it built, and whether it matches

Checked against `harbor_tasks/g4-run-cache-identity/.../solution/hidden_requirements.md`, the
local (never-pushed) diff is a close match on every fact:

- **r1.rule** — `IDENTITY_COMPONENT_KEYS` is exactly the 12-tuple, alphabetical (line 5896).
- **r1.scope** — `LLM.backend` returns `self._request_processor.backend` (resolved, not the
  constructor arg); `backend_params` is copied to `{}`/`dict(...)` at `__init__` before the
  processor can mutate it (lines 5788, 7789–7792).
- **r1.exclusions_or_crossover** — `IDENTITY_BACKEND_PARAM_KEYS` frozenset of exactly
  `{azure_deployment, base_url, batch_size, completion_window}`; `api_key`/`max_retries`/
  `request_timeout` never enter the filtered dict (line 5911, `_identity_backend_params`).
- **r1.observability** — an unset backend param is *absent* (KeyError-shaped), not `None`,
  matching the specific `completion_window` KeyError remark (fix25).
- **r2.rule** — `run_id: Optional[str] = None` keyword-only on `compute_run_identity`/
  `_run_identity`; stored as the `run_id` component only when `cache_enabled` is False.
- **r2.scope** — `__call__`'s patch (visible only in the raw tool call at message index 264 of
  the full rollout JSON, not in the rendered terminal text) mints
  `run_id = os.environ.get("CURATOR_RUN_ID") or uuid.uuid4().hex` before computing identity —
  exactly the described default chain.
- **r2.failure_behavior** — both refusals implemented with the right truthiness (`""` treated
  like `None`), and `reconcile_run_directory` is called *before* `os.makedirs`, with a comment
  explaining why (line 8097–8102) — this ordering was itself lifted from a specific remark
  (`g4.r2.l12`).
- **r2.observability** — `run_hash` prefix is `v{version}-nocache-` + 16-char digest = 27 chars;
  `run_identity.py` imports only stdlib/xxhash/logger, no `random`/`secrets`/`uuid`.

The one implementation deviation worth flagging (moot here, since nothing shipped): `__call__`'s
new `run_id` parameter was appended without a preceding bare `*`, so it isn't strictly
keyword-only the way the spec asks for all three call sites.

## Bottom line

This is a "the work was done, the workflow wasn't finished" run. If the last ~1,900 lines of
turns spent on baseline-vs-mine test comparison had instead gone to `git add && git commit &&
git push`, this run would likely have scored close to the `clues`/`located`-arm ceiling on the
facts it demonstrably reconstructed correctly.
