# g9: 10 runs read (10 counted for findability; infra-only runs excluded: [])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g9.r1.exclusions_or_crossover | 10/10 (100%) | {} |
| g9.r1.failure_behavior | 7/10 (70%) | {'implementation_slip': 1, 'not_found': 2} |
| g9.r1.rule | 9/10 (90%) | {'implementation_slip': 1} |
| g9.r1.scope | 10/10 (100%) | {} |
| g9.r2.failure_behavior | 4/10 (40%) | {'herring_followed': 6} |
| g9.r2.rule | 9/10 (90%) | {'implementation_slip': 1} |
| g9.r2.scope | 10/10 (100%) | {} |

**lost fact-points by cause:** {'implementation_slip': 3, 'herring_followed': 6, 'not_found': 2}
**graded losses:** 11; reader-recorded losses: 11
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g9.r1.h1 | herring | chat | — | 10/10 (100%) | 0 | 3/10 (30%) | 1/10 (10%) |
| g9.r2.g9-tuple-return-1 | herring | chat | — | 9/9 (100%) | 0 | 3/9 (33%) | 1/9 (11%) |
| g9.r1.h2 | herring | chat | — | 10/10 (100%) | 0 | 3/10 (30%) | 1/10 (10%) |
| g9.r2.g9-tuple-return-2 | herring | chat | — | 7/9 (78%) | 0 | 3/7 (43%) | 1/7 (14%) |
| g9.r2.l18 | clue | chat | failure_behavior | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g9.r1.l-rule-3 | clue | chat | rule | 0/10 (0%) | 0 | — | — |
| g9.r1.say20 | clue | chat | failure_behavior | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g9.r1.l-fail-4 | clue | chat | failure_behavior | 0/10 (0%) | 0 | — | — |
| g9.r1.say26 | clue | chat | exclusions_or_crossover | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g9.r1.l-fail-2 | clue | chat | failure_behavior | 9/10 (90%) | 1 | 9/10 (90%) | 8/10 (80%) |
| g9.r2.rev1 | reversal | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r1.l-fail-3 | clue | chat | failure_behavior | 8/10 (80%) | 0 | 8/8 (100%) | 7/8 (88%) |
| g9.r1.l-fw-4 | clue | chat | exclusions_or_crossover | 1/10 (10%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g9.r1.l-fw-1 | clue | chat | exclusions_or_crossover | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r2.l7 | clue | chat | scope | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r2.rev2 | reversal | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r1.l-fail-1 | clue | chat | failure_behavior | 2/10 (20%) | 0 | 1/2 (50%) | 1/2 (50%) |
| g9.r2.l16 | clue | chat | failure_behavior | 1/10 (10%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g9.r2.l11 | clue | wiki comment | rule | 0/10 (0%) | 0 | — | — |
| g9.r1.say22 | clue | chat | failure_behavior | 7/10 (70%) | 0 | 6/7 (86%) | 6/7 (86%) |
| g9.r2.l12 | clue | chat | rule | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g9.r2.l19 | clue | mail | failure_behavior | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g9.r1.rev2 | reversal | chat | failure_behavior | 10/10 (100%) | 0 | 10/10 (100%) | 8/10 (80%) |
| g9.r2.l13 | clue | mail | rule | 3/10 (30%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g9.r2.l4 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r2.l3 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r1.say25 | clue | mail | scope | 6/10 (60%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g9.r1.rev1 | reversal | chat | failure_behavior | 10/10 (100%) | 0 | 10/10 (100%) | 8/10 (80%) |
| g9.r1.l-scope-2 | clue | chat | scope | 0/10 (0%) | 0 | — | — |
| g9.r2.l9 | clue | chat | rule | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g9.r1.l-scope-1 | clue | mail | scope | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g9.r1.say23 | clue | mail | scope | 5/10 (50%) | 0 | 4/5 (80%) | 5/5 (100%) |
| g9.r1.l-rule-2 | clue | mail | rule | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g9.r2.l1 | clue | mail | rule | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g9.r2.l6 | clue | mail | rule | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g9.r1.l-scope-4 | clue | mail | scope | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g9.r2.l10 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r2.l15 | clue | mail | rule | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g9.r2.l8 | clue | wiki comment | scope | 1/10 (10%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g9.r2.l14 | clue | wiki comment | rule | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g9.r2.say23 | clue | mail | scope | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g9.r2.h-role-row | herring | mail | — | 10/10 (100%) | 0 | 7/10 (70%) | 6/10 (60%) |
| g9.r1.l-fw-2 | clue | wiki comment | exclusions_or_crossover | 3/10 (30%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g9.r1.l-rule-1 | clue | wiki comment | rule | 9/10 (90%) | 1 | 9/10 (90%) | 9/10 (90%) |
| g9.r1.fix28 | clue | chat | scope | 1/10 (10%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g9.r2.say24 | clue | wiki comment | failure_behavior | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g9.r1.say21 | clue | wiki comment | failure_behavior | 10/10 (100%) | 0 | 8/10 (80%) | 7/10 (70%) |
| g9.r1.say27 | clue | wiki comment | rule | 10/10 (100%) | 0 | 8/10 (80%) | 10/10 (100%) |
| g9.r1.l-fw-3 | clue | mail | exclusions_or_crossover | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r2.l17 | clue | wiki comment | failure_behavior | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g9.r2.rev3 | reversal | wiki comment | failure_behavior | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g9.r1.l-scope-3 | clue | wiki comment | scope | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g9.r1.l-rule-4 | clue | wiki comment | rule | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g9.r2.l2 | clue | wiki comment | rule | 9/10 (90%) | 0 | 8/9 (89%) | 8/9 (89%) |
| g9.r2.l5 | clue | wiki comment | rule | 0/10 (0%) | 0 | — | — |
| g9.r1.say24 | clue | wiki comment | scope | 6/10 (60%) | 1 | 7/7 (100%) | 7/7 (100%) |
| g9.r2.fix25 | clue | chat | rule | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 300/469 (64%) |
| kind=herring | 46/48 (96%) |
| kind=reversal | 44/50 (88%) |
| literal=no | 87/158 (55%) |
| literal=yes | 303/409 (74%) |
| surface=chat | 202/287 (70%) |
| surface=mail | 98/130 (75%) |
| surface=wiki comment | 90/150 (60%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g9.r1.h1 → g9.r1.rev1 | 10/10 (100%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g9.r1.h2 → g9.r1.rev2 | 10/10 (100%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g9.r2.g9-tuple-return-1 → g9.r2.rev1 | 10/10 (100%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g9.r2.g9-tuple-return-2 → g9.r2.rev2 | 8/10 (80%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g9.r2.h-role-row → g9.r2.rev3 | 10/10 (100%) | 4/10 (40%) | 6/10 (60%) | 6/10 (60%) |

## reader vs prepass agreement: 565/567 (100%); only-one-says-found: Counter({'reader': 2})

- run2 g9.r1.l-rule-1: found only by reader
- run6 g9.r1.say24: found only by reader
