You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Batch mode cost estimate before submission**

When `batch=True` is passed to `curator.LLM`, add a pre-flight step that prints an estimated cost for the batch job before any requests are submitted to the provider.

## Requirements settled earlier

These were agreed before the ticket was written. They are not obvious from the code, so they are repeated here in full:

1.
   - *rule*: The discount factor applied to the estimate must be provider-specific: 50% off standard per-token pricing for OpenAI and Anthropic batch, but the discount must NOT be applied for any provider routed through the `litellm` backend, since litellm does not expose a distinct batch pricing tier in this codebase.
   - *scope*: Only the batch cost pre-flight estimator; does not change actual billing.
   - *exclusions or crossover*: litellm-backed models must show the standard (non-discounted) per-token estimate even when batch=True is set on them.

2.
   - *rule*: The estimate must be computed from a sample of the first N rows (not the full dataset) when the dataset exceeds a size threshold, to avoid iterating the entire dataset just to print an estimate.
   - *scope*: Applies whenever the input dataset length exceeds the threshold; below it, use every row.
   - *failure behavior*: If prompt() raises on any sampled row while estimating, skip that row from the estimate silently rather than aborting the whole pre-flight step.
   - *observability*: The printed estimate must state whether it was computed from a full pass or a sample, and the sample size used.

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
