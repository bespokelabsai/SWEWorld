#!/usr/bin/env bash
# Build-time: users, directories, permissions. Encodes the privilege model.
#
#   ubuntu (1000)  the agent. No sudo, no supervisord, cannot write /opt/sweworld.
#   deploy (999)   the CI runner. Submits deploy requests; cannot deploy itself.
#   root           supervisord + deploy-daemon. The only thing that installs code.
#
# There is deliberately no sudoers entry: gVisor ignores setuid, so sudo cannot
# elevate anyway. Elevation happens through the root deploy-daemon + spool dir.
set -euo pipefail

# IDs are assigned by the system, not pinned: the apt install above gives gid
# 999 to systemd-journal, so `groupadd -g 999 deploy` fails. Nothing here
# depends on specific numbers — only on the users existing in the right groups.
getent group  deploy >/dev/null || groupadd --system deploy
getent passwd deploy >/dev/null || \
  useradd --system -g deploy -m -d /home/deploy -s /bin/bash deploy

id ubuntu >/dev/null 2>&1 || useradd -u 1000 -m -d /home/ubuntu -s /bin/bash ubuntu
# ubuntu:24.04 ships its default `ubuntu` user in the sudo group. The agent's
# model grants no sudo at all, so drop the stale membership. Not being a member
# is a fine outcome, hence the tolerated failure.
gpasswd -d ubuntu sudo >/dev/null 2>&1 || true

for u in svc worldsvc; do
  getent passwd "$u" >/dev/null || useradd --system -s /usr/sbin/nologin "$u"
done
# gitea rewrites ~/.ssh on every start even with SSH disabled, so it needs a
# home it actually owns. Point it at its data dir rather than a /home/gitea it
# has no permission to create.
getent passwd gitea >/dev/null || \
  useradd --system -d /var/lib/world/gitea -s /usr/sbin/nologin gitea

# Assert rather than assume. A swallowed useradd failure otherwise surfaces
# much later as a baffling `install: invalid user`.
for u in deploy ubuntu svc worldsvc gitea; do
  id "$u" >/dev/null 2>&1 || { echo "00-users-dirs: user '$u' was not created" >&2; exit 1; }
done

install -d -m 755 /opt/sweworld /opt/world /var/lib/world /var/lib/sweworld
install -d -m 755 -o deploy -g deploy /opt/sweworld/curator/releases
install -d -m 755 -o svc    -g svc    /var/lib/sweworld/curator

# Deploy spool. Group-writable by deploy so the runner can submit AND clear its
# own stale <svc>.result (the daemon writes those root-owned; without the group
# write a repeat deploy would read the previous result instantly instead of
# blocking). No bits for "other", so the agent cannot read or submit.
install -d -m 0770 -o root -g deploy /opt/sweworld/deploy-queue

install -d -m 755 -o gitea    -g gitea    /var/lib/world/gitea
install -d -m 755 -o deploy   -g deploy   /var/lib/world/act-runner
install -d -m 755 -o worldsvc -g worldsvc /var/lib/world/maddy /var/lib/world/mattermost \
                                          /var/lib/world/roundcube /var/lib/world/roundcube/temp \
                                          /var/lib/world/roundcube/logs
install -d -m 700 -o postgres -g postgres /var/lib/world/postgres
install -d -m 755 /var/lib/world/mysql

# Root-only world state: grader oracle, task scratch. The agent must not see it.
install -d -m 700 /opt/world-state

# Logs stay world-readable so the agent can triage its own service.
install -d -m 755 /var/log/supervisor

install -m 755 /world-src/bin/deploy-service   /usr/local/bin/deploy-service
install -m 755 /world-src/bin/deploy-daemon.sh /usr/local/bin/deploy-daemon.sh
install -m 755 /world-src/bin/request-deploy   /usr/local/bin/request-deploy
install -m 755 /world-src/bin/init-runtime.sh  /usr/local/bin/init-runtime.sh
install -m 755 /world-src/bin/wait-for-service /usr/local/bin/wait-for-service
install -m 755 /world-src/bin/world-verify    /usr/local/bin/world-verify
install -d -m 755 /usr/local/lib/sweworld
install -m 755 /world-src/config/curator-run.sh /usr/local/lib/sweworld/run-curator.sh

echo "00-users-dirs: OK"
