# g4 run 1 (31a202dc, eval 0ebb2b86) — reward 0.875

## What this run found

This is a near-perfect recovery: 7 of 8 declared facts scored 1. The agent's search was
methodical and unusually thorough — it dumped every source whole (Gitea issues+comments,
all ~114 deduplicated wiki pages with comments, the full IMAP mailbox, every Mattermost
channel) into flat local files, then ran a small number of high-yield broad regexes
(`identity|stamp|run_hash|fingerprint` alone surfaced roughly a third of all found
remarks in one pass) followed by narrow `sed` reads around each hit. Of the 40 clues + 4
reversals in the answer key, 30 were genuinely surfaced this way (transcript lines 2650,
2761, 2805, 2850, 2864, 2953, 3008, 3059, 3257, 3360, 3427, 3469, 3760, 3912, 4013,
4019, 4108, 4161, 4210 (seen, not registered — see below), 4211, 4269, 4325, 4375, 4557,
4619, 4839 among them). It correctly treated the wiki hits (page 9's row-level cache
keying design, page 36's hashing-regression postmortem) as neighbouring questions rather
than the ticket's newest word, per the ticket's own guidance, and correctly declined to
implement a mail-sourced parked decision (stale-shard sweep, mail msg 94) that was out of
scope for this specific ticket — a real judgment call visible in its own pre-commit
checklist at line 10093.

## What it missed, and why

Fourteen clues plus one herring/reversal pair genuinely never surfaced in any dump or
grep the agent ran (confirmed by grepping the transcript directly for each remark's
distinctive phrases — not just trusting the pointer sheet's mechanical count). In every
one of these cases the same fact was independently carried by a sibling remark that *was*
found, so the absences cost nothing: `r1.rule`, `r1.exclusions_or_crossover`,
`r1.observability`, `r2.rule`, `r2.scope`, `r2.failure_behavior`, and `r2.observability`
all still scored 1 on redundant coverage. A cluster of r2-scope remarks about
`CURATOR_RUN_ID=$GITHUB_RUN_ID`, `runId` spelling, and "same label twice" being simply
absent together (rather than one grep query missing them all) reads more like
corpus-version drift for this world build than a search failure.

## The one lost fact: `g4.r1.scope`

The grader's final `test_scope` assertion checks that `LLM.backend_params` hands out a
**fresh copy on every read** — it takes the returned dict, mutates it, reads the property
again, and requires the second read to be unaffected. The agent's shipped property
(written at transcript line 7024) is:

```python
self._backend_params = dict(backend_params) if backend_params else {}   # __init__, copies once
...
@property
def backend_params(self):
    return self._backend_params   # same object every call — no copy on read
```

This satisfies half of the answer key's scope statement ("a copy of what `__init__` was
handed, `{}` for `None`") but not the other half: repeated access must not let a caller's
mutation leak back into what the LLM is using. The one remark that states this precisely —
`g4.r1.l-params-copy` ("the processor trims backend_params in place mid-run, so we hold
what came into `__init__` off to one side... a `dict()` of what came into `__init__`...
copied before anything downstream trims it") — never appears anywhere in the agent's
dumps; a direct grep for its distinctive phrases ("trims", "off to one side", "copied
before") returns zero hits against the full transcript.

The agent did scroll past a related clue, `g4.r1.fix27` (line 4210: "popped batch_size off
what `llm.backend_params` handed me... mutating what you got back doesnt reach the llm at
all"), inside a large `#code-review` dump while it was actually hunting for the
twelve-component list. Its own Analysis at that step (line 4249) registers only the
adjacent "12 components, sorted" thread and never quotes or reasons about fix27
specifically — so this near-miss clue, which states the same mutation-safety principle in
the reverse direction, never made it into the implementation. Cause: `not_found` for the
one remark that would have made the requirement explicit, compounded by a `noted`-not-
`registered` near-miss on a sibling clue that hinted at it.

## Herrings

Two of the four herring/reversal pairs surfaced cleanly and the agent correctly followed
the reversal in both cases: `g4.r1.backend-params-whole-dict-dario` (line 3360, "the way
i'm scoping it its the whole dict...") reversed by `g4.r1.rev1` (line 2761,
`IDENTITY_BACKEND_PARAM_KEYS`, four named keys); and `g4.r2.h1-uuid4-nocache` (line 4019,
"the nocache path doesnt hash at all... mints a uuid4") reversed by `g4.r2.rev1` (line
4013, "keyword only, `run_id: Optional[str] = None`"), the two sitting in the same
exchange the agent read in one pass. The other herring, `g4.r2.h2-isoformat-segment`,
never surfaced on its own but its content reached the agent secondhand through its
reversal (`g4.r2.rev2`, line 4325, which recaps "we swapped the uuid4... for a
`datetime.now().isoformat()` segment... its gone"). The fourth herring
(`g4.r1.backend-params-whole-dict-konrad`) and its dedicated reversal (`g4.r1.rev2`) were
both entirely absent, but had zero effect since the parallel dario/rev1 pair carried the
same correction. No shipped code follows any herring.

## Provenance

Merged to `main` (commit `b5ed91c`), CI green on that commit, service healthy post-deploy
— confirmed in the run's own final turns (lines 10968-11039). All provenance facts are 1.
