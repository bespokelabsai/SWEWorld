# The overnight loop

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
in `_suites/bracket_matrix.txt`, never reverted to keep a number alive.

`run.sh` passes `CLAUDE_CODE_OAUTH_TOKEN` and nothing else. `ANTHROPIC_API_KEY`
lives in `.env` for phase-3 one-shots and must not reach an agent turn.
