# g9 run 2 (f7cf25ff-a8ea-41ed-a3b4-10901df1e7ce) eval 3b0b259f — reward 0.8571
transcript: /home/nidhi_bespokelabs_ai/SWEWorld/tasks/rollout_analysis/rollouts/g9/v8/lumen_run2_f7cf25ff_transcript.md  (147 agent steps)

## graded facts

- g9.open_feature: 1
- g9.r1.rule: 1
- g9.r1.scope: 1
- g9.r1.exclusions_or_crossover: 1
- g9.r1.failure_behavior: 0
- g9.r2.rule: 1
- g9.r2.scope: 1
- g9.r2.failure_behavior: 1
- g9.hidden_mean: 0.8571
- g9.suite_ok: 1
- provenance.pushed: 1
- provenance.ci_green: 1
- provenance.deployed: 1
- reward: 0.8571

## failing tests (full ctrf trace)

### test_r1::test_failure_behavior__a_windowed_example_with_under_sixteen_prompt_tokens_is_refused
```
over-long refusal: num_messages: None != 2
```

## where each answer-key remark's exact text surfaces (pointer only — verify by reading)

| remark | kind | surface | carries | first step | first line | lines hit | cmd that surfaced it |
|---|---|---|---|---|---|---|---|
| g9.r1.h1 | herring | chat · #code-review |  | 76 | 4464 | 2 (2 tool) | `` |
| g9.r2.g9-tuple-return-1 | herring | chat · #releases |  | 57 | 3549 | 2 (2 tool) | `` |
| g9.r1.h2 | herring | chat · #code-review |  | 64 | 3881 | 4 (4 tool) | `` |
| g9.r2.g9-tuple-return-2 | herring | chat · #code-review |  | — | — | 0 | |
| g9.r2.l18 | clue | chat · #code-review | failure_behavior | — | — | 0 | |
| g9.r1.l-rule-3 | clue | chat · #engineering | rule | — | — | 0 | |
| g9.r1.say20 | clue | chat · #code-review | failure_behavior | — | — | 0 | |
| g9.r1.l-fail-4 | clue | chat · #pipeline | failure_behavior | — | — | 0 | |
| g9.r1.say26 | clue | chat · #code-review | exclusions_or_crossover | 67 | 4015 | 6 (6 tool) | `` |
| g9.r1.l-fail-2 | clue | chat · #releases | failure_behavior | 59 | 3652 | 2 (2 tool) | `` |
| g9.r2.rev1 | reversal of g9.r2.g9-tuple-return-1 | chat · #releases | rule | 57 | 3542 | 4 (4 tool) | `` |
| g9.r1.l-fail-3 | clue | chat · #pipeline | failure_behavior | — | — | 0 | |
| g9.r1.l-fw-4 | clue | chat · #engineering | exclusions_or_crossover | — | — | 0 | |
| g9.r1.l-fw-1 | clue | chat · #cookbooks | exclusions_or_crossover | 59 | 3657 | 7 (7 tool) | `` |
| g9.r2.l7 | clue | chat · #pipeline | scope | 58 | 3583 | 1 (1 tool) | `` |
| g9.r2.rev2 | reversal of g9.r2.g9-tuple-return-2 | chat · #cookbooks | rule | 57 | 3539 | 9 (9 tool) | `` |
| g9.r1.l-fail-1 | clue | chat · #cookbooks | failure_behavior | — | — | 0 | |
| g9.r2.l16 | clue | chat · #pipeline | failure_behavior | — | — | 0 | |
| g9.r2.l11 | clue | wiki comment · docs/meetings/weekly-notes-week-of-mar-31.md | rule | — | — | 0 | |
| g9.r1.say22 | clue | chat · #cookbooks | failure_behavior | — | — | 0 | |
| g9.r2.l12 | clue | chat · #cookbooks | rule | 76 | 4470 | 6 (6 tool) | `grep -rni "supervised_tokens\|windowed\|window_start" /tmp/chat/*.txt | head -40 | cut -c1` |
| g9.r2.l19 | clue | mail · Re: Weekly update: week of Apr 7 | failure_behavior | 32 | 2272 | 24 (24 tool) | `` |
| g9.r1.rev2 | reversal of g9.r1.h2 | chat · #engineering | failure_behavior | 59 | 3650 | 9 (9 tool) | `` |
| g9.r2.l13 | clue | mail · Dataset card numbers before we publish the reasoning set | rule | — | — | 0 | |
| g9.r2.l4 | clue | chat · #engineering | rule | 57 | 3535 | 7 (7 tool) | `` |
| g9.r2.l3 | clue | chat · #engineering | rule | 57 | 3532 | 5 (5 tool) | `` |
| g9.r1.say25 | clue | mail · user question: does a local run without the tokenizer extra  | scope | — | — | 0 | |
| g9.r1.rev1 | reversal of g9.r1.h1 | chat · #engineering | failure_behavior | 59 | 3642 | 15 (15 tool) | `` |
| g9.r1.l-scope-2 | clue | chat · #code-review | scope | — | — | 0 | |
| g9.r2.l9 | clue | chat · #viewer | rule | 59 | 3639 | 1 (1 tool) | `` |
| g9.r1.l-scope-1 | clue | mail · PR 653: formatter still takes tokenizer=None | scope | 45 | 2924 | 26 (26 tool) | `` |
| g9.r1.say23 | clue | mail · PR 653 before the next cut | scope | 48 | 3074 | 7 (7 tool) | `` |
| g9.r1.l-rule-2 | clue | mail · PR 653 — ran a curated set through the encode path | rule | 48 | 3081 | 23 (23 tool) | `` |
| g9.r2.l1 | clue | mail · PR 653 — where does role validation live, and what do the co | rule | 30 | 2166 | 5 (5 tool) | `` |
| g9.r2.l6 | clue | mail · stats report branch — need someone to run it before the 0.1. | rule | 38 | 2574 | 6 (6 tool) | `/opt/curator-dev/venv/bin/python /tmp/mailget.py 138 > /tmp/m138.txt 2>&1; fold -s -w 175 ` |
| g9.r1.l-scope-4 | clue | mail · sft export — fast tokenizer and manual fallback return diffe | scope | 51 | 3248 | 20 (20 tool) | `` |
| g9.r2.l10 | clue | chat · #pipeline | rule | 59 | 3637 | 7 (6 tool) | `` |
| g9.r2.l15 | clue | mail · PR 653 — what goes in the stats dict when the backend doesnt | rule | 54 | 3379 | 12 (12 tool) | `` |
| g9.r2.l8 | clue | wiki comment · docs/engineering/end-of-run-summary-tables-how-the-formatter | scope | — | — | 0 | |
| g9.r2.l14 | clue | wiki comment · docs/engineering/finetuning-export-what-the-end-of-run-summa | rule | — | — | 0 | |
| g9.r2.say23 | clue | mail · PR 653: which layer drops a bad row, and who counts it | scope | 39 | 2620 | 16 (16 tool) | `` |
| g9.r2.h-role-row | herring | mail · Re: PR 653: which layer drops a bad row, and who counts it |  | 39 | 2622 | 1 (1 tool) | `` |
| g9.r1.l-fw-2 | clue | wiki comment · docs/engineering/viewer-dataset-download-export-format-notes | exclusions_or_crossover | — | — | 0 | |
| g9.r1.l-rule-1 | clue | wiki comment · docs/engineering/overnight-finetune-off-the-curated-export-j | rule | — | — | 0 | |
| g9.r1.fix28 | clue | chat · #engineering | scope | — | — | 0 | |
| g9.r2.say24 | clue | wiki comment · docs/engineering/what-format-batch-counts-as-a-drop-and-what | failure_behavior | — | — | 0 | |
| g9.r1.say21 | clue | wiki comment · docs/engineering/what-the-finetuning-encoder-emits-per-datum | failure_behavior | 13 | 1338 | 4 (4 tool) | `` |
| g9.r1.say27 | clue | wiki comment · docs/engineering/trimming-over-length-rows-for-finetuning-pr | rule | 25 | 1921 | 4 (4 tool) | `` |
| g9.r1.l-fw-3 | clue | mail · Re: Week of Jun 9 recap: bulk inference fix | exclusions_or_crossover | 41 | 2723 | 16 (16 tool) | `` |
| g9.r2.l17 | clue | wiki comment · docs/engineering/request-builder-what-we-drop-and-what-we-ra | failure_behavior | 87 | 5033 | 8 (8 tool) | `` |
| g9.r2.rev3 | reversal of g9.r2.h-role-row | wiki comment · docs/engineering/request-builder-what-we-drop-and-what-we-ra | failure_behavior | 87 | 5046 | 2 (2 tool) | `` |
| g9.r1.l-scope-3 | clue | wiki comment · docs/engineering/chat-formatting-and-assistant-span-masking- | scope | 22 | 1764 | 6 (6 tool) | `` |
| g9.r1.l-rule-4 | clue | wiki comment · docs/engineering/chat-formatting-and-assistant-span-masking- | rule | 22 | 1780 | 7 (7 tool) | `` |
| g9.r2.l2 | clue | wiki comment · docs/engineering/per-example-stats-from-the-windowed-export- | rule | 84 | 4874 | 8 (8 tool) | `` |
| g9.r2.l5 | clue | wiki comment · docs/meetings/weekly-sync-notes-week-of-jun-23-batch-mode.md | rule | — | — | 0 | |
| g9.r1.say24 | clue | wiki comment · docs/engineering/local-offline-inference-what-the-encode-ste | scope | 28 | 2072 | 7 (7 tool) | `` |
| g9.r2.fix25 | clue | chat · #pipeline | rule | 59 | 3635 | 7 (7 tool) | `` |
