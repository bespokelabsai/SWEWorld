# g10 run 3 (35e26f76) — reward 1, all 8 facts pass

## What this run found

The agent worked outward from the code before touching any external source: it read
`online_status_tracker.py` and `base_online_request_processor.py` in full first (lines
430–1951), then systematically exhausted every other source in the world — Gitea issues/PRs
across multiple pages, all 227 BookStack wiki pages dumped with their comments, the entire
107-message mailbox pulled over raw IMAP — before finally reaching Mattermost. None of the
pre-chat sources held anything (consistent with the answer key: all 46 remarks are chat-only).
Once in chat, rather than relying only on the live search endpoint, it dumped the full post
history of every one of the 11 channels (10,997 lines) to local files and ran repeated
`grep -n` sweeps with surrounding context, reading each matched window in full. This is why
the run recovered so much of the design even though only 26 of 46 individual remarks were
literally re-displayed on a terminal screen the agent quoted from: reading a 20–60-line window
around one grep hit routinely swept in 2–3 neighbouring, un-grepped remarks from the same
MuSR subconclusion, since leaves tend to cluster tightly in time and channel.

Both r1 requirements' full designs were reconstructed early (lines 3620–4220): the
`CAPACITY_DEBT_FLOOR_FRACTION = 0.25` debt floor and its "one call, one tick" counter
semantics for r1, and the settle-vs-refund split plus the three separate counters for r2. The
final shipped code (recovered from the full rollout JSON, message 211/cap_c.txt) is an exact
match to every graded fact: `_debt_floor`/`_settle_axis` implement the per-axis
`-0.25 × limit` floor and only tick `num_capacity_debt_clamps` once per call regardless of how
many axes clamped; `refund_capacity` clamps every axis above at the limit via `min(...)` and
restores the 1.0 request slot; a single `_refund_capacity` call was moved to run after both the
requeued and exhausted branches of the retry handler, and it always hands back the original
`blocked` reservation, never `generic_response.token_usage`.

## What it missed and why

17 of 46 remarks were never literally displayed in any terminal screen (verified independently
by grepping the transcript for each remark's distinctive phrasing, not just trusting the
pointer sheet). None of these losses mattered for scoring: every MuSR subconclusion had
redundant leaves, and in every single case where a leaf was missed, a sibling leaf carrying the
identical fact for that subconclusion *was* found and read in full elsewhere — e.g. r1.s4
("topping out isn't a clamp") lost `s4.l2` but kept `s4.l1`, `s4.l3` and `s4.l4`; r2.s1 lost
three of its four leaves but the shipped design is fully specified by `rev1` alone. Three more
remarks (`g10.r2.s1_l1`, `g10.r2.s2_l3`, `g10.r2.s3_l2`) were "partial" finds — the grepped
terminal window happened to cut an 8-line exchange short or land slightly off-center — but
again the underlying fact was independently covered by a sibling leaf.

One correction to the pointer sheet: it marks `g10.r2.h1` as found at step 9/line 1501, but
that hit is a false positive — the matched text is the agent reading the *original,
unmodified* `base_online_request_processor.py` during initial code exploration
(`self._free_capacity(status_tracker, used_tokens, blocked_capacity)`), before any chat search
had even begun. The herring's actual dialogue never appears anywhere in the transcript.

## What it believed and why

All four herrings were correctly identified and rejected, and the agent's final code follows
none of them. Notably, three of the four herrings (`g10.r1.clamp-at-zero-decision`,
`g10.r1.clamp-at-zero-rationale`, `g10.r2.h1`) were themselves never read directly at all —
the agent learned what the team "used to believe" only secondhand, because each reversal's
dialogue explicitly recaps the old (wrong) decision before stating the fix ("that was the
review call last year... and its gone", "0.0 isnt the floor anymore... I wrote the
0.0-is-empty line in 387", "we settled this months ago, one `_free_capacity`... for both
outcomes... thats the half thats gone"). Only `g10.r2.h2` was read as a standalone message
(releases.txt, lines 5596–5603), and the agent explicitly flagged it in its own analysis as
"the OLD plan... explicitly declared dead on Apr 3" once it found the reversal. In every case
the agent's belief settled on the reversal, matching what actually shipped.

## Why nothing was lost

Reward is 1 and every fact scored 1, so `lost_facts` is empty. The eight `passed_facts` entries
each cite the specific remark(s) the agent's own Analysis text relied on and the corresponding
line of shipped code that implements it — see the JSON for the full mapping. The run's final
turns (lines 9500–9739) show the agent re-verifying, before marking the task complete, that
commit `4da9940` is the head of `main`, CI run 14 is green, both `current` and `last-good`
release symlinks point at the new release with no rollback, 57 new tests pass, and `ruff` is
clean — a thorough close-out matching the thoroughness of its research.
