.PHONY: dev prod down logs

# Run development environment
dev:
	docker-compose -f deploy/docker/docker-compose.dev.yml up --build

# Run production environment
prod:
	docker-compose -f deploy/docker/docker-compose.prod.yml up --build -d

# Stop all containers
down:
	docker-compose -f deploy/docker/docker-compose.dev.yml down
	docker-compose -f deploy/docker/docker-compose.prod.yml down

# View logs for production
logs:
	docker-compose -f deploy/docker/docker-compose.prod.yml logs -f
