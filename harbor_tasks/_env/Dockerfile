# sweworld:repo-only-dev — the world an engineer can actually work in.
#
# Base is sweworld:0.3.1-forge, which is already exactly the environment these
# tasks want: worldadmin/curator carries the real history (85.8MB of objects,
# 461 pull requests, 275 issues, 29 releases in gitea.db) while Mattermost's
# Postgres and BookStack's MariaDB are byte-identical to the empty `dev` image
# and maddy holds nothing. Repository and history, no corpus.
#
# The ref is spelled out INLINE on purpose. Do not reintroduce
# `ARG WORLD_IMAGE` + `FROM ${WORLD_IMAGE}`: Horizon rewrites FROM lines through
# a pull-through cache with a TEXTUAL pass that cannot resolve an ARG, and the
# hosted build then dies resolving a literal "${WORLD_IMAGE}".
FROM sweworld:0.3.1-forge

# One venv, shared by the engineer and the verifier.
#
# The world image ships python3, python3-yaml and python3-requests and nothing
# else — no pip, no pydantic, no datasets, no pytest. Without this every task
# here is "write code you can never execute": the agent cannot run curator, and
# the CI step `python3 -m pytest -q tests || true` in world/ci-templates/python.yml
# is a permanent no-op that reports success.
#
# curator itself is deliberately NOT left installed. `src/bespokelabs/__init__.py`
# is a regular package, so an installed copy would shadow whatever the agent
# wrote and every test would grade the vendored snapshot instead of the
# submission. Installing the wheel and then removing just the package is how we
# get its exact dependency closure without keeping the package.
RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3-venv python3-pip; \
    rm -rf /var/lib/apt/lists/*; \
    python3 -m venv /opt/curator-dev/venv; \
    /opt/curator-dev/venv/bin/pip install --no-cache-dir --upgrade pip wheel; \
    /opt/curator-dev/venv/bin/pip install --no-cache-dir bespokelabs-curator==0.1.29; \
    /opt/curator-dev/venv/bin/pip uninstall -y bespokelabs-curator; \
    /opt/curator-dev/venv/bin/pip install --no-cache-dir \
        pytest pytest-asyncio pytest-timeout pytest-json-ctrf==0.3.5; \
    chmod -R a+rX /opt/curator-dev

# Both halves of the world find it the same way.
ENV CURATOR_VENV=/opt/curator-dev/venv
