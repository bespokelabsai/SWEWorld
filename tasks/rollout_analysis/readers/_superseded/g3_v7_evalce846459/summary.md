# g3: 10 runs read (10 counted for findability; infra-only runs excluded: [])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g3.r1.exclusions_or_crossover | 9/10 (90%) | {'not_found': 1} |
| g3.r1.failure_behavior | 10/10 (100%) | {} |
| g3.r1.observability | 9/10 (90%) | {'not_found': 1} |
| g3.r1.rule | 10/10 (100%) | {} |
| g3.r1.scope | 10/10 (100%) | {} |
| g3.r2.exclusions_or_crossover | 9/10 (90%) | {'grader_overspecifies': 1} |
| g3.r2.observability | 10/10 (100%) | {} |
| g3.r2.rule | 6/10 (60%) | {'not_found': 4} |
| g3.r2.scope | 10/10 (100%) | {} |

**lost fact-points by cause:** {'not_found': 6, 'grader_overspecifies': 1}
**graded losses:** 7; reader-recorded losses: 7
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g3.r2.h1 | herring | chat | — | 7/8 (88%) | 1 | 1/8 (12%) | 1/8 (12%) |
| g3.r2.h2 | herring | chat | — | 6/8 (75%) | 2 | 1/8 (12%) | 1/8 (12%) |
| g3.r1.h1 | herring | chat | — | 8/8 (100%) | 0 | 1/8 (12%) | 1/8 (12%) |
| g3.r1.h2 | herring | chat | — | 8/8 (100%) | 0 | 1/8 (12%) | 1/8 (12%) |
| g3.r2.say23 | clue | chat | exclusions_or_crossover | 1/10 (10%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g3.r1.l16 | clue | chat | failure_behavior | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g3.r1.l17 | clue | chat | failure_behavior,observability | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r2.s2b | clue | chat | rule | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g3.r1.rev2 | reversal | chat | rule,scope | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.s1b | clue | chat | rule | 3/10 (30%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g3.r2.s2a | clue | chat | rule | 1/10 (10%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g3.r2.s3a | clue | chat | scope | 2/10 (20%) | 1 | 2/3 (67%) | 3/3 (100%) |
| g3.r2.rev2 | reversal | chat | rule | 9/10 (90%) | 1 | 9/10 (90%) | 10/10 (100%) |
| g3.r2.s2c | clue | chat | observability,rule | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r1.say23 | clue | chat | failure_behavior | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g3.r2.s4c | clue | chat | exclusions_or_crossover | 1/10 (10%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g3.r2.s3c | clue | chat | scope | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r1.l11 | clue | chat | scope | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g3.r1.l15 | clue | chat | observability,exclusions_or_crossover | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r2.say21 | clue | chat | scope | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.s1c | clue | chat | rule,observability | 6/10 (60%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g3.r2.s1d | clue | chat | observability | 9/10 (90%) | 0 | 9/9 (100%) | 8/9 (89%) |
| g3.r2.rev1 | reversal | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r1.rev1 | reversal | chat | rule,failure_behavior | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.s3b | clue | chat | scope | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r1.l14 | clue | chat | exclusions_or_crossover | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r2.s4a | clue | chat | exclusions_or_crossover | 9/10 (90%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g3.r2.say19 | clue | chat | rule | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r1.l7 | clue | chat | scope | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g3.r1.l19 | clue | chat | failure_behavior | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r2.say22 | clue | chat | scope | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r2.s2d | clue | chat | rule,scope | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g3.r1.l8 | clue | mail | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r1.l18 | clue | chat | failure_behavior | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r1.l13 | clue | chat | exclusions_or_crossover,observability | 9/10 (90%) | 1 | 9/10 (90%) | 9/10 (90%) |
| g3.r1.l6 | clue | chat | scope | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r1.l5 | clue | wiki comment | rule,observability | 8/10 (80%) | 1 | 8/9 (89%) | 9/9 (100%) |
| g3.r2.say20 | clue | chat | scope | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r1.l10 | clue | chat | rule,scope | 9/10 (90%) | 0 | 8/9 (89%) | 8/9 (89%) |
| g3.r2.s4b | clue | chat | exclusions_or_crossover | 6/10 (60%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g3.r1.say24 | clue | chat | failure_behavior | 10/10 (100%) | 0 | 9/10 (90%) | 10/10 (100%) |
| g3.r1.l1 | clue | chat | rule,observability | 3/10 (30%) | 1 | 4/4 (100%) | 2/4 (50%) |
| g3.r1.l3 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r1.l4 | clue | chat | rule | 9/10 (90%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g3.r1.l9 | clue | chat | rule | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r1.l12 | clue | mail | exclusions_or_crossover | 8/10 (80%) | 0 | 7/8 (88%) | 7/8 (88%) |
| g3.r2.s4d | clue | mail | exclusions_or_crossover | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g3.r2.s1a | clue | wiki comment | rule | 8/10 (80%) | 1 | 8/9 (89%) | 9/9 (100%) |
| g3.r1.l2 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 306/410 (75%) |
| kind=herring | 32/32 (100%) |
| kind=reversal | 38/40 (95%) |
| literal=no | 106/152 (70%) |
| literal=yes | 270/330 (82%) |
| surface=chat | 330/432 (76%) |
| surface=mail | 28/30 (93%) |
| surface=wiki comment | 18/20 (90%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g3.r1.h1 → g3.r1.rev1 | 10/10 (100%) | 9/10 (90%) | 0/10 (0%) | 0/10 (0%) |
| g3.r1.h2 → g3.r1.rev2 | 10/10 (100%) | 9/10 (90%) | 0/10 (0%) | 0/10 (0%) |
| g3.r2.h1 → g3.r2.rev1 | 9/10 (90%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g3.r2.h2 → g3.r2.rev2 | 8/10 (80%) | 9/10 (90%) | 0/10 (0%) | 0/10 (0%) |

## reader vs prepass agreement: 483/484 (100%); only-one-says-found: Counter({'reader': 1})

- run2 g3.r2.s3b: found only by reader
