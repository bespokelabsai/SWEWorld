#!/bin/bash
# Boot the world as PID 1.
#
# Harbor appends `command: ["sh","-c","sleep infinity"]` to keep a plain image
# alive and exec the agent into it. This image's real init is supervisord, and
# Compose's `command:` overrides CMD rather than ENTRYPOINT — so those args
# would be handed to supervisord as positional arguments and the world would
# never boot. Ignore them and run supervisord in the foreground: it stays PID 1,
# reaping zombies and keeping the container alive, while the harness execs the
# agent and then the verifier in over `docker exec`.
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
