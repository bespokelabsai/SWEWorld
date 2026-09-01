# Todo — make the generator repeatable, and put g1's clues in the world

Plan: ~/.claude/plans/buzzing-shimmying-pelican.md

## Half 2 — the clues into the world

- [x] Back up `clues/` as `clues.pre-inject`
- [x] `prompts/clue_reknit.md` + `clues.reknit()` (in clues.py, beside the other passes) — the holder's turn IS the proven
      sentence; only the turns around it are regenerated
- [x] Guard in code: `anchor()` splices when the rewrite paraphrased (6 of 35 needed it) that does not contain `clue["text"]` verbatim
- [x] `tg/inject.py` — 7 carrier kinds -> ingest-shaped writes into a COPY of the run
- [x] GATE: all 50 remarks + identifiers read back — 0 blocking + verbatim identifiers out of the
      written corpus
- [x] Read back the 8 threads appended to days that already had traffic
- [~] install done (9,791 messages, 5 comments); bake TAG=0.4.2 running
- [ ] `batch-payload-plan-world/` arm, cloned from blind, FROM sweworld:0.4.2
- [x] Teach `build_tasks.py::emit()` the `world` variant (`--world`)
- [ ] Confirm chat + wiki search surface the new remarks in the booted image
- [ ] Measure n=3 against clues 1.00 / blind 0.00

## Half 1 — the pipeline

- [x] `prove --runs 3`, per-fact grid across runs
- [ ] Prove the sampling change on `clues.v4-hosted-0.70` BEFORE building on it
- [x] `finish()` runs `unreversed`, `out_of_order`, `unknit`, `unstated`
- [x] `coverage()` -> `gaps_claimed`; `uncarried()` added and MEASURED USELESS; `unstated()` is the one that fires
- [x] `tg/recipe.py` + `cli.py make [--dry-run|--from|--optional]`
- [ ] `cli.py snap`
- [x] README as the recipe

## Small fixes while there

- [x] `_loop/run.sh` counts every job dir
- [x] CLAUDE.md corrected

## Round two — the corpus reads as people

- [x] `prompts/clue_thread.md` — the exchange exists BECAUSE they were working it out
- [x] Guard inverted: a turn holding the whole remark is now a finding
- [x] `check_carriage` — claim by claim, shown the remark and the thread, `carried`
      computed in code
- [x] `chat_insert` becomes a seeded exchange, not one dropped message
- [x] Page comments become a comment and its replies
- [x] `inject.absent` is claim-level; the answer key renders the exchange
- [x] Recipe + README: `reknit` is the step that makes a plant into a corpus
- [ ] Rewrite all 48 chat/mail exchanges (running, ~96 calls)
- [ ] Run the 2 page comments
- [ ] Re-inject, re-bake 0.4.3, regenerate the answer key
- [ ] Re-measure world n=3 against the 0.50 baseline

## Measured

| arm | n | result |
|---|---|---|
| blind | 1 | 0.00 |
| spec | 2 | 1.00 |
| clues (quoted in the ticket) | 4 | 1.00 |
| world (in the corpus), round one | 3 | 0.80 / 0.10 / 0.60 = **0.50** |

`g1.r1.rule` and `g1.r1.scope` failed 3/3 deterministically on the `PLAN_FILE_NAME`
naming issue, not on retrieval. All five `g1.r2` facts move together, so that is one
engagement variable rather than five failures.

## Review

_(filled in as work lands)_
