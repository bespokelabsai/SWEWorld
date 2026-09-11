# g7: 10 runs read (9 counted for findability; infra-only runs excluded: [5])

## per-fact pass rate (all runs)

| fact | passed | lost causes |
|---|---|---|
| g7.r1.failure_behavior | 4/10 (40%) | {'overridden_by_other_corpus_text': 4, 'found_misread': 1, 'infra': 1} |
| g7.r1.observability | 2/10 (20%) | {'overridden_by_other_corpus_text': 4, 'found_misread': 2, 'implementation_slip': 1, 'infra': 1} |
| g7.r1.rule | 3/10 (30%) | {'not_found': 5, 'borderline_unstated_order': 1, 'infra': 1} |
| g7.r1.scope | 6/10 (60%) | {'found_misread': 1, 'implementation_slip': 2, 'infra': 1} |
| g7.r2.failure_behavior | 9/10 (90%) | {'infra': 1} |
| g7.r2.observability | 9/10 (90%) | {'infra': 1} |
| g7.r2.rule | 9/10 (90%) | {'infra': 1} |
| g7.r2.scope | 9/10 (90%) | {'infra': 1} |

**lost fact-points by cause:** {'overridden_by_other_corpus_text': 8, 'not_found': 5, 'found_misread': 4, 'borderline_unstated_order': 1, 'implementation_slip': 3, 'infra': 8}
**graded losses:** 29; reader-recorded losses: 29
**reader fact values replaced by Horizon's grade (run, fact, reader, horizon):** [(2, 'g7.r1.rule', None, 0), (2, 'g7.r1.scope', None, 1), (2, 'g7.r1.failure_behavior', None, 0), (2, 'g7.r1.observability', None, 0), (2, 'g7.r2.rule', None, 1), (2, 'g7.r2.scope', None, 1), (2, 'g7.r2.failure_behavior', None, 1), (2, 'g7.r2.observability', None, 1), (4, 'g7.r1.rule', None, 0), (4, 'g7.r1.scope', None, 0), (4, 'g7.r1.failure_behavior', None, 1), (4, 'g7.r1.observability', None, 0), (4, 'g7.r2.rule', None, 1), (4, 'g7.r2.scope', None, 1), (4, 'g7.r2.failure_behavior', None, 1), (4, 'g7.r2.observability', None, 1)]

## per remark (live runs)

