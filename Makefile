.PHONY: up down logs test coverage lint import-data dbt-deps dbt-build

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose run --rm backend pytest -q

coverage:
	docker compose run --rm backend \
  	pytest tests \
 	 --cov=app \
  	--cov-branch \
  	--cov-report=term-missing

lint:
	docker compose run --rm backend ruff check app tests

import-data:
	docker compose run --rm -e PYTHONPATH=/app  backend python scripts/load_csv.py /data

dbt-deps:
	cd analytics/dbt && dbt deps --profiles-dir .

dbt-build:
	cd analytics/dbt && dbt build --profiles-dir .
