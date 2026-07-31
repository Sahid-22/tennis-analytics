.PHONY: install dev test lint format typecheck run docker-build docker-run clean

install:
	pip install -r requirements.txt

dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v --cov=tennis_analytics --cov-report=term-missing

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

typecheck:
	mypy tennis_analytics/ --ignore-missing-imports

run:
	python -m streamlit run app.py

refresh:
	python scripts/refresh_data.py

quality:
	python scripts/run_quality_checks.py

docker-build:
	docker build -t tennis-analytics .

docker-run:
	docker run -p 8501:8501 --env-file .env tennis-analytics

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	rm -rf htmlcov .coverage dist *.egg-info .mypy_cache .ruff_cache
