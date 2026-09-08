# What gets published to Horizon's Artifact Registry as the world.
#
# `horizon artifacts environment push --dockerfile <this>` builds it against the
# LOCAL docker daemon and uploads the result, which is how a tag that exists only
# on this box reaches a registry Horizon can pull from.
#
# It copies nothing from the build context, and that is the point. The CLI builds
# from `git archive HEAD` — a clean checkout of the repo ROOT — so a `COPY
# setup.sh` written for a task's own `environment/` directory resolves against
# the repo root instead and the build dies with
#
#     failed to compute cache key: "/task-entrypoint.sh": not found
#
# which reads like a missing file and is really a wrong build context. Pointing
# the publish at a task's local-twin Dockerfile fails exactly that way.
#
# Nothing task-specific belongs here anyway. The published image is the COMPANY:
# the repository and its history, nine months of chat, the wiki and the
# mailboxes, plus the venv the tasks execute in. Each hosted arm's own Dockerfile
# does `FROM <this, by digest>` and adds its own `setup.sh`, `task-entrypoint.sh`
# and — for the tasks that plant at run time — its `plant/`. That is why one
# published environment serves every task and a second task needs no second
# publish.
#
# Both refs are spelled out INLINE. Do not reintroduce `ARG WORLD_IMAGE`:
# Horizon rewrites FROM lines through its pull-through cache with a textual pass
# that cannot resolve an ARG.
#
# Bump the tag here when a new world is baked, publish, and paste the
# `image_reference` the push prints into the pinning arm's `FROM`. The pin is by
# DIGEST because the corpus is the independent variable in these tasks — a moved
# tag would change what a task measures without changing the task.
FROM sweworld:0.4.8

COPY --from=sweworld:repo-only-dev /opt/curator-dev /opt/curator-dev
