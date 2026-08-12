.PHONY: up down logs test coverage lint import-data dbt-profile dbt-deps dbt-build \
	live-tracking live-tracking-down kafka-topics kafka-consume kafka-test \
	venv venv-test venv-lint venv-import-data venv-dbt-debug venv-dbt-build

VENV ?= .venv
VENV_BIN := $(VENV)/bin
LOCAL_DATABASE_URL ?= postgresql+psycopg://volteras:volteras@localhost:5432/volteras

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

live-tracking:
	docker compose --profile live-tracking up --build

live-tracking-down:
	docker compose --profile live-tracking down

kafka-topics:
	docker compose --profile live-tracking exec kafka kafka-topics.sh \
		--bootstrap-server kafka:9092 --list

kafka-consume:
	docker compose --profile live-tracking exec kafka kafka-console-consumer.sh \
		--bootstrap-server kafka:9092 --topic vehicle.location.current.v1 --from-beginning

kafka-test:
	docker compose build location-processor
	docker compose run --rm --no-deps location-processor python -m pytest -q tests

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

dbt-profile:
	@test -f analytics/dbt/profiles.yml || \
		cp analytics/dbt/profiles.example.yml analytics/dbt/profiles.yml

dbt-deps: dbt-profile
	cd analytics/dbt && dbt deps --profiles-dir .

dbt-build: dbt-profile
	cd analytics/dbt && dbt build --profiles-dir .

venv:
	python3 -m venv $(VENV)
	$(VENV_BIN)/python -m pip install -r requirements-venv.txt

venv-test:
	cd backend && ../$(VENV_BIN)/python -m pytest -q

venv-lint:
	cd backend && ../$(VENV_BIN)/ruff check app tests

venv-import-data:
	cd backend && DATABASE_URL=$(LOCAL_DATABASE_URL) ../$(VENV_BIN)/python scripts/load_csv.py ../sample_data

venv-dbt-debug: dbt-profile
	cd analytics/dbt && ../../$(VENV_BIN)/dbt debug --profiles-dir .

venv-dbt-build: dbt-profile
	cd analytics/dbt && ../../$(VENV_BIN)/dbt build --profiles-dir .
