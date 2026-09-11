# g8: 10 runs read (10 counted for findability; infra-only runs excluded: [])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g8.r1.exclusions_or_crossover | 9/10 (90%) | {'found_misread': 1} |
| g8.r1.failure_behavior | 10/10 (100%) | {} |
| g8.r1.observability | 10/10 (100%) | {} |
| g8.r1.rule | 7/10 (70%) | {'implementation_slip': 3} |
| g8.r1.scope | 4/10 (40%) | {'not_found': 3, 'implementation_slip': 1, 'found_misread': 2} |
| g8.r2.exclusions_or_crossover | 10/10 (100%) | {} |
| g8.r2.failure_behavior | 7/10 (70%) | {'not_found': 2, 'found_misread': 1} |
| g8.r2.rule | 10/10 (100%) | {} |
| g8.r2.scope | 10/10 (100%) | {} |

**lost fact-points by cause:** {'implementation_slip': 4, 'not_found': 5, 'found_misread': 4}
**graded losses:** 13; reader-recorded losses: 13
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g8.r1.g8-pre-r1-single-ceiling-dario | herring | chat | — | 8/9 (89%) | 0 | 1/8 (12%) | 1/8 (12%) |
| g8.r1.g8-pre-r1-single-ceiling-konrad | herring | chat | — | 3/9 (33%) | 3 | 2/6 (33%) | 1/6 (17%) |
| g8.r2.detail-passthrough-1 | herring | chat | — | 6/9 (67%) | 1 | 1/7 (14%) | 1/7 (14%) |
| g8.r2.detail-passthrough-2 | herring | chat | — | 7/9 (78%) | 1 | 2/8 (25%) | 1/8 (12%) |
| g8.r1.s4-gideon | clue | chat | failure_behavior | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g8.r1.s3-konrad | clue | chat | exclusions_or_crossover | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g8.r1.s2-nils | clue | chat | scope | 7/11 (64%) | 2 | 4/9 (44%) | 4/9 (44%) |
| g8.r1.s2-gideon | clue | chat | scope | 5/10 (50%) | 0 | 4/5 (80%) | 4/5 (80%) |
| g8.r1.s3-nils | clue | chat | exclusions_or_crossover,scope | 8/10 (80%) | 0 | 7/8 (88%) | 6/8 (75%) |
| g8.r1.s2-dario | clue | chat | scope | 6/10 (60%) | 3 | 4/9 (44%) | 4/9 (44%) |
| g8.r1.s4-konrad | clue | chat | failure_behavior | 9/10 (90%) | 1 | 10/10 (100%) | 10/10 (100%) |
| g8.r1.s2-konrad | clue | chat | scope | 8/9 (89%) | 1 | 4/9 (44%) | 4/9 (44%) |
| g8.r1.s3-nikolai | clue | chat | exclusions_or_crossover | 1/10 (10%) | 1 | 1/2 (50%) | 2/2 (100%) |
| g8.r1.rev2 | reversal | chat | rule | 9/10 (90%) | 1 | 10/10 (100%) | 8/10 (80%) |
| g8.r1.s3-emil | clue | chat | exclusions_or_crossover | 6/10 (60%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g8.r1.s4-nikolai | clue | chat | failure_behavior | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g8.r2.l5 | clue | chat | scope | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g8.r1.s4-dario | clue | chat | failure_behavior | 9/10 (90%) | 1 | 10/10 (100%) | 10/10 (100%) |
| g8.r2.l7 | clue | chat | scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g8.r1.rev1 | reversal | chat | rule | 9/10 (90%) | 1 | 10/10 (100%) | 7/10 (70%) |
| g8.r2.l6 | clue | chat | scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g8.r2.l1 | clue | chat | rule | 5/10 (50%) | 0 | 4/5 (80%) | 5/5 (100%) |
| g8.r2.say22 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g8.r2.l9 | clue | chat | exclusions_or_crossover,rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g8.r2.l8 | clue | chat | scope | 8/10 (80%) | 1 | 9/9 (100%) | 9/9 (100%) |
| g8.r2.l10 | clue | chat | exclusions_or_crossover | 8/10 (80%) | 1 | 7/9 (78%) | 9/9 (100%) |
| g8.r2.l13 | clue | chat | failure_behavior | 6/10 (60%) | 1 | 5/7 (71%) | 6/7 (86%) |
| g8.r1.s1-gideon | clue | chat | rule | 2/11 (18%) | 0 | 2/2 (100%) | 1/2 (50%) |
| g8.r1.s1-dermot | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 8/10 (80%) |
| g8.r2.say23 | clue | chat | exclusions_or_crossover | 9/10 (90%) | 1 | 10/10 (100%) | 10/10 (100%) |
| g8.r2.rev1 | reversal | chat | failure_behavior | 9/11 (82%) | 2 | 9/11 (82%) | 8/11 (73%) |
| g8.r2.l15 | clue | chat | failure_behavior | 3/10 (30%) | 1 | 4/4 (100%) | 4/4 (100%) |
| g8.r2.say21 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g8.r1.s1-dario | clue | chat | rule | 11/11 (100%) | 0 | 10/11 (91%) | 10/11 (91%) |
| g8.r2.l2 | clue | chat | rule | 5/10 (50%) | 1 | 4/6 (67%) | 6/6 (100%) |
| g8.r2.l11 | clue | chat | exclusions_or_crossover | 2/10 (20%) | 1 | 2/3 (67%) | 3/3 (100%) |
| g8.r2.l14 | clue | chat | failure_behavior | 6/10 (60%) | 1 | 7/7 (100%) | 7/7 (100%) |
| g8.r2.l4 | clue | chat | rule | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g8.r2.l12 | clue | chat | exclusions_or_crossover,rule | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g8.r2.rev2 | reversal | chat | failure_behavior | 10/11 (91%) | 1 | 9/11 (82%) | 8/11 (73%) |
| g8.r1.s1-emil | clue | chat | rule | 9/10 (90%) | 1 | 10/10 (100%) | 10/10 (100%) |
| g8.r1.s5-gideon | clue | chat | observability | 5/11 (45%) | 0 | 4/5 (80%) | 4/5 (80%) |
| g8.r1.say25 | clue | chat | observability | 4/10 (40%) | 1 | 5/5 (100%) | 5/5 (100%) |
| g8.r2.l3 | clue | chat | rule | 9/10 (90%) | 1 | 10/10 (100%) | 10/10 (100%) |
| g8.r1.say24 | clue | chat | rule | 10/11 (91%) | 1 | 10/11 (91%) | 10/11 (91%) |
| g8.r1.s5-dermot | clue | chat | observability | 9/11 (82%) | 0 | 8/9 (89%) | 8/9 (89%) |
| g8.r2.fix24 | clue | chat | failure_behavior | 7/10 (70%) | 1 | 3/8 (38%) | 5/8 (62%) |
| g8.r2.l16 | clue | chat | failure_behavior | 5/10 (50%) | 1 | 6/6 (100%) | 6/6 (100%) |
| g8.r1.s5-emil | clue | chat | observability | 11/11 (100%) | 0 | 10/11 (91%) | 10/11 (91%) |
| g8.r1.say23 | clue | chat | rule | 9/11 (82%) | 2 | 9/11 (82%) | 10/11 (91%) |
| g8.r2.say20 | clue | chat | failure_behavior | 3/10 (30%) | 1 | 4/4 (100%) | 4/4 (100%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 332/434 (76%) |
| kind=herring | 29/36 (81%) |
| kind=reversal | 42/42 (100%) |
| literal=no | 63/107 (59%) |
| literal=yes | 340/405 (84%) |
| surface=chat | 403/512 (79%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g8.r1.g8-pre-r1-single-ceiling-dario → g8.r1.rev1 | 8/10 (80%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g8.r1.g8-pre-r1-single-ceiling-konrad → g8.r1.rev2 | 4/10 (40%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g8.r2.detail-passthrough-1 → g8.r2.rev1 | 7/10 (70%) | 9/10 (90%) | 0/10 (0%) | 0/10 (0%) |
| g8.r2.detail-passthrough-2 → g8.r2.rev2 | 8/10 (80%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |

## reader vs prepass agreement: 494/513 (96%); only-one-says-found: Counter({'reader': 10, 'prepass': 9})

- run1 g8.r1.s3-emil: found only by reader
- run1 g8.r2.detail-passthrough-1: found only by reader
- run1 g8.r1.s2-gideon: found only by prepass
- run1 g8.r1.s3-nils: found only by prepass
- run1 g8.r1.s2-dario: found only by prepass
- run1 g8.r2.l5: found only by prepass
- run1 g8.r1.s1-gideon: found only by prepass
- run1 g8.r2.l15: found only by prepass
- run1 g8.r2.l2: found only by prepass
- run2 g8.r1.g8-pre-r1-single-ceiling-konrad: found only by reader
- run2 g8.r2.detail-passthrough-2: found only by reader
- run2 g8.r1.g8-pre-r1-single-ceiling-dario: found only by reader
- run2 g8.r1.s1-gideon: found only by prepass
- run2 g8.r2.l12: found only by reader
- run4 g8.r1.s2-konrad(petar): found only by reader
- run4 g8.r2.l8: found only by prepass
- run5 g8.r2.detail-passthrough-2: found only by reader
- run6 g8.r2.detail-passthrough-1: found only by reader
- run7 g8.r2.detail-passthrough-1: found only by reader
