# g10 run 2 (b0a5402b) eval 5b468409 — reward 1

## What it found

This run scored a clean 1.0 across all 8 graded facts. Its search was unusually
exhaustive for all four surfaces the world offers: it read the four relevant
source files whole before touching any corpus (lines 440-2120), paginated and
grepped all ~400+ Gitea issues (lines 2130-2549, surfacing the parked design in
issue #401), did a **complete** BookStack dump of all 228 pages **including
comments** (lines 2561-2965 — correctly sidestepping the documented trap that
`/api/search` does not index comments), and dumped the **entire** IMAP mailbox
(107 messages, lines 3093-3109). Wiki and mail both came back empty for the
capacity-budget design, which matches the answer key: all 46 remarks live in
chat only, so this is a correct negative rather than a missed search. Chat
itself was worked hard: full per-channel dumps to local files for at least
nine channels, then repeated rounds of broad grep (`refund|settlement`,
`reserve|acquire|booking`, `header_based|apply_rate_limit`) interleaved with
direct `sed`-range reads of the surrounding exchange whenever a hit landed
mid-conversation. That interleaving is why the mechanical pointer sheet
undercounts what the agent actually saw — many facts trace to a channel
window the agent read in full around a grep hit, not to the hit phrase itself.

The two reversal remarks did almost all of the heavy lifting. `g10.r1.rev1`
(#pipeline, line 3667) and `g10.r2.rev1` (#incidents, line 4035) each restate
their whole requirement in one exchange — constant name, value, and the shape
of the design change — and the agent's own Analysis text (lines 4211, 4109)
shows it building its implementation plan directly off those two exchanges.
Both herrings for both requirements were explicitly recognized as superseded
("that's the old plan and its dead", line 4184 embedded in the rev2 read) and
neither made it into the shipped code: `free_capacity` never clamps at 0.0,
and failure and success settle through two separate operations exactly as the
reversals specify.

## What it missed and why it didn't cost anything

Fifteen of the 46 remarks never surfaced at all — grepped for by distinctive
phrase across the full transcript and confirmed absent (`g10.r1.clamp-at-zero-rationale`'s
own posting and `g10.r2.h2`'s own posting were each seen only second-hand,
quoted back inside their reversal; `g10.r1.g10.r1.s1.l1/l3`, `s2.l1/l3`,
`s4.l1`, `g10.r2.s1_l3/l4`, `s2_l1/l3/l4`, `s3_l1/l2`, `say24`). None of these
cost a fact, because every subconclusion the plant spreads across 3-4 remarks
had at least one other carrier the agent did read, and the two reversals
independently restate almost everything anyway. `say24` (`available_token_capacity`
stays `None` forever on an unlimited tracker) is the cleanest case: the exact
text never appears anywhere in the corpus reads, but the ticket's own
`__post_init__` spec text states the same rule directly, so the agent shipped
it correctly from first principles rather than from a remark — a legitimate
"ticket" attribution, not a false credit.

## Verdict

Nothing to diagnose: every fact passed, the implementation matches the answer
key's `rule`/`scope`/`exclusions_or_crossover`/`observability` text closely
(debt floor at exactly `-CAPACITY_DEBT_FLOOR_FRACTION * limit`, one-clamp-per-call
counting, `refund_capacity` clamped and unconditionally incrementing its own
counter, settlement and refund kept as two separate operations that never
touch each other's counter), and the run ended with a real merge, green CI,
and a confirmed deploy (merge commit `8cfeaff`, Gitea Actions run success,
65 new tests passing).
