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
# 0.4.1 = 0.4.0 with the admin account joined to every chat channel.
# Mattermost search is member-scoped and the admin was in the two empty
# channels only, so `search "structured output"` returned 0 against a
# 9,593-message corpus. Trials read that as "there is no chat here".
FROM sweworld:0.4.1

# The populated world is a RELEASE bake and carries no dev virtualenv, while
# the verifier runs pytest with `$CURATOR_VENV/bin/python`. Without this the
# suite never runs at all: every fact scores zero and `suite_error` fires,
# which reads exactly like an agent that failed everything.
COPY --from=sweworld:repo-only-dev /opt/curator-dev /opt/curator-dev

# The world's services can boot slowly on a cold, shared host.
ENV WAIT_TIMEOUT=600

COPY setup.sh /usr/local/bin/task-setup.sh
RUN chmod 0755 /usr/local/bin/task-setup.sh

COPY --chmod=0755 task-entrypoint.sh /usr/local/bin/task-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/task-entrypoint.sh"]
