# Phase C handoff — five plants, two stages left

**Written 2026-09-04 22:35 UTC.** Everything stopped on one external cause: the
Claude subscription hit its **monthly spend limit**, which failed the `claude -p`
judge call on all five tasks within the same minute. The limit resets **01:00
UTC** (or raise it at claude.ai/settings/usage).

**Nothing is lost.** Each stage writes its ledger through `clues.finish()` before
the judge runs, so every task stopped at a recorded position with its work on
disk. Resuming re-enters the state machine where it left off.

---

## Where each task is

| | run | crashed at | sources | remarks | woven | unknit | fact_conflicts | local spend |
|---|---|---|---|---|---|---|---|---|
| **g7** agent-turn-ledger | `pilot` | `consistency` | mixed | 46 | 45 | 0 | 9 | $57.70 |
| **g8** attachment-payload | `fleet1` | `reknit` (done) | **slack** | 50 | 50 | 0 | 1 | $75.05 |
| **g9** example-encoding | `fleet1` | `consistency` | mixed | 53 | 53 | 0 | 10 | $66.39 |
| **g10** token-capacity-budget | `fleet1` | `consistency` | **slack** | 46 | 46 | 0 | 7 | $71.66 |
| **g11** training-step-ledger | `fleet1` | `reknit` (done) | **slack** | 47 | 47 | 0 | 1 | $75.52 |

**All five plants are complete and fully woven.** 242 remarks placed, every
exchange written, `unknit: 0` everywhere — no invented speakers, no monologues,
every claim surviving its carriage check. That was g1's worst defect class.

Three tasks are deliberately **slack-only** (g8, g10, g11) and two mixed
slack/notion/email (g7, g9), at the user's request.

---

## How to resume

The limit must have reset first — check with a one-line `claude -p 'say ok'`.

```bash
cd /home/nidhi_bespokelabs_ai/SWEWorld

setsid nohup python3 task_generator/fleet/orchestrate.py resume pilot \
  --through C --from consistency --stop-after horizon.blind+spec+clues \
  --budget-usd 900 > /tmp/g7-resume.log 2>&1 < /dev/null &

setsid nohup python3 task_generator/fleet/orchestrate.py resume fleet1 --force \
  --through C --from consistency --stop-after horizon.blind+spec+clues \
  --budget-usd 900 > /tmp/rest-resume.log 2>&1 < /dev/null &
```

`--force` is needed on `fleet1` only if another orchestrator for that run is
alive; check first with `ps -eo pid,cmd | grep orchestrate`. **Two drivers on
DISJOINT tasks of one run are safe** (`state.update` takes a flock); two drivers
on the same task are not.

Watch with `python3 task_generator/fleet/orchestrate.py status fleet1`.

### Why `--from consistency` for all five

g8 and g11 have not run `consistency` yet; g7, g9 and g10 have, but under a
**stale orchestrator** (see gotcha 1) and, for g7/g9/g10, under the
**source-blind** version of the check (see gotcha 2). Re-running it costs ~$1.50
a task and produces a conflict list you can actually trust.

---

## What is left

Per task: **`consistency` → `prove --runs 3` → `horizon --arms blind,spec,clues`**,
then the run stops (`--stop-after`). Roughly **$8–12 and 45 minutes each**,
running concurrently.

- **`consistency`** — a model call per graded fact. Asks whether any remark
  states a fact wrongly *and is the last word on it*. Non-zero exit is normal
  when it finds something; the judge decides.
- **`prove --runs 3`** — the real verdict. Builds an implementation from the
  ticket plus the planted remarks alone, three times, and scores it with the
  same suite the paid arm uses. **A fact that fails on ANY run fails.** Read
  `out/<slug>/clues/proof.md`: facts failing on the *same* runs are ONE defect in
  ONE remark, not several.
- **`horizon`** — free, seconds. Emits the three apex arms. Its `unsolvable()`
  gate refuses if the rendered clues digest never types a graded name.

Hosted push/validate/evaluate are **deliberately out of scope** for this run —
`--stop-after horizon.blind+spec+clues` halts before them. They remain available
by resuming without that flag.

---

## Gotchas that will bite you

1. **A long-running orchestrator caches the code it started with.** Python
   imports once. An orchestrator started before a `fleet/` or `tg/` edit will not
   see it — this is why g7 parked saying `rewrite_exchanges` "is not on this
   menu" when it had just been added. **After changing fleet or tg code, restart
   the orchestrator.** Stages already running are unaffected and complete fine.

