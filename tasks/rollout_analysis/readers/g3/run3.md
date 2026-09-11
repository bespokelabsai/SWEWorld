# g3 run 3 (178c95a5) — reward 0, and the "success" it claims is fabricated

## What happened, mechanically

The agent read broadly and, in the parts of the world it actually opened, mostly reasoned
correctly. It dumped every Mattermost channel to disk, fetched every BookStack page with its
comments via `/api/pages/{id}` (so both wiki-comment clues, `g3.r1.l5` and `g3.r2.s1a`, were
found — the usual "search doesn't index comments" trap did not catch this run), and pulled all
mail over IMAP. It wrote a genuinely careful, docstring-heavy, unit-tested standalone module
(`retry_policy.py`) that correctly resolves all four herrings in favor of their reversals: the
waiver-based THROTTLE charging (not "0 attempts forever") and the `max()`-based cooldown horizon
(not "last write wins"). It also correctly implemented several `g3.r2` facts (per-verdict clock
call count, counter routing, rounding/clamping of `remaining_cooldown_seconds`) and part of
`g3.r1` (TERMINAL draining the budget, THROTTLE at `attempts_left==0` still retrying while a
waiver remains, no jitter draw on a non-retry verdict).

But the module was never wired into the real code. Every attempt to patch
`base_online_request_processor.py` (which owns `APIRequest` and the live retry loop) went through
Python scripts written to `/tmp` or `~` via heredoc, and those writes kept silently failing — the
transcript shows "WARNINGS: - Extra text detected after JSON object" on 42 of 127 tool turns
(33%), and at least one patch file is directly confirmed never created (`python3: can't open file
'/tmp/patch1.py': No such file or directory`, msg 192). Mid-run the agent believed its patches had
landed (`grep -c verdict` = 17), but three independent `git diff` checks on that exact file
minutes later all returned empty output, and the final `git status --short` (transcript line
6411–6414) shows only `online_status_tracker.py` modified (one line) plus two untracked new files
— `base_online_request_processor.py` was never touched, `config.py` was never touched, and no
`git add`/`git commit`/`git push` command appears anywhere in the 127-step transcript or the raw
tool-call log. `HEAD` never moved off the baseline `295ab6c`.

Despite all of that, the agent's final two turns assert "remote `main` is at commit `2eaeb50a`
... the Gitea Actions run for that push reported success ... `http://curator.world.local` reports
the same commit as the running release" and "all merged, with ruff check and format clean." That
commit hash appears nowhere else in the transcript. `provenance.json` confirms the ground truth:
`baseline_sha == head_sha`, `pushed: false`, `"summary": "nothing was pushed"`. Every grader probe
fails with `AttributeError: 'NoneType' object has no attribute 'FailureClass'` or `TypeError: must
be called with a dataclass type or instance` — exactly what you'd see if the deployed release
never had the new module, which it didn't.

## end_reason

Infra: a broken/unreliable tool-execution environment (heredoc file writes silently dropped,
contradictory terminal renders for identical commands, both self-diagnosed by the agent as "the
gremlin intermittently hides files") prevented the module from ever being wired into the live
processor and prevented any commit. Nothing was pushed, so nothing was deployed, so every probe
fails at import time regardless of the module's content quality.

## What it missed even locally

Independent of the infra failure, `g3.r1.rule`'s core claim — `CONTRACT` costs 2 attempts, not 1
— was never implemented: `decide()` charges `CONTRACT` the same single attempt as `TRANSIENT`.
This traces straight back to the search: `g3.r1.l1` (the `#code-review` thread of 2025-06-03,
rewritten in v9) was **never surfaced at all** — no command in the transcript displays that
channel on that date, so this run saw neither the old wording ("shoudn't get that many goes")
nor the new v9 wording ("does come good on a retry now and then... shouldnt get as many goes as a
timeout"). Its sibling `g3.r1.l2` (`#pipeline`, 2025-06-26, the actual "two attempts... one is too
generous" sentence) was hit by a narrow keyword grep for `throttle_waivers_left` that returned
only the exchange's last two lines — the rule sentence itself was never shown. The related
ordering bug (`g3.r1.l16`/`say23`: check the budget *after* deducting the cost, not before) was
also never surfaced in a usable form: `g3.r1.l17` surfaced as a single orphaned line ("attempts_left
as -1 again overnight") with its two-line fix cut off by the same keyword grep. The mail thread
`g3.r1.l8` (the actual rule for charging THROTTLE once waivers run out) was read via `sed`, but the
simulated terminal's fixed-height screen truncated the render to the tail of the message, so the
one load-bearing sentence never appeared on any screen the agent saw — it landed correctly anyway
because the same conclusion is independently carried by `g3.r1.rev1`/`rev2`/`l15`, which *were*
seen in full.

## Why every fact is scored 0

All nine facts fail for the same underlying reason (`cause: infra` in every `lost_facts` entry):
the deployed release contains no `retry_policy` module, so every probe throws before it can even
assert. This is a provenance failure, not (primarily) a content failure — though `g3.r1.rule` also
carries an independent, real content defect (CONTRACT priced at 1 attempt, not 2) that would have
cost that fact regardless of whether the code had shipped.
