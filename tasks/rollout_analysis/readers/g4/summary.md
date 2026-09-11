# g4: 10 runs read (8 counted for findability; infra-only runs excluded: [2, 9])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g4.r1.exclusions_or_crossover | 8/10 (80%) | {'never_shipped': 1, 'infra': 1} |
| g4.r1.observability | 8/10 (80%) | {'never_shipped': 1, 'infra': 1} |
| g4.r1.rule | 8/10 (80%) | {'never_shipped': 1, 'infra': 1} |
| g4.r1.scope | 5/10 (50%) | {'not_found': 2, 'never_shipped': 1, 'found_misread': 1, 'infra': 1} |
| g4.r2.failure_behavior | 7/10 (70%) | {'never_shipped': 1, 'infra': 1, 'implementation_slip': 1} |
| g4.r2.observability | 8/10 (80%) | {'never_shipped': 1, 'infra': 1} |
| g4.r2.rule | 8/10 (80%) | {'never_shipped': 1, 'infra': 1} |
| g4.r2.scope | 8/10 (80%) | {'never_shipped': 1, 'infra': 1} |

**lost fact-points by cause:** {'not_found': 2, 'never_shipped': 8, 'found_misread': 1, 'infra': 8, 'implementation_slip': 1}
**graded losses:** 20; reader-recorded losses: 20
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g4.r2.h2-isoformat-segment | herring | chat | — | 4/6 (67%) | 0 | 0/4 (0%) | 1/4 (25%) |
| g4.r1.backend-params-whole-dict-konrad | herring | chat | — | 3/6 (50%) | 0 | 0/3 (0%) | 0/3 (0%) |
| g4.r1.backend-params-whole-dict-dario | herring | chat | — | 5/6 (83%) | 0 | 0/5 (0%) | 0/5 (0%) |
| g4.r2.h1-uuid4-nocache | herring | chat | — | 7/7 (100%) | 0 | 0/7 (0%) | 1/7 (14%) |
| g4.r1.l-schema-dump | clue | chat | rule | 4/7 (57%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g4.r1.l-keys-count | clue | chat | rule,observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.fix27 | clue | chat | scope | 7/8 (88%) | 1 | 4/8 (50%) | 5/8 (62%) |
| g4.r1.l-keys-onelist | clue | chat | rule | 3/8 (38%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g4.r1.l-backend-default | clue | chat | scope,observability | 7/8 (88%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g4.r2.l7 | clue | chat | scope,observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r2.l5 | clue | chat | scope | 4/8 (50%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g4.r1.l-retries-fork | clue | chat | exclusions_or_crossover | 2/8 (25%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g4.r1.say24 | clue | chat | scope | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.rev2 | reversal | chat | exclusions_or_crossover | 6/8 (75%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g4.r1.l-key-on-disk | clue | chat | exclusions_or_crossover,observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.l-params-none | clue | chat | scope | 1/8 (12%) | 2 | 1/3 (33%) | 3/3 (100%) |
| g4.r1.l-schema-order | clue | chat | rule | 3/8 (38%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g4.r2.l6 | clue | chat | scope | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.say22 | clue | chat | rule | 6/8 (75%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g4.r1.l-window-reuse | clue | chat | exclusions_or_crossover | 1/8 (12%) | 1 | 1/2 (50%) | 2/2 (100%) |
| g4.r2.l8 | clue | chat | scope | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r2.rev2 | reversal | chat | rule,observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.fix25 | clue | chat | observability | 7/8 (88%) | 1 | 6/8 (75%) | 7/8 (88%) |
| g4.r2.l1 | clue | chat | rule | 1/8 (12%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g4.r2.rev1 | reversal | chat | rule | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r2.l3 | clue | chat | rule,scope | 2/8 (25%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g4.r1.l-completions-object | clue | chat | rule | 5/8 (62%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g4.r2.l13 | clue | chat | observability | 7/8 (88%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g4.r2.l2 | clue | chat | rule | 0/8 (0%) | 0 | — | — |
| g4.r2.l4 | clue | chat | rule | 7/8 (88%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g4.r1.say23 | clue | chat | rule | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r2.l15 | clue | chat | observability,scope | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.l-backend-resolved | clue | chat | scope | 1/8 (12%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g4.r2.l14 | clue | chat | observability | 4/8 (50%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g4.r1.l-keys-order | clue | chat | rule | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.fix26 | clue | chat | rule | 8/8 (100%) | 0 | 6/8 (75%) | 8/8 (100%) |
| g4.r1.l-genparams-empty | clue | chat | rule | 4/8 (50%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g4.r1.l-parse-func | clue | chat | rule | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.l-genparams-fix | clue | chat | rule | 2/8 (25%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g4.r1.l-param-keys | clue | chat | exclusions_or_crossover | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.rev1 | reversal | chat | exclusions_or_crossover,observability | 8/8 (100%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g4.r1.l-system-prompt | clue | chat | rule | 4/8 (50%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g4.r1.l-params-copy | clue | chat | scope | 1/8 (12%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g4.r2.l9 | clue | chat | failure_behavior | 3/8 (38%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g4.r2.l11 | clue | chat | failure_behavior | 3/8 (38%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g4.r2.say19 | clue | chat | failure_behavior | 7/8 (88%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g4.r2.l10 | clue | chat | failure_behavior | 8/8 (100%) | 0 | 8/8 (100%) | 7/8 (88%) |
| g4.r2.l12 | clue | chat | failure_behavior,scope | 8/8 (100%) | 0 | 8/8 (100%) | 7/8 (88%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 213/319 (67%) |
| kind=herring | 19/25 (76%) |
| kind=reversal | 30/32 (94%) |
| literal=no | 36/89 (40%) |
| literal=yes | 226/287 (79%) |
| surface=chat | 262/376 (70%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g4.r1.backend-params-whole-dict-dario → g4.r1.rev1 | 7/8 (88%) | 8/8 (100%) | 0/8 (0%) | 0/8 (0%) |
| g4.r1.backend-params-whole-dict-konrad → g4.r1.rev2 | 4/8 (50%) | 6/8 (75%) | 0/8 (0%) | 0/8 (0%) |
| g4.r2.h1-uuid4-nocache → g4.r2.rev1 | 8/8 (100%) | 8/8 (100%) | 0/8 (0%) | 0/8 (0%) |
| g4.r2.h2-isoformat-segment → g4.r2.rev2 | 5/8 (62%) | 8/8 (100%) | 0/8 (0%) | 0/8 (0%) |

## reader vs prepass agreement: 370/376 (98%); only-one-says-found: Counter({'prepass': 5, 'reader': 1})

- run1 g4.r2.l5: found only by prepass
- run1 g4.r2.l4: found only by prepass
- run3 g4.r1.l-completions-object: found only by reader
- run7 g4.r2.l5: found only by prepass
- run7 g4.r1.l-schema-order: found only by prepass
- run10 g4.r2.l5: found only by prepass
