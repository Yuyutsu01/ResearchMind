.PHONY: dev down logs

# Modern Docker Compose CLI (Docker v2+)
DOCKER_COMPOSE ?= docker compose

# Run environment
dev:
	$(DOCKER_COMPOSE) -f deploy/docker-compose.yml up --build

# Stop all containers
down:
	$(DOCKER_COMPOSE) -f deploy/docker-compose.yml down

# View logs
logs:
	$(DOCKER_COMPOSE) -f deploy/docker-compose.yml logs -f
