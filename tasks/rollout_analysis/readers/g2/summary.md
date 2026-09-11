# g2: 10 runs read (9 counted for findability; infra-only runs excluded: [8])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g2.r1.exclusions_or_crossover | 9/10 (90%) | {'never_shipped': 1} |
| g2.r1.failure_behavior | 1/10 (10%) | {'not_found': 8, 'never_shipped': 1} |
| g2.r1.observability | 5/10 (50%) | {'not_found': 4, 'never_shipped': 1} |
| g2.r1.rule | 9/10 (90%) | {'never_shipped': 1} |
| g2.r1.scope | 9/10 (90%) | {'never_shipped': 1} |
| g2.r2.exclusions_or_crossover | 9/10 (90%) | {'never_shipped': 1} |
| g2.r2.observability | 9/10 (90%) | {'never_shipped': 1} |
| g2.r2.rule | 9/10 (90%) | {'never_shipped': 1} |
| g2.r2.scope | 9/10 (90%) | {'never_shipped': 1} |

**lost fact-points by cause:** {'not_found': 12, 'never_shipped': 9}
**graded losses:** 12; reader-recorded losses: 21
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g2.r2.h2 | herring | chat | — | 9/9 (100%) | 0 | 0/9 (0%) | 0/9 (0%) |
| g2.r2.h1 | herring | chat | — | 9/9 (100%) | 0 | 0/9 (0%) | 0/9 (0%) |
| g2.r1.herring-marker-inside-budget-dario | herring | chat | — | 9/9 (100%) | 0 | 0/9 (0%) | 0/9 (0%) |
| g2.r1.herring-dropped-count-gideon | herring | chat | — | 9/9 (100%) | 0 | 0/9 (0%) | 0/9 (0%) |
| g2.r2.l-scope-2 | clue | chat | scope | 4/9 (44%) | 0 | 3/4 (75%) | 3/4 (75%) |
| g2.r1.l-floor-nikolai | clue | chat | failure_behavior | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g2.r1.rev2 | reversal | chat | rule,scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r1.l-floor-emil | clue | chat | failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 7/9 (78%) |
| g2.r1.l-bytes-dario | clue | chat | scope | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g2.r1.say26 | clue | chat | failure_behavior | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g2.r2.l-cross-2 | clue | chat | exclusions_or_crossover | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r1.l-floor-dario | clue | chat | failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r1.l-floor-konrad | clue | chat | failure_behavior | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g2.r2.l-scope-4 | clue | chat | scope | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g2.r2.l-obs-3 | clue | chat | observability,rule | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g2.r2.l-cross-3 | clue | chat | exclusions_or_crossover,observability | 2/9 (22%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g2.r1.l-off-konrad | clue | chat | exclusions_or_crossover | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r2.l-obs-1 | clue | chat | observability | 8/9 (89%) | 0 | 7/8 (88%) | 8/8 (100%) |
| g2.r1.say25 | clue | chat | exclusions_or_crossover | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r1.rev1 | reversal | chat | rule | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r2.rev2 | reversal | chat | exclusions_or_crossover | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r1.l-kept-nils | clue | chat | rule | 5/9 (56%) | 0 | 4/5 (80%) | 3/5 (60%) |
| g2.r2.say18 | clue | chat | observability | 5/9 (56%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g2.r1.l-kept-konrad | clue | chat | rule | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g2.r2.l-scope-1 | clue | chat | scope | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g2.r1.l-bytes-nils | clue | chat | scope | 5/9 (56%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g2.r1.l-seam-dermot | clue | mail | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r1.l-bytes-gideon | clue | chat | scope | 5/9 (56%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g2.r2.l-rule-1 | clue | chat | rule | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g2.r2.l-scope-3 | clue | mail | scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r2.l-rule-3 | clue | chat | rule | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r2.l-rule-2 | clue | mail | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r2.l-cross-1 | clue | wiki comment | exclusions_or_crossover | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r1.l-seam-nikolai | clue | chat | rule | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g2.r1.l-kept-gideon | clue | chat | rule | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r1.l-off-dermot | clue | chat | exclusions_or_crossover | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r1.l-log-gideon | clue | chat | observability | 2/9 (22%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g2.r1.l-log-emil | clue | chat | observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r1.l-log-konrad | clue | chat | observability,failure_behavior | 6/9 (67%) | 1 | 6/7 (86%) | 6/7 (86%) |
| g2.r2.rev1 | reversal | chat | rule,exclusions_or_crossover | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r1.l-off-nikolai | clue | chat | exclusions_or_crossover,failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r2.l-rule-4 | clue | wiki comment | rule,observability | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r1.l-seam-dario | clue | mail | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r1.l-log-nikolai | clue | wiki comment | observability | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g2.r2.l-obs-2 | clue | mail | observability,scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g2.r1.l-bytes-emil | clue | chat | scope | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 250/342 (73%) |
| kind=herring | 36/36 (100%) |
| kind=reversal | 33/36 (92%) |
| literal=no | 104/126 (83%) |
| literal=yes | 215/288 (75%) |
| surface=chat | 250/342 (73%) |
| surface=mail | 45/45 (100%) |
| surface=wiki comment | 24/27 (89%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g2.r1.herring-dropped-count-gideon → g2.r1.rev2 | 9/9 (100%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g2.r1.herring-marker-inside-budget-dario → g2.r1.rev1 | 9/9 (100%) | 8/9 (89%) | 0/9 (0%) | 0/9 (0%) |
| g2.r2.h1 → g2.r2.rev1 | 9/9 (100%) | 8/9 (89%) | 0/9 (0%) | 0/9 (0%) |
| g2.r2.h2 → g2.r2.rev2 | 9/9 (100%) | 8/9 (89%) | 0/9 (0%) | 0/9 (0%) |

## reader vs prepass agreement: 413/414 (100%); only-one-says-found: Counter({'reader': 1})

- run7 g2.r2.l-cross-2: found only by reader
