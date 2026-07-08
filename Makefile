.PHONY: dev down logs

# Run environment
dev:
	docker-compose -f deploy/docker-compose.yml up --build

# Stop all containers
down:
	docker-compose -f deploy/docker-compose.yml down

# View logs
logs:
	docker-compose -f deploy/docker-compose.yml logs -f
