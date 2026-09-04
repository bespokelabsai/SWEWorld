# Was every graded thing said, or only implied? — g10

**33 of 52** assertions rest on something a remark says outright.

- `stated` **33** — a reader was told
- `implied` **11** — a reader has to work it out, and may not
- `absent` **1** — nothing in the corpus bears on it
- `not_required` **7** — the assertion checks the suite's own fixture

`implied` is a finding, not a pass. The spec arm scores 1.00 and the clues arm 0.70 on the same suite, and the gap is made of assertions a generous reading calls carried.

> **These verdicts are what provoked the rewrites, not what the plant says now.** 5 remark(s) rewritten, 4 added, 0 not fixed. Re-run `settle --dry-run` for the verdicts on the corpus as it now stands.

| claim | verdict | remarks | why |
|---|---|---|---|
| `g10.r1.exclusions_or_crossover#1` | stated | `g10.r1.g10.r1.s4.l2`, `g10.r1.g10.r1.s4.l1` | Emil says a refill "just gets capped back at the per-minute limit" and Nils says "every refill that tops out at the limit", so a reader is told outright that refill on the token axis stops at max_toke |
| `g10.r1.exclusions_or_crossover#2` | **implied** | `g10.r1.g10.r1.s4.l2`, `g10.r1.g10.r1.s2.l4` | Every cap remark is about the token/per-minute allowance; nobody says the request axis has its own ceiling it refills up to, so the reader has to generalise the token-side cap to available_request_cap |
| `g10.r1.exclusions_or_crossover#3` | stated | `g10.r1.g10.r1.s4.l1`, `g10.r1.g10.r1.s4.l2`, `g10.r1.g10.r1.s3.l1` | Nils reports the counter reaching 47 on a run that never went under and says refills topping out at the limit "shouldn't be" ticking it, and Emil agrees there is "nothing worth recording" — the exclus |
| `g10.r1.exclusions_or_crossover#4` | **implied** | `g10.r1.g10.r1.s4.l3`, `g10.r1.g10.r1.s4.l2` | Nikolai's remark is aimed at the counter, and only describes in passing that a big over-reservation "puts us right on the ceiling"; the reader is left to supply that release itself clamps down to max_ |
| `g10.r1.exclusions_or_crossover#5` | stated | `g10.r1.g10.r1.s4.l3` | Nikolai says a release that hands back a big over-reservation and lands on the ceiling "is not the event we're watching for", which is the decision not to increment. |
| `g10.r1.exclusions_or_crossover#6` | stated | `g10.r1.g10.r1.s4.l4` | Konrad's remark carries the exact scenario and figure — a settle that leaves us at +100 on a 1000 tracker — so the post-settlement capacity value is named in the corpus rather than inferred. |
| `g10.r1.exclusions_or_crossover#7` | stated | `g10.r1.g10.r1.s4.l4`, `g10.r1.rev2` | Konrad says a settle leaving +100 on a 1000 tracker "is not it either" and that it should only tick "when we actually stopped the fall", i.e. only when the debt floor is applied. |
| `g10.r1.observability#1` | stated | `g10.r1.g10.r1.s3.l1`, `g10.r1.rev2`, `g10.r1.g10.r1.s3.l2` | gideon says the tracker carries "a plain counter starting at 0" and dermot/emil name that counter num_capacity_debt_clamps, so the default value of the field is decided out loud. |
| `g10.r1.observability#2` | stated | `g10.r1.g10.r1.s3.l1`, `g10.r1.g10.r1.s4.l1`, `g10.r1.g10.r1.s4.l2`, `g10.r1.g10.r1.s4.l4` | the counter starts at 0 (gideon) and the whole s4 thread rules out ticking on refills capped at the limit, over-reservation releases and settles that stay positive — konrad: "It should only tick when  |
| `g10.r1.observability#3` | stated | `g10.r1.g10.r1.s3.l3`, `g10.r1.g10.r1.s3.l2`, `g10.r1.rev2` | dario answers dermot's double-count report with "one call one tick — whether it was a single axis sitting at the bottom or both of them clamped in the same settle, it still only counts once," which is |
| `g10.r1.observability#4` | stated | `g10.r1.g10.r1.s3.l3`, `g10.r1.rev2` | "one call one tick" plus emil's "counts each such call" fixes the per-call increment, so a second clamping call reaching 2 is the stated rule applied again rather than something the reader must work o |
| `g10.r1.rule#1` | stated | `g10.r1.g10.r1.s1.l4`, `g10.r1.rev1`, `g10.r1.rev2` | Konrad names the constant CAPACITY_DEBT_FLOOR_FRACTION, its home in capacity_budget.py, and its value 0.25 in a single remark, and rev1 repeats the name-value pairing. |
| `g10.r1.rule#2` | n/a | `g10.r1.clamp-at-zero-decision` | A positive 1000-minus-800 reading that is identical before and after the revision — the suite verifying its own tracker state before the step under test. |
| `g10.r1.rule#3` | stated | `g10.r1.rev1`, `g10.r1.rev2`, `g10.r1.g10.r1.s1.l3`, `g10.r1.g10.r1.s1.l2` | rev1 and rev2 both say capacity now goes negative and is floored per axis at -CAPACITY_DEBT_FLOOR_FRACTION * limit with 0.25, and nikolai independently fixes the depth at a quarter of the minute's all |
| `g10.r1.scope#1` | stated | `g10.r1.g10.r1.s2.l1`, `g10.r1.g10.r1.s2.l2` | nils says the row where the caller passed 0 "still has the 100k default standing behind it, so it isn't a special case", which is the decision that a 0 argument reads back as the 100_000 per-minute li |
| `g10.r1.scope#2` | n/a | `g10.r1.g10.r1.s1.l1` | This is the tracker's pre-existing starting state before any settle — the suite's own baseline for the contrast with the floored value, not anything the debt-floor change decides. |
| `g10.r1.scope#3` | stated | `g10.r1.rev1`, `g10.r1.rev2`, `g10.r1.g10.r1.s2.l2` | rev1 commits outright to "floored per axis at -CAPACITY_DEBT_FLOOR_FRACTION * limit, 0.25" and nils commits to the 100k limit behind a 0 argument, so -25000.0 is the composition of two decisions each  |
| `g10.r1.scope#4` | n/a | `g10.r1.g10.r1.s2.l1` | Positive per-axis capacity after ordinary usage is the fixture's pre-floor baseline; no remark supplies 300/400/700 and none needs to. |
| `g10.r1.scope#5` | stated | `g10.r1.rev1`, `g10.r1.g10.r1.s2.l1` | gideon names the bug of holding both halves against the input number when output's own limit is 500/minute, and rev1 settles the fix as a floor "per axis" at -0.25 * limit, so each axis bottoming at a |
| `g10.r1.scope#6` | stated | `g10.r1.g10.r1.s2.l3` | dermot reports settle doing arithmetic on a None for a model with no token ceiling and rules "no ceiling, nothing to take a share of, leave it be" — i.e. that axis gets no floor and stays None. |
| `g10.r1.scope#7` | **absent** | `g10.r1.g10.r1.s2.l3`, `g10.r1.g10.r1.s2.l4` | dermot's "leave it be" is about the token ceiling only and emil's request-bucket remark is about it going negative; nobody says a request axis with no limit reads back None. |
| `g10.r1.scope#8` | stated | `g10.r1.g10.r1.s2.l4` | emil names available_request_capacity directly and rules that since "we reserve exactly one slot per request, it can't overspend, so that one should never be under zero at all", which is exactly the n |
| `g10.r1.scope#9` | stated | `g10.r1.g10.r1.s2.l4` | emil's ruling on the request bucket is about the bucket itself, not about a mode, so it covers the separate-axis tracker's request capacity as well. |
| `g10.r2.exclusions_or_crossover#1` | n/a | `g10.r2.s4_l2`, `g10.r2.rev2` | This reads back the blocked estimate the suite itself constructed (and the input/total axes of _TokenUsage, which belong to another requirement); the 100-output booking is the only piece the corpus ha |
| `g10.r2.exclusions_or_crossover#2` | n/a | `g10.r2.s1_l2` | This is the pre-refund snapshot of the tracker the suite seeded (one slot spent, 1000 of 10000 tokens held), not a claim the failure-path code has to satisfy. |
| `g10.r2.exclusions_or_crossover#3` | stated | `g10.r2.s2_l2`, `g10.r2.rev1`, `g10.r2.rev2`, `g10.r2.s4_l3`, `g10.r2.s4_l2` | dermot says refund_capacity returns the entire token reservation rather than whatever was left unspent, rev1/rev2 say failure refunds the whole estimate via refund_capacity(blocked), and nils says on  |
| `g10.r2.exclusions_or_crossover#4` | stated | `g10.r2.rev1`, `g10.r2.rev2`, `g10.r2.s2_l4` | rev1 says failure refunds the estimate plus 1.0 slot back, rev2 says the slot returns on failure, and konrad says an errored call hands its slot back one per attempt. |
| `g10.r2.observability#1` | **implied** | `g10.r2.s5_l2`, `g10.r2.s5_l3` | Konrad names the two counters and Nikolai reports "the release counts sat at zero" during a run, but nobody says the counters are initialized to 0 — the reader supplies the conventional default for a  |
| `g10.r2.observability#2` | **implied** | `g10.r2.s5_l2`, `g10.r2.s5_l4` | Konrad frames both counters as telling apart "the two kinds of release" and Dermot's rule is about release calls, so a reader can infer acquisition ticks neither, but no remark says consuming leaves b |
| `g10.r2.observability#3` | stated | `g10.r2.s5_l2`, `g10.r2.s5_l4`, `g10.r2.rev1` | Konrad asks for num_capacity_settlements and num_capacity_refunds as separate counters for the two kinds of release, Dario's rev1 makes the success path the settlement (free_capacity(used, blocked)),  |
| `g10.r2.observability#4` | stated | `g10.r2.s5_l2`, `g10.r2.s5_l4`, `g10.r2.rev1` | The same separate-counters decision plus rev1 naming the failure path refund_capacity(blocked) makes a refund tick num_capacity_refunds only, which is exactly what the assertion checks. |
| `g10.r2.observability#5` | stated | `g10.r2.s5_l4`, `g10.r2.s5_l3` | Dermot says outright to count the call rather than whether it moved a number — a release against an unlimited axis goes through the same code path and still increments — which is the (1, 1) after one  |
| `g10.r2.observability#6` | **implied** | `g10.r2.s5_l4`, `g10.r2.s5_l3` | "No token ceiling set" and "unlimited axis ... whether it moved a number" point at the axis staying unlimited through a release, but nobody in this corpus says the tracker carries an attribute called  |
| `g10.r2.observability#7` | **implied** | `g10.r2.s5_l4` | Only Dermot's "unlimited axis" bears on it; the name available_request_capacity and its None value on an unlimited tracker are supplied by the reader, not by any remark. |
| `g10.r2.rule#1` | stated | `g10.r2.rev1`, `g10.r2.rev2`, `g10.r2.s2_l2` | rev1 names refund_capacity(blocked) and spells out its two effects — the whole estimate back plus a literal 1.0 slot — with rev2 and s2_l2 confirming the whole-reservation refund. |
| `g10.r2.rule#10` | **implied** | `g10.r2.s3_l3`, `g10.r2.s4_l1`, `g10.r2.rev1` | both halves are unstated — the token clamp at the limit and the processor helper's forwarding to status_tracker.refund_capacity. |
| `g10.r2.rule#2` | stated | `g10.r2.s2_l4`, `g10.r2.rev1` | konrad says the errored call's slot goes back one per attempt and "never above what the minute started with", which is the request-axis clamp at the per-minute maximum. |
| `g10.r2.rule#3` | **implied** | `g10.r2.s4_l1`, `g10.r2.s4_l3`, `g10.r2.s2_l4` | s4_l1 reports a bucket finishing above the limit but s4_l2/s4_l3 resolve it by refunding the booking instead of the reported usage, so the reader is left to supply a token-axis clamp nobody asked for. |
| `g10.r2.rule#4` | stated | `g10.r2.s2_l4`, `g10.r2.rev1` | same clamp on available_request_capacity that s2_l4 states directly — one slot per attempt, never above the minute's starting ceiling. |
| `g10.r2.rule#5` | **implied** | `g10.r2.s4_l1`, `g10.r2.s4_l3` | the only remark about exceeding the token limit is a symptom whose stated cure is refunding the estimate rather than reported usage; the reader must invent the min-against-limit themselves. |
| `g10.r2.rule#6` | stated | `g10.r2.s1_l2`, `g10.r2.rev1` | dario says a clean response puts back only "the gap between what we booked and what it actually spent", and rev1 attaches that to free_capacity(used, blocked). |
| `g10.r2.rule#7` | stated | `g10.r2.rev1`, `g10.r2.rev2`, `g10.r2.s1_l4`, `g10.r2.s1_l3` | rev1 says on success the slot stays spent and rev2 that the slot returns on failure only, with s1_l3/s1_l4 giving the 240-in-a-200-minute reason. |
| `g10.r2.rule#8` | **implied** | `g10.r2.s3_l3`, `g10.r2.rev1`, `g10.r2.h1` | s3_l3 names _refund_capacity as the thing that should fire on giving up and rev1 names the tracker's refund_capacity(blocked), but nobody says the processor method delegates to the tracker's or what a |
| `g10.r2.rule#9` | **implied** | `g10.r2.s3_l3`, `g10.r2.s2_l4`, `g10.r2.rev1` | the request-slot clamp is stated, but reaching it through a processor-level _refund_capacity that forwards to the tracker is a delegation nobody describes. |
| `g10.r2.scope#1` | n/a | — | This is the suite's own pre-state check that the fixture's reservation of input=700/output=300 was booked (1.0 slot, 1000 tokens) before either branch runs; the reservation arithmetic is the setup thi |
| `g10.r2.scope#2` | stated | `g10.r2.s3_l3`, `g10.r2.rev1`, `g10.r2.s2_l4`, `g10.r2.s3_l2` | s3_l3 says _refund_capacity should fire at the point we give up on a request entirely and nothing calls it there, rev1 says failure refunds estimate plus 1.0 slot back, and s2_l4 caps the slot return  |
| `g10.r2.scope#3` | stated | `g10.r2.s2_l2`, `g10.r2.s3_l3`, `g10.r2.s3_l2`, `g10.r2.rev1` | s2_l2 says an errored attempt returns the entire token reservation rather than whatever was left unspent, and s3_l3/s3_l2 put that refund on the give-up branch, so the 1000-token booking comes back wh |
| `g10.r2.scope#4` | n/a | `g10.r2.s3_l2` | A branch-taken sanity check on the retry loop's existing attempts_left decrement, which the suite sets up and no remark is being asked to specify. |
| `g10.r2.scope#5` | stated | `g10.r2.s2_l4`, `g10.r2.rev1`, `g10.r2.s2_l3` | s2_l4 says outright that an errored call hands its slot back, one per attempt, never above the minute's starting figure, and rev1 repeats the 1.0 slot on the failure path. |
| `g10.r2.scope#6` | stated | `g10.r2.s3_l4`, `g10.r2.s2_l2`, `g10.r2.s3_l1`, `g10.r2.rev1` | s3_l4 says holding the old booking against a requeued request charges the budget twice since it gets estimated again, and s2_l2 fixes the refund at the entire reservation, giving the full 10000.0. |
| `g10.r2.scope#7` | stated | `g10.r2.rev1`, `g10.r2.s1_l3`, `g10.r2.s1_l4` | rev1 says in as many words that on success the slot stays spent, with s1_l3/s1_l4 giving the reason (a request that reached the provider does not un-happen), so the tracker sits at 59.0. |
| `g10.r2.scope#8` | stated | `g10.r2.s1_l2`, `g10.r2.rev1`, `g10.r2.s1_l1` | s1_l2 says on a clean response the only thing returned is the gap between the booking and actual spend, and rev1 names the success call as free_capacity(used, blocked): 1000 booked minus 800 reported  |

