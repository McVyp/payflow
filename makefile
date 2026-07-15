.PHONY: up down clean logs ps help

up: ## build and start all services
	docker compose up --build -d
	@echo "Frontend: http://localhost:5173"
	@echo "Producer API: http://localhost:4000"
	@echo "Consumer API: http://localhost:4001"

down: ## stop containers, keep DB volume
	docker compose down

clean: ## stop containers and wipe volumes + local images
	docker compose down -v --rmi local

logs: ## tail logs from all services
	docker compose logs -f

ps: ## show running containers
	docker compose ps

kill-broker-1: ## kill kafka1 to watch ISR shrink / leader election live
	docker compose stop kafka1

restart-broker-1: ## bring kafka1 back
	docker compose start kafka1

kill-broker-2: ## kill kafka2
	docker compose stop kafka2

restart-broker-2: ## bring kafka2 back
	docker compose start kafka2

kill-broker-3: ## kill kafka3
	docker compose stop kafka3

restart-broker-3: ## bring kafka3 back
	docker compose start kafka3

help: ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'