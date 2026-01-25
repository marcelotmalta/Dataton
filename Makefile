.PHONY: install test lint run build

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest -q

run:
	uvicorn app.main:app --reload

build:
	docker build -t datathon-skeleton .
