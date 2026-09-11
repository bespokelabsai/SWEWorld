# g10: 10 runs read (9 counted for findability; infra-only runs excluded: [8])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g10.r1.exclusions_or_crossover | 7/10 (70%) | {'not_found': 1, 'never_shipped': 1, 'implementation_slip': 1} |
| g10.r1.observability | 9/10 (90%) | {'never_shipped': 1} |
| g10.r1.rule | 9/10 (90%) | {'never_shipped': 1} |
| g10.r1.scope | 9/10 (90%) | {'never_shipped': 1} |
| g10.r2.exclusions_or_crossover | 8/10 (80%) | {'never_shipped': 1, 'not_found': 1} |
| g10.r2.observability | 9/10 (90%) | {'never_shipped': 1} |
| g10.r2.rule | 8/10 (80%) | {'never_shipped': 1, 'not_found': 1} |
| g10.r2.scope | 8/10 (80%) | {'never_shipped': 1, 'not_found': 1} |

**lost fact-points by cause:** {'not_found': 4, 'never_shipped': 8, 'implementation_slip': 1}
**graded losses:** 13; reader-recorded losses: 13
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g10.r1.clamp-at-zero-decision | herring | chat | — | 7/9 (78%) | 1 | 0/8 (0%) | 0/8 (0%) |
| g10.r2.h1 | herring | chat | — | 5/9 (56%) | 1 | 0/6 (0%) | 0/6 (0%) |
| g10.r1.clamp-at-zero-rationale | herring | chat | — | 8/9 (89%) | 0 | 0/8 (0%) | 0/8 (0%) |
| g10.r2.h2 | herring | chat | — | 8/9 (89%) | 0 | 1/8 (12%) | 0/8 (0%) |
| g10.r1.g10.r1.s3.l2 | clue | chat | observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g10.r1.g10.r1.s2.l4 | clue | chat | scope | 6/9 (67%) | 0 | 5/6 (83%) | 6/6 (100%) |
| g10.r1.g10.r1.s1.l3 | clue | chat | rule | 5/9 (56%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g10.r1.g10.r1.s3.l3 | clue | chat | observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g10.r2.s1_l3 | clue | chat | rule | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g10.r1.g10.r1.s4.l2 | clue | chat | exclusions_or_crossover | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g10.r1.g10.r1.s2.l1 | clue | chat | scope | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g10.r1.g10.r1.s4.l1 | clue | chat | exclusions_or_crossover,observability | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g10.r2.s1_l4 | clue | chat | rule | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g10.r2.s3_l4 | clue | chat | scope | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g10.r1.g10.r1.s1.l4 | clue | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g10.r1.g10.r1.s4.l3 | clue | chat | exclusions_or_crossover | 8/9 (89%) | 1 | 8/9 (89%) | 7/9 (78%) |
| g10.r2.s2_l3 | clue | chat | rule | 2/9 (22%) | 1 | 2/3 (67%) | 2/3 (67%) |
| g10.r2.s2_l2 | clue | chat | rule | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g10.r1.g10.r1.s4.l4 | clue | chat | exclusions_or_crossover | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g10.r2.s2_l4 | clue | chat | rule | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g10.r1.g10.r1.s2.l2 | clue | chat | scope | 2/9 (22%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g10.r2.s4_l1 | clue | chat | exclusions_or_crossover,rule | 5/9 (56%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g10.r1.g10.r1.s2.l3 | clue | chat | scope | 0/9 (0%) | 0 | — | — |
| g10.r2.s3_l1 | clue | chat | scope | 5/9 (56%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g10.r2.rev2 | reversal | chat | rule,exclusions_or_crossover | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g10.r2.s4_l2 | clue | chat | exclusions_or_crossover | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g10.r2.s3_l3 | clue | chat | scope,rule | 9/9 (100%) | 0 | 9/9 (100%) | 8/9 (89%) |
| g10.r2.s3_l2 | clue | chat | scope | 5/9 (56%) | 2 | 5/7 (71%) | 5/7 (71%) |
| g10.r1.g10.r1.s1.l1 | clue | chat | rule | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g10.r1.rev1 | reversal | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g10.r1.g10.r1.s3.l1 | clue | chat | observability | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g10.r2.rev1 | reversal | chat | rule,scope | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g10.r2.s2_l1 | clue | chat | rule | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g10.r2.s5_l2 | clue | chat | observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g10.r2.say23 | clue | chat | rule | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g10.r2.say25 | clue | chat | observability | 8/9 (89%) | 0 | 7/8 (88%) | 7/8 (88%) |
| g10.r2.s1_l2 | clue | chat | rule | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g10.r1.rev2 | reversal | chat | rule,observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g10.r2.s5_l1 | clue | chat | observability | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g10.r1.say19 | clue | chat | scope | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g10.r2.s1_l1 | clue | chat | rule | 2/9 (22%) | 1 | 2/3 (67%) | 2/3 (67%) |
| g10.r2.s4_l3 | clue | chat | exclusions_or_crossover | 9/9 (100%) | 0 | 9/9 (100%) | 8/9 (89%) |
| g10.r2.s5_l3 | clue | chat | observability | 8/9 (89%) | 0 | 7/8 (88%) | 8/8 (100%) |
| g10.r2.say24 | clue | chat | observability | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g10.r2.s5_l4 | clue | chat | observability | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g10.r1.g10.r1.s1.l2 | clue | chat | rule | 4/9 (44%) | 0 | 3/4 (75%) | 4/4 (100%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 211/342 (62%) |
| kind=herring | 30/36 (83%) |
| kind=reversal | 34/36 (94%) |
| literal=no | 117/225 (52%) |
| literal=yes | 158/189 (84%) |
| surface=chat | 275/414 (66%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g10.r1.clamp-at-zero-decision → g10.r1.rev1 | 8/9 (89%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g10.r1.clamp-at-zero-rationale → g10.r1.rev2 | 8/9 (89%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g10.r2.h1 → g10.r2.rev1 | 6/9 (67%) | 8/9 (89%) | 0/9 (0%) | 0/9 (0%) |
| g10.r2.h2 → g10.r2.rev2 | 8/9 (89%) | 8/9 (89%) | 0/9 (0%) | 0/9 (0%) |

## reader vs prepass agreement: 399/414 (96%); only-one-says-found: Counter({'prepass': 9, 'reader': 6})

- run1 g10.r2.h2: found only by reader
- run1 g10.r2.s5_l4: found only by prepass
- run2 g10.r2.h1: found only by prepass
- run2 g10.r1.clamp-at-zero-rationale: found only by reader
- run2 g10.r2.h2: found only by reader
- run2 g10.r2.s4_l1: found only by reader
- run3 g10.r1.g10.r1.s4.l3: found only by reader
- run3 g10.r2.s1_l2: found only by prepass
- run3 g10.r2.h1: found only by prepass
- run6 g10.r1.g10.r1.s4.l4: found only by prepass
- run7 g10.r2.s2_l4: found only by prepass
- run7 g10.r2.s3_l4: found only by prepass
- run9 g10.r2.s2_l4: found only by reader
- run10 g10.r2.h1: found only by prepass
- run10 g10.r2.s5_l3: found only by prepass
