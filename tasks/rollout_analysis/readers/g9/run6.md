# g9 run 6 (e26f06c1) — reward 0.8571

## What this run found

This is a strong run: 6 of 7 hidden facts scored, and the miss is a single,
well-explained failure. The agent's search strategy was systematic and
mechanical rather than exploratory — it dumped every Mattermost channel to
local text files (`/tmp/mm/world__<channel>.txt`) and every one of the 239
BookStack pages (with comments) to `/tmp/wj/` (transcript line 1552-1883),
then re-grepped those local dumps repeatedly for topic keywords
(`window_start`, `last_report`, `EncodingReport`, `dropped_indices`,
`marker`/`truncated`, etc.). It read every one of the 13 mail-carried
remarks via Roundcube/IMAP. This bulk-dump-then-grep pattern is why it
recovered both members of each herring/reversal pair for `g9.r1` in a
*single* grep pass (lines 3527-3553): the same wide query that surfaced the
January herrings (`g9.r1.h1`, `g9.r1.h2`) also surfaced their April
reversals (`g9.r1.rev1`, `g9.r1.rev2`), so the agent read the whole arc at
once and correctly implemented the 16-retained-prompt-token floor rather
than the binary "windowed at all → refuse" rule. The same happened for the
`g9.r2` tuple-return herrings (`g9-tuple-return-1/2`) and their reversals
(`rev1`, `rev2`) in the `#releases`/`#cookbooks` dumps (lines 3702-3851):
`format_batch` correctly returns a plain list with counts living on
`self.last_report`, not a `(data, report)` tuple.

## What it missed, and why

`g9.r2.failure_behavior` scored 0. The grader's failing assertion is in
`test_failure_behavior__bad_roles_and_a_bad_tokenizer_abort_the_batch_and_write_no_report`:
`format_batch` given a batch containing one row with an invalid role
sequence should raise `InvalidRoleSequenceError` and leave `last_report`
untouched. The shipped code (transcript line 7314) instead does:

```python
except (InvalidRoleSequenceError, ExampleTooLongError) as row_error:
    dropped_indices.append(index)
```

silently binning a bad-role-sequence row as a drop, exactly like an
over-long example. This is `implementation_slip`-adjacent but is really a
`herring_followed`: the agent's own Analysis at line 7279 ("bin row-level
failures (invalid role sequence, too long) ... let tokenizer-capability
failures propagate") traces straight back to a herring it read and believed
— `g9.r2.h-role-row`, a May 28 mail reply from dario: *"Length and role
sequence are row problems — one bad row says nothing about the next row, so
those get counted and skipped."* The agent absorbed this as settled fact at
lines 5712 and 6432 and never revisited it.

The reversal exists — `g9.r2.rev3`, dario, June 17: *"and yes this is me
contradicting myself - the split i gave on the 653 thread back in may,
length and role sequence both being row problems, that half of it was
wrong ... only the over-long ones are row problems"* — along with its
companion clue `g9.r2.l17` ("if the role sequence is bad thats my data
being broken, not a row to quietly skip"). Both live as **comments** on
wiki page `docs/engineering/request-builder-what-we-drop-and-what-we-raise-on.md`.
That page was fetched into the agent's own local wiki dump (`/tmp/wj`,
239 files, built at line 1552-1883) but its title gave no hint it corrected
a mail thread the agent had already "settled," so it was never opened —
the page appears exactly once in the whole 10,803-line transcript, in the
raw title index at line 1373. No later keyword grep against `/tmp/wj` (for
"role sequence," "InvalidRoleSequenceError," or similar) was ever run, even
though the data was sitting on disk the whole time. The agent's own 138-test
local suite also never exercised `format_batch` on a mixed batch with a
bad-role-sequence row, so nothing caught the bug before push.

Six other `g9.r2.failure_behavior` clues were read correctly and *were*
followed — `g9.r2.l19` (the detailed abort-path mail review, whose
"accumulate into locals, assign once" mechanism the shipped code does
implement for the `ExampleTooLongError`/success path) and `g9.r2.say24`
(TokenizerCapabilityError correctly propagates and leaves `last_report`
untouched). The fact still failed because the InvalidRoleSequenceError half
of the rule was governed by the herring, not by any of those.

## Coverage of the other 39 not-found remarks

Roughly a dozen chat and wiki-comment remarks besides the lost-fact pair
were never surfaced (e.g. `g9.r1.l-rule-3`, `l-fail-4`, `l-fw-4`, `l-fail-1`,
`g9.r2.l16`, `l11`, `l8`, `l5`; wiki page `l-fw-2`; chat `l-scope-2`,
`fix28`). All of these are redundant — each fact they carry was already
established through other, found remarks — so none of them affected the
scored facts. One remark, `g9.r1.say24`, is worth flagging as a partial:
its literal wiki *comment* was never read, but the page *body* of
`docs/engineering/local-offline-inference-...md` (read at lines 1883-1990)
independently states the same fact in near-identical wording ("0 through 8
for the Hello pair ... model_input is the first eight of them"), so the
fact was covered by proxy through an unusual body/comment duplication in
this particular page.

## Bottom line

One lost fact, one clean cause: `g9.r2.h-role-row` (herring, found and
believed) vs. `g9.r2.rev3`/`g9.r2.l17` (reversal, never found because the
one wiki page carrying it was dumped but not read). Classified
`herring_followed`.
