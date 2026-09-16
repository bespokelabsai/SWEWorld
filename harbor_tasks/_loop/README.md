# The overnight loop

> **Historical.** The loop below ran the hand-written `t1`–`t4` groups, which have
> since moved to `failed_tasks/`. `run.sh` resolves its task as
> `harbor_tasks/$GROUP/$VARIANT`, so it cannot launch them from there — what
> still uses `run.sh` is `task_generator/tg/trial.py`, against the `g*` groups.
> For how tasks are built and run now, see
> [`task_generator/README.md`](../../task_generator/README.md) and
> [`harbor_tasks/README.md`](../README.md). The spec-must-reach-1.0 discipline
> described here still holds; the task list does not.

Per task, in order t1 → t2 → t3 → t4:

1. Run `<slug>-spec` — the arm with both hidden requirements written into the
   ticket. **It must reach 1.0.** An agent handed the requirement verbatim and
   failing is evidence about the tests, not the agent.
2. When it does not, read every failure and classify it:
   - **bad test** — it fails an implementation that plausibly follows the
     requirement as written. Fix the test, re-run. This is the common case and
     the whole point of the loop.
   - **genuine gap** — no reading of the requirement makes the implementation
     correct. Record it and stop looping this task; more attempts only buy
     agent variance.
3. Once spec passes, run `<slug>` — the blind arm — **once**, to confirm the
   same tests still fail the hidden facts without the corpus. A hidden fact the
   blind arm passes is a coincidence, recorded as such rather than tuned away.
4. Advance.

Bounded at `max_spec_attempts` per task so one stubborn task cannot consume the
night. A run is ~20 minutes and ~$9 of subscription usage.

Before every re-run the bracket is re-checked in `devbox`: **oracle must still
pass every test** (a fix that breaks satisfiability is worse than the bug) and
pristine must still fail. Fixes that make a fact non-discriminating are recorded
in `failed_tasks/_suites/bracket_matrix.txt`, never reverted to keep a number alive.

`run.sh` passes the agent `CLAUDE_CODE_OAUTH_TOKEN` and sets `CLAUDE_FORCE_OAUTH=1`,
and unsets `ANTHROPIC_API_KEY` after sourcing `.env`. Naming only the token was not
enough: harbor's claude-code adapter reads the key from its own environment and the
CLI prefers it, so the first t12 trial billed the key with the subscription token
sitting unused beside it. `ANTHROPIC_API_KEY` lives in `.env` for phase-3 one-shots
and must not reach an agent turn. `USE_PERSONAL_TOKEN=1` opts into a second
subscription, swapping `CLAUDE_CODE_PERSONAL_OAUTH_TOKEN` in as the OAuth token
(refused with exit 5 if that is not in `.env`), so a day of trials does not lock
interactive work out of the default account's session limit.
