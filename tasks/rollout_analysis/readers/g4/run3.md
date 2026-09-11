# g4 run 3 (76b379d3) eval 0ebb2b86 — reward 0.875

## What this run found

The agent ran a thorough, if somewhat undirected, reconnaissance: it read `llm.py`, `db.py` and
`curator_response.py` in full (transcript lines 254-1587), then spent roughly 30 steps dumping
Gitea issues/comments and all 228 BookStack wiki pages with comments to disk before establishing
(correctly, per the answer key) that neither carries this task's requirements. It then dumped the
full ~10k-line Mattermost history of every channel to `/tmp/chat.txt` and worked it with keyword
greps ("identity", "run_hash", "disable_cache", "run_id", "backend_params", "RunIdentityError",
…), pulling hit clusters into `tight.txt`/`hits.txt` and reading `sed -n` windows around them
(steps 31-59). This is a keyword-density strategy, not an exhaustive per-channel read, and it
shows in what it recovered: 30 of 48 remarks, essentially every remark phrased with a technical
token the agent's grep list covered (`IDENTITY_COMPONENT_KEYS`, `RunIdentityError`,
`backend_params`, `uuid4`, …). The 18 it missed are disproportionately the colloquial turns of an
exchange ("so basically ya, same thing bit me", "quick one before i forget") that carry the same
information in plain English rather than jargon.

All four herrings were correctly not believed. In every case the herring and its reversal landed
inside the same keyword-hit window the agent read in one pass (lines 2649-2662 for the two
`uuid4`/nocache herrings, 3772-3777 for the isoformat and whole-dict-konrad pair), so there was
little opportunity to act on the stale decision before seeing it overturned. The shipped
implementation follows every reversal: `IDENTITY_BACKEND_PARAM_KEYS` is the four-key frozenset,
`compute_run_identity` takes a caller-supplied `run_id` rather than minting a `uuid4` internally,
and the nocache run hash carries no `datetime.isoformat()` segment.

## What it missed, and why

Seven of the eight declared facts passed. The single lost fact, `g4.r1.scope`, fails on one
assertion: `configured.backend_params == given` after the caller mutates the dict the property
handed back — i.e. `LLM.backend_params` must return a **fresh copy on every read**, not the live
object the LLM holds internally. The shipped property (transcript line 6915-6917) is:

```python
@property
def backend_params(self) -> dict:
    """The backend params this LLM was constructed with."""
    return self._backend_params
```

— a direct reference, so mutating the returned dict corrupts the LLM's own state. This exact
scenario is stated almost verbatim by `g4.r1.fix27` (#code-review, 2025-03-14): "popped
`batch_size` off what `llm.backend_params` handed me, read it again and `batch_size` was still
there — so mutating what you got back doesn't reach the LLM." That remark **is** in the
transcript, at line 4715, inside a wide date-range dump the agent pulled while chasing an
unrelated lead (the component-count test). It is never cited again — the agent's only explicit
synthesis of `backend_params` scope, at line 6786 ("`backend_params` returns the dict given at
construction, empty dict if None"), talks about the `None`-vs-`{}` default and says nothing about
copy-on-read, effectively restating a weaker rule than the one it had already scrolled past. The
remark's twin, `g4.r1.l-params-copy` (#code-review, 2025-04-23 — "we hold what came into
`__init__` off to one side… what llm hands back is built off ours, never the processor's"), never
surfaced in any grep at all; a direct search of the full transcript confirms it is absent. Those
two remarks are the *only* carriers of this half of `r1.scope`; with one read-but-unprocessed and
the other never found, nothing pushed the agent toward a copy-per-access implementation, and it
defaulted to the more natural (and wrong) direct-reference property.

Everything else scope-adjacent — the resolved-vs-declared `backend` property, the `None -> {}`
default — was recovered correctly from `g4.r1.l-backend-default`, `g4.r1.say24` and other remarks
the agent did read, which is why the rest of `test_scope` passes and only the last assertion
fails.

## Why the other 17 "not found" remarks didn't cost anything

Every other missed remark (`l-schema-dump`, `l-keys-onelist`, `l-params-none`, `l-schema-order`,
`say22`, `l-window-reuse`, `r2.l1/l2/l3/l9/l13/l14`, `l-backend-resolved`, `l-genparams-empty`,
`l-genparams-fix`, `l-system-prompt`) had at least one sibling remark carrying the same fact that
the agent did find and act on — the plant deliberately over-covers most subconclusions with 2-4
remarks, and the agent's keyword sweep was dense enough to catch at least one per subconclusion
except the backend_params-copy one.

## End state

The run completed cleanly: both requirements implemented, `tests/unittests/test_run_identity.py`
added, pushed, PR #737 merged at commit `925b834`, CI green including the deploy step, service
verified healthy (line 8775). Reward 0.875 = 7/8 facts, entirely attributable to the one missed
scope assertion above — not an infra, provenance, or herring-following failure.
