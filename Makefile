# =============================================================================
# SWEWorld — build, populate and publish the world image.
# =============================================================================
# Build is separate from populate is separate from publish, deliberately: you
# should never push something you did not intend to.
#
#   make build-image              base image: services installed, world empty
#   make run                      boot it and publish every service
#   make bake-image TAG=0.1.0     boot base, ingest data/, verify, commit
#   make push-image TAG=0.1.0     tag into the registry and push (manual)
# =============================================================================
SHELL := /bin/bash

IMAGE     ?= sweworld
REGISTRY  ?=
TAG       ?=
CONTAINER ?= sweworld
HTTP_PORT ?= 8081
# The hostname you will browse the world with. `localhost` is right when you are
# on the machine running docker, or forwarding its ports (VS Code Remote / ssh
# -L). Every app's public base URL is repointed at it on boot — see
# world/bin/init-runtime.sh for why that is necessary.
PUBLIC_HOST ?= localhost

# Published host ports, deliberately identical to the container-internal ones:
# an app that redirects to :PORT must reach the same service inside and out.
# 8080/8090 are avoided because they collide on most dev machines, and a
# forwarded port that collides gets silently remapped to another one.
GITEA_PORT     ?= 3300
MM_PORT        ?= 8065
BOOKSTACK_PORT ?= 7090
ROUNDCUBE_PORT ?= 7080
PASS_PORT      ?= 7250

# Bake boots the base image, populates it, then commits the result.
RELEASE_SOURCE    ?= $(IMAGE):dev
RELEASE_CONTAINER ?= sweworld-bake
# runc for the bake: docker commit cannot capture a gVisor container's writes.
# The published image still RUNS under gVisor; runc is only how it is produced.
RELEASE_RUNTIME   ?= runc

.PHONY: help build-image run stop logs shell verify bake-image push-image clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

build-image: ## Build the base world image (services installed, no generated content)
	docker build -f world/Dockerfile -t $(IMAGE):dev .

run: ## Boot the world and publish every service so you can browse it
	-docker rm -f $(CONTAINER) >/dev/null 2>&1
	docker run -d --name $(CONTAINER) \
	  -e PUBLIC_HOST=$(PUBLIC_HOST) \
	  -e PUBLIC_GITEA_PORT=$(GITEA_PORT) -e PUBLIC_MM_PORT=$(MM_PORT) \
	  -e PUBLIC_BOOKSTACK_PORT=$(BOOKSTACK_PORT) \
	  -e PUBLIC_ROUNDCUBE_PORT=$(ROUNDCUBE_PORT) -e PUBLIC_PASS_PORT=$(PASS_PORT) \
	  -p $(HTTP_PORT):80 \
	  -p $(GITEA_PORT):3300 -p $(MM_PORT):8065 \
	  -p $(BOOKSTACK_PORT):7090 -p $(ROUNDCUBE_PORT):7080 -p $(PASS_PORT):7250 \
	  -p 2525:25 -p 1143:143 -p 1587:587 \
	  $(IMAGE):dev
	@echo ">> waiting for the world to come up..."
	@docker exec $(CONTAINER) wait-for-service --all
	@echo
	@echo "   Browse the world at:"
	@echo "     Gitea       http://$(PUBLIC_HOST):$(GITEA_PORT)"
	@echo "     Mattermost  http://$(PUBLIC_HOST):$(MM_PORT)"
	@echo "     BookStack   http://$(PUBLIC_HOST):$(BOOKSTACK_PORT)"
	@echo "     Roundcube   http://$(PUBLIC_HOST):$(ROUNDCUBE_PORT)"
	@echo "     Credentials http://$(PUBLIC_HOST):$(PASS_PORT)"
	@echo
	@echo "   Sign in as worldadmin / worldadmin"
	@echo "   (BookStack and Roundcube want the email: worldadmin@world.local)"

stop: ## Stop and remove the running world
	-docker rm -f $(CONTAINER)

logs: ## Tail every supervised service's log
	docker exec $(CONTAINER) bash -c 'tail -n 40 -F /var/log/supervisor/*.log'

shell: ## Shell into the world as the agent (ubuntu, no sudo)
	docker exec -it -u ubuntu -w /home/ubuntu $(CONTAINER) bash

verify: ## Run the acceptance checks against the running world
	docker exec $(CONTAINER) wait-for-service --all
	docker exec $(CONTAINER) /usr/local/bin/world-verify

bake-image: ## Boot base, ingest data/, gate on verify, commit $(IMAGE):TAG
	@test -n "$(TAG)" || { echo "!! bake-image: TAG is required, e.g. make bake-image TAG=0.1.0"; exit 1; }
	@echo ">> [bake] TAG=$(TAG) SOURCE=$(RELEASE_SOURCE) RUNTIME=$(RELEASE_RUNTIME)"
	-docker rm -f $(RELEASE_CONTAINER) >/dev/null 2>&1
	docker run -d --runtime=$(RELEASE_RUNTIME) --name $(RELEASE_CONTAINER) $(RELEASE_SOURCE)
	@echo ">> [bake] waiting for every tier..."
	docker exec $(RELEASE_CONTAINER) wait-for-service --all
	@echo ">> [bake] ingesting data/ into the world..."
	docker cp data $(RELEASE_CONTAINER):/opt/world-state/data
	docker cp scripts $(RELEASE_CONTAINER):/opt/world-state/scripts
	docker exec $(RELEASE_CONTAINER) bash -c 'cd /opt/world-state && \
	  python3 scripts/ingest_git.py  --data-dir data && \
	  python3 scripts/ingest_docs.py --data-dir data && \
	  python3 scripts/ingest_comments.py --data-dir data && \
	  python3 scripts/ingest_chat.py --data-dir data && \
	  python3 scripts/ingest_mail.py --data-dir data'
	@echo ">> [bake] GATE: verifying the populated world..."
	docker exec $(RELEASE_CONTAINER) /usr/local/bin/world-verify
	@echo ">> [bake] gate PASSED -> stopping services and committing $(IMAGE):$(TAG)"
	docker exec $(RELEASE_CONTAINER) bash -c 'supervisorctl -c /etc/supervisor/supervisord.conf stop all || true'
	docker commit $(RELEASE_CONTAINER) $(IMAGE):$(TAG)
	-docker rm -f $(RELEASE_CONTAINER)
	@echo ">> [bake] committed $(IMAGE):$(TAG) — not published."

push-image: ## Tag $(IMAGE):TAG into $(REGISTRY) and push (deliberate, manual)
	@test -n "$(TAG)"      || { echo "!! push-image: TAG is required"; exit 1; }
	@test -n "$(REGISTRY)" || { echo "!! push-image: REGISTRY is required"; exit 1; }
	docker tag $(IMAGE):$(TAG) $(REGISTRY)/$(IMAGE):$(TAG)
	docker push $(REGISTRY)/$(IMAGE):$(TAG)

clean: ## Remove local world images and containers
	-docker rm -f $(CONTAINER) $(RELEASE_CONTAINER) 2>/dev/null
	-docker rmi $(IMAGE):dev 2>/dev/null
