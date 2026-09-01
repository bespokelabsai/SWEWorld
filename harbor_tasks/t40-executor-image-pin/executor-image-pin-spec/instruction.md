You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Docker code executor image pinning**

Pin the Docker image used by the Docker backend of `CodeExecutor` to a specific tag rather than `latest`, and allow callers to override it via `backend_params`.

## Requirements settled earlier

These were agreed before the ticket was written. They are not obvious from the code, so they are repeated here in full:

1.
   - *rule*: The default image tag must be pinned to a specific version string maintained in project documentation (not derivable from the code alone), and this task must update the code to reference that pinned tag instead of `latest`.
   - *scope*: Default Docker image tag.

2.
   - *rule*: When a caller overrides the image via `backend_params={'image': ...}`, the executor must still enforce the same non-root user and read-only filesystem mount constraints applied to the default pinned image — an overridden image must not be allowed to run as root inside the container even if the custom image's own Dockerfile defaults to root.
   - *scope*: Security constraints applied regardless of which image is used.
   - *failure behavior*: If the enforced non-root/read-only settings are incompatible with a custom image (e.g. it requires root), the container must fail to start with a clear error, not silently run with elevated privileges.

## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Some of what this company decided, it never got round to doing. The history holds designs that were agreed and then parked — "that's its own ticket", "when we get to it" — and parked is not cancelled. Where a decision was settled and the code does not reflect it yet, carrying it out is part of this ticket, not a reason to leave it alone.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- Wiki pages carry **comments**, and BookStack's search does not index them — a term that exists only in a comment returns nothing from `/api/search`. `/api/pages/{id}` returns that page's `comments` alongside its body, so a page worth reading is worth fetching whole.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
