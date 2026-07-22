.PHONY: up down logs test lint import-data

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose run --rm backend pytest -q

test-coverage:
	docker compose run --rm backend \
  	pytest tests \
 	 --cov=app \
  	--cov-branch \
  	--cov-report=term-missing

lint:
	docker compose run --rm backend ruff check app tests

import-data:
	docker compose run --rm -e PYTHONPATH=/app  backend python scripts/load_csv.py /data

