# g4 run 7 (rollout 22c149ca, eval 0ebb2b86) — reward 1/1

## What this run found

This is a clean sweep: all 8 graded facts (g4.r1.rule/scope/exclusions_or_crossover/observability,
g4.r2.rule/scope/failure_behavior/observability) scored 1. The agent's search strategy explains why:
after a broad dump of the whole `chat.txt` export (~11k lines, 12 channels) and the wiki, it ran
three successive keyword-grep passes (`run identity|run_identity|identity_version|...`, then
`components|digest|xxh64|...`, then `system_prompt|return_completions_object|...`) and — critically
— followed almost every hit with a full `sed -n '<range>p'` dump of the surrounding 30-90 lines
rather than trusting the single matched line. That habit is why 33 of the 48 planted remarks were
read in genuine multi-turn context (e.g. the full `g4.r2.h1-uuid4-nocache` herring exchange at
transcript line 2503-2512, or the full `g4.r1.rev1` reversal at line 3443-3462), not just skimmed.

The agent's own closing self-summary (line 9043) is unusually explicit about provenance, separating
"the record beyond the ticket" from the ticket itself and naming `IDENTITY_COMPONENT_KEYS`,
`IDENTITY_BACKEND_PARAM_KEYS`, the `response_format` serialization, the `v3-nocache-` hash scheme,
and both `RunIdentityError` refusals — direct evidence the hidden requirements were reconstructed
deliberately, not stumbled into.

## What it missed, and why it didn't matter

11 of 48 remarks were never surfaced at all (`l-keys-onelist`, `l-retries-fork`, `say22`, `r2.l1`,
`r2.l2`, `r2.l3`, `l-genparams-fix`, `r2.l9`, `r2.l11`, `l-backend-resolved`, and — a genuine
pointer-sheet false positive — `l-schema-order`, whose flagged hit at line 3877 turns out to be
`l-keys-count` text resurfacing under a different grep query, confirmed by direct search that the
real remark's text never appears anywhere in the transcript). Every one of these losses was
survivable because the plant's `spread()` design put at least 2 sources and 3+ weeks between
carriers of the same fact: e.g. missing `l-backend-resolved`'s #cookbooks exchange didn't cost the
`scope` fact because `l-backend-default` (read in full, line 5419-5425) independently establishes
"naming the default backend can't change identity," and the ticket itself already specifies the
`LLM.backend` property.

Four remarks were only **partially** seen: `l-window-reuse` and `fix25` were cut short by the exact
`sed`/`grep -c1-200` bounds the agent chose (losing the explicit "needs to fork" punchline and the
KeyError detail respectively, though the surrounding substance came through); `l-params-none` only
surfaced its opening question, never the `{"batch_size":64,...}` payload or the "should be `{}`"
conclusion; and the `g4.r2.h2-isoformat-segment` herring was never read directly — only encountered
secondhand inside its own reversal's recap ("we swapped the uuid4... for a datetime.now().isoformat()
segment... its gone," line 2817-2818).

## What it believed, and why

Both herring pairs were handled correctly. For `g4.r1` (whole-`backend_params` hashing), the agent
saw only 2-3 of the herring's 7-9 turns via grep fragments but read both reversals (`rev1`, `rev2`)
in full multi-turn context, and its own analysis states the supersession explicitly: "Those earlier
Jan decisions (whole backend_params dict) were explicitly superseded in March/April by
IDENTITY_BACKEND_PARAM_KEYS. My implementation follows the later decision." (line 8512). For `g4.r2`
(uuid4/isoformat in the nocache path), the herring and its reversal (`r2.h1-uuid4-nocache` /
`r2.rev1`) were both read in full 8-turn context at the very first substantive chat dump the agent
requested (line 2503-2512 and 2333-2341), so there was never real ambiguity. No shipped code follows
either herring.

## Why nothing was lost

Because reward is 1/1, there are no lost facts to diagnose. `passed_facts` traces each of the 8
facts to the remarks the agent's own Analysis lines cite by name or paraphrase — most facts had 3-4
independent carriers, which is the real reason a run this thorough came away with a perfect score
despite missing nearly a quarter of the plant outright.
