# =============================================================================
# SWEWorld — the company world as a single container image.
# =============================================================================
# supervisord is PID 1 (root) and owns every service as a native Linux process.
# No compose, no Docker-in-Docker, no Kubernetes. Follows the AlphaShop world
# pattern so both environments run the same way under the same harness.
#
#   docker build -f world/Dockerfile -t sweworld .
#   docker run -d --name sweworld -p 8080:80 sweworld
#
# Four collaboration tools, plain HTTP behind one nginx vhost ingress:
#   git.world.local   Gitea       (github)   SQLite
#   chat.world.local  Mattermost  (slack)    PostgreSQL
#   docs.world.local  BookStack   (notion)   MariaDB
#   mail.world.local  Roundcube over Maddy   SQLite
# =============================================================================
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG GITEA_VERSION=1.27.2
ARG ACT_RUNNER_VERSION=0.2.11
ARG MADDY_VERSION=0.9.5
ARG MATTERMOST_VERSION=11.9.1
ARG ROUNDCUBE_VERSION=1.7.3
ARG BOOKSTACK_VERSION=v25.11
ARG GO_VERSION=1.23.4
ARG NODE_VERSION=20.18.1

ENV LANG=C.UTF-8 \
    TZ=UTC \
    WORLD_DOMAIN=world.local \
    PATH=/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

# --- base packages -----------------------------------------------------------
# postgres for mattermost, mariadb for bookstack (each is the only database its
# service supports), php-fpm shared by bookstack and roundcube.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ca-certificates curl wget git unzip zstd xz-utils gnupg tzdata \
      supervisor nginx \
      postgresql postgresql-client \
      mariadb-server mariadb-client \
      php-fpm php-cli php-curl php-gd php-mbstring php-xml php-zip \
      php-mysql php-sqlite3 php-intl php-bcmath php-tidy php-ldap \
      composer sqlite3 \
      python3 python3-yaml python3-requests \
      rsync jq netcat-openbsd iproute2 procps less vim-tiny nano \
      build-essential; \
    rm -rf /var/lib/apt/lists/*

# --- world binaries ----------------------------------------------------------
RUN set -eux; \
    arch=amd64; \
    # gitea + act_runner (single static binaries)
    curl -fsSL -o /usr/local/bin/gitea \
      "https://dl.gitea.com/gitea/${GITEA_VERSION}/gitea-${GITEA_VERSION}-linux-${arch}"; \
    curl -fsSL -o /usr/local/bin/act_runner \
      "https://dl.gitea.com/act_runner/${ACT_RUNNER_VERSION}/act_runner-${ACT_RUNNER_VERSION}-linux-${arch}"; \
    chmod +x /usr/local/bin/gitea /usr/local/bin/act_runner; \
    # maddy
    curl -fsSL "https://github.com/foxcpp/maddy/releases/download/v${MADDY_VERSION}/maddy-${MADDY_VERSION}-x86_64-linux-musl.tar.zst" \
      | tar --zstd -C /tmp -x; \
    install -m755 /tmp/maddy-*/maddy /usr/local/bin/maddy; \
    rm -rf /tmp/maddy-*; \
    # mattermost
    curl -fsSL "https://releases.mattermost.com/${MATTERMOST_VERSION}/mattermost-team-${MATTERMOST_VERSION}-linux-amd64.tar.gz" \
      | tar -C /opt -xz; \
    # go toolchain — CI builds agent-authored services offline
    curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-${arch}.tar.gz" | tar -C /usr/local -xz; \
    # node: every JavaScript Action (actions/checkout included) is executed by
    # act_runner as `node dist/index.js`. Without it every workflow dies with
    # "Cannot find: node in PATH" after successfully resolving the action.
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
      | tar -C /usr/local --strip-components=1 -xJ

# --- roundcube (webmail over maddy's IMAP) -----------------------------------
RUN set -eux; \
    curl -fsSL "https://github.com/roundcube/roundcubemail/releases/download/${ROUNDCUBE_VERSION}/roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz" \
      | tar -C /opt -xz; \
    mv "/opt/roundcubemail-${ROUNDCUBE_VERSION}" /opt/roundcube

# --- bookstack (notion analogue) ---------------------------------------------
# Cloned + composer install at build time; the world runs offline afterwards.
RUN set -eux; \
    git clone --depth 1 --branch "${BOOKSTACK_VERSION}" \
      https://github.com/BookStackApp/BookStack.git /opt/bookstack; \
    cd /opt/bookstack; \
    COMPOSER_ALLOW_SUPERUSER=1 composer install --no-dev --no-interaction \
      --optimize-autoloader --no-progress

# --- world source ------------------------------------------------------------
COPY world/ /world-src/

# --- privilege model, users, directories -------------------------------------
RUN /world-src/bootstrap/00-users-dirs.sh

# --- datastores: init clusters, create databases ------------------------------
RUN /world-src/bootstrap/10-datastores.sh

# --- mail: maddy config + mailboxes -------------------------------------------
RUN /world-src/bootstrap/15-mail.sh

# --- gitea: install lock, admin, CI runner registration -----------------------
RUN /world-src/bootstrap/20-gitea.sh

# --- bookstack: env, key, schema ----------------------------------------------
RUN /world-src/bootstrap/25-bookstack.sh

# --- mattermost: config, admin, team ------------------------------------------
RUN /world-src/bootstrap/30-mattermost.sh

# --- ingress + supervisord ----------------------------------------------------
RUN set -eux; \
    rm -f /etc/nginx/sites-enabled/default; \
    install -m644 /world-src/nginx/sweworld.conf /etc/nginx/conf.d/sweworld.conf; \
    install -m644 /world-src/supervisord/supervisord.conf /etc/supervisor/supervisord.conf; \
    cp -a /world-src/supervisord/conf.d/. /etc/supervisor/conf.d/; \
    install -d -m755 /opt/world/passstore; \
    cp -a /world-src/passstore/. /opt/world/passstore/

# 80 = the whole world (nginx vhosts). Mail ports are direct: ingestion and
# desktop clients speak raw SMTP/IMAP, which nginx does not proxy.
EXPOSE 80 3300 7080 7090 7250 8065 25 143 587 993

HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=20 \
  CMD /usr/local/bin/wait-for-service --all --quiet || exit 1

ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
