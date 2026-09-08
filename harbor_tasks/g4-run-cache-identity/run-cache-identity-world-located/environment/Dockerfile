# One thin layer on the world image.
#
# The base ref is spelled out INLINE. Do not reintroduce `ARG WORLD_IMAGE` +
# `FROM ${WORLD_IMAGE}`: Horizon rewrites FROM lines through its Docker Hub
# pull-through cache with a textual pass that cannot resolve an ARG, and the
# hosted build then dies trying to resolve a literal "${WORLD_IMAGE}".
#
# sweworld:0.4.4 is the same world with the corpus baked in: the repository and
# its history, and nine months of chat, wiki and mail. The remarks this task's
# requirements are hidden in are somewhere in there.
FROM sweworld:0.4.4

COPY --from=sweworld:repo-only-dev /opt/curator-dev /opt/curator-dev

# The terminal recorder. Harbor records the agent's session through tmux and
# asciinema, and neither is in the world image — so without this the trial still
# runs, still grades, and simply produces no transcript. That is the worst shape
# a missing dependency can take: every diagnosis of WHY an arm scored what it did
# has come from reading those recordings back. Unpinned deliberately; an exact
# version pin rots faster than the recorder's interface.
# archive.ubuntu.com and security.ubuntu.com both went unreachable from GCP on
# 2026-09-05 -- 22s for the first fetch and then nothing -- and took three local
# g6 trials and a hosted validation down with them. Neither mirror FAILED; they
# hung, so no timeout helped and the failures read as task defects. The
# GCE-local mirror answers both pockets in under 15ms from this box and from
# Horizon's builders, which are in the same region.
RUN sed -i \
      -e 's|http://archive\.ubuntu\.com|http://us-central1.gce.archive.ubuntu.com|g' \
      -e 's|http://security\.ubuntu\.com|http://us-central1.gce.archive.ubuntu.com|g' \
      /etc/apt/sources.list /etc/apt/sources.list.d/*.sources \
      /etc/apt/sources.list.d/*.list 2>/dev/null; \
    printf 'Acquire::Retries "2";\nAcquire::http::Timeout "20";\n' \
      > /etc/apt/apt.conf.d/99-world-timeouts

# NOT fatal, and that is the point. The recorder is how a run gets diagnosed, not
# how it gets measured: the trial trains, grades and reports without it. A mirror
# outage was able to fail the whole build, which is the wrong failure for a
# diagnostic aid to cause. It says so loudly and the build continues.
RUN apt-get update \
 && apt-get install -y --no-install-recommends tmux asciinema \
 && rm -rf /var/lib/apt/lists/* \
 || echo "WARNING: tmux/asciinema unavailable -- the trial will grade but record nothing"

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
