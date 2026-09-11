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

# The recorder install lives in the shared template below. It used to be
# repeated here too, so every hosted image ran apt twice — which doubled
# the exposure the night both Ubuntu mirrors went unreachable.


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

# `$CURATOR_VENV` -- which this task's ticket tells the agent to use, by name.
# It is an ENV on sweworld:repo-only-dev, and both world arms reach that virtualenv
# through `COPY --from=...`, which copies FILES and not the source image's ENV.
# So on the world arms the variable is empty and `$CURATOR_VENV/bin/python`
# expands to `/bin/python`. Five of ten rollouts in one g6 evaluation noticed and
# fell back to the literal path the ticket also prints; for the other five the
# ticket was simply wrong. Declared here, in the shared body, rather than in each
# of the two arms that lose it -- on the arms that inherit it this restates what
# is already true and costs nothing.
ENV CURATOR_VENV=/opt/curator-dev/venv

# curator's own tests/conftest.py does `import vcr` at module scope, and the venv
# holds curator's RUNTIME dependency closure plus pytest -- not its dev extras.
# So `$CURATOR_VENV/bin/pytest tests/` dies at COLLECTION for the whole tree,
# which the same ticket promises will "run the library and its tests". Nine of
# ten rollouts in one g6 evaluation hit it, and one spent about fifteen turns
# writing a fake `vcr` module and then re-running the suite on unmodified main to
# convince itself the fallout was not its own. psutil is the same shape one file
# further in (tests/unittests/test_online_vllm.py).
#
# Pinned, unlike the recorder above: this decides whether a test tree COLLECTS,
# so a new major landing under a rebuild would break the agent's feedback loop
# with no error that names the cause. Measured on the pristine tree with these
# two present: tests/unittests is 47 passed, 17 skipped, 5 errors. The 5 are
# test_caching.py against this vcrpy and are there before an agent touches
# anything -- an honest baseline, not a green one.
RUN /opt/curator-dev/venv/bin/pip install --no-cache-dir vcrpy==8.3.0 psutil==7.2.2 \
 || echo "WARNING: vcrpy/psutil unavailable -- curator's own tests will not collect"

# The world's services can boot slowly on a cold, shared host.
ENV WAIT_TIMEOUT=600

COPY setup.sh /usr/local/bin/task-setup.sh
RUN chmod 0755 /usr/local/bin/task-setup.sh

# This task's plant, ingested by task-setup.sh once the world is up, instead of
# being baked into a per-task world image. `plant/` always exists and holds a
# README when there is nothing to plant: Harbor drops zero-byte files, and
# BuildKit then fails a COPY of a missing directory with "failed to calculate
# checksum of ref", which names no path and reads like a platform fault.
# 0700, because this directory IS the answer key to a discovery task. At COPY's
# default 0755 the agent reads the planted corpus straight off local disk --
# every chat remark, every page comment, every mail -- and skips the whole
# exercise the task exists to measure. A g2 rollout already printed the listing
# from `ls /opt/*`, sitting at drwxr-xr-x beside world-state's drwx------. The
# ingest is unaffected: it runs as root from the healthcheck.
COPY --chmod=0700 plant /opt/task-plant

COPY --chmod=0755 task-entrypoint.sh /usr/local/bin/task-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/task-entrypoint.sh"]
