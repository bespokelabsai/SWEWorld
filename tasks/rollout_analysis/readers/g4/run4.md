# g4 run 4 (world-hosted v5, eval 0ebb2b86, rollout ad4a75af) — reward 1

## What this run found

The agent (lumen, 200 steps) worked the ticket cold, cloned `curator`, and by step 33 had
already tried a narrow Mattermost keyword search (`python3 /tmp/mm.py identity`) that
surfaced fragments of both `r1` herrings, the `r2` uuid4-nocache herring, and several clues
(`l-keys-count`, `l-backend-default`, `l-retries-fork`, `rev2`, `l-key-on-disk`). Recognising
"chat contains the real design discussion" (line 2769), it then wrote a dumper that pulled
**every** channel's full post history over the Mattermost REST API into `/tmp/chat.txt`
(10,309 lines, all 10 channels, full date range) rather than relying on search snippets. From
there it drove three broad greps — the identity-jargon pattern
`compute_run_identity|run_identity|IDENTITY_BACKEND_PARAM_KEYS|identity stamp|...` (line 2800),
a bare `component` grep (line ~3804), and an `adopt|mismatch|upgraded|matched|reconcile|stamp`
grep (line ~4120) — each followed by `sed` reads of the surrounding 40-60 line windows to get
full conversational context (e.g. lines 7141-7152, 7190-7240, 7880-7920, 9340-9400, 9780-9830,
10100-10160, 6360-6420 were each read in full, not just the grep hit line). This caught 38 of
48 planted remarks, all 4 herrings and all 4 reversals.

## What it missed and why

Ten remarks (`l-params-none`, `l-schema-order`, `l-window-reuse`, `l-completions-object`,
`l-backend-resolved`, `l-genparams-empty`, `l-system-prompt`, `l-params-copy`, `g4.r2.l2`,
`g4.r2.l11`) never surfaced anywhere in the transcript — confirmed by grepping the transcript
directly for each remark's distinctive phrasing, not just trusting the pointer sheet. All ten
share one cause: none contain any of the three grepped terms, so nothing pulled them up even
though the full corpus was sitting on disk in `/tmp/chat.txt` the whole run. The agent's search
was keyword-driven against a fully-available dump rather than genuinely exhaustive — it read
strategically around hits rather than sequentially through all 10,309 lines. Notably this had
**zero cost**: for scope, `l-backend-resolved`'s content (LLM.backend resolves to
`self._request_processor.backend`) was independently derived by the agent reading `llm.py`'s
source directly (line 6277), and every other missed remark's fact was carried redundantly by
2-5 other remarks the agent did read (e.g. `r1.rule` alone had 9 surfaced carriers).

## What it believed and why

All four herrings were seen — three via the initial narrow search, one (`h2-isoformat-segment`)
via the broad dump — and all four were correctly rejected in favour of their reversals before
any code was written. The agent's synthesis notes show it explicitly tracking the corrected
design at each point: "backend_params in digest limited to IDENTITY_BACKEND_PARAM_KEYS ...
with the same 'sorted items line shape' as generation_params" (line 3671, reconciling the
herring's phrasing with the reversal's actual scope) and "no, you hand it one. keyword only,
run_id: Optional[str] = None ... and the uuid4 comes out" (line 2927, quoting `rev1` verbatim).
Nothing in the shipped `run_identity.py` diff hashes the whole `backend_params` dict or mints a
bare `uuid4()` inside the disable-cache branch — the final diff (line 10139-10145) implements
exactly the reversed design: `if cache_enabled and run_id is not None: raise RunIdentityError`
and `if not cache_enabled and not run_id: raise RunIdentityError`.

## Why every fact still scored 1

`g4.r1.rule` and `.scope` were carried by 9 and 3 surfaced remarks respectively (`l-schema-dump`,
`l-keys-count`, `l-keys-onelist`, `say22`, `l-keys-order`, `fix26`, `l-parse-func`,
`l-genparams-fix`, `say23` for rule; `fix27`, `l-backend-default`, `say24` for scope).
`.exclusions_or_crossover` and `.observability` were each carried by 4-5 remarks centred on
`IDENTITY_BACKEND_PARAM_KEYS` and the api_key/max_retries/request_timeout exclusion
(`l-retries-fork`, `rev2`, `l-key-on-disk`, `l-param-keys`, `rev1`). On `r2`, `.rule` and
`.scope` were carried by the `run_id: Optional[str] = None` thread (`rev1`, `l1`, `l3`, `l4`,
`l6`) and the CURATOR_RUN_ID/uuid4 default-minting thread (`l5`, `l6`, `l7`, `l8`, `l15`).
`.failure_behavior` rested on `l9`, `say19`, `l10`, and `l12` — the agent explicitly confirmed
"cache_enabled True + run_id not None (including \"\") => RunIdentityError" (line 3515) before
implementing the two refusal branches. `.observability` came from `l13`'s "always 27 chars" and
`l15`'s AST-scan requirement, both of which the agent checked off by name in its pre-push
review (lines 10652-10658).

There are no lost facts to explain — this is a clean success driven by redundant plant coverage
surviving an imperfect (though thorough by ordinary standards) keyword search, plus one instance
of the agent recovering a missed clue's content straight from the repository source instead.
