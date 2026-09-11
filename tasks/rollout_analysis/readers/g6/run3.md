# g6 run 3 (1adecb6c, eval 30b9f0dd) — reward 0

## Why it scored zero

Every failing test bottoms out in the same import error: `bespokelabs.curator.cost` on the
graded checkout exports only `COST_PROCESSOR, RATE_LIMIT_HEADER, cost_processor_factory,
defaultdict, external_model_cost, litellm` — the untouched baseline surface. `provenance.pushed:
0` confirms it. This is **not** a research or reasoning failure: it is a harness/environment
failure. From roughly step 130 onward (transcript line ~7396) the sandbox repeatedly reverted
both the local checkout and the Gitea remote back to the original commit `295ab6c` ("ci: run the
test suite on every push", first seen as the real starting HEAD at line 323) — *after* the agent
had built, committed, pushed and watched CI go green on its own account. This "push → green CI →
silent rollback" cycle recurs at least seven times (lines 7897, 8155, 8205, 8978, 9135, 9612,
9774, 9825, 9978, 10028 each record a fresh "Rolled back again to 295ab6c"), consuming the last
third of the run. The agent invented an ad hoc "nonce-verified" timestamp scheme to fight what it
correctly diagnosed as stale/replayed terminal frames, but the terminal kept lying to it anyway —
its very last verification (line 10037-10090) returns garbage (`/tmp/pD.py N`, `NOLOG8`)
immediately before its final Analysis (line 10188) confidently declares "remote main = 2a45213 ...
CI run ... status=success" and marks `task_complete: true`. Nothing it built ever reached the
grader.

## What it found

The research phase (roughly steps 1-92, transcript lines 1-5050) was genuinely thorough: a
background script paged through every Mattermost channel's `/channels/{id}/posts` into per-channel
dump files (line 3477), a second script dumped all ~200 BookStack pages *including comments* to
`/tmp/wikiall/` (line 4417) — explicitly because the agent reasoned BookStack search does not
index comments, matching the answer key's own stated trap — and a third indexed every mail message
via IMAP (lines 2089-2193). Grepping these dumps with an iteratively-expanded keyword list
(`batch_multiplier`, `x2`, `cancel`, `resolve_model_price`, `source ==`, `supports_batch_discount`)
recovered 21 of 33 remarks, both herrings, and both reversals, and from them the agent correctly
reconstructed nearly the whole MuSR tree for both requirements: provider-before-model-before-window
failure ordering (`g6.r1.l4`, line 3387; `g6.r1.l5`, line 1539), a null litellm input price counting
as `unknown_model` (`g6.r1.l7`, line 2339; `g6.r1.l8`, line 1414), no silent fallback to the `"*"`
window tier (`g6.r1.l10`, found as a paraphrase on a wiki comment rather than its native
`#code-review` carrier, line 1546), `batch_multiplier()` as the sole owner of the discount
(`g6.r2.g6r2-s1-l2/l4`, `g6.r2.g6r2-s3-l3`, lines 3805/5035/2339), the external-table exemption for
klusterai/inference.net (`g6.r2.g6r2-s2-l1/l2/l4`, lines 3947/2418/2773), and the user-supplied-price
exemption (`g6.r2.g6r2-s3-l2`, line 1240). It also correctly sided with both reversals over both
herrings: at line 3834 it states plainly "the x2 overrides removed... factor lives in
batch_multiplier() now," having seen the herring only as fragments inside the same grep that
surfaced the reversal.

## What it missed, and why

The 12 unrecovered remarks (`g6.r2.g6r2-s1-l1`, `g6.r1.l6`, `g6.r1.l11`, `g6.r2.g6r2-s3-l1`,
`g6.r1.l1`, `g6.r2.fix18`, `g6.r2.g6r2-s2-l3`, `g6.r1.l14`, `g6.r2.g6r2-s1-l3`, `g6.r1.l12`,
`g6.r1.l9`) were not missed because a channel or page went unvisited — every one sat in a dump the
agent already had locally — but because its keyword strategy tracked API identifiers rather than
the narrative phrasing those particular remarks use ("nonetype", "24h row", "quarter of the
invoice", "misspelled the provider", "negotiated input cost"). This cost nothing substantively:
every fact those remarks carry was independently secured through another remark that was found.

## The real damage

By step ~90 the terminal begins replaying stale screens (line 4616), and by step ~130 the
environment starts actively reverting pushed work. The agent's final self-description of what it
shipped — `ModelPrice`/`UnpricedModelError` with a three-string closed `REASONS` vocabulary,
provider-first validation, no wildcard-tier fallback, `resolve_model_price` that never returns a
`None` price, `supports_batch_discount` as a class flag defaulting off, `batch_multiplier()` as the
single owner of the factor, the `x2` overrides deleted, external tables returned as-listed even in
batch mode — tracks the answer key's rule/scope/exclusions/observability facts for both `g6.r1` and
`g6.r2` almost exactly. It simply never landed. Every one of the seven declared facts is lost to
`cause: infra`, not to a wrong requirement, a followed herring, or a corpus contradiction.
