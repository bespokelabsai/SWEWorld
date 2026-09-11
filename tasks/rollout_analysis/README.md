# Rollout analysis tooling

What produced `tasks/g1-g11-lumen-rollout-analysis.md`: every lumen rollout of a task's
world-hosted eval, read against that task's answer key, remark by remark. The unit of
work is (transcript × answer-key remark), and **the readers decide; the scripts only count**.

## Stages

| step | command | writes |
|---|---|---|
| 1. choose | edit `targets.json`: task id, version, eval id(s), arm, slug | — |
| 2. pull | `~/horizon_env/bin/python pull.py [g7 g9]` | `rollouts/<g>/`, `full/<g>/`, `manifest.json` |
| 3. pre-pass | `python3 prepass.py [g7 g9]` | `prepass/<g>.json` and a pointer sheet per run in `prepass/<g>/` |
| 4. read | one Sonnet subagent per rollout, prompt = `reader_instructions.md` + that run's paths | `readers/<g>/run<N>.json` + `.md` |
| 5. check | read each reader's claims about the ticket, "only carrier", and cause against the key, plant, ticket and grader; log in `readers/corrections.md`; encode overrules in `aggregate.py` `OVERRIDES` / `NEVER_SHIPPED` | — |
| 6. aggregate | `python3 aggregate.py <g>` | `readers/<g>/summary.md` |
| 7. pool | `python3 synth.py` | `synth.md` |

- **Pull.** `pull.py` fetches the full rollout record because `horizon rollouts pull`
  truncates the grader trace at 2048 bytes.
- **Pre-pass.** It only *aims* the reading: it lists where each remark's exact rendered text
  first surfaces. It has false positives (it matched repo source once), and a remark that
  was re-wrapped on screen can be missed.
- **Read.** Each reader's prompt is a short header — task id, version, eval, run, rollout,
  the declared facts, and absolute paths to the transcript, pointer sheet, full record,
  answer key, grader, oracle and plant — followed by "Read and follow exactly:
  `reader_instructions.md`". Write the outputs with unique names when one version pools
  several evals (g8 used `run<N>_<eval>.json`). Run at most 20 readers at once; that is the
  session cap.
- **Check.** Never edit a reader's JSON to change a verdict; override it in `aggregate.py`
  with a comment naming the evidence.

## Things that bit

- **Opus readers are refused.** The API safeguard `[reasoning_extraction]` refused 8 of 10
  Opus 5 readers, on both tries. Sonnet readers worked.
- **`extracted_score` ≠ reward.** Horizon's `extracted_score` is the mean of *all* subscores.
  Report `reward`, the mean of the hidden facts, which the pre-pass takes from the grade.
- **A version folder can hold several evals.** g11 v7 had a 10/10-errored eval next to the
  target one, so filter by rollout id and not by folder.
- **Readers can nest their data differently.** One reader put its clue rows under `clues`;
  `readers/g6/run9.json` was merged back, and the original is kept as `.orig`.
- **Readers share the scratch directory.** Their temporary helper files collide, so tell
  them to use unique names. Their outputs are per-run and safe.
- **Answer key newer than the served world.** The repo's key can be newer than the world a
  run was served (g7 v4, g6 v6). Readers judge against the transcript, and the difference
  goes in `notable`.

## Swap done 2026-09-11: g7 → v5 eval 8deffce4, g9 → v8 eval 3b0b259f (old verdicts in `readers/_superseded/`)

Later the same day g3 went the same way: v9 eval 035777f5, the rerun on the corpus and
grader fix. Its v7 verdicts, pre-pass and pulled records are in `_superseded/g3_v7_evalce846459`
under `readers/`, `prepass/`, `full/` and `rollouts/`. `synth.py` also gained a corpus-spread
section (chat only / mostly chat / spread), which the report's top section reads from.

g11 followed: v11 eval a8572080, the rerun on the G11-H fix (konrad's `rev2` now retracts both
halves of his herring). Its v7 (eval 94bf8242) material is in `_superseded/g11_v7_eval94bf8242`,
and the three run-1 overrides that belonged to that eval were removed from `aggregate.py`.

The checklist that was followed, kept for the next rerun:

Nidhi is rerunning **g7** and running **10 new g9 rollouts**. When they are done:

1. Put the new eval ids and versions in `targets.json` for `g7` and `g9`.
2. **Move the old `readers/g7/` and `readers/g9/` aside.** The old results are to be dropped
   from the report, not merged.
3. Re-run steps 2–7 for `g7 g9` only.
4. Replace the g7 and g9 sections of the report, move g9 into the pooled rates (take it out
   of `synth.py`'s `THIN` set), and refresh the summary, ranking, register and pooled
   numbers.
5. If the g7 rerun is on the pushed G7-A fix, say whether its 8 lost points came back.

## Shareable page

`python3 build_page.py <out.html>` re-renders the report as the published page (charts read the
report's own tables). Published 2026-09-11 at
https://claude.ai/code/artifact/470d7a2e-e848-4b5f-a481-890cf3e8848c — republish to that URL
(pass it as `url` from a new session) so the link stays the same.
