# One thin layer on the world image.
#
# The base ref is spelled out INLINE. Do not reintroduce `ARG WORLD_IMAGE` +
# `FROM ${WORLD_IMAGE}`: Horizon rewrites FROM lines through its Docker Hub
# pull-through cache with a textual pass that cannot resolve an ARG, and the
# hosted build then dies trying to resolve a literal "${WORLD_IMAGE}".
#
# sweworld:repo-only-dev is the world with the repository and its full history and
# nothing else — Mattermost, BookStack and mail are empty — plus the virtualenv
# an engineer needs to actually run curator. See harbor_tasks/_env/Dockerfile.
FROM us-central1-docker.pkg.dev/apex-485220/horizon/environments/sweworld-batch-payload-plan@sha256:f34db48366a6603074553d14986d5a58fb55abe8a71231321f838d90c1e6347f

# No `COPY --from=sweworld:repo-only-dev` — Horizon cannot resolve a second
# local tag either, so /opt/curator-dev is already inside the published image.

# tmux and asciinema are the terminal recording, not the trial: without them
# the run still grades and the only record of what the agent typed is gone.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tmux asciinema \
 && rm -rf /var/lib/apt/lists/*

# The terminal recorder. Harbor records the agent's session through tmux and
# asciinema, and neither is in the world image — so without this the trial still
# runs, still grades, and simply produces no transcript. That is the worst shape
# a missing dependency can take: every diagnosis of WHY an arm scored what it did
# has come from reading those recordings back. Unpinned deliberately; an exact
# version pin rots faster than the recorder's interface.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tmux asciinema \
 && rm -rf /var/lib/apt/lists/*

# The world's services can boot slowly on a cold, shared host.
ENV WAIT_TIMEOUT=600

COPY setup.sh /usr/local/bin/task-setup.sh
RUN chmod 0755 /usr/local/bin/task-setup.sh

# This task's plant, ingested by task-setup.sh once the world is up, instead of
# being baked into a per-task world image. `plant/` always exists and holds a
# README when there is nothing to plant: Harbor drops zero-byte files, and
# BuildKit then fails a COPY of a missing directory with "failed to calculate
# checksum of ref", which names no path and reads like a platform fault.
COPY plant /opt/task-plant

COPY --chmod=0755 task-entrypoint.sh /usr/local/bin/task-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/task-entrypoint.sh"]