### `g10.r1.exclusions_or_crossover#2` — implied

```python
assert refilled.available_request_capacity == 60.0
```

Every cap remark is about the token/per-minute allowance; nobody says the request axis has its own ceiling it refills up to, so the reader has to generalise the token-side cap to available_request_capacity on their own.

### `g10.r1.exclusions_or_crossover#4` — implied

```python
assert released.available_token_capacity == 1000.0     # capped, not 1800.0
```

Nikolai's remark is aimed at the counter, and only describes in passing that a big over-reservation "puts us right on the ceiling"; the reader is left to supply that release itself clamps down to max_tokens_per_minute instead of adding through to 1800.

### `g10.r1.scope#7` — absent

```python
assert unlimited.available_request_capacity is None
```

dermot's "leave it be" is about the token ceiling only and emil's request-bucket remark is about it going negative; nobody says a request axis with no limit reads back None.

### `g10.r2.observability#1` — implied

```python
assert (settlements(settled), refunds(settled)) == (0, 0)
```

Konrad names the two counters and Nikolai reports "the release counts sat at zero" during a run, but nobody says the counters are initialized to 0 — the reader supplies the conventional default for a `num_*` field.

### `g10.r2.observability#2` — implied

```python
assert (settlements(settled), refunds(settled)) == (0, 0)   # consuming counts as neither
```

