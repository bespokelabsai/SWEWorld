# g4 run 8 (ad4ce258, eval 0ebb2b86, world-hosted v5) — reward 1

## What this run found

A clean sweep: all 8 declared facts scored 1, plus `open_feature`, `suite_ok`, and every
provenance check. The agent's method was to stop treating Mattermost/BookStack as things to
*search* and instead treat them as a corpus to *download*: it authenticated to both, then dumped
all 12 chat channels (~9,600 messages) to `/tmp/chat/*.txt` and all 228 wiki pages — body **and**
comments, since BookStack search does not index comments — to `/tmp/wikitxt/*.txt` (transcript
lines 2330-2445, 2661-2709). Only after that did it start grepping: `compute_run_identity`,
`components`, `v3-|nocache`, and a combined `identity|digest|stamp|components|mismatch|run_hash`
scan that returned 107 hits across the corpus (line 3444), each followed up with `sed` reads of
the surrounding conversation. It also correctly established a negative — no wiki page documents
the cache-identity design at all (lines 3185-3349) — matching the answer key's own statement that
g4's 48 remarks live entirely in chat.

That method recovered essentially the whole design: the 12-key alphabetical
`IDENTITY_COMPONENT_KEYS` tuple with `parse_func_hash`/`prompt_func_hash` (not the bare names) at
step 30/62 (lines 2287, 3862); the 4-key `IDENTITY_BACKEND_PARAM_KEYS` frozenset at step 38 (line
3552-3558); the resolved-backend and copied-backend_params scope facts (lines 2285, 5631, 2571);
the `v3-nocache-` prefix and 27-char/16-hex observability facts (lines 2794, 2838); and the
two-directional `RunIdentityError` refusal for `g4.r2.failure_behavior` (lines 3763, 3908, 4431,
2953) — refuse a `run_id` on a cached run, refuse `None` *or* `""` on an uncached one, before the
run directory is ever created. The raw rollout JSON (message indices 219-231) confirms the shipped
`run_identity.py` implements every one of these verbatim, down to `json.dumps(...,
sort_keys=True, separators=(",", ":"))` and `dict(sorted((generation_params or {}).items()))`.

## What it believed, and why

The four herrings all resolve correctly. The two nocache herrings
(`g4.r2.h1-uuid4-nocache`, `g4.r2.h2-isoformat-segment`) were both directly read alongside their
own reversals in the same `sed` dump (lines 2486-2513 and 2789-2793 respectively), so the agent
never had to reconcile a contradiction across separate reads — it saw "X was decided" and "X is
gone" in one screen each time. The two `backend_params`-whole-dict herrings are more interesting:
neither original Jan-1928/30 remark was ever displayed (see below), but the agent caught a live
apparent contradiction anyway — an Apr-21 pipeline thread quotes the herring's exact wording
("backend_params goes into the digest whole...") immediately followed, lines later in the same
scrollback, by the reversal naming `IDENTITY_BACKEND_PARAM_KEYS`. It flagged this explicitly
("Need to resolve which is settled", line 3588) and correctly read the second as chronologically
later and authoritative, not a live disagreement.

## What it missed, and why (no fact lost)

13 of the 48 answer-key remarks never appeared in the displayed terminal output, despite sitting
in the agent's own `/tmp/chat` dump the entire time: `g4.r1.backend-params-whole-dict-konrad`,
`g4.r1.backend-params-whole-dict-dario`, `g4.r1.l-keys-onelist`, `g4.r1.l-retries-fork`,
`g4.r1.rev2`, `g4.r1.l-schema-order`, `g4.r1.l-window-reuse`, `g4.r1.l-genparams-empty`,
`g4.r1.l-genparams-fix`, `g4.r1.l-system-prompt`, `g4.r1.l-params-copy`,
`g4.r1.l-completions-object`, `g4.r2.l1`, `g4.r2.l2`. The pattern is consistent: these are early
dated (before the agent's first grep hit landed in that channel — e.g. the Jan-28/30 herrings sit
before the earliest code-review/incidents range the agent ever `sed`-read) or phrased without any
term in the agent's search vocabulary (`digest`, `identity`, `components`, `run_hash`, `v3-`,
`compute_run_identity`). The agent worked forward from grep-hit locations and hand-picked `sed`
ranges rather than reading each channel start-to-finish, so anything sitting outside those windows
was simply never scrolled into view.

None of this cost a fact. Every one of the 13 misses carries a fact that was independently
recovered from a different, redundant remark elsewhere in the corpus (e.g. `l-retries-fork` and
`l-window-reuse` are subsumed by `l-param-keys`/`rev1`, which state the same
`IDENTITY_BACKEND_PARAM_KEYS` rule directly). In two cases (`l-params-copy`, `l-genparams-fix`)
the agent arrived at the correct code independently by reading the *source* — it noticed
`_factory.py` mutates `backend_params` in place ("The factory mutates the params dict, so the LLM
must snapshot backend_params in `__init__`", line 6583) and derived the copy-on-init fix without
ever seeing the chat remark that states the same thing.

## Why every fact passed

`g4.r1.rule`/`scope`/`exclusions_or_crossover`/`observability` and `g4.r2.rule`/`scope`/
`failure_behavior`/`observability` all trace to multiply-redundant remarks that the search did
surface, and the raw tool-call JSON confirms the shipped `run_identity.py` matches the answer
key's rule text essentially verbatim — same key names, same order, same frozenset, same
canonicalisation, same two-sided refusal logic. The agent also wrote its own end-to-end smoke test
(lines 9548-9558) rather than trusting unit tests alone, directly asserting `run_identity.json` on
disk, `response.json.run_identity`, and a stable `run_hash` across reruns — belt-and-braces that
would have caught anything the design reading missed, though in this run it wasn't needed.
