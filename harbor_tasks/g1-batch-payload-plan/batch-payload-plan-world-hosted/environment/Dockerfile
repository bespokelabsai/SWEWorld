# The hosted twin of batch-payload-plan-world.
#
# Identical task, identical corpus; the only difference is where the world image
# comes from. Locally that is `sweworld:0.4.8` in the daemon. Horizon has no such
# tag, so the world is published to the Artifact Registry first
# (`horizon artifacts environment push sweworld-batch-payload-plan --dockerfile
# harbor_tasks/_env/world-registry.Dockerfile`) and pulled from there by digest.
# That push prints the digest below; do not point it at a task's own
# environment/Dockerfile, which cannot resolve its COPYs from the repo root.
#
# Pinned by DIGEST, not by tag. The corpus is the independent variable in this
# task — the requirements are hidden in it — so a re-push that quietly moved a
# tag would change what the task measures without changing the task.
#
# The base ref is spelled out INLINE. Do not reintroduce `ARG WORLD_IMAGE` +
# `FROM ${WORLD_IMAGE}`: Horizon rewrites FROM lines through its pull-through
# cache with a textual pass that cannot resolve an ARG, and the hosted build then
# dies trying to resolve a literal "${WORLD_IMAGE}".
#
# No `COPY --from=sweworld:repo-only-dev` here — unlike the local twin, this
# image already carries /opt/curator-dev, because Horizon cannot resolve a second
# local-only tag either.
FROM us-central1-docker.pkg.dev/apex-485220/horizon/environments/sweworld-batch-payload-plan@sha256:ed68222934576dd9dcafc85659cfa50a356afcb728f4e5ce6137d6f271118f31

# tmux and asciinema are the terminal recording, not the trial: without them the
# run still grades, and the only record of what the agent actually typed is gone.
# Diagnosing why an arm scored what it did has meant reading those transcripts
# every time, so a missing recorder costs the next investigation, not this one.
# Unpinned deliberately — an exact version pin rots faster than the recorder API.
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

RUN apt-get update \
 && apt-get install -y --no-install-recommends tmux asciinema \
 && rm -rf /var/lib/apt/lists/* \
 || echo "WARNING: tmux/asciinema unavailable -- the trial will grade but record nothing"

# The world's services can boot slowly on a cold, shared host.
ENV WAIT_TIMEOUT=600

COPY setup.sh /usr/local/bin/task-setup.sh
RUN chmod 0755 /usr/local/bin/task-setup.sh

COPY --chmod=0755 task-entrypoint.sh /usr/local/bin/task-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/task-entrypoint.sh"]
