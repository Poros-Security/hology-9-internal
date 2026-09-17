.PHONY: up down ps test solve package

HOST ?= 127.0.0.1
PORT ?= 1337

up:
	SUI5G_PORT=$(PORT) docker compose up -d --build --wait

down:
	docker compose down

ps:
	docker compose ps

test:
	python3 -m unittest discover -s tests -v

solve:
	python3 solver/solve.py --host $(HOST) --port $(PORT)

package:
	tar --exclude='__pycache__' -czf /tmp/sui5g-import.tar.gz challenge.yml src dist solver tests Makefile compose.yml README.md VERIFICATION.md
