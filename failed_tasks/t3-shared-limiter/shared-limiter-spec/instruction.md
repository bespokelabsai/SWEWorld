You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Rate limiter shared across chained LLM blocks**

Support passing an existing rate limiter instance between two `curator.LLM` blocks in a pipeline (e.g. TopicGenerator -> Poet) so they share the same requests-per-minute budget instead of each block getting its own independent limiter.

## Requirements settled earlier

These were agreed before the ticket was written. They are not obvious from the code, so they are repeated here in full:

1.
   - *rule*: When a shared limiter is passed, the second block in the chain must NOT re-initialize `max_requests_per_minute` / `max_tokens_per_minute` from its own `backend_params`; those values must be ignored in favor of the shared limiter's configuration.
   - *scope*: Only applies when a limiter object (not raw numbers) is explicitly passed into `backend_params`.
   - *exclusions or crossover*: If no shared limiter is passed, each block must continue to build its own independent limiter from its own backend_params exactly as before.

2.
   - *rule*: The shared limiter must track token and request budgets per-process, and must be reset (not reused) between two separate top-level pipeline invocations run back-to-back in the same Python process.
   - *scope*: Applies to reuse of the same limiter object across multiple `.__call__()` invocations of the pipeline.
   - *failure behavior*: If the limiter is not reset and a second invocation starts while budget already appears exhausted from the first, it must raise a clear error rather than silently stalling forever.
   - *observability*: A `.remaining_budget()` accessor must be available on the limiter for the pipeline to log at the start of each invocation.

## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
