# g6: 10 runs read (8 counted for findability; infra-only runs excluded: [1, 3])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g6.r1.exclusions_or_crossover | 8/10 (80%) | {'infra': 2} |
| g6.r1.observability | 5/10 (50%) | {'infra': 2, 'not_found': 2, 'implementation_slip': 1} |
| g6.r1.rule | 8/10 (80%) | {'infra': 2} |
| g6.r2.exclusions_or_crossover | 3/10 (30%) | {'infra': 2, 'implementation_slip': 5} |
| g6.r2.observability | 7/10 (70%) | {'infra': 2, 'implementation_slip': 1} |
| g6.r2.rule | 8/10 (80%) | {'infra': 2} |
| g6.r2.scope | 8/10 (80%) | {'infra': 2} |

**lost fact-points by cause:** {'infra': 14, 'implementation_slip': 7, 'not_found': 2}
**graded losses:** 23; reader-recorded losses: 23
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g6.r2.batch-discount-uniform-then-cancel-1 | herring | chat | — | 0/5 (0%) | 1 | 0/1 (0%) | 0/1 (0%) |
| g6.r2.batch-discount-uniform-then-cancel-2 | herring | chat | — | 1/5 (20%) | 2 | 0/3 (0%) | 0/3 (0%) |
| g6.r1.l4 | clue | chat | exclusions_or_crossover,observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g6.r2.g6r2-s1-l1 | clue | chat | rule | 1/7 (14%) | 1 | 1/2 (50%) | 2/2 (100%) |
| g6.r1.l6 | clue | chat | exclusions_or_crossover | 0/8 (0%) | 0 | — | — |
| g6.r1.l11 | clue | chat | observability | 4/8 (50%) | 2 | 2/6 (33%) | 4/6 (67%) |
| g6.r2.g6r2-s4-l3 | clue | chat | observability,scope | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g6.r2.g6r2-s2-l1 | clue | chat | scope | 2/8 (25%) | 1 | 2/3 (67%) | 3/3 (100%) |
| g6.r2.g6r2-s4-l1 | clue | chat | observability,rule | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g6.r2.g6r2-s3-l1 | clue | chat | exclusions_or_crossover | 1/8 (12%) | 1 | 1/2 (50%) | 2/2 (100%) |
| g6.r1.l1 | clue | chat | rule | 4/8 (50%) | 0 | 3/4 (75%) | 4/4 (100%) |
| g6.r2.fix18 | clue | chat | observability | 3/8 (38%) | 1 | 1/4 (25%) | 3/4 (75%) |
| g6.r2.g6r2-s3-l3 | clue | mail | exclusions_or_crossover,rule | 8/8 (100%) | 0 | 8/8 (100%) | 5/8 (62%) |
| g6.r2.g6r2-s2-l4 | clue | mail | scope,exclusions_or_crossover | 7/8 (88%) | 1 | 7/8 (88%) | 8/8 (100%) |
| g6.r2.g6r2-s1-l4 | clue | wiki comment | rule,observability | 2/8 (25%) | 0 | 2/2 (100%) | 1/2 (50%) |
| g6.r2.rev1 | reversal | chat | rule,scope | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g6.r2.g6r2-s1-l2 | clue | chat | rule | 7/8 (88%) | 0 | 6/7 (86%) | 7/7 (100%) |
| g6.r1.l2 | clue | wiki comment | rule | 4/8 (50%) | 1 | 4/5 (80%) | 4/5 (80%) |
| g6.r1.l13 | clue | mail | observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g6.r2.g6r2-s2-l3 | clue | wiki comment | scope | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g6.r1.l14 | clue | chat | observability | 2/8 (25%) | 1 | 3/3 (100%) | 3/3 (100%) |
| g6.r2.g6r2-s1-l3 | clue | chat | rule | 3/8 (38%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g6.r1.l5 | clue | wiki comment | exclusions_or_crossover,observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g6.r1.l12 | clue | wiki comment | observability | 3/8 (38%) | 1 | 3/4 (75%) | 3/4 (75%) |
| g6.r1.l3 | clue | mail | rule | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g6.r2.rev2 | reversal | chat | rule,scope,exclusions_or_crossover | 7/7 (100%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g6.r2.g6r2-s3-l2 | clue | wiki comment | exclusions_or_crossover | 7/7 (100%) | 0 | 6/7 (86%) | 4/7 (57%) |
| g6.r1.l7 | clue | mail | exclusions_or_crossover | 7/7 (100%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g6.r2.g6r2-s2-l2 | clue | mail | scope | 6/7 (86%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g6.r2.g6r2-s4-l2 | clue | wiki page | observability | 6/7 (86%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g6.r1.l10 | clue | chat | exclusions_or_crossover,observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g6.r1.l9 | clue | chat | exclusions_or_crossover | 5/8 (62%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g6.r1.l8 | clue | wiki comment | exclusions_or_crossover | 7/8 (88%) | 0 | 7/7 (100%) | 6/7 (86%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 156/228 (68%) |
| kind=herring | 4/10 (40%) |
| kind=reversal | 15/15 (100%) |
| literal=no | 37/74 (50%) |
| literal=yes | 138/179 (77%) |
| surface=chat | 90/144 (62%) |
| surface=mail | 45/46 (98%) |
| surface=wiki comment | 34/56 (61%) |
| surface=wiki page | 6/7 (86%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g6.r2.batch-discount-uniform-then-cancel-1 → g6.r2.rev1 | 1/8 (12%) | 8/8 (100%) | 0/8 (0%) | 0/8 (0%) |
| g6.r2.batch-discount-uniform-then-cancel-2 → g6.r2.rev2 | 1/8 (12%) | 8/8 (100%) | 0/8 (0%) | 0/8 (0%) |

## reader vs prepass agreement: 248/253 (98%); only-one-says-found: Counter({'prepass': 5})

- run4 g6.r2.g6r2-s1-l2: found only by prepass
- run4 g6.r2.g6r2-s2-l2: found only by prepass
- run4 g6.r2.batch-discount-uniform-then-cancel-1: found only by prepass
- run4 g6.r2.batch-discount-uniform-then-cancel-2: found only by prepass
- run8 g6.r1.l11: found only by prepass
