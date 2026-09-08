# One thin layer on the world image.
#
# The base ref is spelled out INLINE. Do not reintroduce `ARG WORLD_IMAGE` +
# `FROM ${WORLD_IMAGE}`: Horizon rewrites FROM lines through its Docker Hub
# pull-through cache with a textual pass that cannot resolve an ARG, and the
# hosted build then dies trying to resolve a literal "${WORLD_IMAGE}".
#
# sweworld:0.4.7 is the same world with the corpus baked in: the repository and
# its history, and nine months of chat, wiki and mail. The remarks this task's
# requirements are hidden in are somewhere in there.
#
# 0.4.7 is 0.4.6 with g1's four planted mail threads rewritten to read like mail
# rather than like chat with a Subject line. Bodies only, edited in place in
# maddy's store so every UID, INTERNALDATE and flag survived -- re-appending over
# IMAP would have parked those 26 messages at the end of eight mailboxes, which
# in a task that measures whether an agent can FIND them is not cosmetic.
FROM sweworld:0.4.7

COPY --from=sweworld:repo-only-dev /opt/curator-dev /opt/curator-dev

# The world's services can boot slowly on a cold, shared host.
ENV WAIT_TIMEOUT=600

COPY setup.sh /usr/local/bin/task-setup.sh
RUN chmod 0755 /usr/local/bin/task-setup.sh

COPY --chmod=0755 task-entrypoint.sh /usr/local/bin/task-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/task-entrypoint.sh"]
