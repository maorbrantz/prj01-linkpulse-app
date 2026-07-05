.PHONY: help venv test test-api test-worker build run-local stop-local logs clean

VENV := .venv
ifeq ($(OS),Windows_NT)
	PY := $(VENV)/Scripts/python.exe
else
	PY := $(VENV)/bin/python
endif

help:
	@echo "targets: venv test build run-local stop-local logs clean"

venv:
	python -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r services/api/requirements-dev.txt
	$(PY) -m pip install -r services/worker/requirements-dev.txt

test: test-api test-worker

test-api:
	cd services/api && ../../$(PY) -m pytest

test-worker:
	cd services/worker && ../../$(PY) -m pytest

build:
	docker build -t linkpulse-api:local services/api
	docker build -t linkpulse-worker:local services/worker
	docker build -t linkpulse-web:local services/web

run-local:
	docker compose up --build

stop-local:
	docker compose down -v

logs:
	docker compose logs -f

clean:
	docker compose down -v --remove-orphans