| remark | kind | surface | carries | found | partial | registered as requirement (of found) | code followed (of found) |
|---|---|---|---|---|---|---|---|
| g7.r1.g7-h2-truncate-is-the-pattern | herring | chat | — | 2/9 (22%) | 2 | 0/4 (0%) | 0/4 (0%) |
| g7.r2.h1-sentinel-substring-ci | herring | chat | — | 7/9 (78%) | 2 | 0/9 (0%) | 0/9 (0%) |
| g7.r1.g7-h1-checkpoint-authoritative | herring | chat | — | 8/9 (89%) | 1 | 0/9 (0%) | 0/9 (0%) |
| g7.r2.h2-sentinel-placement-free | herring | chat | — | 4/9 (44%) | 2 | 0/6 (0%) | 0/6 (0%) |
| g7.r2.g7r2-l03 | clue | chat | rule | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g7.r1.rev2 | reversal | chat | failure_behavior,scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.l1 | clue | chat | rule | 2/9 (22%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g7.r2.rev1 | reversal | chat | rule,scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.say24 | clue | chat | scope | 6/9 (67%) | 1 | 6/7 (86%) | 6/7 (86%) |
| g7.r1.l13 | clue | chat | observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r2.g7r2-l01 | clue | chat | rule | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g7.r2.g7r2-l06 | clue | chat | scope | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g7.r1.l15 | clue | chat | observability | 9/9 (100%) | 0 | 8/9 (89%) | 8/9 (89%) |
| g7.r1.l8 | clue | chat | scope | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g7.r1.l9 | clue | mail | failure_behavior | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g7.r2.g7r2-l08 | clue | mail | failure_behavior | 3/9 (33%) | 0 | 3/3 (100%) | 3/3 (100%) |
| g7.r1.l4 | clue | chat | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.l16 | clue | mail | observability,failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 5/9 (56%) |
| g7.r2.g7r2-l05 | clue | mail | scope | 2/9 (22%) | 0 | 2/2 (100%) | 2/2 (100%) |
| g7.r1.fix28 | clue | chat | failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r2.g7r2-l09 | clue | chat | failure_behavior | 0/9 (0%) | 0 | — | — |
| g7.r2.g7r2-l02 | clue | chat | rule | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g7.r1.l3 | clue | mail | rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.rev1 | reversal | chat | rule,scope,failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.say22 | clue | chat | rule | 4/9 (44%) | 1 | 4/5 (80%) | 4/5 (80%) |
| g7.r1.l6 | clue | chat | scope | 8/9 (89%) | 1 | 8/9 (89%) | 9/9 (100%) |
| g7.r1.say25 | clue | chat | scope | 7/9 (78%) | 1 | 6/8 (75%) | 8/8 (100%) |
| g7.r1.say20 | clue | chat | failure_behavior | 9/9 (100%) | 0 | 8/9 (89%) | 9/9 (100%) |
| g7.r1.l14 | clue | wiki comment | observability | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g7.r2.g7r2-l07 | clue | wiki comment | scope | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.l7 | clue | mail | scope | 7/9 (78%) | 0 | 7/7 (100%) | 7/7 (100%) |
| g7.r1.l10 | clue | chat | failure_behavior,rule | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.say23 | clue | chat | rule | 1/9 (11%) | 0 | 0/1 (0%) | 1/1 (100%) |
| g7.r2.g7r2-l04 | clue | wiki page | scope | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g7.r1.l2 | clue | wiki comment | rule | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g7.r1.say21 | clue | chat | observability | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g7.r2.rev2 | reversal | chat | rule,scope,failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r2.g7r2-l11 | clue | mail | observability | 8/9 (89%) | 0 | 6/8 (75%) | 7/8 (88%) |
| g7.r1.fix29 | clue | chat | rule | 8/9 (89%) | 0 | 3/8 (38%) | 3/8 (38%) |
| g7.r1.l5 | clue | wiki comment | scope | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g7.r1.l12 | clue | mail | failure_behavior | 9/9 (100%) | 0 | 9/9 (100%) | 7/9 (78%) |
| g7.r2.g7r2-l13 | clue | wiki comment | observability | 9/9 (100%) | 0 | 8/9 (89%) | 8/9 (89%) |
| g7.r1.fix27 | clue | chat | observability | 9/9 (100%) | 0 | 8/9 (89%) | 7/9 (78%) |
| g7.r2.say18 | clue | chat | observability | 1/9 (11%) | 0 | 1/1 (100%) | 1/1 (100%) |
| g7.r2.g7r2-l12 | clue | chat | observability | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g7.r1.l11 | clue | wiki comment | failure_behavior | 6/9 (67%) | 0 | 6/6 (100%) | 6/6 (100%) |
| g7.r2.g7r2-l14 | clue | wiki comment | observability | 8/9 (89%) | 0 | 8/8 (100%) | 8/8 (100%) |
| g7.r1.fix26 | clue | chat | failure_behavior | 2/9 (22%) | 0 | 1/2 (50%) | 2/2 (100%) |
| g7.r2.g7r2-l10 | clue | wiki comment | failure_behavior | 4/9 (44%) | 0 | 4/4 (100%) | 4/4 (100%) |
| g7.r2.say19 | clue | chat | observability | 9/9 (100%) | 0 | 9/9 (100%) | 9/9 (100%) |
| g7.r1.fix30 | clue | chat | scope | 9/9 (100%) | 0 | 7/9 (78%) | 4/9 (44%) |

## found rate by remark quality (live runs; found = yes or partial)

| bucket | found |
|---|---|
| kind=clue | 264/387 (68%) |
| kind=herring | 28/36 (78%) |
| kind=reversal | 36/36 (100%) |
| literal=no | 75/153 (49%) |
| literal=yes | 253/306 (83%) |
| surface=chat | 218/306 (71%) |
| surface=mail | 51/72 (71%) |
| surface=wiki comment | 55/72 (76%) |
| surface=wiki page | 4/9 (44%) |

## herrings (live runs)

| herring → reversal | saw herring | saw reversal | believed herring | code followed herring |
|---|---|---|---|---|
| g7.r1.g7-h1-checkpoint-authoritative → g7.r1.rev1 | 8/9 (89%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g7.r1.g7-h2-truncate-is-the-pattern → g7.r1.rev2 | 2/9 (22%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g7.r2.h1-sentinel-substring-ci → g7.r2.rev1 | 7/9 (78%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |
| g7.r2.h2-sentinel-placement-free → g7.r2.rev2 | 4/9 (44%) | 9/9 (100%) | 0/9 (0%) | 0/9 (0%) |

## reader vs prepass agreement: 454/460 (99%); only-one-says-found: Counter({'reader': 6})

- run2 g7.r1.l1: found only by reader
- run6 g7.r1.g7-h2-truncate-is-the-pattern: found only by reader
- run6 g7.r2.h2-sentinel-placement-free: found only by reader
- run6 g7.r1.l1: found only by reader
- run7 g7.r1.g7-h2-truncate-is-the-pattern: found only by reader
- run7 g7.r2.h2-sentinel-placement-free: found only by reader
