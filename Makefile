.PHONY: install test lint run build mlflow-ui compose-up compose-down

lint:
	.venv/bin/flake8 app/ tests/

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

test:
	.venv/bin/pytest tests/

run:
	uvicorn app.main:app --reload

build:
	docker build -t datathon-skeleton .

mlflow-ui:
	mlflow ui --host 0.0.0.0 --port 5000

compose-up:
	docker-compose up -d

compose-down:
	docker-compose down
