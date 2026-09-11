# g3: 10 runs read (9 counted for findability; infra-only runs excluded: [3])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g3.r1.exclusions_or_crossover | 8/10 (80%) | {'never_shipped': 1, 'found_misread': 1} |
| g3.r1.failure_behavior | 9/10 (90%) | {'never_shipped': 1} |
| g3.r1.observability | 8/10 (80%) | {'never_shipped': 1, 'found_misread': 1} |
| g3.r1.rule | 9/10 (90%) | {'never_shipped': 1} |
| g3.r1.scope | 9/10 (90%) | {'never_shipped': 1} |
| g3.r2.exclusions_or_crossover | 9/10 (90%) | {'never_shipped': 1} |
| g3.r2.observability | 8/10 (80%) | {'never_shipped': 1, 'not_found': 1} |
| g3.r2.rule | 6/10 (60%) | {'never_shipped': 1, 'not_found': 3} |
| g3.r2.scope | 9/10 (90%) | {'never_shipped': 1} |

**lost fact-points by cause:** {'never_shipped': 9, 'not_found': 4, 'found_misread': 2}
**graded losses:** 15; reader-recorded losses: 15
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g3.r2.h1 | herring | chat | — | 9/9 (100%) | 0 | 1/9 (11%) | 1/9 (11%) |
| g3.r2.h2 | herring | chat | — | 9/9 (100%) | 0 | 1/9 (11%) | 1/9 (11%) |
| g3.r1.h1 | herring | chat | — | 9/9 (100%) | 0 | 1/9 (11%) | 1/9 (11%) |
| g3.r1.h2 | herring | chat | — | 8/9 (89%) | 1 | 0/9 (0%) | 0/9 (0%) |
| g3.r2.say23 | clue | chat | exclusions_or_crossover | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g3.r1.l16 | clue | chat | failure_behavior | 5/9 (56%) | 1 | 5/6 (83%) | 5/6 (83%) |
| g3.r1.l17 | clue | chat | failure_behavior,observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.s2b | clue | chat | rule | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g3.r1.rev2 | reversal | chat | rule,scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.s1b | clue | chat | rule | 7/9 (78%) | 0 | 6/7 (86%) | 7/7 (100%) |
| g3.r2.s2a | clue | chat | rule | 2/9 (22%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g3.r2.s3a | clue | chat | scope | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r2.rev2 | reversal | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.s2c | clue | chat | observability,rule | 7/9 (78%) | 0 | 6/7 (86%) | 7/7 (100%) |
| g3.r1.say23 | clue | chat | failure_behavior | 7/9 (78%) | 1 | 7/8 (88%) | 7/8 (88%) |
| g3.r2.s4c | clue | chat | exclusions_or_crossover | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g3.r2.s3c | clue | chat | scope | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g3.r1.l11 | clue | chat | scope | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g3.r1.l15 | clue | chat | observability,exclusions_or_crossover | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.say21 | clue | chat | scope | 8/9 (89%) | 0 | 7/8 (88%) | 8/8 (100%) |
| g3.r2.s1c | clue | chat | rule,observability | 6/9 (67%) | 1 | 5/7 (71%) | 6/7 (86%) |
| g3.r2.s1d | clue | chat | observability | 9/9 (100%) | 0 | 8/9 (89%) | 8/9 (89%) |
| g3.r2.rev1 | reversal | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r1.rev1 | reversal | chat | rule,failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.s3b | clue | chat | scope | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g3.r1.l14 | clue | chat | exclusions_or_crossover | 7/9 (78%) | 1 | 7/8 (88%) | 7/8 (88%) |
| g3.r2.s4a | clue | chat | exclusions_or_crossover | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.say19 | clue | chat | rule | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g3.r1.l7 | clue | chat | scope | 7/9 (78%) | 0 | 6/7 (86%) | 7/7 (100%) |
| g3.r1.l19 | clue | chat | failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.say22 | clue | chat | scope | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g3.r2.s2d | clue | chat | rule,scope | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g3.r1.l8 | clue | mail | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r1.l18 | clue | chat | failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r1.l13 | clue | chat | exclusions_or_crossover,observability | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r1.l6 | clue | chat | scope | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g3.r1.l5 | clue | wiki comment | rule,observability | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g3.r2.say20 | clue | chat | scope | 8/9 (89%) | 0 | 7/8 (88%) | 8/8 (100%) |
| g3.r1.l10 | clue | chat | rule,scope | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r2.s4b | clue | chat | exclusions_or_crossover | 6/9 (67%) | 1 | 6/7 (86%) | 6/7 (86%) |
| g3.r1.say24 | clue | chat | failure_behavior | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g3.r1.l1 | clue | chat | rule,observability | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g3.r1.l3 | clue | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r1.l4 | clue | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r1.l9 | clue | chat | rule | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g3.r1.l12 | clue | mail | exclusions_or_crossover | 6/9 (67%) | 0 | 5/6 (83%) | 5/6 (83%) |
| g3.r2.s4d | clue | mail | exclusions_or_crossover | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g3.r2.s1a | clue | wiki comment | rule | 5/9 (56%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g3.r1.l2 | clue | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 306/369 (83%) |
| kind=herring | 36/36 (100%) |
| kind=reversal | 36/36 (100%) |
| literal=no | 122/144 (85%) |
| literal=yes | 256/297 (86%) |
| surface=chat | 343/396 (87%) |
| surface=mail | 24/27 (89%) |
| surface=wiki comment | 11/18 (61%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g3.r1.h1 → g3.r1.rev1 | 9/9 (100%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g3.r1.h2 → g3.r1.rev2 | 8/9 (89%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g3.r2.h1 → g3.r2.rev1 | 9/9 (100%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g3.r2.h2 → g3.r2.rev2 | 9/9 (100%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |

## reader vs prepass agreement: 440/441 (100%); only-one-says-found: Counter({'reader': 1})

- run10 g3.r2.say19: found only by reader
