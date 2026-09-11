# g11 run 7 (79ffaf93) — reward 0.8889

## What this run found

This is a strong, thorough run: it cloned the repo, read every Gitea issue/PR comment (738,
paginated), fetched **both** copies of every BookStack page plus their comments (correctly
diagnosing that search doesn't index comments and going after the raw pages instead), dumped the
entire admin IMAP mailbox (index and full bodies), and then dumped all ~10k Mattermost posts to
local files it could grep repeatedly. Wiki and mail turned out to hold nothing on the ledger; the
whole hidden record lived in chat, and the agent found the overwhelming majority of it: 38 of 43
non-herring remarks (all 26 of `g11.r1`'s clues/reversals, 17 of 21 of `g11.r2`'s), plus both
herrings for each requirement. Its running self-summaries (e.g. transcript line 5476) show it
correctly assembling the full parked design — `CHECKPOINT_REASONS`, `canonical_reasons`,
`CHECKPOINT_NAME_TEMPLATE`, the same-name-replaces-last-row merge rule, `epoch_of_batch` for the
checkpoint epoch, and the `min_lr_ratio`/`MIN_LR_RATIO` decay floor — and it shipped essentially
all of it. `g11.r1` scored 5/5 and `g11.r2` scored 3/4.

## What it missed, and why

The one lost fact is `g11.r2.failure_behavior` (warmup longer than the run must be *clipped* to
the run length, not left uncapped). The failing assertion shows exactly what happened: for
`warmup_steps=10, total_steps=3` the shipped code returns `[1e-05, 2e-05, 3e-05]` — i.e.
`base_lr * step / warmup_steps` using the *uncapped* `warmup_steps=10` — instead of the required
`[3.33e-05, 6.67e-05, 1e-04]`, which needs `effective_warmup = min(warmup_steps, total_steps)`.

That fix is stated in exactly one place: `g11.r2.rev2` (#general, 2025-06-02, konrad: "...that's
the bit thats going... `1 <= step <= effective_warmup`... `effective_warmup = min(warmup_steps,
total_steps)`... clipped, not raising"). Two other remarks also carry this fact — `g11.r2.l12`
(#general, 04-29, "crept along all three and never got near base_lr") and `g11.r2.l13` (#viewer,
06-02, the explicit `warmup=10/total=3` and `warmup=99/total=1` test cases). None of the three was
ever surfaced: a grep of the whole transcript for their distinctive phrases (`effective_warmup`,
`1 <= step <=`, `crept along all three`, `warmup 99`, `no exeption`) returns nothing. `#general`
(273 lines) was touched exactly once, by a narrow `grep -n '2025-04-07T13:[45]' /tmp/chat2/general.txt`
(line 4798/4826) anchored to an already-found, unrelated clue — never dumped whole, never searched
for later dates. `#viewer`'s June content was likewise never opened. One broad grep
(`floor|min_lr|10%|tenth|never goes below|bottom`, line 3951) could plausibly have caught rev2's
"bottoms out at a tenth of base_lr" phrasing, but it was piped through `head -20` and returned only
`help.txt`/`incidents.txt`/`code-review.txt` hits before truncating — general.txt's position in the
recursive listing meant it was never reached.

## What it believed, and why

The agent saw both `g11.r2` herrings early (line 3547–3586, 3619–3626) and recorded them as
"confirmed" (line 3640: "LR schedule confirmed: warmup strict `step < warmup_steps`; linear decay
to exactly 0.0 at total_steps"). It later found `g11.r2.rev1` and correctly revised the *decay*
half — dropping decay-to-zero for the `min_lr_ratio` floor (line 4048). It never revised the
*warmup-compare* half, because that correction lives only in `g11.r2.rev2`, which it never saw.
The shipped `learning_rate_at` (transcript lines 5894–5930) still uses the strict, uncapped
`if warmup_steps > 0 and step < warmup_steps` — verbatim herring behavior — while the floor logic
right below it is fully correct. This split outcome (one half of a herring pair reversed, the
other shipped as-is) is the direct cause of the lost fact, and it is invisible everywhere except
the one test that pins `warmup_steps > total_steps`: for every in-range case, `step==warmup_steps`
lands on `base_lr` under both the strict-decay-branch and the inclusive-ramp-branch formulas, so
`g11.r2.rule`/`observability`/`exclusions_or_crossover` all still scored 1 despite the wrong
condition underneath.

## Notable

The world this run played against was v11, which rewrote `g11.r2.rev2`'s wording (adding "...the
end doesnt sit at zero any more, it bottoms out at a tenth of base_lr and holds there, and a first
step at rate 0 is not something i want to keep defending"); the checked-in answer key still shows
the older text. This is moot for grading this run, since the transcript shows `#general` was never
read for any 2025-06-02 content under either wording.
