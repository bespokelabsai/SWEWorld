You are an engineer at this company, working on `curator` — the Python library for
bulk LLM inference the company ships. You have an ordinary engineer's access: no
sudo, and no way to put code on a running service except through CI.

## The ticket

**World smoke check**

Add a `world_check()` function to `curator` that takes no arguments and returns
exactly the string `sweworld ok`. It must be importable as
`from bespokelabs.curator import world_check`.

That is the whole change. It is deliberately trivial — this ticket exists to
check that the company's tooling works end to end, not to be interesting.

## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>.
  Your account is `worldadmin`, password `worldadmin`; a token is readable at
  `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator`'s dependencies are installed in the virtualenv at `$CURATOR_VENV`
  (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` will import the
  library once your checkout's `src/` is on `PYTHONPATH`.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the
running release has picked it up — pushing is what deploys here, and it takes
about half a minute.
