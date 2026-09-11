# g3 (retry-backoff-policy) — world-hosted v7, eval ce846459, run 2, rollout 63d214a1

**reward 0.6667** (6 of 9 facts). Not a broken run: PR #737 merged, CI green, deployed.

## What it found

The agent built the strongest part of its process on chat: it bulk-dumped every Mattermost
channel and every wiki page's comments to local files, then built a deduped, chronologically
sorted context file (`ctx2.txt`, 541 lines) and read the first ~180 lines of it in full 40-line
chunks (transcript lines 2182–2338). That pass alone recovered the whole herring/reversal
timeline for both requirements — Jan/Feb "no ceiling on THROTTLE" and "plain assignment for
the cooldown" correctly identified as superseded by the Mar/Apr waiver-pool and `max()`-horizon
decisions (lines 2182, 2282, 2584) — and the shipped code implements the reversed (correct)
version in both cases: `throttle_cooldown_until = max(current, now + delay)` and a per-request
`throttle_waivers_left` that a THROTTLE decrements before ever touching `attempts_left`. It also
opened both wiki-comment carriers (`g3.r1.l5`, `g3.r2.s1a`, via `cat /tmp/wiki2/<id>.txt`) and
two of the three mail threads (`g3.r1.l8`, `g3.r2.s4d`) in full. This got it six of nine facts:
`g3.r1.rule`, `g3.r1.scope`, `g3.r1.failure_behavior`, `g3.r2.scope`, `g3.r2.exclusions_or_crossover`,
`g3.r2.observability`.

## What it missed, and why

At transcript line 2433 the agent judged `ctx2.txt` "much noise" and abandoned full-context
reading — it had reached only about a third of the way through (line 180/541, into March) —
and switched to `ctx3.txt`, a single-line keyword-filtered dump with **no surrounding turns**,
for everything from April onward. That switch is the proximate cause of every one of the 15
not-found remarks and both of the two real losses:

- **`g3.r1.exclusions_or_crossover` and `g3.r1.observability`** both fail on the same bug: the
  shipped `decide()` never zeroes `attempts_left` on a `TERMINAL` verdict (`assert (False, 0, 4,
  2, 'terminal:abort') == (False, 5, 4, 2, 'terminal:abort')` — the budget survives untouched).
  The *only* remark in the entire plant that states this — `g3.r1.l13`, dermot at 14:18 on
  2025-04-24 ("we empty the attempts, so your seven lands at zero. passes we dont touch, still
  six") — was cut by exactly this switch: `ctx3.txt` kept only the neighbouring line at 14:15
  ("`invalid api key` classifies as terminal:abort. theres nothing to retry into so we stop
  there", transcript line 2502) because that was the line the keyword grep matched; the reply
  two turns later that actually states the zeroing behavior was never captured anywhere. The
  agent's own follow-up reading plan (line 2534) lists five threads to re-expand in full and
  never names this one. The redundant carrier, mail thread `g3.r1.l12`, was independently lost
  to a different gap: the mail triage (line 3495) filtered the mailbox to ~15 files by
  retry-keyword subject match, and this thread's subject ("smoke run timings on the wiki before
  we cut 0.1.26") didn't match despite its body restating the same fact.

- **`g3.r2.rule`** fails on one assertion in an otherwise-fully-passing test:
  `remaining_cooldown_seconds(horizoned, 500.0) == 8.001` for a horizon of `508.0009`, but the
  shipped function is `max(0.0, cooldown_until - now)` with no `round()` call, returning
  `8.000900000000001`. The tracker-field placement, the 0.0 default, and all three monotonic-max
  cases in the same test passed — this is purely a missing three-decimal round. The one remark
  that states rounding is required, `g3.r2.s1c` ("clamp at 0.0, round to three decimals ...
  4.999999999998 comes out 5.0"), sits past the abandoned line and was never surfaced —
  confirmed by a zero-hit grep across the full transcript for `-3.2`, `4.999999999998`, and
  `round to three`. Notably `g3.r2.observability`, which exercises the same function, still
  passed, because its test values (1002.0/1004.5/1005.0 against a 1005.0 horizon) are exact
  under plain subtraction and never expose the missing round().

## Herrings

All four resisted correctly (`believed: reversal` in every case) — the agent explicitly narrated
the Jan/Feb positions as superseded before writing any code, and the shipped implementation
matches the reversed versions, not the herrings.

## Coordinator follow-up: is `finish_reason == "length"` treated as terminal?

**No.** `classify_failure` implements exactly the ticket's own four ordered signals with no
message marker or special case for `"length"`/`"finish_reason"` anywhere in the shipped code
(grepped every assistant-authored message: zero matches). The pre-existing call site (lines
516–524, 4715–4723 — code the agent read, not code it wrote) already raises a plain
`ValueError(f"finish_reason was {generic_response.finish_reason}")`, which the type-MRO table
maps to `CONTRACT` — costing 2 attempts via `g3.r1.rule`, not a fail-on-first abort. No new
exception class, no `TERMINAL` branch, no "fail it out on the first" logic exists anywhere. The
agent never quoted or saw konrad's line — `g3.r1.l1` is one of the 15 not-found remarks (zero
hits for "finish_reason length four times" / "shoudn't get that many goes" across the whole
transcript), consistent with it sitting in the #code-review 2025-06-03 window past the point
the agent stopped reading `ctx2.txt` in full. The agent got the CONTRACT-costs-2 rule right
anyway, via `g3.r1.l2`/`l3`/`rev2` — but by the generic classification table lining up, not by
reasoning about konrad's specific complaint.
