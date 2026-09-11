# g7: 10 runs read (9 counted for findability; infra-only runs excluded: [5])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g7.r1.failure_behavior | 7/10 (70%) | {'not_found': 1, 'infra': 1, 'found_misread': 1} |
| g7.r1.observability | 5/10 (50%) | {'implementation_slip': 2, 'not_found': 1, 'infra': 1, 'found_misread': 1} |
| g7.r1.rule | 2/10 (20%) | {'not_found': 5, 'grader_overspecifies': 2, 'infra': 1} |
| g7.r1.scope | 5/10 (50%) | {'implementation_slip': 2, 'not_found': 1, 'infra': 1, 'found_misread': 1} |
| g7.r2.failure_behavior | 9/10 (90%) | {'infra': 1} |
| g7.r2.observability | 9/10 (90%) | {'infra': 1} |
| g7.r2.rule | 9/10 (90%) | {'infra': 1} |
| g7.r2.scope | 9/10 (90%) | {'infra': 1} |

**lost fact-points by cause:** {'not_found': 8, 'implementation_slip': 4, 'grader_overspecifies': 2, 'infra': 8, 'found_misread': 3}
**graded losses:** 25; reader-recorded losses: 25
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** none

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g7.r1.g7-h2-truncate-is-the-pattern | herring | chat | — | 0/8 (0%) | 1 | 0/1 (0%) | 0/1 (0%) |
| g7.r2.h1-sentinel-substring-ci | herring | chat | — | 6/8 (75%) | 1 | 1/7 (14%) | 0/7 (0%) |
| g7.r1.g7-h1-checkpoint-authoritative | herring | chat | — | 6/8 (75%) | 1 | 1/7 (14%) | 0/7 (0%) |
| g7.r2.h2-sentinel-placement-free | herring | chat | — | 2/8 (25%) | 0 | 1/2 (50%) | 0/2 (0%) |
| g7.r2.g7r2-l03 | clue | chat | rule | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g7.r1.rev2 | reversal | chat | failure_behavior,scope | 7/9 (78%) | 2 | 7/9 (78%) | 7/9 (78%) |
| g7.r1.l1 | clue | chat | rule | 0/9 (0%) | 0 | — | — |
| g7.r2.rev1 | reversal | chat | rule,scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.say24 | clue | chat | scope | 7/9 (78%) | 0 | 5/7 (71%) | 6/7 (86%) |
| g7.r1.l13 | clue | chat | observability | 9/9 (100%) | 0 | 9/9 (100%) | 8/9 (89%) |
| g7.r2.g7r2-l01 | clue | chat | rule | 0/9 (0%) | 0 | — | — |
| g7.r2.g7r2-l06 | clue | chat | scope | 2/9 (22%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g7.r1.l15 | clue | chat | observability | 9/9 (100%) | 0 | 7/9 (78%) | 9/9 (100%) |
| g7.r1.l8 | clue | chat | scope | 6/9 (67%) | 0 | 4/6 (67%) | 4/6 (67%) |
| g7.r1.l9 | clue | mail | failure_behavior | 2/9 (22%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g7.r2.g7r2-l08 | clue | mail | failure_behavior | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g7.r1.l4 | clue | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 8/9 (89%) |
| g7.r1.l16 | clue | mail | observability,failure_behavior | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g7.r2.g7r2-l05 | clue | mail | scope | 4/9 (44%) | 0 | 3/4 (75%) | 4/4 (100%) |
| g7.r1.fix28 | clue | chat | failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 8/9 (89%) |
| g7.r2.g7r2-l09 | clue | chat | failure_behavior | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g7.r2.g7r2-l02 | clue | chat | rule | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g7.r1.l3 | clue | mail | rule | 9/9 (100%) | 0 | 8/9 (89%) | 8/9 (89%) |
| g7.r1.rev1 | reversal | chat | rule,scope,failure_behavior | 8/9 (89%) | 1 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.say22 | clue | chat | rule | 4/9 (44%) | 0 | 2/4 (50%) | 2/4 (50%) |
| g7.r1.l6 | clue | chat | scope | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g7.r1.say25 | clue | chat | scope | 7/9 (78%) | 0 | 6/7 (86%) | 7/7 (100%) |
| g7.r1.say20 | clue | chat | failure_behavior | 8/9 (89%) | 0 | 7/8 (88%) | 7/8 (88%) |
| g7.r1.l14 | clue | wiki comment | observability | 9/9 (100%) | 0 | 7/9 (78%) | 9/9 (100%) |
| g7.r2.g7r2-l07 | clue | wiki comment | scope | 8/9 (89%) | 0 | 7/8 (88%) | 8/8 (100%) |
| g7.r1.l7 | clue | mail | scope | 8/9 (89%) | 1 | 8/9 (89%) | 8/9 (89%) |
| g7.r1.l10 | clue | chat | failure_behavior,rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.say23 | clue | chat | rule | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g7.r2.g7r2-l04 | clue | wiki page | scope | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g7.r1.l2 | clue | wiki comment | rule | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g7.r1.say21 | clue | chat | observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r2.rev2 | reversal | chat | rule,scope,failure_behavior | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g7.r2.g7r2-l11 | clue | mail | observability | 9/9 (100%) | 0 | 6/9 (67%) | 9/9 (100%) |
| g7.r1.fix29 | clue | chat | rule | 9/9 (100%) | 0 | 5/9 (56%) | 7/9 (78%) |
| g7.r1.l5 | clue | wiki comment | scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.l12 | clue | mail | failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r2.g7r2-l13 | clue | wiki comment | observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.fix27 | clue | chat | observability | 9/9 (100%) | 0 | 7/9 (78%) | 7/9 (78%) |
| g7.r2.say18 | clue | chat | observability | 0/9 (0%) | 0 | — | — |
| g7.r2.g7r2-l12 | clue | chat | observability | 5/9 (56%) | 0 | 5/5 (100%) | 5/5 (100%) |
| g7.r1.l11 | clue | wiki comment | failure_behavior | 9/9 (100%) | 0 | 6/9 (67%) | 8/9 (89%) |
| g7.r2.g7r2-l14 | clue | wiki comment | observability | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g7.r1.fix26 | clue | chat | failure_behavior | 2/9 (22%) | 0 | 1/2 (50%) | 2/2 (100%) |
| g7.r2.g7r2-l10 | clue | wiki comment | failure_behavior | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g7.r2.say19 | clue | chat | observability | 8/9 (89%) | 0 | 7/8 (88%) | 8/8 (100%) |
| g7.r1.fix30 | clue | chat | scope | 8/9 (89%) | 0 | 4/8 (50%) | 4/8 (50%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 262/387 (68%) |
| kind=herring | 17/32 (53%) |
| kind=reversal | 35/36 (97%) |
| literal=no | 61/149 (41%) |
| literal=yes | 253/306 (83%) |
| surface=chat | 199/302 (66%) |
| surface=mail | 51/72 (71%) |
| surface=wiki comment | 60/72 (83%) |
| surface=wiki page | 4/9 (44%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g7.r1.g7-h1-checkpoint-authoritative → g7.r1.rev1 | 7/9 (78%) | 8/9 (89%) | 0/9 (0%) | 0/9 (0%) |
| g7.r1.g7-h2-truncate-is-the-pattern → g7.r1.rev2 | 0/9 (0%) | 7/9 (78%) | 0/9 (0%) | 0/9 (0%) |
| g7.r2.h1-sentinel-substring-ci → g7.r2.rev1 | 6/9 (67%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g7.r2.h2-sentinel-placement-free → g7.r2.rev2 | 2/9 (22%) | 8/9 (89%) | 0/9 (0%) | 0/9 (0%) |

## reader vs prepass agreement: 450/455 (99%); only-one-says-found: Counter({'reader': 4, 'prepass': 1})

- run1 g7.r1.l9: found only by reader
- run3 g7.r2.h1-sentinel-substring-ci: found only by prepass
- run7 g7.r2.g7r2-l06: found only by reader
- run7 g7.r2.g7r2-l09: found only by reader
- run10 g7.r1.g7-h2-truncate-is-the-pattern: found only by reader
