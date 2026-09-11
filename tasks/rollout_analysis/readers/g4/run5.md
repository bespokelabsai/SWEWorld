# g4 run 5 (rollout 3794f374, eval 0ebb2b86) — reward 1

## What this run found

This is a clean sweep: all 8 graded facts (`g4.r1.{rule,scope,exclusions_or_crossover,observability}`,
`g4.r2.{rule,scope,failure_behavior,observability}`) scored 1, the test suite passed, and PR #737
merged to `main` (commit `3a83f74`) with CI green and the deploy requested. The agent never had the
ticket's hidden requirements handed to it (world arm) and had to reconstruct both `g4.r1` (twelve
alphabetical identity components, only four backend params fork the cache) and `g4.r2` (a cache-off
run is identified by a caller-supplied `run_id`, never internal randomness) from Mattermost chat alone.
Wiki and mail were dumped and grepped but carried nothing task-specific — this task genuinely has no
wiki/mail carriers, matching the answer key's own framing.

The agent's search strategy was blunt but effective: dump every channel (~10k messages, 12 channels)
to local text files, then iterate `grep <keyword> chat/` → read a wide (20-60 line) window around each
hit rather than trusting the single matched line. That habit of reading *wide* windows is what saved
it: of the 48 planted remarks, only 33 ever appear as literal corpus text in the visible transcript
(verified by grepping the full 10732-line transcript for each remark's distinctive phrasing) — the
other 15 (31%) were never surfaced in this run. Every fact nonetheless has 2-6 redundant carrying
remarks by design (`clues.spread()`), and the agent's wide-window reads happened to sweep up at least
one carrier per fact every time — often the single densest one. `g4.r1.l-backend-default` alone
("naming the default cant change identity") supplies almost the entirety of `g4.r1.scope`, and
`g4.r1.rev1` alone supplies almost the entirety of `g4.r1.exclusions_or_crossover`; both were found.

## Herrings — correctly resolved every time

All four herrings were handled correctly (`believed: reversal` in all four cases; the implementation
never followed a herring). The most interesting case is `g4.r2.h2-isoformat-segment` /
`g4.r2.rev2`: the agent read the *reversal* (cookbooks.txt:605, step 38 — "we swapped the uuid4 ...
for a datetime.now().isoformat() segment ... its gone") **before** it ever read the original herring
text (cookbooks.txt:274-278, step 54), so it never had a window in which it believed the wrong design.
For `g4.r1.backend-params-whole-dict-dario` / `g4.r1.rev1` the same thing happened in the other order
but with the same result — rev1 (step 34) was read before the herring (step 84). The one genuinely
interesting moment is at line 2535: the agent had tentatively concluded the nocache path mints its own
`uuid4()`, then hit a message saying otherwise dated later, and paused explicitly ("Critical nocache
design ... But a Mar 31 message says uuid4. Need to read that context.") rather than committing to the
stale belief — exactly the intended MuSR mechanic working as designed.

## What it missed, and why it didn't matter

The 15 not-found remarks split cleanly by fact, and in every case at least one sibling remark for the
same fact *was* found:

- `g4.r1.scope` missing `l-params-none`, `l-backend-resolved`, `l-params-copy` — covered by `fix27`,
  `l-backend-default`, `say24`.
- `g4.r1.exclusions_or_crossover` missing `l-retries-fork`, `l-window-reuse` — covered by `rev1`,
  `rev2`, `l-key-on-disk`, `l-param-keys`.
- `g4.r1.rule` missing `l-completions-object`, `l-genparams-empty`, `l-genparams-fix` — covered by
  six other rule remarks, plus the ticket's own text for `generation_params` phrasing almost word for
  word matches `l-genparams-fix`.
- `g4.r2.rule` missing `l1`, `l2`, `l3` — covered by `rev1`, `l6`, `l4`.
- `g4.r2.observability` missing `l14` — covered by `l13`, `l15`.
- `g4.r2.failure_behavior` missing `l9`, `l11` — covered by `say19`, `l10`, `l12`.

None of these misses are attributable to a bad search query in an identifiable sense — they read as
ordinary coverage gaps from grepping ~10 keywords across 12 channels rather than reading every channel
end to end. No near-miss here looks like a truncated fetch or a crashed script; the earlier real
failures (a write-then-read truncation bug and a literal-`\n` bug, both around step ~15-20) were
self-inflicted and self-corrected before the substantive search began, and cost turns rather than
information.

## Why the losses didn't cost facts

Every one of the 8 facts had a "does most of the work by itself" remark that the agent happened to
read: `l-keys-order` (names the exact 12 keys, alphabetical, with a live nit fixing an ordering bug —
this alone determines `g4.r1.rule`'s shape), `l-backend-default` (`g4.r1.scope`), `rev1`
(`g4.r1.exclusions_or_crossover`, also carries `observability`), `rev1` for `g4.r2.rule`, `l12`
(`g4.r2.scope` and `failure_behavior` together — this is the remark whose closing line is echoed
almost verbatim in the shipped `llm.py` comment "Refuse first, create afterwards"), and `l13`/`l15`
for `g4.r2.observability`. Because the plant's redundancy concentrates enough information in a small
number of remarks per fact, a search that finds "most but not all" of the corpus still recovers every
fact when it happens to land on the dense ones, as it did here.

## Implementation fidelity

The shipped code is not just passing-by-luck: `IDENTITY_COMPONENT_KEYS` is the exact 12-tuple in
alphabetical order; `IDENTITY_BACKEND_PARAM_KEYS` is the exact 4-member frozenset/tuple; the
`_identity_backend_params` helper's docstring explicitly explains the "missing key raises `KeyError`,
not `None`" behaviour required by `fix25`; `run_identity.py`'s imports are `json, os, dataclasses,
pathlib, typing, xxhash, logger` — no `random`/`secrets`/`uuid`, matching the AST-scan requirement the
agent had directly read (incidents.txt:204-211: "no uuid, no os.urandom either ... llm.py. thats the
only import of it left"). `LLM.__call__` mints `os.environ.get("CURATOR_RUN_ID") or uuid.uuid4().hex`
and passes it down, with the identity check running (and refusing) before the run directory is
created. After committing, the agent re-read its own diff, noticed `run_id` on `__call__` was not
keyword-only, explicitly cited the remark that required it, and patched the commit before pushing —
direct evidence the corpus was driving specific code decisions rather than the ticket or prior
knowledge of curator's real API alone.
