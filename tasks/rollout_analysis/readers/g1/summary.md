# g1: 10 runs read (10 counted for findability; infra-only runs excluded: [])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g1.r1.exclusions_or_crossover | 9/10 (90%) | {'found_misread': 1} |
| g1.r1.failure_behavior | 9/10 (90%) | {'not_found': 1} |
| g1.r1.observability | 5/10 (50%) | {'found_misread': 3, 'not_found': 1, 'implementation_slip': 1} |
| g1.r1.rule | 3/10 (30%) | {'not_found': 4, 'found_misread': 2, 'implementation_slip': 1} |
| g1.r1.scope | 3/10 (30%) | {'not_found': 4, 'found_misread': 2, 'implementation_slip': 1} |
| g1.r2.exclusions_or_crossover | 10/10 (100%) | {} |
| g1.r2.failure_behavior | 10/10 (100%) | {} |
| g1.r2.observability | 10/10 (100%) | {} |
| g1.r2.rule | 10/10 (100%) | {} |
| g1.r2.scope | 10/10 (100%) | {} |

**lost fact-points by cause:** {'not_found': 10, 'found_misread': 8, 'implementation_slip': 3}
**graded losses:** 21; reader-recorded losses: 21
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g1.r2.h2 | herring | chat | — | 6/10 (60%) | 1 | 1/7 (14%) | 1/7 (14%) |
| g1.r1.h1 | herring | chat | — | 8/10 (80%) | 0 | 0/8 (0%) | 0/8 (0%) |
| g1.r2.h1 | herring | chat | — | 8/10 (80%) | 0 | 1/8 (12%) | 1/8 (12%) |
| g1.r1.h2 | herring | chat | — | 7/10 (70%) | 0 | 0/7 (0%) | 0/7 (0%) |
| g1.r2.l8 | clue | chat | exclusions_or_crossover,observability | 8/10 (80%) | 0 | 5/8 (62%) | 7/8 (88%) |
| g1.r2.l11 | clue | chat | exclusions_or_crossover | 7/10 (70%) | 0 | 6/7 (86%) | 7/7 (100%) |
| g1.r2.l7 | clue | chat | scope | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g1.r2.l14 | clue | chat | observability,failure_behavior | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g1.r2.l4 | clue | chat | rule,observability | 2/10 (20%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g1.r1.f1 | clue | chat | failure_behavior | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g1.r1.say30 | clue | chat | scope | 5/10 (50%) | 0 | 4/5 (80%) | 4/5 (80%) |
| g1.r1.say28 | clue | chat | failure_behavior | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g1.r2.l15 | clue | chat | observability | 8/10 (80%) | 0 | 7/8 (88%) | 7/8 (88%) |
| g1.r1.say23 | clue | chat | rule | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g1.r1.say24 | clue | chat | observability | 6/10 (60%) | 0 | 5/6 (83%) | 6/6 (100%) |
| g1.r2.rev2 | reversal | chat | rule,failure_behavior | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g1.r1.say22 | clue | chat | rule | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g1.r1.say25 | clue | chat | scope | 3/10 (30%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g1.r1.say29 | clue | chat | observability | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g1.r1.l13 | clue | chat | scope,observability | 10/10 (100%) | 0 | 9/10 (90%) | 8/10 (80%) |
| g1.r2.rev1 | reversal | chat | rule,failure_behavior | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g1.r2.l2 | clue | chat | rule | 3/10 (30%) | 0 | 2/3 (67%) | 3/3 (100%) |
| g1.r1.l15 | clue | chat | scope | 3/10 (30%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g1.r1.l3 | clue | chat | rule,observability | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g1.r1.l5 | clue | chat | rule | 3/10 (30%) | 0 | 2/3 (67%) | 3/3 (100%) |
| g1.r1.l6 | clue | chat | rule,observability | 10/10 (100%) | 0 | 7/10 (70%) | 6/10 (60%) |
| g1.r2.l13 | clue | chat | failure_behavior | 2/10 (20%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g1.r1.rev2 | reversal | chat | exclusions_or_crossover,rule | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g1.r1.l2 | clue | wiki comment | rule | 6/10 (60%) | 1 | 6/7 (86%) | 6/7 (86%) |
| g1.r2.l1 | clue | chat | rule | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g1.r1.f2 | clue | chat | failure_behavior | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g1.r2.l10 | clue | chat | exclusions_or_crossover | 2/10 (20%) | 1 | 2/3 (67%) | 2/3 (67%) |
| g1.r1.l10 | clue | mail | rule | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g1.r2.l3 | clue | chat | rule | 7/10 (70%) | 0 | 6/7 (86%) | 7/7 (100%) |
| g1.r1.l14 | clue | mail | scope | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g1.r2.l12 | clue | chat | failure_behavior | 7/10 (70%) | 0 | 6/7 (86%) | 7/7 (100%) |
| g1.r2.l6 | clue | mail | scope | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g1.r1.l8 | clue | chat | rule | 8/10 (80%) | 0 | 7/8 (88%) | 7/8 (88%) |
| g1.r2.l5 | clue | chat | scope | 3/10 (30%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g1.r1.l11 | clue | chat | rule,observability | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g1.r1.l16 | clue | chat | scope,observability | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g1.r1.rev1 | reversal | chat | rule,scope,exclusions_or_crossover | 9/10 (90%) | 1 | 9/10 (90%) | 9/10 (90%) |
| g1.r1.l1 | clue | chat | rule,observability | 9/10 (90%) | 0 | 8/9 (89%) | 8/9 (89%) |
| g1.r2.l9 | clue | wiki comment | exclusions_or_crossover | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g1.r1.l7 | clue | chat | rule,observability | 10/10 (100%) | 0 | 7/10 (70%) | 8/10 (80%) |
| g1.r1.l4 | clue | chat | exclusions_or_crossover | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g1.r1.l9 | clue | chat | rule | 6/10 (60%) | 0 | 4/6 (67%) | 6/6 (100%) |
| g1.r1.f4 | clue | chat | failure_behavior | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g1.r1.l12 | clue | mail | rule,observability | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g1.r1.f3 | clue | chat | failure_behavior | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 283/419 (68%) |
| kind=herring | 30/40 (75%) |
| kind=reversal | 37/40 (92%) |
| literal=no | 71/110 (65%) |
| literal=yes | 279/389 (72%) |
| surface=chat | 305/440 (69%) |
| surface=mail | 31/39 (79%) |
| surface=wiki comment | 14/20 (70%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g1.r1.h1 → g1.r1.rev1 | 8/10 (80%) | 9/10 (90%) | 0/10 (0%) | 0/10 (0%) |
| g1.r1.h2 → g1.r1.rev2 | 7/10 (70%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g1.r2.h1 → g1.r2.rev1 | 8/10 (80%) | 7/10 (70%) | 0/10 (0%) | 0/10 (0%) |
| g1.r2.h2 → g1.r2.rev2 | 6/10 (60%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |

## reader vs prepass agreement: 490/499 (98%); only-one-says-found: Counter({'prepass': 5, 'reader': 4})

- run2 g1.r2.l11: found only by reader
- run2 g1.r2.l7: found only by prepass
- run2 g1.r2.l2: found only by prepass
- run2 g1.r2.l13: found only by prepass
- run2 g1.r2.l10: found only by prepass
- run3 g1.r1.h2: found only by reader
- run5 g1.r1.l2: found only by prepass
- run6 g1.r2.h2: found only by reader
- run6 g1.r2.l10: found only by reader
