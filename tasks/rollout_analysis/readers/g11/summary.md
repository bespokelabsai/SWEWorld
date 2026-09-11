# g11: 10 runs read (10 counted for findability; infra-only runs excluded: [])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g11.r1.exclusions_or_crossover | 9/10 (90%) | {'implementation_slip': 1} |
| g11.r1.failure_behavior | 7/10 (70%) | {'not_found': 3} |
| g11.r1.observability | 8/10 (80%) | {'implementation_slip': 1, 'not_found': 1} |
| g11.r1.rule | 9/10 (90%) | {'implementation_slip': 1} |
| g11.r1.scope | 8/10 (80%) | {'implementation_slip': 1, 'not_found': 1} |
| g11.r2.exclusions_or_crossover | 10/10 (100%) | {} |
| g11.r2.failure_behavior | 9/10 (90%) | {'herring_followed': 1} |
| g11.r2.observability | 10/10 (100%) | {} |
| g11.r2.rule | 7/10 (70%) | {'not_found': 3} |

**lost fact-points by cause:** {'not_found': 8, 'implementation_slip': 4, 'herring_followed': 1}
**graded losses:** 13; reader-recorded losses: 13
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g11.r1.ledger-twin-checkpoints-dario | herring | chat | — | 5/9 (56%) | 1 | 0/6 (0%) | 0/6 (0%) |
| g11.r1.ledger-twin-checkpoints-emil | herring | chat | — | 7/9 (78%) | 0 | 0/7 (0%) | 0/7 (0%) |
| g11.r2.lr-decay-to-zero-dario | herring | chat | — | 9/9 (100%) | 0 | 1/9 (11%) | 0/9 (0%) |
| g11.r2.lr-decay-to-zero-konrad | herring | chat | — | 9/9 (100%) | 0 | 1/9 (11%) | 0/9 (0%) |
| g11.r1.l8 | clue | chat | rule,failure_behavior | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g11.r1.l1 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 9/10 (90%) |
| g11.r1.l10 | clue | chat | scope,observability | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g11.r1.l2 | clue | chat | rule | 6/10 (60%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g11.r1.l9 | clue | chat | scope | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g11.r1.l11 | clue | chat | scope | 5/10 (50%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g11.r1.l13 | clue | chat | exclusions_or_crossover | 4/10 (40%) | 0 | 4/4 (100%) | 3/4 (75%) |
| g11.r1.l12 | clue | chat | scope | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g11.r1.l17 | clue | chat | failure_behavior | 7/10 (70%) | 3 | 7/10 (70%) | 7/10 (70%) |
| g11.r1.l3 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g11.r1.l19 | clue | chat | observability | 7/10 (70%) | 0 | 6/7 (86%) | 5/7 (71%) |
| g11.r1.l4 | clue | chat | observability | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g11.r1.l14 | clue | chat | exclusions_or_crossover | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g11.r1.rev2 | reversal | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g11.r1.l18 | clue | chat | observability | 10/10 (100%) | 0 | 9/10 (90%) | 8/10 (80%) |
| g11.r1.l5 | clue | chat | rule | 3/10 (30%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g11.r2.l1 | clue | chat | rule,observability | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g11.r1.l15 | clue | chat | exclusions_or_crossover,observability | 10/10 (100%) | 0 | 10/10 (100%) | 9/10 (90%) |
| g11.r1.l16 | clue | chat | failure_behavior | 10/10 (100%) | 0 | 10/10 (100%) | 9/10 (90%) |
| g11.r2.rev1 | reversal | chat | rule,exclusions_or_crossover,observability | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g11.r2.l5 | clue | chat | rule,observability | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g11.r1.say25 | clue | chat | observability | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g11.r1.rev1 | reversal | chat | rule | 11/11 (100%) | 0 | 11/11 (100%) | 11/11 (100%) |
| g11.r2.l8 | clue | chat | rule | 9/10 (90%) | 1 | 8/10 (80%) | 10/10 (100%) |
| g11.r2.l2 | clue | chat | rule | 5/10 (50%) | 2 | 7/7 (100%) | 7/7 (100%) |
| g11.r2.l6 | clue | chat | observability,rule | 7/10 (70%) | 1 | 6/8 (75%) | 8/8 (100%) |
| g11.r2.l4 | clue | chat | rule | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g11.r1.l7 | clue | chat | rule | 9/10 (90%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g11.r2.l3 | clue | chat | rule | 9/10 (90%) | 1 | 9/10 (90%) | 10/10 (100%) |
| g11.r2.l7 | clue | chat | observability | 6/10 (60%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g11.r1.l6 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g11.r2.l9 | clue | chat | rule,exclusions_or_crossover | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g11.r2.say20 | clue | chat | rule | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g11.r2.l11 | clue | chat | exclusions_or_crossover,observability | 0/10 (0%) | 0 | — | — |
| g11.r1.say24 | clue | chat | observability | 10/10 (100%) | 0 | 9/10 (90%) | 9/10 (90%) |
| g11.r2.l12 | clue | chat | failure_behavior | 6/10 (60%) | 2 | 6/8 (75%) | 7/8 (88%) |
| g11.r2.say19 | clue | chat | exclusions_or_crossover | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g11.r2.l14 | clue | chat | exclusions_or_crossover | 4/10 (40%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g11.r2.l10 | clue | chat | rule | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g11.r2.rev2 | reversal | chat | rule,failure_behavior | 10/11 (91%) | 0 | 10/10 (100%) | 10/10 (100%) |
| g11.r2.l13 | clue | chat | failure_behavior | 8/10 (80%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g11.r2.l15 | clue | chat | exclusions_or_crossover | 7/10 (70%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g11.r1.say23 | clue | chat | observability | 10/10 (100%) | 0 | 10/10 (100%) | 10/10 (100%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 302/390 (77%) |
| kind=herring | 31/36 (86%) |
| kind=reversal | 41/42 (98%) |
| literal=no | 100/146 (68%) |
| literal=yes | 274/322 (85%) |
| surface=chat | 374/468 (80%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g11.r1.ledger-twin-checkpoints-dario → g11.r1.rev1 | 7/10 (70%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g11.r1.ledger-twin-checkpoints-emil → g11.r1.rev2 | 9/10 (90%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g11.r2.lr-decay-to-zero-dario → g11.r2.rev1 | 10/10 (100%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) |
| g11.r2.lr-decay-to-zero-konrad → g11.r2.rev2 | 10/10 (100%) | 9/10 (90%) | 1/10 (10%) | 1/10 (10%) |

## reader vs prepass agreement: 465/468 (99%); only-one-says-found: Counter({'prepass': 3})

- run2 g11.r2.l12: found only by prepass
- run3 g11.r1.ledger-twin-checkpoints-emil: found only by prepass
- run5 g11.r2.l4: found only by prepass