Konrad frames both counters as telling apart "the two kinds of release" and Dermot's rule is about release calls, so a reader can infer acquisition ticks neither, but no remark says consuming leaves both counters untouched.

### `g10.r2.observability#6` — implied

```python
assert unlimited.available_token_capacity is None
```

"No token ceiling set" and "unlimited axis ... whether it moved a number" point at the axis staying unlimited through a release, but nobody in this corpus says the tracker carries an attribute called available_token_capacity, let alone that it holds None.

### `g10.r2.observability#7` — implied

```python
assert unlimited.available_request_capacity is None
```

Only Dermot's "unlimited axis" bears on it; the name available_request_capacity and its None value on an unlimited tracker are supplied by the reader, not by any remark.

### `g10.r2.rule#10` — implied

```python
assert delegated.available_token_capacity == 10000.0
```

both halves are unstated — the token clamp at the limit and the processor helper's forwarding to status_tracker.refund_capacity.

### `g10.r2.rule#3` — implied

```python
assert refunded.available_token_capacity == 10000.0
```

s4_l1 reports a bucket finishing above the limit but s4_l2/s4_l3 resolve it by refunding the booking instead of the reported usage, so the reader is left to supply a token-axis clamp nobody asked for.

### `g10.r2.rule#5` — implied

```python
assert refunded.available_token_capacity == 10000.0
```

the only remark about exceeding the token limit is a symptom whose stated cure is refunding the estimate rather than reported usage; the reader must invent the min-against-limit themselves.

### `g10.r2.rule#8` — implied

```python
assert (delegated.available_request_capacity, delegated.available_token_capacity) == (59.0, 9200.0)
```

s3_l3 names _refund_capacity as the thing that should fire on giving up and rev1 names the tracker's refund_capacity(blocked), but nobody says the processor method delegates to the tracker's or what arguments it takes — that shape is borrowed by analogy from h1, a remark rev1 overturns.

### `g10.r2.rule#9` — implied

```python
assert delegated.available_request_capacity == 60.0
```

the request-slot clamp is stated, but reaching it through a processor-level _refund_capacity that forwards to the tracker is a delegation nobody describes.