2. **`fact_conflicts` counts from before 22:20 UTC are source-blind and
   overstated.** `fact_consistency` used to show the judge only remarks whose
   `covers` names the fact — and `normalise()` truncates `covers` to two entries.
   A remark that resolves the conflict from mail or the wiki was invisible. Fixed
   (it now shows every remark in the requirement, labelled with source), but
   g7's 9 and g10's 7 were measured before the fix.

3. **A fresh plant always exits non-zero.** `finish()` appends a `never run —
   cli.py consistency …` row to `fact_conflicts`, which is HARD. `gates.clue_gate`
   filters that into `detail["owed"]`; do not "fix" it.

4. **`unstated: absent` findings are frequently stale.** They come from
   `claims.json`, which `settle` writes *before* its own rewrites. The judge
   verifies against the live plant and overrides — correctly — but the gate
   raises a false hard finding at every plant stage. **Unfixed.** The clean fix is
   to treat `unstated` as soft when `settle` has run since `claims.json` was
   written, mirroring the `owed` logic in gotcha 3.

5. **The judge can state a wrong fact confidently.** One decision claimed "$0.87
   left" of budget when the task had spent $62.60 of $150. Its *reasoning* was
   sound. Check its numbers, not just its logic.

6. **Everything runs on the OAuth subscription**, never the API key.
   `tg/auth.py` removes `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN` from the child
   environment and sets `CLAUDE_FORCE_OAUTH=1`; `agent.run` aborts the run if the
   CLI ever reports using the key. Verify with
   `cat /proc/<claude pid>/environ | tr '\0' '\n' | grep -i anthropic`.

---

## Changes made this session — do not revert

### Shared `tg/` (each is a separate, reviewable fix)

| file | change | why |
|---|---|---|
| `tg/horizon.py` | preserve `.rollouts/` and `.validation/` across the re-emit `rmtree` | it deleted phase B's rollouts, the only evidence `verdict_ab` reads; cost three manual restores and one false BLOCKED verdict |
| `tg/horizon.py` | `ENV CURATOR_DISABLE_RICH_DISPLAY=1` in the DOCKERFILE template | curator's trackers start a live display on construction and wedge a non-TTY agent shell; 3 of 12 g7 blind rollouts died that way. CONFTEST and GRADER already set it — the agent never inherited it |
| `tg/clues.py` | `unclashed` added to `SOFT` | computed by `finish()` and read by nothing — the exact "a check with no reader is not a gate" disease |
| `tg/clues.py` + `tg/corpus.py` + `prompts/clue_place.md` | `Corpus.purposes` from `data/channels.yaml`, `channel_guide()`, `OFF_TOPIC_ROOMS = ("random","general")` | placement ranked rooms by token overlap and was never told what a room is FOR; remarks about tokenizers landed in `#cookbooks` under a `why` that said no room fitted |
| `tg/clues.py` | `rebalance()` takes the requested sources and renormalises | it walked the global 40/30/30 MIX regardless, so `--sources slack` was cosmetic — a plant asked for slack-only came out 21/8/8. **Cost $34 in discarded plants** |
| `tg/clues.py` + `prompts/clue_consistency.md` | `fact_consistency` shows every remark in the requirement, labelled by source | see gotcha 2. `repair` was fixed the same way for the same reason; `consistency` is newer and never got it |

### `fleet/` (all fleet-local)

Thirteen defects found in a pre-flight review, four fatal after money is spent —
`verdict_clues` unimplemented, a 2h timeout shorter than `clues` (which has **no
checkpoint**), caps below cost, and `repair` jumping *forward* past five stages.
Plus per-task `--sources`, `--stop-after`, per-phase rewind counters, and the
`plant`/`emit_clues` judge situations with the `rewrite_exchanges` action.

`rewrite_exchanges` is the repair for `fact_conflicts`: it runs
`reknit --only <ids named by the gate> --redo`, re-weaving just those exchanges
(~2 calls each). `replace` re-places with identical wording and does **not** fix
an exchange that says the wrong thing; `reclues` throws away sound placement.

---

## Verifying a finished plant

```bash
python3 task_generator/fleet/orchestrate.py verify        # free, every gate on every task
```

Per task, the evidence worth reading:

- `out/<slug>/clues/proof.md` — all facts green across all 3 builds
- `out/<slug>/clues/README.md` — the plant in date order, with source and carrier
- `gates.clue_gate(task)` — 0 hard
- source mix matches intent (slack-only for g8/g10/g11)
- zero invented speakers (`unknit: 0`)

The corpus is pinned: every clue stage runs with
`--run .../data_gen/build/phase4/runs/corpus`, so `ledger["corpus"]` records the
real run rather than the `latest` symlink. **Keep passing it** — `plan.py` injects
it automatically for stages in `plan.TAKES_RUN`.
